# Embedded Outage in Real Hourly Series — Time-Series Extension

## What this is

The first genuine multi-point time series in this testbed. Branch
8030–7389 (the most severe contingency in both the 3-point and 60-hour
static sweeps) is tripped for 72 consecutive real hours (5297–5368,
ending exactly at the year's actual peak-load hour), with 24h before and
24h after for context. Every hour is run twice — once with the branch
tripped, once as a counterfactual with it in service — using the same
real load for both. The difference between the two isolates the
outage's own marginal effect from ordinary load variation, which would
otherwise be a real confound (this was flagged as a risk before running,
not discovered after the fact).

## What it can and cannot support — checked, not assumed

**Δ1 (onset jump):** meaningful, and cleanly isolated. stress_diff is
exactly 0.0 for every hour before the outage starts (max|diff| =
0.00e+00, not just small) and exactly 0.0 again for every hour after
restoration — including the very first post-restoration hour. That's
not an assumption; it's what the actual 120-hour run produced. It
confirms directly, not just by argument, that this static framework has
no memory: the model returns to whatever N-0 gives for that hour's real
load **instantly** on restoration.

**τ½ and R: still not supportable**, and now for an empirically
demonstrated reason rather than a theoretical one — there is no decay
process to time, because there is no detectable residual effect at all
one hour after restoration. Embedding a real multi-hour outage doesn't
change this; it was never going to, since the limitation is the static
power-flow model itself, not the length of the outage.

**Δ2 (curvature): genuinely new and supportable now.** During the
72-hour outage, the outage's marginal stress effect is not a smooth
ramp — it oscillates with the daily load cycle. Autocorrelation peaks
sharply at 24h lag (+0.64, vs. −0.40 to −0.52 at the 6/18/30h offsets),
and the marginal effect correlates with load directly within the window
(r = 0.60): near zero or slightly negative overnight (as low as
−0.00011, i.e. the outage trivially *reduces* stress at the lowest-load
points), up to +0.0015 during the day. The three successive daily peaks
are 0.00122, 0.00122, 0.00141 — essentially flat across the first two
days, then a real step up on the third as the window closes in on the
year's actual annual peak. That step, not a uniform trend, is the
curvature.

## Honest scope

This shows the outage's marginal effect is structured and physically
sensible — tracking the daily load cycle, with a genuine (not assumed)
late uptick approaching the year's highest-stress hour — using a real
multi-point time series for the first time in this testbed, with the
load-variation confound explicitly controlled for via the counterfactual
difference rather than just disclosed and left alone. It is still not a
rupture/cascade test, still not dynamic, and still cannot speak to
recovery half-life or resilience — that requires actual transient
simulation (inertia, governor response), which this static framework
cannot produce no matter how the time window is chosen.

## Method
- Branch 8030–7389 tripped hours 5297–5368 (72h), window 5273–5392 (120h
  total: 24h pre, 72h outage ending at hour 5368 = year's peak, 24h post).
- Every hour run twice (actual vs. counterfactual-always-in-service),
  same real area-load/system-load scaling as all prior sweeps.
- 240 power-flow solves, 100% convergence both scenarios.
- Data: `embedded_outage_timeseries.csv` (hour, system_load_mw, in_outage,
  coherence/stress for both scenarios, and the differenced series).
