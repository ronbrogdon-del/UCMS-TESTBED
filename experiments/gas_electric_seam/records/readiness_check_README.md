# Texas7k gas network in GasTranSim: load and steady-hold check

Prepared 21 November 2026 for the SCFL gas–electric seam test (instrument verification on a coupled synthetic testbed).
Ronald L. Brogdon, Upstream Coherence Measurement Stratum (UCMS), ORCID https://orcid.org/0009-0009-0507-2971

This is a simulator readiness check only. No shortfall was injected, and no SCFL computation was run on this output.

## Tools
- GasTranSim.jl v0.3.0 (https://github.com/kaarthiksundar/GasTranSim.jl), explicit staggered-grid method of Gyrya and Zlotnik (Applied Mathematical Modelling 65, 2019)
- Julia 1.13.4 (conda-forge)
- Equation of state: GasTranSim `:simple_cnga`. Its coefficients b1 = 1.00300865 and b2 = 2.96848838e-8 are identical to `z_b1` and `z_b2` in Texas7k_Gas.json.

## Findings about Texas7k_Gas.json
1. Units: pressure in kPa; flows in standard m³/h (inferred: the pipe equations give 4,601 file units per kg/s, against 4,600 m³/h per kg/s from the file's own STP constants).
2. Negative pressures: the pipe data satisfy p1² − p2² = k·q|q| exactly (2,472 pipes). Across the 27 pipes where the sign of p flips, the magnitudes are continuous. The negative signs are an artifact of a solve in squared pressure; the pressure is |p| (3,651–4,156 kPa at those nodes).
3. Resistance: 839 of 2,468 pipes have k inconsistent with their friction factor, length and diameter (558 by exactly a factor of 2 in resistance). The solved flows follow k.
4. 23 pipes have zero length; 4 have negative length.

## Conversion choices (t7k_to_gts.py; logged in conversion_log.json)
- Pressure |p|, kPa → Pa. Flow std m³/h → kg/s.
- Zero-length pipes: end nodes merged (2,451 → 2,428 nodes).
- Negative lengths: absolute value.
- Friction factor re-derived from k (843 pipes changed), so the simulator starts from the file's solved state.
- Pipes shorter than 1,000 m (172) lengthened to 1,000 m with friction scaled to keep the same steady pressure drop (required by the explicit scheme's stability limit).
- Slack node 699: pressure-controlled. All other nodes: fixed withdrawal at the file's qf. Compressors: fixed ratio r.
- Time step 1.74 s; output every 600 s.

## Steady-hold result (2 simulated hours, no injection; run time about 4.5 minutes)
| | file friction | friction from k (delivered case) |
|---|---|---|
| Median node pressure drift | 0.44% | 0.05% |
| 95th percentile | 1.96% | 0.29% |
| Maximum | 14.3% | 0.57% |
| Nodes drifting > 5% | 13 | 0 |
| Drift in last 30 min (max) | 0.75% | 0.10% |

No numerical failures; minimum pressure 3,210 kPa.

The delivered case (gts_t7k_k) holds steady and is still settling slightly (expected: the file was solved with a constant compressibility, GasTranSim uses the CNGA model). A spin-up run to full settling, used as the starting state for control and shortfall runs, belongs in the calibration phase (protocol Section 2A).

## Not yet done
- Coupling to the electric side (gas pressure at plant nodes → generator availability → power flow).
- Shortfall injection (GasTranSim has a built-in disruption feature for nodes and pipes).
- Driving load and weather shapes.

## Files
- gts_t7k_k/: GasTranSim input files (network, params, ic, bc, disruptions) and conversion_log.json
- t7k_to_gts.py: converter. Usage: `python3 t7k_to_gts.py Texas7k_Gas.json <out_dir> 1000 2 k`
- hold_run.jl: steady-hold run script
