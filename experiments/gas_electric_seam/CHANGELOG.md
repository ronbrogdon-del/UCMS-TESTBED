# Gas–Electric Seam Testbed: version log

Each model version names the commit that contains it. Cite the version and commit with any result.
Every new layer or modelling change gets its own entry.

## seam-v0.3-compressor (25 Nov 2026), commits 0bd1d22 to 14bade5
Adds scheduled compressor-station failures to the coupled loop (isolate: station valved off;
bypass: units trip, ratio to 1.0), each mode grounded in a real event (records/compressor_failure/precedents.md).
Screening: five single-station failures at normal supply, 12 h; none caused a runback.
Compound: 41% supply strain plus Houston or Victoria station isolated at 2 h, 30 h; first plant
runback 17.5 h and 17.4 h vs 20.1 h strain only. 30 h control added.
SCFL input package v4 (4 conditions x 30 noise seeds, 31 Houston plant nodes within 80 km,
PROVENANCE.json stamped with commit 14bade5) and standard notebook v4.
Exploratory, pre-freeze. Tag on the commit that adds this entry.

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
