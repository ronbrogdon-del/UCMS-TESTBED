"""
TIER1_MULTISCENARIO_FOLLOWUPS_v1
=========================================================================
Four follow-up checks on the seam-vs-non-seam pattern found in
tier1_multiscenario_structural.py / tier1_multiscenario_permtest.py:

  1. EFFECT SIZE: median(|dVm|_seam) - median(|dVm|_nonseam), in p.u.,
     per case, plus the 2016-group vs 2024-group averages explicitly
     (medians used instead of means since case2's MW/perm-test
     disagreement suggested the means are leverage-sensitive).
  2. VOLTAGE ANGLE: same bus-pair-level test as the Vm one, but on VA
     (degrees) instead -- does the same 2016-vs-2024 pattern show up in
     angle separation across seams, not just magnitude?
  3. LINE FLOW: classify INDIVIDUAL in-service branches (not deduplicated
     bus-pairs -- flow is a per-circuit quantity, parallel circuits on
     the same bus pair can carry very different flow) as seam/non-seam,
     compare |S| = sqrt(PF^2+QF^2) (MVA) between groups.
  4. N-1 DELTA1: trip each seam branch individually (full set, ~127-131
     per case) and a random sample of non-seam branches (capped at 300
     per case to keep runtime bounded -- full non-seam population is
     ~2500+ per case, infeasible to all re-solve here), re-run AC power
     flow, define Delta1 = max(|Vm_after - Vm_before|) across all buses
     (system-wide voltage disturbance from removing ONE line). Compares
     whether seam-branch trips are more disruptive than non-seam trips,
     and whether that gap grows 2016->2024. Non-convergence on a trip is
     recorded as its own severity signal, not silently dropped.

All three new observables (VA, flow, N-1 Delta1) use the SAME permutation
+ exact Mann-Whitney machinery as the original Vm test, for direct
comparability.
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

if not hasattr(np, 'in1d'):
    np.in1d = np.isin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tier1_multiscenario_structural import CASES, _read_sanitized, seam_and_nonseam_pairs, abs_dv
from matpowercaseframes import CaseFrames
from pypower.api import runpf, ppoption

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
OUT_DIR = os.path.join(REPO_ROOT, 'experiments')

N_PERM = 100_000
CHUNK = 2_000
RNG_SEED = 42
N1_NONSEAM_SAMPLE = 300  # cap on non-seam branches re-solved for the N-1 check

YEAR_2016 = ['baseline_ACTIVSg2000', 'case1_2016summerpeak', 'case2_2016lowload']
YEAR_2024 = ['case3_2024summerpeak', 'case4_2024lowload', 'case5_2024highrenewables', 'case6_2024lowloadwithgfm']


def permutation_test_mean_diff(seam_vals, nonseam_vals, B=N_PERM, chunk=CHUNK, rng=None):
    if rng is None:
        rng = np.random.default_rng(RNG_SEED)
    n1 = len(seam_vals)
    values = np.concatenate([seam_vals, nonseam_vals])
    N = len(values)
    n2 = N - n1
    S = values.sum()
    T_obs = seam_vals.mean() - nonseam_vals.mean()
    count_ge = 0
    done = 0
    while done < B:
        b = min(chunk, B - done)
        rand = rng.random((b, N))
        part_idx = np.argpartition(rand, n1 - 1, axis=1)[:, :n1]
        sub_vals = values[part_idx]
        sum1 = sub_vals.sum(axis=1)
        mean1 = sum1 / n1
        mean2 = (S - sum1) / n2
        T_perm = mean1 - mean2
        count_ge += int((T_perm >= T_obs).sum())
        done += b
    p_greater = (count_ge + 1) / (B + 1)
    return T_obs, p_greater


def load_solve_full(path):
    """Like tier1_multiscenario_structural.load_and_solve, but also
    returns cf and the full ppc result (for branch flows / repeat solves)."""
    safe_path = _read_sanitized(path)
    try:
        cf = CaseFrames(safe_path)
    finally:
        os.remove(safe_path)
    ppc = {
        'version': '2', 'baseMVA': float(cf.baseMVA),
        'bus': cf.bus.to_numpy(dtype=float), 'gen': cf.gen.to_numpy(dtype=float),
        'branch': cf.branch.to_numpy(dtype=float), 'gencost': cf.gencost.to_numpy(dtype=float),
    }
    opt = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)
    result, success = runpf(ppc, opt)
    if not success:
        raise RuntimeError(f"Power flow did not converge for {path}")
    return cf, ppc, result


def value_by_bus(result, col):
    bus_ids = result['bus'][:, 0].astype(int)
    return dict(zip(bus_ids, result['bus'][:, col]))


# --------------------------------------------------------------------- #
# 1. EFFECT SIZE (median-based, on the Vm pairs already characterized)
# --------------------------------------------------------------------- #
def effect_size_section(rng):
    print("\n" + "=" * 70 + "\n1. EFFECT SIZE (median |dVm|, seam minus non-seam-connected)\n" + "=" * 70)
    rows = []
    for name, path in CASES.items():
        cf, ppc, result = load_solve_full(path)
        vm_by_bus = value_by_bus(result, 7)
        seam_pairs, nonseam_pairs = seam_and_nonseam_pairs(cf)
        seam_dv = abs_dv(seam_pairs, vm_by_bus)
        nonseam_dv = abs_dv(nonseam_pairs, vm_by_bus)
        med_seam, med_nonseam = np.median(seam_dv), np.median(nonseam_dv)
        eff = med_seam - med_nonseam
        eff_pct_of_nonseam = 100 * eff / med_nonseam if med_nonseam > 0 else np.nan
        print(f"  {name:28s} median_seam={med_seam:.5f}  median_nonseam={med_nonseam:.5f}  "
              f"effect={eff:+.5f} p.u. ({eff_pct_of_nonseam:+.1f}% of non-seam median)")
        rows.append({'case': name, 'median_seam_dVm': med_seam, 'median_nonseam_dVm': med_nonseam,
                      'effect_size_dVm_pu': eff, 'effect_size_pct_of_nonseam': eff_pct_of_nonseam})
    df = pd.DataFrame(rows)
    df['year_group'] = df['case'].apply(lambda c: '2016' if c in YEAR_2016 else '2024')
    summary = df.groupby('year_group')['effect_size_dVm_pu'].mean()
    print(f"\n  2016-group mean effect size: {summary['2016']:+.5f} p.u.")
    print(f"  2024-group mean effect size: {summary['2024']:+.5f} p.u.")
    print(f"  Ratio (2024/2016 effect size): {summary['2024']/summary['2016']:.2f}x")
    df.to_csv(os.path.join(OUT_DIR, 'tier1_followup_effect_size.csv'), index=False)
    return df


# --------------------------------------------------------------------- #
# 2. VOLTAGE ANGLE (same bus-pair test, VA instead of Vm)
# --------------------------------------------------------------------- #
def voltage_angle_section(rng):
    print("\n" + "=" * 70 + "\n2. VOLTAGE ANGLE (degrees) -- same seam-vs-nonseam test\n" + "=" * 70)
    rows = []
    for name, path in CASES.items():
        cf, ppc, result = load_solve_full(path)
        va_by_bus = value_by_bus(result, 8)  # VA column
        seam_pairs, nonseam_pairs = seam_and_nonseam_pairs(cf)
        seam_dv = abs_dv(seam_pairs, va_by_bus)
        nonseam_dv = abs_dv(nonseam_pairs, va_by_bus)
        T_obs, p_perm = permutation_test_mean_diff(seam_dv, nonseam_dv, rng=rng)
        mw = mannwhitneyu(seam_dv, nonseam_dv, alternative='greater', method='exact')
        med_eff = np.median(seam_dv) - np.median(nonseam_dv)
        print(f"  {name:28s} median_eff={med_eff:+7.3f} deg  T_obs={T_obs:+7.4f}  "
              f"perm_p={p_perm:.5f}  MW_p_exact={mw.pvalue:.3e}")
        rows.append({'case': name, 'median_seam_dVA_deg': np.median(seam_dv),
                      'median_nonseam_dVA_deg': np.median(nonseam_dv),
                      'effect_size_dVA_deg': med_eff, 'T_obs_mean_diff': T_obs,
                      'perm_p_one_sided': p_perm, 'mannwhitney_p_exact_one_sided': mw.pvalue})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT_DIR, 'tier1_followup_voltage_angle.csv'), index=False)
    return df


# --------------------------------------------------------------------- #
# 3. LINE FLOW (individual branches, |S| MVA)
# --------------------------------------------------------------------- #
def branch_seam_classification(cf):
    """Per-branch (not deduplicated), POSITIONAL (0-based, aligned with the
    numpy ppc['branch'] array) seam/non-seam classification. Returns
    (in_service_mask, is_seam_full) as full-length boolean arrays -- do
    NOT use cf.branch.index for this (CaseFrames' pandas index labels are
    not guaranteed 0-based and caused an off-by-one out-of-bounds bug in
    an earlier version of this function)."""
    area_map = dict(zip(cf.bus['BUS_I'].astype(int), cf.bus['BUS_AREA'].astype(int)))
    f_area = cf.branch['F_BUS'].astype(int).map(area_map).to_numpy()
    t_area = cf.branch['T_BUS'].astype(int).map(area_map).to_numpy()
    in_service_mask = (cf.branch['BR_STATUS'].to_numpy() == 1)
    is_seam_full = (f_area != t_area)
    return in_service_mask, is_seam_full


def line_flow_section(rng):
    print("\n" + "=" * 70 + "\n3. LINE FLOW |S| (MVA) -- individual branches, seam vs non-seam\n" + "=" * 70)
    rows = []
    for name, path in CASES.items():
        cf, ppc, result = load_solve_full(path)
        branch_res = result['branch']  # same row order as cf.branch (BR_STATUS filter applied after)
        S = np.sqrt(branch_res[:, 13] ** 2 + branch_res[:, 14] ** 2)  # PF, QF columns
        in_service = cf.branch['BR_STATUS'].to_numpy() == 1
        area_map = dict(zip(cf.bus['BUS_I'].astype(int), cf.bus['BUS_AREA'].astype(int)))
        f_area = cf.branch['F_BUS'].astype(int).map(area_map).to_numpy()
        t_area = cf.branch['T_BUS'].astype(int).map(area_map).to_numpy()
        is_seam_full = (f_area != t_area)

        seam_S = S[in_service & is_seam_full]
        nonseam_S = S[in_service & ~is_seam_full]

        T_obs, p_perm = permutation_test_mean_diff(seam_S, nonseam_S, rng=rng)
        # exact U-distribution overflows for n this large (~3000-3700); asymptotic
        # normal approximation (with tie/continuity correction) is the standard,
        # numerically stable choice at this sample size
        mw = mannwhitneyu(seam_S, nonseam_S, alternative='greater', method='asymptotic')
        med_eff = np.median(seam_S) - np.median(nonseam_S)
        print(f"  {name:28s} n_seam_branch={len(seam_S):4d} n_nonseam_branch={len(nonseam_S):4d}  "
              f"median_eff={med_eff:+7.3f} MVA  perm_p={p_perm:.5f}  MW_p_asymptotic={mw.pvalue:.3e}")
        rows.append({'case': name, 'n_seam_branches': len(seam_S), 'n_nonseam_branches': len(nonseam_S),
                      'median_seam_S_mva': np.median(seam_S), 'median_nonseam_S_mva': np.median(nonseam_S),
                      'effect_size_S_mva': med_eff, 'T_obs_mean_diff': T_obs,
                      'perm_p_one_sided': p_perm, 'mannwhitney_p_asymptotic_one_sided': mw.pvalue})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT_DIR, 'tier1_followup_line_flow.csv'), index=False)
    return df


# --------------------------------------------------------------------- #
# 4. N-1 DELTA1 (system-wide max |dVm| from tripping ONE branch)
# --------------------------------------------------------------------- #
def n1_delta1_section(rng):
    print("\n" + "=" * 70 + "\n4. N-1 Delta1: max system |dVm| from tripping one branch\n" + "=" * 70)
    rows = []
    for name, path in CASES.items():
        t0 = time.time()
        cf, ppc, result0 = load_solve_full(path)
        vm0 = value_by_bus(result0, 7)
        in_service_mask, is_seam_full = branch_seam_classification(cf)
        seam_idx = np.flatnonzero(in_service_mask & is_seam_full)
        nonseam_idx = np.flatnonzero(in_service_mask & ~is_seam_full)

        rng.shuffle(nonseam_idx)
        nonseam_idx_sample = nonseam_idx[:min(N1_NONSEAM_SAMPLE, len(nonseam_idx))]

        def trip_and_measure(branch_row_idx):
            ppc_trip = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in ppc.items()}
            ppc_trip['branch'] = ppc['branch'].copy()
            ppc_trip['branch'][branch_row_idx, 10] = 0  # BR_STATUS -> out
            opt = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)
            try:
                res, ok = runpf(ppc_trip, opt)
            except Exception:
                return None, False
            if not ok:
                return None, False
            vm1 = value_by_bus(res, 7)
            common = set(vm0) & set(vm1)
            if not common:
                return None, False
            d1 = max(abs(vm1[b] - vm0[b]) for b in common)
            return d1, True

        seam_d1, seam_fail = [], 0
        for idx in seam_idx:
            d1, ok = trip_and_measure(idx)
            if ok:
                seam_d1.append(d1)
            else:
                seam_fail += 1

        nonseam_d1, nonseam_fail = [], 0
        for idx in nonseam_idx_sample:
            d1, ok = trip_and_measure(idx)
            if ok:
                nonseam_d1.append(d1)
            else:
                nonseam_fail += 1

        seam_d1 = np.array(seam_d1)
        nonseam_d1 = np.array(nonseam_d1)
        T_obs, p_perm = permutation_test_mean_diff(seam_d1, nonseam_d1, rng=rng)
        mw = mannwhitneyu(seam_d1, nonseam_d1, alternative='greater', method='exact')
        med_eff = np.median(seam_d1) - np.median(nonseam_d1)
        dt = time.time() - t0
        print(f"  {name:28s} n_seam_trips={len(seam_idx):4d} (fail {seam_fail})  "
              f"n_nonseam_trips={len(nonseam_idx_sample):4d} (fail {nonseam_fail})")
        print(f"    median Delta1 seam={np.median(seam_d1):.5f}  nonseam={np.median(nonseam_d1):.5f}  "
              f"effect={med_eff:+.5f} p.u.  perm_p={p_perm:.5f}  MW_p_exact={mw.pvalue:.3e}  [{dt:.0f}s]")
        rows.append({
            'case': name, 'n_seam_trips': len(seam_idx), 'seam_trip_nonconverged': seam_fail,
            'n_nonseam_trips_sampled': len(nonseam_idx_sample), 'nonseam_trip_nonconverged': nonseam_fail,
            'median_delta1_seam': np.median(seam_d1), 'median_delta1_nonseam': np.median(nonseam_d1),
            'effect_size_delta1': med_eff, 'T_obs_mean_diff': T_obs,
            'perm_p_one_sided': p_perm, 'mannwhitney_p_exact_one_sided': mw.pvalue,
        })
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT_DIR, 'tier1_followup_n1_delta1.csv'), index=False)
    return df


def main():
    rng = np.random.default_rng(RNG_SEED)
    eff_df = effect_size_section(rng)
    va_df = voltage_angle_section(rng)
    flow_df = line_flow_section(rng)
    n1_df = n1_delta1_section(rng)
    return eff_df, va_df, flow_df, n1_df


if __name__ == '__main__':
    main()
