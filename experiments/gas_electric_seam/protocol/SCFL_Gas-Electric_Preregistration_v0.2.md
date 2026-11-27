# SCFL Gas–Electric Seam: Instrument Verification on a Coupled Synthetic Testbed
## Pre-Registered Experimental Protocol

### Status
This document freezes the experimental design before any sealed simulation run. A blind calibration phase (Section 2A) precedes the freeze and may set injection parameters; it never involves the SCFL engine. After the freeze, simulator outputs may inform interpretation, but they may not change the protocol defined here. Dataset inspection was completed on 21 November 2026 (see Section 2.4), before this protocol was frozen.

### Scope statement
This is instrument verification on a synthetic coupled electric–gas model. It tests whether the frozen SCFL engine reads a precursor window at the gas–electric seam when a gas shortfall of known size and timing is injected. It does not measure precursor windows on the real ERCOT gas–electric seam. That requires observed gas-delivery and generation data and is reserved for a separate, funded, pre-registered phase.

---

# 1. Objective

Determine whether SCFL readings at the gas–electric seam leave a pre-declared control band before the electric side breaks, under injected gas shortfalls of known size, location and timing. That interval is a precursor window.

Primary outcome:

- Precursor-window length: the interval between the SCFL control-band exit (Section 10) and the impact time (Section 11).

Secondary outcomes:

- Detection consistency within each onset class
- False-exit rate, from no-shortfall control runs
- Sensitivity across severity tiers and onset classes

---

# 2. Dataset and Simulator Definition

## 2.1 Network dataset

Texas Combined Electric–Gas Test Case, Texas A&M University (synthetic; no confidential infrastructure data).

- Electric: Texas7k, 6,717 buses, 731 generators (475 gas-fired). Source formats used: Texas7k.m and Texas7k.RAW.
- Gas: Texas7k_Gas.json, 2,451 nodes, 2,495 pipes, 32 compressors, 115 electric-load gas nodes linked to substations.
- Citation: Y. Abu-Khalifa and A. B. Birchfield, "Techniques for creating synthetic combined electric and natural gas transmission grids," IEEE Transactions on Industry Applications, 2023.

The dataset is a single solved snapshot. It contains no time series, prices, congestion or reserve data.

## 2.2 Simulator

- Coupled transient gas / power simulator: [TO BE FILLED: name, version, source]
- Gas–power coupling method: [TO BE FILLED]

The protocol cannot be frozen until the simulator is named.

## 2.3 Variables produced by the simulator

Time step (fixed by the simulator configuration, not by the dataset):

- [TO BE FILLED]

Gas layer:

- Node pressures (subject to the resolution of Section 2.4, item 2)
- Pipe and compressor flows
- Storage withdrawal and injection
- Supply-entry flows

Electric layer:

- Load
- Generation by unit and fuel
- Prices, congestion and reserves: include only if the simulator produces them; declare here before the freeze: [ ]

## 2.4 Dataset findings and open items (inspection of 21 November 2026)

Checks that passed: one connected gas network; no dangling or self-loop branches; nodal flow balance closes to rounding error at every node except the slack; all 115 electric-load gas nodes map to real substations, each with gas-fired units; bus count consistent across .m, .RAW and the .AUX substation table.

Resolved:

1. Node count: the JSON has 2,451 gas nodes. This matches the published description of the case (Birchfield and Abu-Khalifa, "Structural characterisation for the synthesis of large-scale combined electric–gas networks," IET Energy Systems Integration, 2024, doi:10.1049/esi2.12170: 6,717 electric buses and 2,451 gas nodes). The 2,459 on the case web page is treated as a page error.

Open items to resolve before the freeze:

2. Pressure field: 154 nodes carry negative "p" values (minimum about −4,156). Meaning and units of "p" to be confirmed.
3. Units: no units stated in the file.

Known issues, handled as stated:

4. Texas7k.AUX is corrupted (a generator block spliced into the bus section; buses 210092–250121 missing there). Not used.
5. The slack node shows qf = 0 while it supplies about 135,757 units to balance the network. Slack supply is taken from the flow solution, not from qf.
6. 7 electric-load gas nodes draw gas although every gas-fired unit at their substation is offline. Treatment: [ ]
7. 2 substations with gas-fired units (155.9 MW in service) have no gas link. Treatment: [ ]

Resolution of items 2–3 and the chosen treatments for items 6–7 shall be recorded here before the freeze.

