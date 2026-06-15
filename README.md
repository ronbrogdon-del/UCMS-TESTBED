# SCFL Testbed — ACTIVSg2000

Persistent, version-controlled testbed for SCFL operator experiments on the
ACTIVSg2000 synthetic Texas grid case. Built to replace ad-hoc Colab sessions
(which lose all state on runtime reset) with a durable, reproducible setup.

## Status (as of 2026-06-15)

**Working:**
- `src/activsg2000_loader.py` — loads ACTIVSg2000.m via `matpowercaseframes`
  (bypasses a bug in pandapower's `from_mpc` gencost handling). Confirms
  2000 buses / 3206 branches / 544 generators.
- `src/activsg2000_powerflow.py` — converts to a `pypower` ppc dict and runs
  AC power flow. Base case converges (Newton's method, 3 iterations).
- `data/scenarios_ACTIVSg2000.m` + `data/activsg2000_area_load_8784h.csv` —
  real 2016 hourly area-level load data (8784 hours x 8 areas), sourced from
  the public MATPOWER repository.

**Ground truth established:**
- The 2000 buses partition into 8 areas (per `BUS_AREA`). 95.7% of each bus's
  branch connections stay within its own area; only 127 of 2667 in-service
  branches (4.8%) cross area boundaries. This is a real, externally-defined
  partition usable as known-correct structure for testing Dimensional Audit /
  orthogonal workspace construction.

## Important framing

This dataset is **synthetic** (per its own header: "does NOT represent the
actual grid" — deliberate, to avoid CEII). It is excellent for:
- Non-destructive simulation (contingency sweeps, stress-hour analysis,
  Dimensional Audit ground-truth testing) — standard engineering practice,
  same category as aerospace FEA/wind-tunnel simulation.

It is **not** a substitute for:
- Real-world rupture-grade validation (Section III/V of the evidence ledger)
  — it is noise-free and model-perfect by construction, so it cannot probe
  noise-driven failure modes (e.g. the eigenstructure false-positive floor
  found on the stochastic OU rig).

See `ledger/evidence_ledger.md` for the full proven/disproven/untested
accounting and `notes/` for related framing discussions.

## Next experiments (not yet run)

1. **Dimensional Audit ground-truth test** — does orthogonalization of the
   network state recover a basis that respects the 8-area partition? This is
   the experiment most likely to move an item from Section IV to Section II
   of the ledger.
2. **Stress-hour test** — define "stress hours" independently (e.g. top-1%
   load per area, from `activsg2000_area_load_8784h.csv`) *before* computing
   any operator, then apply those loads via power flow and observe Δ1/τ½
   behavior. Non-circular by construction (event definition precedes operator
   computation).
3. **N-1/N-k contingency sweeps** (using `contab_ACTIVSg2000.m`, not yet
   downloaded) — trip branches, re-solve, look for non-convergence / voltage
   collapse as synthetic rupture conditions.

## Setup

```bash
pip install -r requirements.txt
python src/activsg2000_loader.py      # sanity check: prints case dimensions
python src/activsg2000_powerflow.py   # sanity check: confirms PF convergence
```
