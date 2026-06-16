"""
N-1 Contingency Sweep — Seam Branches, Three Operating Points
=================================================================
README's already-stated next experiment, finally run. Also replaces the
load-ramp precursor approach: a contingency is a true structural
discontinuity, not derived from the load series, so it has no
autocorrelation problem.

WHAT THIS CAN AND CANNOT MEASURE (read before interpreting results) --
this is a STATIC power-flow study, not a dynamic/transient simulation
(no inertia, no governor response, confirmed back when frequency
response was scoped out). That constrains what "Δ1, Δ2, τ½, R" can mean
here, and forcing numbers out of a framework that can't support them
would be worse than not computing them:

  - Δ1 (drift): meaningful as a SINGLE JUMP -- post-contingency minus
    pre-contingency, at the same operating point. NOT a continuous-time
    rate, because there's no continuous time here, just two snapshots.
  - Δ2 (curvature): NOT COMPUTED. Curvature needs three points in time;
    a single before/after pair gives you one difference, not a second
    difference. Forcing a Δ2 out of two snapshots would be made up.
  - τ½ (recovery half-life): NOT COMPUTED. Recovery is a dynamic process
    (the system decaying back toward baseline over time/seconds-minutes
    after a fault). A static power flow has no time axis after the trip
    -- restoring the branch makes the model snap back to N-0 instantly,
    which would make any τ½ number measure our own choice of test
    window, not the grid's actual recovery dynamics. Skipped rather than
    faked.
  - R (resilience/integrated deviation): NOT COMPUTED for the same
    reason -- it's defined as an integral over a recovery trajectory we
    don't have.
  - What IS genuinely tested: severity of the jump (Δ1) across 131 seam
    contingencies, at 3 different loading conditions (peak/median/min),
    including whether some contingencies cause outright non-convergence
    (voltage collapse) -- the cleanest ground-truth "rupture" signal
    this testbed can currently produce.

Method:
  - Three operating points: the year's peak-load hour (5368), median-load
    hour (384), min-load hour (2259) -- same area-proportional load /
    system-proportional generation scaling as the annual series, for
    exact consistency with it.
  - For each operating point: solve N-0 (baseline), then for each of the
    131 in-service seam branches, trip it alone (BR_STATUS=0) and re-solve.
  - Seam-coherence and coupling-stress computed using the SAME reference
    baseline (V-bar, per-pair sigma, K_ij) derived from the full annual
    N-0 series, so contingency snapshots are comparable to the rest of
    this project's results, not a new incompatible scale.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from activsg2000_loader import load_case
from activsg2000_powerflow import case_to_ppc
from pypower.api import runpf, ppoption
from tier1_candidate_operators import build_seam_pairs

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
OPT = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)

BUS_PD_COL, BUS_QD_COL, BUS_AREA_COL, BUS_VM_COL = 2, 3, 6, 7
GEN_BUS_COL, GEN_PG_COL, GEN_STATUS_COL = 0, 1, 7
BR_F, BR_T, BR_STATUS_COL = 0, 1, 10

OPERATING_POINTS = {'peak': 5368, 'median': 384, 'min': 2259}  # hour numbers (1-indexed)


def build_reference_baseline(cf):
    """V-bar and per-pair sigma from the full annual series; K_ij from admittance."""
    d = np.load(os.path.join(OUT_DIR, 'annual_voltage_series.npz'))
    vm, bus_ids = d['vm'], d['bus_ids']
    bus_idx = {b: i for i, b in enumerate(bus_ids)}
    Vbar = vm.mean(axis=0)
    Vtilde = vm - Vbar

    pairs = build_seam_pairs(cf)  # (bus_i, bus_j, K_ij), 127 unique
    sigma = {}
    for (bi, bj, k) in pairs:
        ii, jj = bus_idx[bi], bus_idx[bj]
        sigma[(bi, bj)] = (Vtilde[:, ii] - Vtilde[:, jj]).std()
    return Vbar, bus_idx, pairs, sigma


def coherence_stress_for_snapshot(vm_snapshot, Vbar, bus_idx, pairs, sigma):
    Vt = vm_snapshot - Vbar
    C_vals, weighted_terms, K_total = [], 0.0, 0.0
    for (bi, bj, k) in pairs:
        ii, jj = bus_idx[bi], bus_idx[bj]
        diff = Vt[ii] - Vt[jj]
        s = sigma[(bi, bj)]
        if s > 1e-12:
            C_vals.append(1.0 - abs(diff) / s)
        weighted_terms += k * abs(diff)
        K_total += k
    return float(np.mean(C_vals)), float(weighted_terms / K_total)


def per_pair_coherence(vm_snapshot, Vbar, bus_idx, bi, bj, sigma):
    Vt = vm_snapshot - Vbar
    diff = Vt[bus_idx[bi]] - Vt[bus_idx[bj]]
    s = sigma[(bi, bj)]
    return 1.0 - abs(diff) / s if s > 1e-12 else np.nan


def build_scaled_ppc(base_ppc, area_masks, basecase_area_total, basecase_system_total, hour_row, area_load_cols):
    bus0, gen0 = base_ppc['bus'], base_ppc['gen']
    bus_t = bus0.copy()
    for a in range(1, 9):
        lam_load = hour_row[f'area_{a}'] / basecase_area_total[a]
        m = area_masks[a]
        bus_t[m, BUS_PD_COL] *= lam_load
        bus_t[m, BUS_QD_COL] *= lam_load
    lam_gen = hour_row['system_total'] / basecase_system_total
    ref_bus_id = bus0[bus0[:, 1] == 3, 0]
    gen_is_ref = np.isin(gen0[:, GEN_BUS_COL], ref_bus_id)
    gen_online = gen0[:, GEN_STATUS_COL] == 1
    gen_scale_mask = gen_online & ~gen_is_ref
    gen_t = gen0.copy()
    gen_t[gen_scale_mask, GEN_PG_COL] *= lam_gen
    return bus_t, gen_t


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
    print(f"Reference baseline built from annual series ({len(pairs)} seam pairs).")

    branch = cf.branch[cf.branch['BR_STATUS'] == 1].copy()
    branch['orig_pos'] = np.arange(len(cf.branch))[cf.branch['BR_STATUS'].to_numpy() == 1]
    area_map = dict(zip(cf.bus['BUS_I'].astype(float), cf.bus['BUS_AREA'].astype(int)))
    branch['AF'] = branch['F_BUS'].map(area_map)
    branch['AT'] = branch['T_BUS'].map(area_map)
    seam_branches = branch[branch['AF'] != branch['AT']].reset_index(drop=True)
    print(f"Seam branches to trip (raw circuit elements, not deduplicated): {len(seam_branches)}")

    all_results = []
    for op_name, hour in OPERATING_POINTS.items():
        hour_row = yr[yr['hour'] == hour].iloc[0]
        bus_t, gen_t = build_scaled_ppc(base_ppc, area_masks, basecase_area_total,
                                         basecase_system_total, hour_row, load_cols)

        ppc_base = {**base_ppc, 'bus': bus_t, 'gen': gen_t}
        result0, success0 = runpf(ppc_base, OPT)
        if not success0:
            print(f"  [{op_name}] N-0 baseline failed to converge -- skipping this operating point")
            continue
        vm0 = result0['bus'][:, BUS_VM_COL]
        C0, S0 = coherence_stress_for_snapshot(vm0, Vbar, bus_idx, pairs, sigma)
        print(f"\n--- Operating point: {op_name} (hour {hour}, load {hour_row['system_total']:.0f} MW) ---")
        print(f"  N-0 baseline: coherence={C0:.4f} stress={S0:.6f}")

        n_fail = 0
        for ridx, row in seam_branches.iterrows():
            branch_t = base_ppc['branch'].copy()
            branch_t[int(row['orig_pos']), BR_STATUS_COL] = 0  # trip this branch (correct row position)
            ppc_t = {**base_ppc, 'bus': bus_t, 'gen': gen_t, 'branch': branch_t}
            result, success = runpf(ppc_t, OPT)

            rec = {
                'operating_point': op_name, 'hour': hour, 'system_load_mw': hour_row['system_total'],
                'branch_idx': int(row['orig_pos']), 'f_bus': row['F_BUS'], 't_bus': row['T_BUS'],
                'area_f': int(row['AF']), 'area_t': int(row['AT']),
                'converged': bool(success),
            }
            if success:
                vm1 = result['bus'][:, BUS_VM_COL]
                C1, S1 = coherence_stress_for_snapshot(vm1, Vbar, bus_idx, pairs, sigma)
                pair_key = tuple(sorted((row['F_BUS'], row['T_BUS'])))
                c_pair_pre = per_pair_coherence(vm0, Vbar, bus_idx, pair_key[0], pair_key[1], sigma)
                c_pair_post = per_pair_coherence(vm1, Vbar, bus_idx, pair_key[0], pair_key[1], sigma)
                rec.update({
                    'coherence_pre': C0, 'coherence_post': C1, 'delta1_coherence': C1 - C0,
                    'stress_pre': S0, 'stress_post': S1, 'delta1_stress': S1 - S0,
                    'tripped_pair_coherence_pre': c_pair_pre, 'tripped_pair_coherence_post': c_pair_post,
                    'vmin_post': vm1.min(), 'vmax_post': vm1.max(),
                })
            else:
                n_fail += 1
                rec.update({k: np.nan for k in [
                    'coherence_pre', 'coherence_post', 'delta1_coherence', 'stress_pre', 'stress_post',
                    'delta1_stress', 'tripped_pair_coherence_pre', 'tripped_pair_coherence_post',
                    'vmin_post', 'vmax_post']})
            all_results.append(rec)

        print(f"  {len(seam_branches) - n_fail}/{len(seam_branches)} contingencies converged, "
              f"{n_fail} caused non-convergence (voltage collapse)")

    results_df = pd.DataFrame(all_results)
    results_df.to_csv(os.path.join(OUT_DIR, 'n1_seam_contingency_sweep.csv'), index=False)

    print("\n=== Top 10 most severe contingencies by |delta1_stress|, across all operating points ===")
    conv = results_df[results_df['converged']]
    top = conv.reindex(conv['delta1_stress'].abs().sort_values(ascending=False).index).head(10)
    print(top[['operating_point', 'f_bus', 't_bus', 'area_f', 'area_t',
               'delta1_coherence', 'delta1_stress', 'vmin_post', 'vmax_post']].to_string(index=False))

    if (~results_df['converged']).any():
        print("\n=== Non-convergent contingencies (most severe outcome: voltage collapse) ===")
        print(results_df[~results_df['converged']][
            ['operating_point', 'f_bus', 't_bus', 'area_f', 'area_t']].to_string(index=False))

    return results_df


if __name__ == '__main__':
    main()
