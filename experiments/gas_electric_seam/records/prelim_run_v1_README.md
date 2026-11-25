# Preliminary exploratory run: Texas7k gas network, regional supply shortfall (gas-only)

Run date: 21 November 2026
Ronald L. Brogdon, Upstream Coherence Measurement Stratum (UCMS), ORCID https://orcid.org/0009-0009-0507-2971

## Status
Exploratory. The shortfall size, location and timing are illustrative placeholders, not protocol tiers. Because SCFL will be run on this output, the injection region used here (north Texas, around gas node 546) must be excluded from, or declared in, the sealed test design.

Gas-only: there is no electric-side coupling, so no impact time is defined. Gas withdrawals at plant nodes are held fixed; the response shows up as pressure.

## Simulator
GasTranSim.jl v0.3.0, Julia 1.13.4, CNGA equation of state. Texas7k converted with t7k_to_gts.py (friction from k, 1 km minimum pipe length; see the readiness README). Spun up for 4 h with no injection; both runs start from that saved state.

## Runs
| | control | shortfall |
|---|---|---|
| Horizon | 8 h | 8 h |
| Output interval | 300 s (97 points) | 300 s (97 points) |
| Injection | none | 12 processing plants within 250 km pipeline distance of node 546: supply cut 50%, linear ramp from 1 h to 3 h, then held |

The cut equals 4.4% of total system supply. The region's 19 gas-fired plant nodes within 250 km take 25% of all gas-for-power draw. Cut plants: 546, 553, 556, 605, 613, 618, 650, 658, 661, 674, 681, 697 (scenario.json).

## Checks
- Same time axis in both runs; all 115 plant nodes present; no missing or NaN values.
- Before the ramp (0–1 h), shortfall and control agree to within 0.0001 kPa.
- Control drift over 8 h: up to 0.79% at any plant node (residual settling).
- Minimum pressure anywhere: 3,171 kPa (control), 3,168 kPa (shortfall).

## What the physics shows (shortfall minus control, plant nodes)
- Pressure falls steadily from the start of the ramp and is still falling at 8 h.
- 18 plant nodes are more than 1% below control at 8 h; worst −4.1% (nodes 55, 57, 61, 62, 63). The median plant node is −0.13%.
- Worst-node trajectory: 2 h −0.4%, 3 h −1.2%, 4 h −2.1%, 6 h −3.3%, 8 h −4.1%.
- No node approaches a low-pressure limit within 8 h.

## Files
- plant_nodes.csv: gas node to substation number, name, location, gas draw
- control_pressure_kPa.csv, shortfall_pressure_kPa.csv: one column per plant node; elapsed_s is authoritative, timestamps are nominal (synthetic start 2026-01-01T00:00)
- checks.json, scenario.json
