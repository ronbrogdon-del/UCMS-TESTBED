# TIER1_CANDIDATE_SPEC_v1 — Results

**Status: CANDIDATE, not canon.** Math came from a third-party draft, not
your Zenodo papers (still not located). Treat every number below as
provisional pending reconciliation.

## A/B — Seam coherence & coupling stress (continuous, all 8784 hours)

- 127 deduplicated seam pairs used (matches the established ground-truth
  count exactly — good consistency check).
- Seam coherence C(t): mean 0.228, range [-2.18, 0.91]. **This mean is not
  a finding** — for a roughly-Gaussian zero-mean difference series
  normalized by its own std (which is what C_ij is, by construction),
  E[1 - |Z|] ≈ 1 - √(2/π) ≈ 0.20 is the expected value under pure noise
  with no structure at all. The observed 0.228 is right where you'd
  expect it whether or not anything interesting is happening. The
  *level* of this operator isn't informative; only deviations from this
  baseline would be.
- Coupling stress (normalized): mean 0.0013, range [0.0001, 0.0059].

## C/D — Precursor operator, Δ1/Δ2, τ½, R

Events defined independently of any operator: top 1% system-load hours
(88 hours, threshold 61,480 MW) — same non-circularity rule already
stated in this repo's README.

**Null test result (the part that matters):** precursor curvature
(max |Δ2| in the 24h before each event) was compared against 2000 random
88-hour draws.
- Coherence-curvature: true mean 0.1972 vs. null mean 0.2125 — **true
  value at the 2.9th percentile** of the null distribution.
- Stress-curvature: true mean 0.000373 vs. null mean 0.000411 — **true
  value at the 2.1st percentile**.

Both land in the LOW tail, not the high tail. A genuine precursor signal
would show curvature elevated before events (high percentile). This
shows the opposite: the approach to peak-demand hours is smoother than a
random hour, not more volatile.

**What this actually means:** not "the operator failed" so much as "the
event definition was wrong for this purpose." Top-1%-load hours are
routine, predictable diurnal/seasonal peaks — the load curve ramps up
gradually all afternoon, so of course curvature is low beforehand. That's
not a rupture-like event in any SCFL sense; it's the most forecastable
thing in the dataset. A real test of precursor capability needs a
genuinely discontinuous event (an N-1 contingency trip, a non-convergence
point from Section 1's PV sweep, a sudden hour-to-hour load jump well
above the typical diurnal ramp rate) — none of which this run used.

τ½ and R were computed per-event for the stress series (all 88 events
recovered within the 168h window, no censoring needed) but interpreting
them is secondary to the event-definition issue above — recovery dynamics
around a smoothly-approached, smoothly-receding routine peak aren't
testing what τ½/R are meant to test either.

## Bottom line
- A and B are implemented and running cleanly.
- C/D's null test is the real result here: this candidate spec, tested
  honestly, does NOT show a precursor signal for routine peak-load
  events — and routine peak-load events were the wrong test case to
  begin with. The right next step is re-running the precursor test
  against an actual discontinuity (contingency trip), not iterating on
  this event definition.
- Everything here stays tagged CANDIDATE_SPEC_v1 until reconciled with
  the real canon.
