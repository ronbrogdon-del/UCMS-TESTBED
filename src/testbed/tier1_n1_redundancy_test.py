"""
TIER1_N1_REDUNDANCY_TEST_v1 — Does seam-tie redundancy explain the N-1
Delta1 inversion?
=========================================================================
tier1_multiscenario_followups.py found that seam-branch N-1 outages are
significantly MORE disruptive than non-seam outages in all three 2016
cases, but that gap shrinks/vanishes in all four 2024 cases -- the
OPPOSITE direction from every static (Vm/VA/flow) finding. The proposed
explanation: 2024 cases have more seam branches in absolute terms
(191-213 vs 131-137), i.e. more parallel/alternate ties between the same
pair of areas, so any single seam line now carries less unique
importance even though the area boundary's static electrical signature
got stronger.

This script tests that explanation directly, three ways, using the
PER-BRANCH trip data (not just the case-level summary from the prior
script):

  1. PREMISE CHECK: is redundancy (number of seam branches connecting
     the same area-pair, counting the branch itself) actually higher in
     2024 than 2016, branch-by-branch, not just in raw seam-branch
     count?
  2. POOLED CORRELATION: across all seam-branch trips from all 7 cases,
     does higher redundancy predict lower Delta1 (Spearman, robust to
     the heavy right-skew Delta1 distributions have)?
  3. REGRESSION + STRATIFIED MATCH: does a year-2024 dummy's effect on
     Delta1 attenuate once redundancy is controlled for (mediation-style
     check)? And, more strictly: among ONLY redundancy=1 branches (the
     sole, non-redundant tie for their area-pair) in both eras, does the
     2016-vs-2024 Delta1 gap persist? If it disappears even in the
     controlled comparison above but PERSISTS in this matched subset,
     redundancy is not the full explanation.

Re-solves every seam-branch N-1 trip across all 7 cases (full seam
population each time, ~131-213/case) -- non-seam trips are NOT needed
for this test and are skipped, cutting runtime roughly in half versus
the original follow-up script.
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, mannwhitneyu
import statsmodels.api as sm

if not hasattr(np, 'in1d'):
    np.in1d = np.isin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tier1_multiscenario_structural import CASES
from tier1_multiscenario_followups import load_solve_full, value_by_bus, branch_seam_classification, \
    permutation_test_mean_diff, YEAR_2016, YEAR_2024, RNG_SEED

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
OUT_DIR = os.path.join(REPO_ROOT, 'experiments')

from pypower.api import runpf, ppoption


def collect_seam_trip_data():
    """Returns one row per seam-branch trip, across all 7 cases, with
    area-pair redundancy count and Delta1 attached."""
    all_rows = []
    for name, path in CASES.items():
        cf, ppc, result0 = load_solve_full(path)
        vm0 = value_by_bus(result0, 7)
        area_map = dict(zip(cf.bus['BUS_I'].astype(int), cf.bus['BUS_AREA'].astype(int)))
        in_service_mask, is_seam_full = branch_seam_classification(cf)
        seam_idx = np.flatnonzero(in_service_mask & is_seam_full)

        f_bus = cf.branch['F_BUS'].astype(int).to_numpy()
        t_bus = cf.branch['T_BUS'].astype(int).to_numpy()
        area_pairs = {idx: tuple(sorted((area_map[f_bus[idx]], area_map[t_bus[idx]]))) for idx in seam_idx}

        # redundancy: how many seam branches (in THIS case) share this area-pair, including itself
        pair_counts = pd.Series([area_pairs[idx] for idx in seam_idx]).value_counts().to_dict()

        opt = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)
        for idx in seam_idx:
            ppc_trip = dict(ppc)
            ppc_trip['branch'] = ppc['branch'].copy()
            ppc_trip['branch'][idx, 10] = 0
            try:
                res, ok = runpf(ppc_trip, opt)
            except Exception:
                ok = False
            if ok:
                vm1 = value_by_bus(res, 7)
                common = set(vm0) & set(vm1)
                delta1 = max(abs(vm1[b] - vm0[b]) for b in common) if common else np.nan
            else:
                delta1 = np.nan

            all_rows.append({
                'case': name,
                'year_group': '2016' if name in YEAR_2016 else '2024',
                'branch_idx': idx,
                'f_bus': f_bus[idx], 't_bus': t_bus[idx],
                'area_pair': area_pairs[idx],
                'redundancy': pair_counts[area_pairs[idx]],
                'delta1': delta1,
                'converged': bool(ok),
            })
        n_conv = sum(r['converged'] for r in all_rows if r['case'] == name)
        print(f"  {name}: {len(seam_idx)} seam trips, {n_conv} converged, "
              f"redundancy range {min(pair_counts.values())}-{max(pair_counts.values())}")
    return pd.DataFrame(all_rows)


def main():
    print("Collecting per-branch N-1 trip data (seam branches only, full population per case)...")
    df = collect_seam_trip_data()
    df_ok = df[df['converged']].copy()
    df_ok['year2024'] = (df_ok['year_group'] == '2024').astype(int)

    out_path = os.path.join(OUT_DIR, 'tier1_n1_redundancy_trips.csv')
    df.to_csv(out_path, index=False)
    print(f"\nWrote per-trip data: {out_path}  (n={len(df)}, converged={len(df_ok)})")

    # --- 1. Premise check: redundancy by year ---
    print("\n" + "=" * 70 + "\n1. PREMISE CHECK: redundancy (parallel seam ties per area-pair)\n" + "=" * 70)
    red_by_case = df.groupby('case')['redundancy'].agg(['median', 'mean', 'max'])
    print(red_by_case.reindex(list(CASES.keys())).to_string())
    red_2016 = df[df['year_group'] == '2016']['redundancy']
    red_2024 = df[df['year_group'] == '2024']['redundancy']
    print(f"\n  Pooled median redundancy: 2016={red_2016.median():.1f}  2024={red_2024.median():.1f}")
    print(f"  Pooled mean redundancy:   2016={red_2016.mean():.2f}  2024={red_2024.mean():.2f}")
    mw_red = mannwhitneyu(red_2024, red_2016, alternative='greater', method='asymptotic')
    print(f"  Mann-Whitney (2024 redundancy > 2016 redundancy): p={mw_red.pvalue:.3e}")

    # --- 2. Pooled correlation: redundancy vs Delta1 ---
    print("\n" + "=" * 70 + "\n2. POOLED CORRELATION: redundancy vs Delta1 (all 7 cases, converged trips)\n" + "=" * 70)
    rho, p_rho = spearmanr(df_ok['redundancy'], df_ok['delta1'])
    print(f"  Spearman rho = {rho:.4f}  (p={p_rho:.3e}, n={len(df_ok)})")

    # --- 3a. Regression: does year2024's effect attenuate after controlling for redundancy? ---
    print("\n" + "=" * 70 + "\n3a. REGRESSION: Delta1 ~ year2024  vs  Delta1 ~ year2024 + redundancy\n" + "=" * 70)
    X1 = sm.add_constant(df_ok[['year2024']])
    m1 = sm.OLS(df_ok['delta1'], X1).fit()
    print("  Model A (year2024 only):")
    print(f"    year2024 coef = {m1.params['year2024']:+.5f}  (p={m1.pvalues['year2024']:.3e})  R2={m1.rsquared:.3f}")

    X2 = sm.add_constant(df_ok[['year2024', 'redundancy']])
    m2 = sm.OLS(df_ok['delta1'], X2).fit()
    print("  Model B (year2024 + redundancy):")
    print(f"    year2024 coef   = {m2.params['year2024']:+.5f}  (p={m2.pvalues['year2024']:.3e})")
    print(f"    redundancy coef = {m2.params['redundancy']:+.5f}  (p={m2.pvalues['redundancy']:.3e})  R2={m2.rsquared:.3f}")
    atten = 100 * (1 - m2.params['year2024'] / m1.params['year2024'])
    print(f"  Attenuation of year2024 coefficient after adding redundancy: {atten:.1f}%")

    # --- 3b. Stratified match: redundancy == 1 only ---
    print("\n" + "=" * 70 + "\n3b. STRATIFIED MATCH: redundancy == 1 (sole tie) branches only\n" + "=" * 70)
    df_r1 = df_ok[df_ok['redundancy'] == 1]
    n_2016_r1 = (df_r1['year_group'] == '2016').sum()
    n_2024_r1 = (df_r1['year_group'] == '2024').sum()
    print(f"  n redundancy=1 branches: 2016={n_2016_r1}  2024={n_2024_r1}")
    if n_2016_r1 >= 5 and n_2024_r1 >= 5:
        d16 = df_r1[df_r1['year_group'] == '2016']['delta1'].to_numpy()
        d24 = df_r1[df_r1['year_group'] == '2024']['delta1'].to_numpy()
        T_obs, p_perm = permutation_test_mean_diff(d16, d24, rng=np.random.default_rng(RNG_SEED))
        mw_r1 = mannwhitneyu(d16, d24, alternative='greater', method='asymptotic')
        print(f"  median Delta1: 2016={np.median(d16):.5f}  2024={np.median(d24):.5f}")
        print(f"  (2016 > 2024 test, matched at redundancy=1): perm_p={p_perm:.5f}  MW_p={mw_r1.pvalue:.3e}")
        if p_perm < 0.05 or mw_r1.pvalue < 0.05:
            print("  -> Year gap PERSISTS even at matched redundancy=1: redundancy alone does not fully explain it.")
        else:
            print("  -> Year gap DISAPPEARS at matched redundancy=1: consistent with redundancy as the explanation.")
    else:
        print("  Insufficient sample in one or both groups at redundancy=1 for a reliable stratified test.")

    return df


if __name__ == '__main__':
    main()