8. No solver is distributed with the dataset. The authors report solving the case (the qf flows are a steady-state solution), but their solver is unpublished. Availability: [ ]

---

# 2A. Calibration Phase (before the freeze)

A calibration pass checks that injections behave as designed in the simulator. It does not test SCFL.

## Blind rule

- Calibration runs are never fed to the SCFL engine, and no SCFL reading is computed or viewed during calibration.
- Calibration runs are excluded from the sealed dataset and from every statistic in Sections 12–14.
- Calibration uses simulator output only.

## What calibration checks

1. Severity tiers: each tier produces its intended effect. The lowest tier may produce no impact; the highest tier reliably produces impact within the simulated horizon.
2. Impact-time definition: it triggers cleanly and is not tripped by numerical noise.
3. Onset classes: glacial, brittle and flash ramps produce clearly separated onset-to-impact intervals. Glacial leaves enough time before impact for a precursor window to be possible.
4. Control runs: no-shortfall runs remain stable and produce no impact.
5. Numerical stability: the simulator converges through all injection types.

## Calibration record

- Calibration runs performed (count, inputs, locations): [ ]
- Results of checks 1–5: [ ]
- Changes made to Sections 4, 5, 6, 8 or 11 as a result, with reasons: [ ]

Sections 4, 5, 6, 8 and 11 are filled in from the calibration record and then frozen. No change is permitted after the first sealed run. Calibration is an internal run and does not require a separate deposit; it is reported with the sealed results.

---

# 2B. Operator Tuning Phase (before the freeze)

Section 2A checks the physics injection and never uses the SCFL engine. This phase is separate: it tunes the engine's operator settings on a dedicated tuning set, then freezes them.

## Operators in scope

- Tuned: DRIFT, SHIFT, RUPTURE, STRESS, QUENCH.
- KINETIC is in scope only if a form for this data class is supplied before the freeze; otherwise it is reported as not computed.
- QUENCH is tuned only on tuning runs that include a recovery phase (Section 7). Without one it is reported, not relied on.

## Tuning set

- Built from scenarios that are disjoint from the sealed set: different failure stations, strain levels, regions, onset timings and noise seeds.
- The exploratory runs v1–v4 (November 2026) belong to the tuning set. They are excluded from the sealed dataset and from every statistic in Sections 12–14.
- Each tuning package is stamped with its testbed commit.

## Roles

- The operator settings are chosen and adjusted by the UCMS team leader. They are proprietary and are not published or retained by anyone outside UCMS.
- Testbed construction, tuning data and checks of readings against simulator ground truth are done separately from the choice of settings.

## What is frozen at the end of tuning

1. Engine fingerprints (v1.1.0 or a successor version, stated).
2. A fingerprint of the full operator configuration, deposited without the values.
3. The decision rule for a precursor window: which operator readings count, the search window, and how a control exit is scored.
4. The role assigned to each operator in this test (for example, SHIFT as strain-onset reading, STRESS as break marker), stated before the sealed run.
5. The period setting (hourly unless changed here).

## Claims carried into the sealed test (decided 26 November 2026, after tuning package 1)

1. **Precursor gate (Stage 1).** Under supply strain, SHIFT opens a gate; in controls it does not. Ground truth is physical: a run has strain if processing-plant supply is cut in the simulator. Gate timing is reported against strain severity and ramp speed; no fixed time target is claimed.
2. **Acute break at the monitored plants (Stage 2, Tier A).** A station failure is an acute break if, in the simulator, it lowers the pressure at any monitored plant by at least 20 kPa within 1 hour, compared with the identical run without the failure. This definition uses simulator output only and was fixed before the confirmation package was built. In tuning package 1 the two Houston-area isolations dropped plant pressure by 48–50 kPa within 1 hour; every other failure dropped it by 5.3 kPa or less.
3. **Not claimed: distant breaks.** With the monitored plants alone, a distant station failure could not be told apart from strain that is still building. In the simulator the margin's erosion rate kept increasing in every strain case and did not ease and resume, so no physical event was available to score a "renewed worsening" label without fitting it to the readings. STRESS re-acceleration results are reported as exploratory. Locating distant breaks (adding compressor-station pressures to the state series) is a follow-on study.

## Confirmation package

Before the freeze, one confirmation package with fresh noise seeds, new strain severities and ramps, and failures at stations not used in tuning checks claims 1 and 2 with the rule unchanged. If the rule needs any change after the confirmation package, a further confirmation package is required.

Pass criteria for the confirmation package (fixed 26 November 2026, before the package was run; seeds 20261201–20261230, 30 per case):

