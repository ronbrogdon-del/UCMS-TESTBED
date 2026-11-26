# Confirmation package result (scored 26 November 2026)

Readings: 330 inputs, all READY; 2,310 output files match the operator's fingerprints; engine inputs identical to the package.
Scored against the pass criteria fixed in protocol Section 2B (commit 1908f5f) and the answer key `acute_truth.json`.
Counts only; operator settings and readings are not published here.

| Check | Criterion | Result | Pass? |
|---|---|---|---|
| Gate opens, each strain case (10 cases) | >= 29/30 | 30/30 in every case | PASS |
| Gate stays shut, control | <= 1/30 | 0/30 | PASS |
| Tier A, Houston c15 early (acute, 52.8 kPa) | >= 27/30 | 30/30 | PASS |
| Tier A, Houston c20 late (acute, 41.4 kPa) | >= 27/30 | 0/30 | **FAIL** |
| Tier A, non-acute failures c21, c23, c27, c1 | <= 1/30 each | 0/30 each | PASS |

**Overall: FAIL** (one row). Stage 1 (precursor gate) passed every row. Tier A missed the acute break that
occurs three hours into an established strain: RUPTURE did not fire and the STRESS 20-min rise (34–41) did not
reach twice the tuning ceiling. Both tuning-package acute breaks occurred within about an hour of strain onset,
so the tuning set did not cover a late acute break.

Gate opening time after strain onset (median): 30% loss 2.42 h; 41% loss 0.83 h; 47% loss with 1 h ramp 0.58 h; 41% loss with 4 h ramp 1.21 h.
