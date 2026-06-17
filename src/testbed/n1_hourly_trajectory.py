"""
N-1 Seam Contingency Severity -- Hourly Trajectory
=================================================================
Extends n1_seam_contingency_sweep.py (which covers exactly 3 hours:
peak/median/min) to ~60 hours spanning the FULL range of the real
annual load profile, sampled by load PERCENTILE (not calendar-evenly),
so the sample directly covers the stress spectrum rather than whatever
the calendar happens to produce.

Purpose (per the lighter-path decision): does N-1 severity (Delta1,
the only operator a static snapshot can legitimately support -- see
n1_seam_contingency_sweep.py's docstring for why Delta2/tau_half/R are
NOT computed here either) track system load in a sensible way across
many real operating points, not just 3? This is a quasi-steady-state
stress trajectory, NOT a rupture/cascade simulation -- there is still
no fault, no time axis after an event, no dynamics. It only tests
whether the severity metric responds sensibly as the system approaches
real higher-stress conditions throughout the year.

Same load/gen scaling, same seam-branch set, same coherence/stress
reference baseline (from the existing annual_voltage_series.npz) as
the 3-point sweep, for direct comparability.

Resumable: saves a checkpoint after each hour so an interruption doesn't
lose completed work.
"""

import os
import sys
import time
import numpy as np
np.in1d = np.isin  # numpy 2.x compat shim required by this pypower version

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from activsg2000_loader import load_case
from activsg2000_powerflow import case_to_ppc
from pypower.api import runpf, ppoption
from n1_seam_contingency_sweep import (
    build_reference_baseline, build_scaled_ppc, coherence_stress_for_snapshot,
    per_pair_coherence, BUS_PD_COL, BUS_AREA_COL, BR_STATUS_COL,
)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
OPT = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)

N_HOURS_SAMPLE = 60
CHECKPOINT_PATH = os.path.join(OUT_DIR, 'n1_hourly_trajectory_checkpoint.csv')
FINAL_PATH = os.path.join(OUT_DIR, 'n1_hourly_trajectory.csv')


def select_hours_by_load_percentile(yr, n_sample):
    """Sort all 8784 hours by system load, take evenly-spaced indices across
    the sorted order. This samples the full stress spectrum directly,
    rather than relying on the calendar to happen to cover it."""
    yr_sorted = yr.sort_values('system_total').reset_index(drop=True)
    idx = np.linspace(0, len(yr_sorted) - 1, n_sample).round().astype(int)
    idx = sorted(set(idx))  # de-dup in case of rounding collisions
    return yr_sorted.loc[idx, 'hour'].astype(int).tolist()


