# Annual Voltage Series — Notes

8784/8784 hours converged. Method: see docstring in
`src/testbed/build_annual_voltage_series.py` — area-proportional load
scaling (real 2016 hourly data) + system-wide proportional generation
scaling (NOT the single-slack assumption used in Section 1's PV/QV sweep;
different purpose, stated explicitly to avoid conflating the two).

## Sanity checks (face validity)

- Global voltage range: 0.968–1.188 p.u. No bus ever drops below its 0.90
  VMIN. 134/2000 buses exceed their stated 1.10 VMAX at some hour; 19
  exceed 1.15.
- **These overvoltage events correlate -0.92 with system load** — i.e.
  they happen almost exclusively at the lowest-demand hours of the year
  (131 of those 134 buses are over 1.10 simultaneously at the year's
  minimum-load hours). This is classic light-load overvoltage: real grids
  counteract it by switching off shunt capacitors and adjusting
  transformer taps. This static model holds shunts/taps fixed across all
  8784 hours, so the effect shows up unmitigated. Expected behavior given
  the simplification, not a bug — but it means any operator computed on
  this series will see a real, physically-explained voltage swing at
  light-load hours that has nothing to do with stress/precursor dynamics.
  Worth remembering before interpreting any signal that spikes at
  low-load hours.

## What this means for the operators built on top of this data

Seam-coherence and coupling-stress operators (TIER1_CANDIDATE_SPEC_v1) will
inherit this light-load-overvoltage signature. If either operator shows a
strong seasonal/diurnal pattern that tracks system load inversely, that's
this artifact surfacing, not a new finding — check against the load
profile before reading too much into any such pattern.

## Status
Annual voltage series complete, 0 failures, face-validity checks pass and
are explained by known physics. Ready as input for TIER1_CANDIDATE_SPEC_v1.
