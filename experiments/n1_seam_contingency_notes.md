# N-1 Seam Contingency Sweep — Results (Corrected)

## A bug was caught and fixed before this was finalized

The first run of this script had an indexing bug: `seam_branches` was
built with `.reset_index(drop=True)`, which discarded the connection
between each seam branch's position in the 131-row filtered list and its
actual row position in the full 3206-row branch array being modified.
The loop then used the filtered list's 0-130 index directly as a row
position into the full array — tripping essentially arbitrary branches,
not the intended ones, for every single contingency.

This was caught via a sanity check that shouldn't have been skipped: the
first run showed the *exact same* 33 contingencies failing to converge at
all three operating points (peak, median, min load) — implausible for
genuine load-dependent voltage collapse, which should vary with loading.
A connectivity check ruled out islanding; a warm-start test then showed
those branches converge fine when tripped correctly. That confirmed the
indexing bug rather than a real result. Fixed (carry an explicit
`orig_pos` column through filtering instead of relying on the dataframe
index), reverified against the full branch array, and rerun. The
previous "33 voltage collapse contingencies" and severity ranking
reported before this fix are **wrong and discarded** — this file
supersedes them.

## Corrected results

131 seam branches × 3 operating points (peak/median/min load) = 393
contingency solves.

**Convergence: 393/393 (100%).** No single seam-branch loss causes
outright power-flow non-convergence at any of the three tested load
levels, for this topology and dispatch assumption.

**Voltage limit violations (VMIN=0.90, VMAX=1.10, uniform across all
buses):**

| Operating point | Undervoltage | Overvoltage |
|---|---|---|
| Peak (66,276 MW) | 0/131 | 0/131 |
| Median (34,912 MW) | 0/131 | 131/131 |
| Min (23,072 MW) | 0/131 | 131/131 |

Zero undervoltage violations anywhere across all 393 tests. At peak
load, not a single seam contingency causes any limit violation at all.
At median and minimum load, *every* seam contingency causes an
overvoltage violation somewhere in the system.

**This inverts the usual intuition (peak load = most dangerous) and the
reason is already on record:** the annual voltage series notes already
documented light-load overvoltage as a known artifact of this static
model (no switched shunts or OLTC tap adjustment, so generator voltage
setpoints push nearby buses high when load drops). Losing a seam line at
light load tips already-elevated buses over the 1.10 threshold. This is
a real result about THIS MODEL's behavior, not a finding about how the
real ERCOT-like grid would behave under contingency — a real grid
manages exactly this condition with the equipment this static study
doesn't include.

## Most severe contingencies by stress jump (Δ1)

Top result: branch 8030-7389 (areas 8↔7), most severe at min-load
(Δ1 stress = +0.00158, vs. the typical contingency's Δ1 in the
0.0001-0.0005 range). Second: 6015-4174 (areas 6↔4). Both show their
largest jump at min or median load, not peak — consistent with the
overvoltage-driven pattern above.

## What this does and doesn't tell us about Δ1/Δ2/τ½/R (scope, stated explicitly)

- **Δ1 (drift):** computed as a single pre/post jump per contingency.
  Meaningful as implemented.
- **Δ2, τ½, R:** NOT computed. All three require a time axis after the
  event (curvature needs 3 points; half-life and resilience are
  integrals over a recovery trajectory). A static power-flow snapshot
  has none of that — there is no dynamic relaxation to measure. Faking
  these from two snapshots would be worse than not reporting them.
  Getting real versions of these needs either genuine transient
  simulation (inertia/governor data this case doesn't have) or the
  temporary-outage-embedded-in-the-real-time-series approach discussed
  earlier (and noted there to be confounded with natural load variation).

## Status
Bug found, disclosed, fixed, reverified, rerun. Corrected results above
supersede the original (wrong) sweep. Tagged CANDIDATE_SPEC_v1 for the
operator definitions; the contingency methodology itself is standard N-1
screening, not candidate.
