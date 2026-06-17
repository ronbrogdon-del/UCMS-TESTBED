# Does Seam-Tie Redundancy Explain the N-1 Delta1 Inversion? (2026-06-17)

Script: `src/testbed/tier1_n1_redundancy_test.py`
Data: `experiments/tier1_n1_redundancy_trips.csv` (1,235 individual seam-branch
trips across all 7 cases, every one converged)

## Short answer: partially. Redundancy is real and matters, but explains
## less than 15% of the year effect — most of the N-1 inversion is still
## unexplained.

## 1. Premise check: redundancy did increase substantially

"Redundancy" here = how many seam branches (in that case) connect the
same pair of areas, counting the branch itself — i.e. how many parallel
or alternate inter-area ties exist for that specific area-pair.

| Era | Median redundancy | Mean redundancy |
|---|---|---|
| 2016 (3 cases) | 11-12 | 12.0-12.4 |
| 2024 (4 cases) | 18-20 | 17.8-20.3 |

Mann-Whitney (2024 > 2016): p = 1.3e-38. The premise holds — this is not
a marginal difference, redundancy roughly grew 1.6-1.7x.

## 2. Pooled correlation: real, but modest

Across all 1,235 converged seam trips, Spearman rho = -0.2215 (p=3.4e-15).
Higher redundancy does predict lower Delta1, robustly — but rho=-0.22
is a modest effect, not a dominant one. Redundancy is A factor, not THE
factor.

## 3a. Regression: redundancy explains ~14% of the year effect, not most of it

| Model | year2024 coefficient | p | redundancy coefficient | p | R² |
|---|---|---|---|---|---|
| A: Delta1 ~ year2024 | -0.00605 | 3.8e-21 | — | — | 0.070 |
| B: Delta1 ~ year2024 + redundancy | -0.00522 | 2.7e-14 | -0.00011 | 0.0011 | 0.078 |

Adding redundancy attenuates the year2024 coefficient by **13.8%**, and
barely moves R² (0.070 → 0.078). The year2024 effect remains highly
significant (p=2.7e-14) after controlling for redundancy. **Redundancy
is a real, independently significant contributor, but it is not close to
sufficient to explain the year-over-year drop in N-1 severity.**
Something else — overall grid stiffness, generator mix/inertia changes,
topology beyond just seam-tie count, or some combination — is doing most
of the work and hasn't been identified yet.

## 3b. Stratified match at redundancy=1 — inconclusive, not confirmatory

The script's own auto-generated message at this step says the year gap
"disappears" at matched redundancy=1 — **that conclusion should be
discounted.** The actual sample sizes there are n=5 (2016) vs n=8 (2024)
out of 1,235 trips: true sole-tie (non-redundant) area-pair connections
are rare in this grid even in 2016, since most area pairs already had
multiple ties. With 5 vs 8 points, perm_p=0.147 and MW_p=0.210 reflect
having essentially no statistical power, not a genuine disappearance of
the effect. This stratified check is underpowered and should be treated
as inconclusive, not as evidence either way. Flagging this explicitly
rather than letting the script's naive p>0.05-means-no-effect logic
stand uncorrected — that logic is wrong here and would oversell the
redundancy explanation if taken at face value.

## Bottom line

The hypothesis from the last round — "more seam ties in 2024 means each
one matters less, explaining the N-1 inversion" — is real but small.
Confirmed: redundancy went up substantially, and redundancy does
predict lower trip severity. Not confirmed: that this is most or all of
the explanation. ~86% of the year2024 effect on Delta1 is still
unaccounted for. Worth treating as one contributing factor among others,
not the answer, if this gets written up anywhere.

## Caveats

- All 1,235 trips converged (no islanding failures here, unlike the
  earlier non-seam sample which had many) — seam branches being major
  inter-area ties, this isn't surprising and is a feature of seam
  branches specifically, not a general claim about N-1 robustness.
- Redundancy is defined purely by area-pair tie count, not by electrical
  impedance/capacity of the alternate paths — two ties between the same
  areas could still leave one critically overloaded if the other is a
  much weaker line. A capacity-weighted redundancy measure would be a
  sharper test and hasn't been run.
- Single regression specification (OLS, no case fixed effects beyond
  the binary year dummy, no interaction terms). Case-level fixed effects
  or a redundancy x year interaction term would be the natural next
  step if this needs to be tightened further.
