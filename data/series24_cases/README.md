# Texas2k Series24 Cases with Improved Dynamics

Six dynamics scenarios for the Texas2k (ACTIVSg2000) synthetic grid, sourced
from the TAMU Electric Grid Test Case Repository
(https://electricgrids.engr.tamu.edu/activsg2000-dynamics-cases-2024/).
Unlike the single static `data/ACTIVSg2000.m` baseline already in this repo,
each case here ships full dynamics data (PSS/E `.dyr`/`.dyd`, PowerWorld
`.idv` patches) alongside the power-flow case in five formats (Matpower
`.m`, PowerWorld `.PWB`, PowerWorld auxiliary `.AUX`, PSLF `.EPC`).

All six share the same 2000-bus topology but differ in load level,
generation mix, and inverter control modeling — giving a real spread of
operating conditions instead of one static snapshot.

| Folder | Scenario | Buses | Gens | Branches |
|---|---|---|---|---|
| `case1_2016summerpeak` | 2016 Summer Peak (identical power flow to original ACTIVSg2000 case) | 2000 | 544 | 3220 |
| `case2_2016lowload` | 2016 Low Load | 2000 | 544 | 3220 |
| `case3_2024summerpeak` | 2024 Summer Peak | 2000 | 743 | 3911 |
| `case4_2024lowload` | 2024 Low Load | 2000 | 743 | 3913 |
| `case5_2024highrenewables` | 2024 High Renewables | 2000 | 743 | 3663 |
| `case6_2024lowloadwithgfm` | 2024 Low Load + Grid-Forming Inverters (GFM) | 2000 | 748 | 3913 |

Bus/gen/branch counts verified directly from each case's `.m` file
(`mpc.bus`, `mpc.gen`, `mpc.branch` row counts), not taken from
documentation.

## Why this matters for Tier-1 validation

The existing Tier-1 work (`src/testbed/tier1_candidate_operators.py`,
`experiments/state_matrix_vm_seed{42,123}.npy`) was run against the single
static baseline case. Running the same SCFL operators across all six
scenarios here tests whether operator stability holds across a decade of
grid evolution (2016→2024) and across load/renewable/inverter-control
variation — not just on one configuration. This is the natural next step
toward a genuinely multi-condition "serious testbed," as opposed to a
single-snapshot one.

## Provenance

Synthetic data, no CEII (per each case's own file header). Built at Texas
A&M University. See:

- A.B. Birchfield, T. Xu, K.M. Gegner, K.S. Shetye, and T.J. Overbye,
  "Grid Structural Characteristics as Validation Criteria for Synthetic
  Networks," IEEE Transactions on Power Systems, vol. 32, no. 4,
  pp. 3258-3265, July 2017.
- J. Baek and A. B. Birchfield, "A tuning method for exciters and governors
  in realistic synthetic grids with dynamics," 2023 North American Power
  Symposium (NAPS), Asheville, NC, USA, Oct. 2023, pp. 1-6.

Contact for case questions: Adam Birchfield (abirchfield@tamu.edu).
