# Gas–Electric Seam Testbed (Texas7k combined electric–gas case)

Ronald L. Brogdon, Upstream Coherence Measurement Stratum (UCMS)
ORCID: https://orcid.org/0009-0009-0507-2971 · measurement@coherencemanagement.org

Status: **exploratory, pre-freeze** (work of 21–24 November 2026). Nothing here is a sealed result.

## Study question

On the transmission-to-plant gas–electric seam, does an SCFL precursor window open early enough to give engineers options before gas-fired plants run back or trip? Instrument verification on a coupled synthetic testbed, not a measurement of the real ERCOT seam. Protocol draft: `protocol/SCFL_Gas-Electric_Preregistration_v0.2.md`.

## What is here

| Folder | Contents |
|---|---|
| `src/` | Converter (Texas7k → GasTranSim), spin-up, case builders, gas-only runner, coupled gas–electric driver, electric-side preparation, seam mapping, SCFL input builder, standard four-cell notebook builders |
| `env/` | Julia `Project.toml` / `Manifest.toml` for GasTranSim |
| `records/` | Conversion log, seam map, coupling data, scenario files, readiness and preliminary-run READMEs, spin-up drift, trial summaries, coupled-run minute-by-minute records |
| `inputs/` | SCFL input packages (input-folder format) v1 (margin), v2 (clean/noise), v3 (30 noise seeds) with `SHA256SUMS` |
| `notebooks/` | Standard four-cell Colab notebooks for v1–v3 |
| `protocol/` | Pre-registration draft v0.2 |

**Not included:** the Texas7k dataset (download from https://electricgrids.engr.tamu.edu/7k-electric-gas/), the SCFL engine, and any SCFL readings (held until the write-up).

## Tools

- GasTranSim.jl v0.3.0, commit `4a21da84e7cb94e3e6ef2b12cbe1d05810d49525` (https://github.com/kaarthiksundar/GasTranSim.jl), explicit staggered-grid method (Gyrya and Zlotnik, Applied Mathematical Modelling, 2019); Julia 1.13.4; CNGA equation of state (coefficients identical to `z_b1`, `z_b2` in Texas7k_Gas.json).
- pandapower 3.5.6 with matpowercaseframes for the electric case (base AC power flow converges: 6,717 buses, 74.7 GW load).

## Data findings (Texas7k_Gas.json)

- 2,451 gas nodes (matches the IET paper; the case page's 2,459 is treated as a page error).
- Units: pressure kPa, flows standard m³/h (inferred).
- Negative `p` values (154 nodes) are a sign artifact of a squared-pressure solve; pressure = |p|.
- 839 pipes have resistance `k` inconsistent with friction/length/diameter (558 by exactly 2× resistance); friction re-derived from `k`.
- 23 zero-length pipes (merged), 4 negative lengths (absolute value), Texas7k.AUX corrupted in the bus section (not used).
- No capacity limits in the data (compressors: ratio only; pipes: no maximum operating pressure).

## Modelling choices

- Pipes under 1 km lengthened to 1 km with the same steady pressure drop (explicit-scheme stability).
- 76-hour no-shortfall spin-up to settle (`records/longspin_drift.csv`; final drift −0.055 kPa/h).
- Supply cap: the slack node is replaced by a fixed supply at its settled delivery (`make_case.py ... cap`).
- Minimum delivery pressure 2.8 MPag (2,901.3 kPa abs), low end of a published OEM gas-turbine fuel specification (2.8–5 MPag).
- Margin for SCFL inputs: weakest plant pressure minus minimum delivery pressure.
- Declared sensor noise (v2, v3): Gaussian sd 1.4 kPa (Rosemount 3051P reference accuracy 0.04% of a 0–1,500 psig span, read as 3σ), fixed seeds.

## Coupling rules (agreed 24 Nov 2026; `src/coupled_run.jl`)

1. Plant gas node below 2.8 MPag → units run back to minimum load; below 2.52 MPag → trip (declared assumption). Latched.
2. Lost MW replaced from non-gas spare, then from gas plants still above the floor; remainder is firm load shed, pro rata statewide (copper plate, v1).
3. Loop ("uri" mode): shed fraction cuts processing-plant supply and electric-compressor boost (10% of compressors, placeholder); "posturi" mode protects gas facilities.
4. Plant gas withdrawal follows plant MW.

## Results so far (exploratory)

- Gas-only, 41% of state supply lost: no plant below the floor within 12 h; line pack is the buffer (`records/trials_summary.csv`).
- Coupled, 41% lost from hour 1: first runback at 20.1 h; 50 plants in runback and 10.4 GW lost by 30 h, all covered by spare; no load shed, so the loop never engaged (Uri and post-Uri identical) (`records/coupled_cut41_*`).
- Compared with Uri: gas-supply-driven losses are of the same order (Uri: 9.3 GW cumulative gas derate due to supply), but the testbed lacks Uri's non-gas freezing outages and demand surge, so its timing is not comparable.

## Reproducing

Scripts currently use absolute paths from the build workspace (`/home/claude/...`); a path-independent replication package with a single run command and expected-output fingerprints is planned before the freeze.
