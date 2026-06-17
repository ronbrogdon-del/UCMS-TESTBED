# Stiffness, Generator Mix, and Topology Geometry as Predictors of the
# N-1 Delta1 Inversion (2026-06-17)

Script: `src/testbed/tier1_n1_three_predictors_test.py`
Data: `experiments/tier1_n1_three_predictors_merged.csv` (1,235 seam-branch
trips, joined to `tier1_n1_redundancy_trips.csv` by branch_idx),
`experiments/tier1_n1_three_predictors_premise.csv` (case-level premise
checks)

## Headline: generator/inertia mix is the dominant explanation, not
## redundancy. Combined with stiffness, it reduces the year2024 effect
## by 76% and makes it statistically non-significant.

This is a materially stronger result than the redundancy-only test
(13.8% attenuation, year effect stayed significant at p=2.7e-14).

## What each predictor actually measures

- **Stiffness**: \|Z_ii\|, the driving-point (Thevenin) impedance
  magnitude at each branch's two endpoint buses, averaged. From the
  network Ybus only (`pypower.makeYbus`, sparse LU solve for the needed
  diagonal entries of Zbus) — NOT a true short-circuit study, which
  would need generator sub-transient reactances from the .dyr files.
  Lower \|Z_ii\| = stiffer/electrically stronger bus, by the standard
  S_sc ~ V²/\|Z_ii\| relationship.
- **Generator/inertia mix**: each case's .dyr file parsed for generator
  model type per bus — GENROU/GENSAL = synchronous, REGCA1 = grid-
  following inverter, REGFMA1 = grid-forming inverter (case6 only, 5
  units). Joined to `cf.gen` (online status + dispatched MW) for
  AREA-level online inverter share of capacity. Branch covariate =
  average inverter share of the branch's two endpoint areas. System-
  level online synchronous inertia (sum of H x MBASE) also computed as
  a case-level check. Coverage: ~98.8% of online generator buses matched
  to a model type (4-5 unmatched per case, excluded, not imputed).
  Baseline case has no .dyr file and is excluded from this predictor
  specifically (NaN, not zero).
- **Topology geometry**: (a) edge betweenness centrality of each seam
  branch in the full 2000-bus graph (`networkx`, unweighted, exact
  Brandes algorithm) — global structural importance, distinct from
  local area-pair tie count; (b) alt_area_degree — how many OTHER areas
  each endpoint area connects to in the 8-node area-supergraph (local
  meshing / rerouting potential through the broader mesh, not the same
  thing as direct-tie redundancy).

## Premise checks (per-branch, pooled 2016 vs 2024)

| Predictor | Median 2016 | Median 2024 | p (Mann-Whitney) |
|---|---|---|---|
| stiffness \|Z_ii\| | 0.0500 | 0.0410 | 0.016 |
| betweenness | 0.00341 | 0.00404 | 0.896 (n.s.) |
| alt_area_degree | 6 | 7 | 0.0022 |
| inverter share (branch-local) | 21.8% | 64.5% | 5.8e-49 |

Inverter share shows by far the largest, cleanest shift of any premise
checked so far (including the original redundancy premise). Stiffness
and alt_area_degree show real but modest shifts. Betweenness shows
essentially no shift at the seam-branch level despite the network
growing — seam branches' relative global centrality didn't change much
even as the network around them did.

## Univariate correlations with Delta1 (pooled, all converged trips)

| Predictor | Spearman rho | p | n |
|---|---|---|---|
| redundancy | -0.222 | 3.4e-15 | 1235 |
| stiffness \|Z_ii\| | **+0.295** | 3.2e-26 | 1235 |
| betweenness | -0.158 | 2.3e-8 | 1235 |
| alt_area_degree | -0.038 | 0.177 (n.s.) | 1235 |
| inverter share | **-0.383** | 7.3e-40 | 1104 |

Inverter share is the single strongest correlate of any predictor
tested across both rounds (this one and the redundancy round). Higher
local inverter penetration predicts LOWER N-1 severity. Stiffness is
second-strongest: weaker buses (\|Z_ii\| higher) predict higher severity,
as expected. alt_area_degree alone doesn't predict Delta1 at all.

## Regression progression (the decisive test)

n=1,104 complete cases (baseline excluded — no inverter_share data).

| Model | Predictors added | R² | year2024 coef | year2024 p |
|---|---|---|---|---|
| A | (none) | 0.047 | -0.00511 | 3.3e-13 |
| B | + redundancy | 0.058 | -0.00421 | 1.1e-8 |
| C | + stiffness | 0.098 | -0.00383 | 1.1e-7 |
| D | + inverter share | **0.156** | **-0.00129** | **0.088 (n.s.)** |
| E | + topology (betweenness, alt_area_degree) | 0.162 | -0.00121 | 0.110 (n.s.) |

**Model D is where the story changes.** Adding inverter share alone
(on top of redundancy + stiffness) nearly doubles R² (0.098 -> 0.156)
and drops the year2024 coefficient by more than half, crossing below
conventional significance (p=0.088). Topology geometry (model E) adds
almost nothing further to R² (0.156 -> 0.162) and barely moves the
year2024 coefficient — betweenness itself stays a real, independently
significant predictor in the full model (p=0.0135) even though it adds
little overall explanatory power; alt_area_degree is not significant in
any model.

**Total: redundancy + stiffness + inverter share + topology together
attenuate the year2024 coefficient by 76.4% (vs. 13.8% for redundancy
alone) and the year2024 effect becomes statistically indistinguishable
from zero (p=0.11).** Generator/inertia mix is doing most of that work;
stiffness is a real secondary contributor; topology geometry contributes
the least of the three new candidates tested.

## Answering the three paths directly

- **Stiffness as a predictor: confirmed, real, secondary.** Significant
  in every model it appears in (p<1e-11 throughout), correct sign, and
  the network premise (stiffer in 2024) checks out — but a network-only
  Ybus proxy, not a true short-circuit-strength study.
- **Generator/inertia mix as a predictor: confirmed, dominant.** Largest
  premise shift, strongest univariate correlation, and the one variable
  whose addition pushes the year effect to non-significance. This is
  the main finding of this round.
- **Topology geometry beyond tie-count: partially confirmed, minor.**
  Betweenness is real and independently significant but contributes
  little R²; the area-mesh-degree measure isn't a significant predictor
  at all, alone or combined. "Meshing beyond tie-count" matters less
  than expected once mix and stiffness are accounted for.

## Caveats

- Stiffness is network-only (no generator sub-transient reactances from
  the .dyr files incorporated) — a true short-circuit-strength study
  would change this number, possibly substantially at generator-adjacent
  buses.
- Inverter share is capacity-weighted (online dispatched MW by model
  type), not true inertia-weighted (H x MBASE) at the branch/area level
  — system-level true inertia WAS computed (reported in the premise
  CSV) but not used as the branch-level regression covariate; redoing
  the regression with an inertia-weighted local measure instead of a
  capacity-share measure is a natural tightening, not yet done.
- Betweenness is unweighted (hop-count shortest paths), not impedance-
  weighted — an electrical-distance-weighted betweenness would be a
  more electrically meaningful version of the same idea.
- Single OLS specification throughout, no case fixed effects beyond the
  binary year dummy, no interaction terms (e.g. redundancy x year). All
  five predictors entered linearly; no test for nonlinear relationships.
- ~5 generator buses per case (under 1.5%) unmatched to a .dyr model
  type, excluded rather than imputed.
