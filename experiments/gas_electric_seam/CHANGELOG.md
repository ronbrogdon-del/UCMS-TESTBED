# Gas–Electric Seam Testbed: version log

Each model version names the commit that contains it. Cite the version and commit with any result.
Every new layer or modelling change gets its own entry.

## seam-v0.2-coupled (24 Nov 2026), commit a2b8308
Baseline. Texas7k converted for GasTranSim (friction from k, 1 km minimum pipe length, |p|),
76 h no-shortfall spin-up, supply cap option, coupled gas–electric loop v1 (rules 1–4 agreed
24 Nov 2026: runback/trip at 2.8/2.52 MPag, non-gas-first redispatch then pro-rata shed,
Uri vs post-Uri loop with 10% electric compressors placeholder, gas draw follows MW),
SCFL input packages v1–v3, standard four-cell notebooks, pre-registration draft v0.2.
Exploratory, pre-freeze.

## seam-v0.1-gas-only (21–24 Nov 2026), included in a2b8308
Gas-only runs: preliminary north Texas 50% cut, 30-seed noise set, uncapped and capped
41% supply trials. Superseded as baseline by v0.2.