def main():
    t_start = time.time()
    cf = load_case()
    base_ppc = case_to_ppc(cf)
    bus0 = base_ppc['bus']
    area_of_bus = bus0[:, BUS_AREA_COL].astype(int)
    area_masks = {a: (area_of_bus == a) for a in range(1, 9)}
    basecase_area_total = {a: bus0[area_masks[a], BUS_PD_COL].sum() for a in range(1, 9)}
    basecase_system_total = bus0[:, BUS_PD_COL].sum()

    yr = pd.read_csv(os.path.join(DATA_DIR, 'activsg2000_area_load_8784h.csv'))
    load_cols = [f'area_{a}' for a in range(1, 9)]
    yr['system_total'] = yr[load_cols].sum(axis=1)

    Vbar, bus_idx, pairs, sigma = build_reference_baseline(cf)
    print(f"Reference baseline built from annual series ({len(pairs)} seam pairs).")

    branch = cf.branch[cf.branch['BR_STATUS'] == 1].copy()
    branch['orig_pos'] = np.arange(len(cf.branch))[cf.branch['BR_STATUS'].to_numpy() == 1]
    area_map = dict(zip(cf.bus['BUS_I'].astype(float), cf.bus['BUS_AREA'].astype(int)))
    branch['AF'] = branch['F_BUS'].map(area_map)
    branch['AT'] = branch['T_BUS'].map(area_map)
    seam_branches = branch[branch['AF'] != branch['AT']].reset_index(drop=True)
    print(f"{len(seam_branches)} seam branches per hour.")

    target_hours = select_hours_by_load_percentile(yr, N_HOURS_SAMPLE)
    print(f"Selected {len(target_hours)} hours spanning the load percentile range.")

    if os.path.exists(CHECKPOINT_PATH):
        done_df = pd.read_csv(CHECKPOINT_PATH)
        all_results = done_df.to_dict('records')
        done_hours = set(done_df['hour'].unique())
        print(f"Resuming: {len(done_hours)} hours already done.")
    else:
        all_results = []
        done_hours = set()

    remaining = [h for h in target_hours if h not in done_hours]
    print(f"{len(remaining)} hours remaining to compute.")

    max_this_run = int(os.environ.get('N1_MAX_HOURS_THIS_RUN', len(remaining)))
    remaining = remaining[:max_this_run]
    print(f"Processing {len(remaining)} hours this invocation (cap={max_this_run}).")

    for i, hour in enumerate(remaining):
        hour_row = yr[yr['hour'] == hour].iloc[0]
        bus_t, gen_t = build_scaled_ppc(base_ppc, area_masks, basecase_area_total,
                                         basecase_system_total, hour_row, load_cols)
        ppc_base = {**base_ppc, 'bus': bus_t, 'gen': gen_t}
        result0, success0 = runpf(ppc_base, OPT)
        if not success0:
            print(f"  hour {hour}: N-0 baseline failed to converge -- skipping")
            continue
        vm0 = result0['bus'][:, 7]
        C0, S0 = coherence_stress_for_snapshot(vm0, Vbar, bus_idx, pairs, sigma)

        n_fail = 0
        for ridx, row in seam_branches.iterrows():
            branch_t = base_ppc['branch'].copy()
            branch_t[int(row['orig_pos']), BR_STATUS_COL] = 0
            ppc_t = {**base_ppc, 'bus': bus_t, 'gen': gen_t, 'branch': branch_t}
            result, success = runpf(ppc_t, OPT)

            rec = {
                'hour': hour, 'system_load_mw': hour_row['system_total'],
                'branch_idx': int(row['orig_pos']), 'f_bus': row['F_BUS'], 't_bus': row['T_BUS'],
                'area_f': int(row['AF']), 'area_t': int(row['AT']), 'converged': bool(success),
            }
            if success:
                vm1 = result['bus'][:, 7]
                C1, S1 = coherence_stress_for_snapshot(vm1, Vbar, bus_idx, pairs, sigma)
                rec.update({
                    'coherence_pre': C0, 'coherence_post': C1, 'delta1_coherence': C1 - C0,
                    'stress_pre': S0, 'stress_post': S1, 'delta1_stress': S1 - S0,
                    'vmin_post': vm1.min(), 'vmax_post': vm1.max(),
                })
            else:
                n_fail += 1
                rec.update({k: np.nan for k in [
                    'coherence_pre', 'coherence_post', 'delta1_coherence', 'stress_pre', 'stress_post',
                    'delta1_stress', 'vmin_post', 'vmax_post']})
            all_results.append(rec)

        pd.DataFrame(all_results).to_csv(CHECKPOINT_PATH, index=False)
        elapsed = time.time() - t_start
        print(f"  [{i+1}/{len(remaining)}] hour {hour} (load {hour_row['system_total']:.0f} MW): "
              f"{len(seam_branches)-n_fail}/{len(seam_branches)} converged "
              f"({elapsed:.0f}s elapsed)")

    results_df = pd.DataFrame(all_results)
    results_df.to_csv(FINAL_PATH, index=False)
    print(f"\nDone. {results_df['hour'].nunique()} hours x up to {len(seam_branches)} branches "
          f"= {len(results_df)} contingency-solves. Total time: {time.time()-t_start:.0f}s")
    return results_df


if __name__ == '__main__':
    main()
