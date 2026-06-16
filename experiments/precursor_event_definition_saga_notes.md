# Precursor Event Definition — v1/v2/v3, and Why None of Them Land Yet

## v1: top-1% system load (88 hrs)
Null test: true precursor curvature at 2.9th/2.1st percentile of random —
LOWER than chance. Explanation: routine peak demand is approached
smoothly (predictable diurnal ramp). Not a rupture-like event to begin
with.

## v2: bottom-1% system headroom (88 hrs)
**Mistake, caught before being reported as a result.** Headroom = fixed
capacity − load. With capacity held fixed, bottom-1%-headroom is
mathematically the *identical* set of 88 hours as top-1%-load — confirmed
by direct set comparison (88/88 overlap). Not an independent test;
discarded.

## v3: top-1% hour-to-hour load RAMP, |ΔLoad(t)| (88 hrs)
Genuinely different event set (0/88 overlap with v1). Null test result:
true precursor curvature at the **100th percentile** of 2000 random draws
for both coherence and stress — i.e. higher than every single random
draw.

**Before treating that as a finding:** checked whether the 24h lookback
window before each event already contains elevated ramp activity, which
would mean the "precursor" is just detecting that the event sits inside a
longer ramp, not a separate buildup. It does: mean |ΔLoad| in the 24h
before each event is 1,750 MW/h vs. 1,362 MW/h overall (~28% higher), and
on average ~9 of those 24 hours are themselves at least half the p99 ramp
threshold. Real load ramps (e.g. the morning rise) are multi-hour
processes; picking the single sharpest hour as "the event" and looking at
the preceding day almost guarantees you're still inside the same ramp.

**Conclusion: the 100th-percentile result is very likely this artifact,
not a precursor signal.** Not disproven outright, but the obvious mundane
explanation fits the data well enough that it shouldn't be reported as a
finding without controlling for it.

## What an actually clean test needs
Either:
1. **Isolated events** — require the lookback window itself to NOT
   contain other elevated-ramp hours (i.e. only count a ramp as an
   "event" if it's a genuine spike out of otherwise calm conditions, not
   the peak of a multi-hour climb), or
2. **A structurally different event type** — an actual N-1 contingency
   trip (branch removed, re-solved) is a topological discontinuity with
   no load-ramp autocorrelation problem at all, since it isn't derived
   from the load series in the first place. This also directly matches
   Section 3 of the original test-suite document ("Rupture-Trajectory
   Ensembles") and the README's already-stated next experiment, neither
   of which has been started.

## Status
Three event definitions tried, three different and honestly-reported
outcomes (smoother-than-random, an identical-set mistake caught before
being reported, and a likely-artifactual positive). No clean precursor
result yet. All tagged CANDIDATE_SPEC_v1.