| Check | Pass |
|---|---|
| Gate opens, each strain case | at least 29 of 30 seeds |
| Gate stays shut, control | at most 1 of 30 seeds |
| Tier A flags each acute break (Houston c20 late, Houston c15 early) | at least 27 of 30 seeds |
| Tier A flags each non-acute failure (stations c21, c23, c27, c1) | at most 1 of 30 seeds |

The package passes only if every row passes. Gate opening times are reported for every strain case. Scoring uses the answer key in `records/tune2/acute_truth.json`.

## Sealed scenario selection

- The sealed scenarios are drawn by a seeded script from the eligible lists in Sections 4–6. The seed is set by a person outside UCMS and is not known to anyone tuning the operators until after the freeze tag.
- No change to settings, decision rule or roles is permitted after the freeze tag.

## Publication

- Results are published whatever the outcome, together with the tuning record (counts and checks, not setting values).

---

# 3. Simulation Driving Inputs

The dataset snapshot does not contain demand evolution, so driving curves are imposed.

## Load shapes (select before the freeze)

- Normal weekday
- Peak summer
- Peak winter
- Shoulder season
- Extreme demand

Selected: [ ]

## Weather shapes (select before the freeze)

- Normal conditions
- Sustained heat event
- Sustained cold event
- Rapid weather-transition event

Selected: [ ]

Candidate source: the Texas A&M Electric Grid Test Case Repository's weather data (PoWer Weather format), from the same group that built the case. Source used: [ ]

Weather enters the simulation only through electric load and gas demand. The mapping from each weather shape to those two quantities shall be documented here: [ ]

Source and scaling method for every driving curve shall be documented before any run: [ ]

---

# 4. Disturbance Injection Framework

## Eligible injection locations

- Individual gas nodes
- Pipeline corridors
- Storage assets
- Supply-entry points

Frozen list of locations (by node or branch identifier): [ ]

Selection rule used to choose them: [ ]

---

# 5. Shortfall Severity Ladder

| Tier | Capacity reduction |
|--------|--------|
| Tier 1 | [ ] |
| Tier 2 | [ ] |
| Tier 3 | [ ] |
| Tier 4 | [ ] |

Severity values are fixed before any run.

---

# 6. Onset-Speed Taxonomy and Expected Outcomes

Onset speed is a declared property of each injection. Each class has its own pre-declared expected outcome. A flash run with no precursor window is the expected result, not a failure.

## Glacial

Gradual deterioration over an extended interval.

- Ramp duration: [ ]
- Maximum reduction: [ ]
- Expected outcome: control-band exit before impact time.

## Brittle

Intermediate-rate deterioration.

- Ramp duration: [ ]
- Maximum reduction: [ ]
- Expected outcome: control-band exit before impact time.

## Flash

Abrupt deterioration.

- Ramp duration: [ ]
- Maximum reduction: [ ]
- Expected outcome: no control-band exit before impact time (no precursor window).

---

# 7. Recovery Assumptions (secondary module)

Recovery affects only the post-event horizon. It does not affect the precursor-window outcome, which ends at impact time. Recovery is therefore a secondary module, run on a declared subset of scenarios so the primary run count stays manageable.

- Classes: no recovery / slow recovery / rapid recovery
- Definitions: [ ]
- Subset of scenarios receiving recovery runs: [ ]

---

# 8. Control-Band Construction

## Baseline runs

Number of no-shortfall runs per driving-input combination:

- [ ]

## Control envelope

Method (choose one before the freeze):

- Mean ± kσ
- Quantile envelope
- Other pre-declared method: [ ]

Band specification:

- [ ]

The control runs also supply the false-exit rate (Section 13).

---

# 9. SCFL Instrument

- Engine: SCFL engine v1.1.0, frozen 31 October 2026
- Freeze record: https://doi.org/10.5281/zenodo.23839571
- Readings evaluated (names only; definitions are as frozen in the engine): [ ]
- Seam inputs (which simulator variables are fed to the engine, on which side of the seam): [ ]

No reading, input or engine version may change after the first run.

Independence rule: no variable used to define impact time (Section 11) may be fed to the engine as an input.

---

# 10. Control-Band Exit Definition

A control-band exit is recorded when all pre-registered conditions hold.

## Threshold criteria

- [ ]

## Persistence criteria

- [ ]

## Data-quality filters

- [ ]

---

# 11. Impact Time and Precursor-Window Measurement

## Impact time definition

