# Tier-1 Follow-Up Checks — Effect Size, Voltage Angle, Line Flow, N-1 (2026-06-17)

Script: `src/testbed/tier1_multiscenario_followups.py`
Outputs: `experiments/tier1_followup_{effect_size,voltage_angle,line_flow,n1_delta1}.csv`

Four follow-ups on the seam-vs-non-seam |dVm| pattern in
`tier1_multiscenario_permtest.py`. Headline: **the pattern does NOT
generalize uniformly across observables** — three different shapes show
up depending what's measured. That's the actual finding here, not a
inconvenience to explain away.

## 1. Effect size (median |dVm|, seam minus connected-non-seam)

| Case | Median seam \|dVm\| | Median non-seam \|dVm\| | Effect (p.u.) | Effect (% of non-seam) |
|---|---|---|---|---|
| baseline | 0.00608 | 0.00508 | +0.00100 | +19.7% |
| case1 2016 summer peak | 0.00559 | 0.00497 | +0.00063 | +12.7% |
| case2 2016 low load | 0.00411 | 0.00313 | +0.00098 | +31.4% |
| case3 2024 summer peak | 0.00696 | 0.00568 | +0.00128 | +22.5% |
| case4 2024 low load | 0.00640 | 0.00364 | +0.00276 | +75.7% |
| case5 2024 high renewables | 0.00695 | 0.00328 | +0.00368 | +112.2% |
| case6 2024 low load+GFM | 0.00639 | 0.00364 | +0.00276 | +75.7% |

**2016-group mean effect: +0.00087 p.u. 2024-group mean effect: +0.00262
p.u. — the 2024 effect is 3.00x the 2016 effect**, consistent with the
earlier significance-cliff finding, now in plain physical units (p.u.
voltage) instead of just p-values.

## 2. Voltage angle — pattern present in ALL seven cases, not just 2024

This is different from voltage magnitude. Median angle separation
(seam minus non-seam) is significant (permutation p<0.0001, exact
Mann-Whitney p<1e-5) in every single case, including all three 2016-era
ones:

| Case | Median angle effect (deg) |
|---|---|
| baseline | +0.545 |
| case1 | +0.619 |
| case2 | +0.488 |
| case3 | +0.847 |
| case4 | +1.191 |
| case5 | +1.246 |
| case6 | +1.196 |

So angle separation across seams is a real, year-independent structural
feature — present even in 2016 — that roughly doubles in size by 2024
(≈0.5-0.6° → ≈0.85-1.25°), but doesn't show the 2016 "non-significant"
floor that magnitude showed. **Different observable, different shape of
the same underlying story**: magnitude crosses a significance threshold
only in 2024; angle is significant throughout and just grows.

## 3. Line flow |S| (MVA) — scenario-specific, not year-specific

This is the one that breaks the clean "2016 vs 2024" narrative outright.
Individual in-service branches (not deduplicated bus-pairs, since flow
is a per-circuit quantity):

| Case | Effect (median seam − non-seam, MVA) | perm p | MW p (asymptotic) |
|---|---|---|---|
| baseline | −24.6 | 0.062 | 0.89 |
| case1 2016 summer peak | −21.7 | 0.045 | 0.80 |
| case2 2016 low load | −1.3 | 0.075 | 0.095 |
| case3 2024 summer peak | −11.3 | 0.103 | 0.37 |
| case4 2024 low load | **+15.4** | **<0.0001** | **1.8e-8** |
| case5 2024 high renewables | **+27.6** | **<0.0001** | **5.3e-13** |
| case6 2024 low load+GFM | **+15.4** | **<0.0001** | **1.7e-8** |

case3 (2024 summer peak) is statistically indistinguishable from the
2016 cases — small/negative effect, not significant. case4/5/6 (the
*other* three 2024 scenarios — low load, high renewables, low
load+GFM) flip to a large, significant positive effect. **This tracks
load level / generation mix, not calendar year**: it's the three
non-summer-peak 2024 scenarios that show elevated seam loading, not
"2024" as a block. Worth remembering before reusing the "2016 vs 2024"
framing elsewhere — it held for magnitude and (loosely) angle, but flow
shows it's really about operating condition, with year acting as a
confound because 3 of 4 2024 cases happen to be non-peak conditions.

## 4. N-1 Delta1 (max system-wide |dVm| from tripping one branch) — the pattern INVERTS

Each seam branch tripped individually (full set per case); non-seam
branches sampled at random (300/case, capped for runtime — full
non-seam population is 3000+/case). Delta1 = max |Vm_after − Vm_before|
across all 2000 buses, one trip at a time.

| Case | Median Delta1 seam | Median Delta1 non-seam | Effect | perm p | MW p (exact) |
|---|---|---|---|---|---|
| baseline | 0.00967 | 0.00525 | +0.00443 | **0.020** | **1.6e-5** |
| case1 | 0.00805 | 0.00506 | +0.00299 | **0.031** | **4.5e-5** |
| case2 | 0.00697 | 0.00344 | +0.00354 | **0.0064** | **1.8e-7** |
| case3 2024 summer peak | 0.00290 | 0.00303 | **−0.00012** | 0.50 | 0.36 |
| case4 2024 low load | 0.00257 | 0.00212 | +0.00046 | 0.14 | 0.0051 |
| case5 2024 high renewables | 0.00350 | 0.00270 | +0.00080 | 0.47 | 0.0030 |
| case6 2024 low load+GFM | 0.00257 | 0.00219 | +0.00038 | 0.20 | 0.0096 |

**All three 2016 cases: seam-branch outages are significantly more
disruptive than non-seam outages, on both tests, no exceptions.** All
four 2024 cases: that gap shrinks or vanishes on the primary
(mean-difference) test (case3 even flips sign, though not
significantly); Mann-Whitney still detects a weaker rank-based signal in
3 of 4 2024 cases, but not case3, and not at the strength seen in 2016.

This is the opposite direction from the static-snapshot findings above.
**One plausible (not yet tested) explanation**: the 2024 cases have
more seam branches in absolute terms (191-213 vs 131-137 in 2016) —
more inter-area ties were added between 2016 and 2024 — so any single
seam line carries proportionally less unique importance even though the
boundary as a whole shows a stronger static electrical signature.
That's a real, testable follow-up (e.g. N-2 on seam pairs, or
normalizing by seam redundancy), not yet run.

## What this means for the "seams got more significant 2016→2024" claim

Stated plainly: that claim is **observable-dependent, not a single
clean fact about the grid**. It holds clearly for voltage magnitude and
(less cleanly) for line flow. It does NOT hold for the dynamic N-1
severity measure — if anything that one points the other way. Voltage
angle shows a related but distinct pattern (always present, growing in
size rather than crossing a significance threshold). Any future paper
or pitch claiming "seam structure became more electrically significant"
needs to specify WHICH observable, not generalize across all of them.

## Caveats

- N-1 non-seam sample capped at 300/case (not the full ~3000+ population)
  for runtime; seam trips use the full population in every case.
- Non-convergence on a trip (radial-bus islanding, etc.) is excluded
  from the Delta1 distributions, not imputed — failure counts are in
  the CSV (`seam_trip_nonconverged` / `nonseam_trip_nonconverged`)
  and were noticeably higher for non-seam trips in every case, itself
  a data point not yet analyzed.
- Multiple comparisons across 4 follow-ups x 7 cases x ~2 tests each
  = ~56 p-values, none corrected. The case3/4/5/6 N-1 Mann-Whitney
  significances (p~0.003-0.01) would not survive a strict correction;
  the case4/5/6 line-flow and the 2016 N-1 results (p<1e-4) would.
