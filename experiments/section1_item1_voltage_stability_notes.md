# Section 1, Item 1 — Voltage Stability Curves (PV/QV) — Findings

Method: see docstring in `src/testbed/voltage_stability_curves.py`. Single-shot
AC power flow (Newton, pypower) repeated at increasing load levels — NOT
continuation power flow. Upper (stable) branch only; nose point is
approximate, bounded by step size (0.05 lambda for PV, 5% of area Q for QV).

## Results

| Area | Nominal load (MW) | Rep. boundary bus | V nominal (p.u.) | Approx. loadability margin (λ) | Approx. reactive margin (MVAr) |
|---|---|---|---|---|---|
| 1 | 1,307 | 1091 | 1.024 | 2.15 | 278 |
| 2 | 1,474 | 2039 | 0.993 | 2.00 | 376 |
| 3 | 1,676 | 3048 | 1.040 | 1.80 | 1,424 |
| 8 | 3,188 | 8126 | 1.032 | 1.45 | 2,709 |
| 4 | 6,751 | 4008 | 0.988 | 1.20 | 383 |
| 6 | 12,263 | 6112 | 0.996 | 1.10 | 347 |
| 7 | 18,190 | 7274 | 1.020 | 1.05 | 4,123 |
| 5 | 22,262 | 5049 | 1.009 | 1.05 | 10,723 |

(Sorted by nominal area load, ascending.)

## The finding that actually matters here: this measures area size, not intrinsic stability

The loadability margin column is **monotonically decreasing as area size
increases** (with a tie between the two largest areas, both at 1.05). That's
not a coincidence of this dataset — it's a direct artifact of the method:

The PV sweep scales one area's load and lets a **single slack bus** (located
in Area 7) absorb the entire increment. A 5% load increase in a 22,000 MW
area (Area 5) is a ~1,100 MW absolute increment; the same 5% in a 1,300 MW
area (Area 1) is ~65 MW. The single slack bus hits its effective limit (here,
a numerical Newton-Raphson divergence, since `runpf` does not enforce
generator P/Q limits) much sooner in absolute-MW terms for the big areas,
regardless of how "stable" that area's own internal voltage profile actually
is.

**This means the margin ranking above is mostly telling you "how big is this
area relative to the single slack bus's effective capacity," not "which
areas are intrinsically voltage-weak."** Areas 5 and 7 looking fragile here
is largely explained by them being the two largest areas in the system
(22,262 MW and 18,190 MW respectively — together 60% of total system load),
not by anything specific to their internal topology.

The QV sweep is less confounded by this (it stresses a single bus locally
rather than scaling a whole area's generation requirement), and those
trajectories look like genuine, well-behaved voltage-collapse approaches —
e.g. Area 5's rep bus declines smoothly from 1.009 p.u. to 0.588 p.u. across
35 converged steps before diverging. That one is a real local result.

## What this means for next steps (not done yet)

A methodologically sound per-area loadability margin needs **distributed
slack** (participation-factor generation response, proportional across all
generators or at least all generators in the stressed area) instead of
single-slack absorption. pypower supports this via the `bus[:, BUS_TYPE]`
PV-bus set and a participation vector, or via a small wrapper that
re-dispatches Pg proportionally before each solve. That re-run is needed
before the PV margin numbers above should be used for anything beyond "here
is what this specific simplified test showed."

**Status: baseline PV/QV sweep complete, single-slack caveat identified and
documented. Distributed-slack re-run is a flagged follow-up, not yet done.**