Impact time is the first time step at which the electric side breaks, defined by stage:

- Gas-only stage: the first time step at which the pressure at any gas-fired plant node (an "Electric Load" gas node) falls below the declared minimum delivery pressure.
- Coupled stage: the first time step at which a gas-fired unit derates or trips because its gas node is below the minimum delivery pressure, as passed to the power flow; secondary marker: first load shed.

Minimum delivery pressure: [ ] kPa, taken from a cited engineering source for gas-turbine fuel-supply requirements, fixed before calibration, and never adjusted in response to SCFL readings.

Calibration (Section 2A, check 2) confirms that this trigger fires in the highest severity tier and never in control runs.

Impact time is read from simulator output and is never an engine input (Section 9).

## Per-run record

- Control-band exit time (if any)
- Impact time (if any)
- Precursor window = Impact time − Exit time

Positive values indicate a precursor window.

## Handling of incomplete runs

- Shortfall run, no exit before impact: recorded as a miss, included in all rates, and excluded from the mean only if reported separately with the miss count.
- Shortfall run, no impact within the simulated horizon: recorded as "no impact" and reported separately.
- Control run with an exit: recorded as a false exit.

---

# 12. Fundability Classification

This classification decides whether the result justifies seeking funding for the real-data phase. It is an internal decision rule, set relative to the control band, not a claim about the real grid.

## Fundable

Criteria: in glacial and brittle runs, readings leave the control band before impact time, while flash runs and control runs do not.

Required threshold:

- Share of glacial and brittle runs with a precursor window: [ ]
- Maximum false-exit rate in control runs: [ ]

## Second look

Criteria: precursor windows appear in some glacial and brittle runs but below the Fundable threshold, or the control band is too wide to separate shortfall runs from control runs.

Required threshold:

- [ ]

## Not this seam

Criteria: shortfall runs stay inside the control band, or exits in shortfall runs are indistinguishable from false exits in control runs.

Required threshold:

- [ ]

These classifications are frozen before any run. The result is published whatever the classification.

---

# 13. Statistical Evaluation

## Scenario count

Full factorial (load shapes × weather shapes × locations × tiers × onset classes) is not run. The reduced design shall be declared here: [ ]

Total shortfall runs: [ ]
Total control runs: [ ]

## Aggregation method

- [ ]

## Confidence method

- [ ]

## Resampling method

- [ ]

## Outlier treatment

- [ ]

## False-exit rate

Computed from control runs only, with the same exit definition (Section 10).

---

# 14. Falsification Criteria

The hypothesis that the frozen engine reads a precursor window at this seam on this testbed is unsupported if one or more of the following occur:

1. Glacial and brittle shortfall runs do not leave the control band before impact time, at the rate required in Section 12.
2. The mean precursor window in glacial and brittle runs, counting misses as stated in Section 11, is non-positive.
3. Exits in shortfall runs are statistically indistinguishable from false exits in control runs.
4. Flash runs show precursor windows at a rate comparable to glacial and brittle runs. That would suggest the exits come from the injection mechanics, not from a precursor reading.

---

# 15. Reporting Requirements

Each run shall report:

- Run type (shortfall or control)
- Driving inputs (load shape, weather shape)
- Injection location
- Severity tier
- Onset class
- Recovery class (secondary module only)
- Control-band exit time
- Impact time
- Precursor window
- Classification outcome

The report labels all results as instrument verification on a synthetic testbed.

---

# Revision Lock

This preregistration is frozen on:

Date: __________

Version: __________

Author: Ronald L. Brogdon, Upstream Coherence Measurement Stratum (UCMS)
ORCID: https://orcid.org/0009-0009-0507-2971
Contact: measurement@coherencemanagement.org

Collaborator: [ ]

