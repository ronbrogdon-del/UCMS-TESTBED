# Testbed replication, 28 Nov 2026

Run by Ronald L. Brogdon in Colab (GES_Replicate_Testbed.ipynb) from repository tag
blind-test-amend-1 (a43b8b6), GasTranSim 4a21da8, Julia 1.13.4. Finished 8:05 am CT.

The rebuilt testbed reproduced the recorded one exactly:
- Spin-up chunks 7-11: 0.00 kPa difference (limit 0.05); chunks 1-6 also 0.00 (informational).
- T03 tuning case rerun (24 h): 0.000 kPa max weakest-margin difference over 1,441 minutes,
  runback count difference 0, events {} vs recorded {}.
- Result: REPLICATION PASSED.

`testbed_state.zip` is the starting state for the blind build (converted network, chunk 11
final state, raw Texas7k_Gas.json, copy of the report). Every blind run must start from it.

| File | SHA-256 |
|---|---|
| testbed_state.zip | 770b5a405316b170882735b5989dd36b134d749005416c48496980ea32147401 |
| REPLICATION_REPORT.md | 2db5774aca418caf96a4221f2384be6be72a53b7275d9257046f70b9842c8352 |
| Texas7k_Gas.json (inside zip) | 8051de2894b624e3bc2eb36d6b742d59a52da4acc66dcd516899be3e71de7b51 |

The zip hash matches the one the notebook printed on screen. The report copy inside the zip
is byte-identical to REPLICATION_REPORT.md.

Estimated blind build: 17 runs x 36 h, about 45 core-hours.
