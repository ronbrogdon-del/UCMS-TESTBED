# SCFL Evidence Ledger v1.3 — Operators + Methods

Maintenance rule:
Nothing moves toward more certainty without a named test that did the moving.

- Disproven -> requires a new method, not new data.
- Untested -> requires falsification-capable data (or, for methods, a
  falsification-capable EXPERIMENT DESIGN), not optimism.
- Proven (internal) -> requires external replication to lose the qualifier.

Untested != provisionally true.
Untested = unproven.

**Note on this revision (v1.2 -> v1.3):** Dimensional Audit was moved out of
PROVEN. "Never contradicted" and "never degenerate" are absence-of-failure
claims, not pass-a-test claims -- by this ledger's own rule, that is UNTESTED,
not proven. Unlike the Section III items (which lack the right DATA),
Dimensional Audit lacks the right EXPERIMENT DESIGN entirely -- no test with a
known-correct answer has ever been run against it, on any data. It is closer
kin to the Section IV operators ("applied consistently, never tested") than to
D1/tau-half (which were measured against expected outcomes on the rig).

---

## I. DISPROVEN -- Method failures (not data failures)

These approaches are answered. They do not leave this bin without a new
method.

| Item | How it failed | On what substrate |
|---|---|---|
| CCV(t) | Undefined (0/0 when D2=0); degenerate one-hot weighting; fails by definition | Any dataset; definition-level |
| Naive coupling | False-alarmed on null; missed true coupling | Stochastic rig (adequate substrate) |
| Naive eigenstructure | ~20% false-positive floor; no estimator or rule rescued it across 50 seeds | Stochastic rig (adequate substrate) |

Interpretation: these are method failures, not data failures. Better data will
not save them.

---

## II. PROVEN -- Internal only (pending external replication)

These items were TESTED on falsification-capable synthetic data (rupture
timing, nulls, noise, multi-regime transitions) and behaved as predicted -- a
measured outcome was checked against an expected one.

| Item | Status |
|---|---|
| D1 Drift | Variance collapse (50-71%) under orthogonalization, measured on the rig against expected reduction; internally validated |
| tau-half Stability | +/-5% stability across regimes, measured against analytic values; internally validated |

Both items here have a concrete measured-vs-expected comparison behind them.
That comparison is the bar for this bin.

---

## III. UNTESTED -- Data limitations or never run

These items remain unproven, regardless of how plausible they feel.

| Item | Why untested | What it needs |
|---|---|---|
| Eigenstructure sensitivity | ERCOT log had no rupture event; sensitivity cannot be tested without one | Real telemetry spanning a documented rupture + matched quiet periods |
| D2 precursor windows | Never tested against matched null segments | Falsification-capable dataset with nulls |
| Recoverability | Never tested at all | Real, multi-regime, labeled events + nulls |
| Directional locator | Weak positive on 4 ERCOT events; volatility confound unresolved | Events on multiple axes; volatility-normalized test |

Interpretation: these are open questions, not "almost validated." They require
rupture-grade data.

---

## IV. APPLIED (BUT NOT TESTED) -- Methods and the Scan-100 Operators

Items in this bin have been APPLIED -- used repeatedly, producing outputs --
but never subjected to a test with a known-correct answer to check against.
This is distinct from Section III: these don't need better data so much as a
test DESIGN that has never existed for them.

### Dimensional Audit / Orthogonal Workspace construction
A method, not an operator. Structural backbone of SCFL; used throughout the
corpus to construct every orthogonal basis in this ledger. Applied
consistently, with no internal contradiction observed -- but "no contradiction
observed" is an absence-of-failure claim, not a pass-a-test claim. No
falsification-capable experiment (known-correct basis to compare against) has
ever been run, on any data, internal or external. **Status: UNTESTED, not
proven** -- pending a test design, not just better data.

### Scan-100 Residency Operators (D1, D2, PRE, COH, CL, TL, IOO)
Successfully applied to the 100-scholar contemplative cohort and the 119th
Congress. Produced meaningful variance, anchor-scholar identification,
fault-line detection, entity-class vs. event-class coherence. Not tested on
falsification-capable data.

| Operator |
|---|
| D1 |
| D2 |
| PRE |
| COH |
| CL |
| TL |
| IOO |

Interpretation: these are structurally deployed, not validated. They classify
thinkers; they do not detect rupture physics.

---

## V. The Dataset Gap -- The Gatekeeper for Section III

Everything used so far (EEG, time series, financial logs, hospital data) was
applied to operators but cannot validate them.

A falsification-capable dataset must include:

- high-frequency sampling
- real noise
- multi-regime transitions
- documented rupture
- pre-rupture phase
- post-rupture envelope
- matched null segments
- ground-truth timing

Until such a dataset exists:
- Section III stays untested
- Section II stays internal-only
- Section I stays disproven

This is the data-side epistemic floor of SCFL. Section IV has a SEPARATE
floor -- a test-design floor -- that exists independent of data quality.

---

## One-sentence canonical summary

Two items (D1, tau-half) are internally validated against measured outcomes;
three operators (CCV(t), naive coupling, naive eigenstructure) are disproven
by method; four measurement operators are untested pending rupture-grade data;
and Dimensional Audit plus the seven Scan-100 residency operators are applied
but have never been subjected to any falsification test, on any data -- no
item moves categories without a named test against a known-correct answer.