Instrument: SCFL engine v1.1.0 (https://doi.org/10.5281/zenodo.23839571)
Dataset: Texas Combined Electric–Gas Test Case (Abu-Khalifa and Birchfield, 2023), files as inspected 21 November 2026

---

# 2C. Blind Test with Conventional Baselines (pre-registered 26 November 2026)

## Questions

1. **Confirmatory, operating alarms.** Does the Stage 1 precursor gate open before an operator-style low-pressure alarm would sound?
2. **Confirmatory, statistical detectors.** Does the gate open earlier than conventional statistical detectors run on the same inputs, with no more false gates?
3. **Exploratory.** How do DRIFT (hourly severity) and the Tier A break check (RUPTURE and STRESS) behave on unseen scenarios? Reported, not pass/fail: neither has a confirmed decision rule, and the pool contains none of the cases built to test them (rerouting without a threshold crossing, single-sensor drift). Those belong to a separate source-discrimination workstream.

## Gate

The gate time is the engine's SHIFT lock-in (frozen engine v1.1.0) run with the UCMS operator settings frozen at the freeze tag. The settings file is not published; its SHA-256 fingerprint is recorded in the freeze tag, and the blind notebook checks it before running.

## Comparison alarms (script `src/baselines.py`, thresholds `records/blind/baseline_thresholds.json`)

All use only the 31 plant pressures, the first 6 hours as baseline, and 3-sample (15-minute) persistence.
- **B0 operator-style alarm (question 1):** weakest-plant pressure at or below 2 bar above the 2.8 MPag runback floor (3,101.3 kPa abs). A fixed setpoint following the typical spacing of a GE 7FA low-low fuel-pressure alarm, 1–2 bar above the low-pressure trip. Not calibrated.
- **B1 level alarm:** weakest-plant pressure at least 3.5 kPa below its baseline mean.
- **B2 rate alarm:** 1-hour least-squares slope of weakest-plant pressure at or below -4.75 kPa/h.
- **B3 multivariate alarm:** Hotelling T² of the 31 pressures against the baseline mean and a Ledoit-Wolf covariance, at least 70, counted only while mean pressure is below baseline.

B1–B3 thresholds are 1.5 times the largest value seen across the 60 tuning control inputs, rounded up to the grid step. On tuning data, B0 sounded 9–14 hours after strain onset; B1 fired within about 5 minutes of the gate; B3 fired 30–60 minutes earlier than the gate.

## Scenario pool and draw (script `src/blind_draw.py`)

- Supply loss: processing plants within 475, 500, 550, 575, 600, 650, 675 or 700 km of node 546 cut (19.1–53.5% of processing supply).
- Ramp: 0.25, 0.5, 1, 2, 4 or 6 hours. Strain start: 06:30, 07:00, 07:30, 08:00, 08:30 or 09:00.
- Failure: none (half the draw weight), or one of ten station failures used in tuning or confirmation (Houston c15 or c20 isolated; Victoria isolated or bypassed; c21, c23, c27, c1, Dallas c2 or Permian isolated), 0.5, 1, 2, 3, 4 or 6 hours after strain start. The export station (compressor 3) is excluded.
- 16 strain scenarios and 4 control labels; 10 noise seeds each (200 inputs); 36-hour runs (6-hour baseline, 30-hour test window); capped supply, coupled loop in Uri mode; inputs labelled by random six-character codes in random order.
- Seed: the NIST Randomness Beacon 2.0 pulse at 18:00:00 UTC on 27 November 2026 (`https://beacon.nist.gov/beacon/2.0/pulse/time/1795802400000`), used only if the freeze tag is on GitHub before that time; otherwise the pulse at 18:00:00 UTC on the first later day on which the tag precedes it. The draw seed is the first 8 bytes of SHA-256("SCFL-seam-blind-1|" + outputValue).
- The answer key's SHA-256 is committed before the inputs are sent for measurement; the key is published after the readings are returned.

## Pass criteria (confirmatory)

| Check | Pass |
|---|---|
| Gate opens, strain inputs | at least 95% (at least 152 of 160) |
| Gate stays shut, control inputs | at most 1 of 40 |
| Gate before first plant runback | in every strain input of every scenario that reaches a runback in the simulator |
| Question 1: gate before B0 | in at least 95% of strain inputs in which B0 sounds |
| Question 2: gate earlier than each of B1, B2, B3 | paired by input; reported as the share of strain inputs where the gate is earlier, the median difference, and false gates per method. The gate adds detection value over a detector only if it is earlier in more than half of strain inputs with no more false gates. |

Each confirmatory row is reported as pass or fail; the gate result and each comparison are published whatever the outcome.

## Exploratory scoring

- Tier A break check (rule v4-Tune-2, unchanged): flagged inputs per scenario. Answer key: an isolation at Houston c15 or c20 is acute (it was in all five tuning and confirmation cases); all other failures are not.
- DRIFT: hourly totals against the tuning-control ceiling, confirmation timing after the gate.

## Known limits

- The person running the engine sees only codes. The person building the inputs (Claude, for UCMS) holds the answer key; this cannot affect readings because the engine, settings and rules are frozen and fingerprinted first.
- Synthetic case, one seam, slow-onset scenarios only.
