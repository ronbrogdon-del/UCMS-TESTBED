"""
TIER1_MULTISCENARIO_PERMTEST_v1 — Exact/Rigorous Version of the Seam
Structure Test
=========================================================================
Tightens tier1_multiscenario_structural.py's bootstrap-percentile-of-5000
into two independent, more rigorous tests of the same question (does the
seam vs. connected-non-seam |dVm| difference look real, not noise):

  1. Monte Carlo permutation test on the difference-of-means statistic,
     T = mean(|dVm|_seam) - mean(|dVm|_nonseam), with B=100,000 draws
     (vs. the prior 5,000) and a proper two-sample label-shuffle (the
     prior version only resampled from the non-seam pool; this version
     pools seam+non-seam together and reshuffles which pairs get the
     "seam" label, which is the textbook permutation-test null). Reports
     a p-value with a Davison-Hinkley (+1/+1) correction so p is never
     reported as exactly 0, plus a Monte Carlo standard error.
  2. Mann-Whitney U / Wilcoxon rank-sum test (scipy), which has a real
     closed-form (or, for these sample sizes, fast-exact-algorithm) null
     distribution under exchangeability -- not a simulation at all. This
     is the actual "exact" test; the permutation test above is reported
     alongside it for direct comparability with the original framing,
     not as a replacement.

Both are reported one-sided (alternative: seam > non-seam, matching the
direction already seen in the exploratory run) AND two-sided, with the
one-sided result's non-independence from the exploratory run stated
explicitly -- this is a more rigorous test of the SAME hypothesis
already observed, not a fresh out-of-sample confirmation.

Imports the case loading / seam-pair construction from
tier1_multiscenario_structural.py rather than duplicating it.
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tier1_multiscenario_structural import CASES, load_and_solve, seam_and_nonseam_pairs, abs_dv

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
OUT_DIR = os.path.join(REPO_ROOT, 'experiments')

N_PERM = 100_000
CHUNK = 2_000
RNG_SEED = 42


def permutation_test_mean_diff(seam_vals, nonseam_vals, B=N_PERM, chunk=CHUNK, rng=None):
    """Two-sample permutation test on T = mean(seam) - mean(nonseam).
    Pools both groups, reshuffles the seam/non-seam label B times,
    recomputes T each time. Returns (T_obs, p_greater, p_two_sided, mc_se)."""
    if rng is None:
        rng = np.random.default_rng(RNG_SEED)

    n1 = len(seam_vals)
    values = np.concatenate([seam_vals, nonseam_vals])
    N = len(values)
    n2 = N - n1
    S = values.sum()
    T_obs = seam_vals.mean() - nonseam_vals.mean()

    count_ge = 0
    count_abs_ge = 0
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
        count_abs_ge += int((np.abs(T_perm) >= abs(T_obs)).sum())
        done += b

    p_greater = (count_ge + 1) / (B + 1)
    p_two_sided = (count_abs_ge + 1) / (B + 1)
    # Monte Carlo standard error on the proportion estimate
    mc_se = np.sqrt(p_greater * (1 - p_greater) / B)
    return T_obs, p_greater, p_two_sided, mc_se


def main():
    rng = np.random.default_rng(RNG_SEED)
    rows = []

    for name, path in CASES.items():
        t0 = time.time()
        print(f"\n=== {name} ===")
        cf, vm_by_bus = load_and_solve(path)
        seam_pairs, nonseam_pairs = seam_and_nonseam_pairs(cf)
        seam_dv = abs_dv(seam_pairs, vm_by_bus)
        nonseam_dv = abs_dv(nonseam_pairs, vm_by_bus)
        print(f"  n_seam={len(seam_dv)}  n_nonseam_connected={len(nonseam_dv)}")

        T_obs, p_perm_greater, p_perm_two_sided, mc_se = permutation_test_mean_diff(
            seam_dv, nonseam_dv, rng=rng)

        # method='exact': literal exact U-distribution, not the asymptotic
        # normal approximation that 'auto' silently picks for n>8 per side
        mw = mannwhitneyu(seam_dv, nonseam_dv, alternative='greater', method='exact')
        mw_two = mannwhitneyu(seam_dv, nonseam_dv, alternative='two-sided', method='exact')

        dt = time.time() - t0
        print(f"  T_obs (mean diff)              = {T_obs:.6f}")
        print(f"  permutation p (one-sided, B={N_PERM}) = {p_perm_greater:.6f}  (MC se ~{mc_se:.6f})")
        print(f"  permutation p (two-sided)             = {p_perm_two_sided:.6f}")
        print(f"  Mann-Whitney U p (one-sided, EXACT)     = {mw.pvalue:.3e}")
        print(f"  Mann-Whitney U p (two-sided, EXACT)     = {mw_two.pvalue:.3e}")
        print(f"  [{dt:.1f}s]")

        rows.append({
            'case': name,
            'n_seam': len(seam_dv),
            'n_nonseam_connected': len(nonseam_dv),
            'mean_diff_T_obs': T_obs,
            'perm_p_one_sided': p_perm_greater,
            'perm_p_two_sided': p_perm_two_sided,
            'perm_mc_se': mc_se,
            'mannwhitney_p_one_sided': mw.pvalue,
            'mannwhitney_p_two_sided': mw_two.pvalue,
            'mannwhitney_statistic_U': mw.statistic,
        })

    out = pd.DataFrame(rows)
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, 'tier1_multiscenario_permtest.csv')
    out.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
    return out


if __name__ == '__main__':
    main()
