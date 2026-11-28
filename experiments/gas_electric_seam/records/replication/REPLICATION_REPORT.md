# Gas-electric seam testbed: replication report

Repository tag blind-test-amend-1 (a43b8b6); GasTranSim 4a21da8; Julia 1.13.4.

- Texas7k_Gas.json SHA-256 8051de2894b624e3bc2eb36d6b742d59a52da4acc66dcd516899be3e71de7b51
- Conversion: identical to records/conversion_log.json (2,428 nodes, 2,472 pipes, 32 compressors)
- chunk  1 (4-16 h): margin 936.37 -> 930.66 kPa; recorded 936.37 -> 930.66; difference 0.00 kPa (informational); 56 min
- chunk  2 (16-28 h): margin 930.66 -> 927.13 kPa; recorded 930.66 -> 927.13; difference 0.00 kPa (informational); 57 min
- chunk  3 (28-40 h): margin 927.13 -> 924.81 kPa; recorded 927.13 -> 924.81; difference 0.00 kPa (informational); 56 min
- chunk  4 (40-52 h): margin 924.81 -> 923.23 kPa; recorded 924.81 -> 923.23; difference 0.00 kPa (informational); 56 min
- chunk  5 (52-64 h): margin 923.23 -> 922.14 kPa; recorded 923.23 -> 922.14; difference 0.00 kPa (informational); 57 min
- chunk  6 (64-76 h): margin 922.14 -> 921.38 kPa; recorded 922.14 -> 921.38; difference 0.00 kPa (informational); 56 min
- chunk  7 (76-88 h): margin 429.20 -> 428.30 kPa; recorded 429.20 -> 428.30; difference 0.00 kPa; 57 min
- chunk  8 (88-100 h): margin 428.30 -> 427.67 kPa; recorded 428.30 -> 427.67; difference 0.00 kPa; 57 min
- chunk  9 (100-112 h): margin 427.67 -> 427.20 kPa; recorded 427.67 -> 427.20; difference 0.00 kPa; 58 min
- chunk 10 (112-124 h): margin 427.20 -> 426.86 kPa; recorded 427.20 -> 426.86; difference 0.00 kPa; 56 min
- chunk 11 (124-136 h): margin 426.86 -> 426.60 kPa; recorded 426.86 -> 426.60; difference 0.00 kPa; 57 min
- Spin-up: chunks 7-11 match the record within 0.00 kPa (limit 0.05)
- T03 rerun (24 h): weakest-margin max difference 0.000 kPa over 1441 minutes; runback count difference 0; events {} vs recorded {}; run time 105 min
- Estimated blind build time: 17 runs x 36 h = about 45 h on one core; divide by the number of cores
- REPLICATION PASSED
