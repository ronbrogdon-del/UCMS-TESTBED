# Tier-1 Multi-Scenario Structural Test — Results (2026-06-17)

## UPDATE (same day): exact/rigorous test results

The original run below used a 5,000-draw bootstrap sampled only from the
non-seam pool, reported as a percentile — informative but not a real
p-value. Superseded by `src/testbed/tier1_multiscenario_permtest.py`,
which runs two independent, properly rigorous tests of the same
question:

1. **Permutation test** on T = mean(\|dVm\|_seam) − mean(\|dVm\|_nonseam):
   pools seam+non-seam together, reshuffles the seam label B=100,000
   times (20x the prior bootstrap), reports a real p-value with Monte
   Carlo standard error.
2. **Mann-Whitney U test, `method='exact'`** (scipy): the literal exact
   U-distribution under exchangeability, not a simulation, not the
   asymptotic normal approximation that scipy's default `'auto'` mode
   silently substitutes for samples this size. No ties present, so no
   tie-correction caveat applies.

| Case | T_obs (mean diff) | permutation p (one-sided) | Mann-Whitney p (exact, one-sided) |
|---|---|---|---|
| baseline ACTIVSg2000 | 0.00066 | 0.142 | 0.117 |
| case1 2016 summer peak | 0.00068 | 0.136 | 0.119 |
| case2 2016 low load | 0.00052 | 0.153 | **0.028** |
| case3 2024 summer peak | 0.00214 | **0.0034** | **0.0078** |
| case4 2024 low load | 0.00325 | **0.00003** | **3.9e-7** |
| case5 2024 high renewables | 0.00373 | **0.00001** | **3.4e-9** |
| case6 2024 low load+GFM | 0.00325 | **0.00006** | **3.9e-7** |

**This sharpens the earlier exploratory pattern into a real significance
cliff, not just a percentile gradient.** None of the three 2016-era cases
clear conventional significance on the mean-difference permutation test
(p=0.14-0.15); the rank-based exact test agrees for baseline and case1
(p=0.12) but flags case2 as borderline (p=0.028) where the mean-based
test does not (p=0.153) — a real disagreement between the two tests,
not noise, and not yet resolved (see caveats). All four 2024 cases clear
significance on BOTH tests, with case5 (high renewables) the strongest
by a wide margin (p=3.4e-9) and case3 (summer peak) the weakest of the
four (p=0.0078) but still clearly significant.

**Caveat on the case2 discrepancy:** Mann-Whitney is sensitive to the
whole distribution shape (effectively a rank-based test), while the
permutation test here targets the mean specifically. A significant
Mann-Whitney with a non-significant mean-difference test suggests case2's
non-seam pool may have a few high-leverage values pulling its mean up
without shifting its rank distribution much — i.e., the median/typical
non-seam pair may differ from seam pairs even though the mean doesn't
cleanly separate. Not yet investigated further; flagged here rather than
glossed over.

**Caveat on multiple comparisons:** 7 cases x 2 tests = 14 p-values
reported above, none corrected for multiple comparisons (e.g. Bonferroni/
FDR). The 2024-case results are strong enough that this wouldn't change
the qualitative conclusion (case5 at p=3.4e-9 survives any reasonable
correction), but the case2 borderline result (p=0.028) would not survive
even a mild correction and should be treated as exploratory, not
confirmed.

Full per-case output: `experiments/tier1_multiscenario_permtest.csv`.

---

## Original run (superseded by the update above, kept for the record)


Script: `src/testbed/tier1_multiscenario_structural.py`
Output: `experiments/tier1_multiscenario_structural.csv`

## What this is, and isn't

This is a different operator family from `tier1_candidate_operators.py`.
That script needs an 8784-hour annual time series and independently-
defined load-peak events to compute Delta1/Delta2/precursor/tau_half/R.
The six Series24 cases (and the original baseline) are each a single
static power-flow snapshot — there's no time axis available, so those
time-series operators cannot be honestly applied to them.

What's well-posed on a snapshot: stratifying bus *pairs* by whether they
cross an area boundary ("seam") or not, and comparing |Vm_i - Vm_j|
across the two strata. Each case supplies its own seam set (areas are
consistent across all seven cases — verified directly, not assumed — but
topology isn't: branch counts range 3206-3913 across the seven).

All seven cases converged under AC power flow (pypower, default
tolerance), confirmed by direct tool call, not asserted.

## Results

| Case | n seam pairs | mean \|dVm\| seam | vs. random-pair null | vs. connected-non-seam null |
|---|---|---|---|---|
| baseline ACTIVSg2000 | 127 | 0.0077 | 0.0th pctile (seam pairs *closer* in voltage than random pairs — expected) | 87.1th pctile |
| case1 2016 summer peak | 131 | 0.0077 | 0.0th | 86.6th |
| case2 2016 low load | 131 | 0.0055 | 0.0th | 85.6th |
| case3 2024 summer peak | 131 | 0.0103 | 0.0th | 99.7th |
| case4 2024 low load | 131 | 0.0094 | 0.0th | **100.0th** |
| case5 2024 high renewables | 131 | 0.0094 | 0.0th | **100.0th** |
| case6 2024 low load + GFM | 131 | 0.0094 | 0.0th | **100.0th** |

(n_boot=5000 for both null distributions, seed 42; "100.0th pctile" means
the true seam-pair mean exceeded every one of the 5000 bootstrap draws,
i.e. p < 1/5000 in that direction at this sample size — not literally
p=0, and not yet replicated with an exact permutation test.)

## The pattern, stated plainly

Against the *generic random-pair* null, seam pairs are always more
voltage-similar than two random buses anywhere on the grid — unsurprising,
since electrical proximity in general correlates with voltage similarity,
and this isn't specific to the area/seam partition.

Against the more meaningful *connected, non-seam* null (same comparison,
but both groups are real physical branches — the only difference is
whether the branch crosses an area boundary), the pattern shifts sharply
between the 2016 and 2024 cases:

- **2016 cases (baseline, case1, case2):** seam pairs sit around the
  85th-87th percentile of the non-seam-connected null. Seams are somewhat
  more divergent than typical same-area connections, but not dramatically
  so.
- **All four 2024 cases, regardless of scenario (summer peak, low load,
  high renewables, low load+GFM):** seam pairs sit at the 99.7th-100th
  percentile. The area-boundary distinction is far more electrically
  pronounced.

The fact that this shows up identically across all four structurally
different 2024 scenarios — not just the one with high renewables, or just
the one with GFM inverters — points to it being a property of the
2016→2024 topology/dispatch evolution itself (more transmission, updated
generation mix), not an artifact of any single scenario's load or
generation profile.

## Caveats — read before citing this anywhere

- Single run. Bootstrap-percentile precision floors at 1/n_boot; an exact
  permutation test would give a real p-value instead of "100.0th of 5000."
- "Connected, non-seam" as the null is one reasonable choice, not the
  only one — e.g. matching by voltage level or by area would be stricter
  and might change the picture.
- This says the area partition's *electrical* salience grew 2016→2024 in
  this synthetic case. It says nothing yet about whether that salience
  growth tracks anything in the real ERCOT grid — these are TAMU synthetic
  cases, not real PMU/SCADA data (same caveat as the rest of this repo's
  ACTIVSg2000 work).
- Not yet reconciled against Ronald's published Zenodo canon definitions
  (same open item flagged at the top of `tier1_candidate_operators.py`).
