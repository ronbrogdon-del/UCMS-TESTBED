# Tier-1 Multi-Scenario Structural Test — Results (2026-06-17)

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
