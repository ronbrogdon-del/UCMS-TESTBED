"""
Embedded Outage in Real Hourly Series -- Time-Series Extension
=================================================================
The N-1 sweeps so far (3-point and 60-hour) are single before/after
snapshots: meaningful for Delta1 only. This embeds one persistent
contingency across many REAL consecutive hours, to get an actual
multi-point trajectory.

WHAT THIS CAN AND CANNOT GIVE (state up front, not after the fact):
  - Delta1 (onset jump): meaningful, and isolated cleanly from ordinary
    load variation by running every hour TWICE -- once with the branch
    tripped, once as a counterfactual with it in service -- and taking
    the difference. Outside the outage window the two are identical by
    construction, so the difference series is exactly zero there and
    isolates the outage's own effect during/after it.
  - Delta2 (curvature): meaningful in a real sense for the first time --
    does severity accelerate, decelerate, or plateau over many hours of
    a PERSISTENT outage as real load evolves underneath it. This is
    genuine curvature in an actual time series, not faked from 2 points.
  - tau_half (recovery half-life) and R (resilience integral): STILL not
    meaningful, for the same reason as the static snapshot sweeps -- a
    static power flow has no memory between hours. The moment the branch
    is restored, the model returns to whatever N-0 gives for that hour's
    real load, instantly, with no decay process to time. This run
    INCLUDES a post-restoration tail specifically to demonstrate that
    snap-back directly (does the differenced series go to ~0 immediately
    on restoration?) rather than just asserting it.

Window: branch 8030-7389 (the most severe contingency in both prior
sweeps) tripped for the 72 real hours immediately leading up to and
including hour 5368 (the year's actual peak-load hour) -- a genuine
load ramp into the system's highest-stress point, with the contingency
persisting throughout. Plus 24h before (baseline) and 24h after
(restoration check). 120 hours total, run twice (with/without outage).
"""

import os
import sys
import numpy as np
np.in1d = np.isin

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from activsg2000_loader import load_case
from activsg2000_powerflow import case_to_ppc
from pypower.api import runpf, ppoption
from n1_seam_contingency_sweep import (
    build_reference_baseline, build_scaled_ppc, coherence_stress_for_snapshot,
    BUS_PD_COL, BUS_AREA_COL, BR_STATUS_COL,
)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
OPT = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)

PEAK_HOUR = 5368
OUTAGE_LEN = 72
PRE_LEN = 24
POST_LEN = 24
TRIP_F_BUS, TRIP_T_BUS = 8030.0, 7389.0


def main():
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

    # locate the exact branch row to trip
    branch_full = cf.branch.reset_index(drop=True)
    match = branch_full[
        ((branch_full['F_BUS'] == TRIP_F_BUS) & (branch_full['T_BUS'] == TRIP_T_BUS)) |
        ((branch_full['F_BUS'] == TRIP_T_BUS) & (branch_full['T_BUS'] == TRIP_F_BUS))
    ]
    if len(match) == 0:
        raise ValueError(f"Branch {TRIP_F_BUS}-{TRIP_T_BUS} not found")
    trip_row_pos = match.index[0]
    print(f"Tripping branch row {trip_row_pos}: {TRIP_F_BUS}-{TRIP_T_BUS}")

    outage_start = PEAK_HOUR - OUTAGE_LEN + 1
    outage_end = PEAK_HOUR
    window_start = outage_start - PRE_LEN
    window_end = outage_end + POST_LEN
    window_hours = list(range(window_start, window_end + 1))
    print(f"Window: hours {window_start}-{window_end} ({len(window_hours)}h). "
          f"Outage: {outage_start}-{outage_end} ({OUTAGE_LEN}h, ending at peak hour {PEAK_HOUR}).")

    records = []
    for hour in window_hours:
        hour_row = yr[yr['hour'] == hour].iloc[0]
        bus_t, gen_t = build_scaled_ppc(base_ppc, area_masks, basecase_area_total,
                                         basecase_system_total, hour_row, load_cols)
        in_outage = outage_start <= hour <= outage_end

        # counterfactual: branch always in service
        ppc_cf = {**base_ppc, 'bus': bus_t, 'gen': gen_t}
        res_cf, ok_cf = runpf(ppc_cf, OPT)

        # actual: branch tripped only during the outage window
        branch_t = base_ppc['branch'].copy()
        if in_outage:
            branch_t[trip_row_pos, BR_STATUS_COL] = 0
        ppc_act = {**base_ppc, 'bus': bus_t, 'gen': gen_t, 'branch': branch_t}
        res_act, ok_act = runpf(ppc_act, OPT)

        rec = {'hour': hour, 'system_load_mw': hour_row['system_total'], 'in_outage': in_outage,
               'converged_cf': bool(ok_cf), 'converged_actual': bool(ok_act)}
        if ok_cf:
            vm_cf = res_cf['bus'][:, 7]
            C_cf, S_cf = coherence_stress_for_snapshot(vm_cf, Vbar, bus_idx, pairs, sigma)
            rec.update({'coherence_cf': C_cf, 'stress_cf': S_cf})
        if ok_act:
            vm_act = res_act['bus'][:, 7]
            C_act, S_act = coherence_stress_for_snapshot(vm_act, Vbar, bus_idx, pairs, sigma)
            rec.update({'coherence_actual': C_act, 'stress_actual': S_act})
        records.append(rec)

    df = pd.DataFrame(records)
    df['coherence_diff'] = df['coherence_actual'] - df['coherence_cf']
    df['stress_diff'] = df['stress_actual'] - df['stress_cf']
    out_path = os.path.join(OUT_DIR, 'embedded_outage_timeseries.csv')
    df.to_csv(out_path, index=False)

    print(f"\nConvergence: actual {df['converged_actual'].mean():.2%}, counterfactual {df['converged_cf'].mean():.2%}")
    print(f"\nstress_diff outside outage window (should be ~0 by construction):")
    print(f"  pre-outage:  max|diff| = {df.loc[~df['in_outage'] & (df['hour']<outage_start), 'stress_diff'].abs().max():.2e}")
    post = df[(df['hour'] > outage_end)]
    print(f"  post-outage: max|diff| = {post['stress_diff'].abs().max():.2e}  (first post hour: {post['stress_diff'].iloc[0]:.2e})")
    print(f"\nstress_diff during outage: min={df.loc[df['in_outage'],'stress_diff'].min():.2e} "
          f"max={df.loc[df['in_outage'],'stress_diff'].max():.2e} "
          f"at onset={df.loc[df['hour']==outage_start,'stress_diff'].values[0]:.2e} "
          f"at end/peak={df.loc[df['hour']==outage_end,'stress_diff'].values[0]:.2e}")

    return df


if __name__ == '__main__':
    main()
