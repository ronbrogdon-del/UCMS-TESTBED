# N-1 Seam Contingency Severity — Hourly Trajectory (60 hours, load-percentile sampled)

## What this is and isn't

This extends `n1_seam_contingency_sweep.py` (which covered exactly 3 hours:
peak/median/min) to 60 hours, chosen by sorting all 8784 real annual hours
by system load and sampling evenly across that sorted order — so the
sample directly spans the full real load range rather than relying on the
calendar to happen to cover it.

This is **still a static power-flow study, not a dynamic/transient
simulation.** Only Δ1 (single pre/post jump per contingency) is computed,
for the same reason given in the original sweep: there is no time axis
after a trip, so Δ2/τ½/R would be fabricated, not measured. This is a
quasi-steady-state stress trajectory across real operating conditions —
**not** a rupture-cascade detection test. No fault sequence, no recovery
dynamics, no "known rupture" exists in this data (confirmed by direct
inspection of the .dyd/.dyr/.idv files — they're generator/inverter model
*parameters* and PowerWorld editing commands, not a disturbance event).

Consistency check: hour 2259 (this run's lowest-load point) is the same
hour as the original 3-point sweep's "min" operating point. Both runs
report the identical top contingency (branch 8030–7389, Δ1 stress =
+0.001584) — confirming this extension is methodologically identical to,
not a divergent redo of, the existing result.

## Result: severity is U-shaped in load, not monotonic

A naive linear/rank correlation between system load and severity is
**negative** (Spearman ρ = −0.529 for mean |Δ1 stress|, ρ = −0.895 for
max |Δ1 stress|, both p < 0.0001) — taken at face value this would say
"severity falls as load rises," which is true across most of the range
but is the wrong overall conclusion.

A quadratic fit makes the actual shape explicit: positive curvature term
for both metrics, R² = 0.43 (mean) and **R² = 0.92 (max)** — the U-shape
explains the max-severity trajectory almost completely. Fitted minimum
sits at ≈56,000 MW; the empirically lowest-severity hour in the sample is
at 51,024 MW — consistent with each other and roughly in the middle of
the observed 23,072–66,276 MW range.

Concretely: the lowest-load hour (23,072 MW) and the highest-load hour
(66,276 MW, the year's actual peak) have almost identical mean severity
(0.000116 vs 0.000120) — both elevated relative to the calm middle — but
for different and physically distinct reasons:

- **At light load:** elevated severity is overvoltage-driven (max bus
  voltage post-contingency reaches 1.195 p.u. at the lowest-load hour,
  with vmin staying pinned at the 0.99 floor — no undervoltage at all).
  This matches the already-documented static-model artifact: no switched
  shunts or OLTC tap adjustment, so generator voltage setpoints push
  nearby buses high when load drops and a seam line is lost.
- **At peak load:** elevated severity is undervoltage-driven instead
  (min post-contingency voltage drops to 0.953 p.u. at the year's peak
  hour) — this is the physically expected direction for heavy loading,
  and is new information the original 3-point sweep didn't surface,
  because it only reported binary limit violations (0/131 at peak) and
  peak voltage in this run never quite crosses the 0.90 floor — the
  *continuous* Δ1 severity is still climbing well before it would,
  visible only because this run has resolution between the 3 original
  points.

## Honest scope of the claim

This is real evidence that Δ1 (the one operator a static contingency
snapshot legitimately supports) responds in a structured, physically
interpretable way to real annual operating variation — elevated at both
extremes for distinct, identifiable reasons, calm in the middle. It is
**not** evidence about rupture/cascade detection, precursor windows, or
Δ2/τ½/R, none of which this method can produce. Whether this generalizes
beyond seam branches, beyond this static-dispatch assumption, or to an
actual transient event remains open.

## Method
- 60 hours, sampled by load percentile (not calendar) from the real
  8784-hour annual area-load series.
- Same area-proportional load / system-proportional generation scaling,
  same 131 seam branches, same coherence/stress reference baseline
  (V̄, σ from the full annual N-0 series) as the original 3-point sweep.
- 7,860 total contingency-solves (60 hours × 131 branches), 100%
  convergence, zero failures.
- Raw per-contingency data: `n1_hourly_trajectory.csv`.
  Per-hour aggregates: `n1_hourly_trajectory_summary.csv`.
