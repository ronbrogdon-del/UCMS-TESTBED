#!/bin/bash
# Operator tuning set T1 (Section 2B). 18 h runs: 6 h settled lead-in, events from 07:00.
# Usage: make_tuning_t1.sh <ic.json>
set -e
cd /home/claude
IC=$1; O=tune1; mkdir -p $O
mk() { python3 -I scripts/make_case.py gts_t7k_k $IC t7k_raw/Texas7k_Gas.json $O/$1 $2 $3 $4 $5 18 60 cap >/dev/null; echo "built $1"; }
fail() { python3 -I scripts/add_failure.py $O/$1 $2 $3 $4 $5 300 "$6" >/dev/null; echo "  + $2 $4 at $5 h"; }
ISO="isolate: Kermit 2003, Prairie Lea (Oasis Waha-to-Katy), Owingsville 2020 (records/compressor_failure/precedents.md)"
BYP="bypass: Tennessee Gas Centerville 2023 (records/compressor_failure/precedents.md)"
mk T01_control        0   0   7 7
mk T02_s20            600 0.5 7 9
mk T03_s41            600 1.0 7 9
mk T04_s61            750 1.0 7 9
mk T05_s41_slow       600 1.0 7 13
mk T06_s41_fast       600 1.0 7 7.25
mk T07_s41_c15        600 1.0 7 9;  fail T07_s41_c15  houston_c15 15   isolate 8   "$ISO"
mk T08_s41_c2         600 1.0 7 9;  fail T08_s41_c2   dallas_east_c2 2 isolate 8 "$ISO"
mk T09_s41_c1         600 1.0 7 9;  fail T09_s41_c1   northeast_c1 1   isolate 8   "$ISO"
mk T10_s41_c20_early  600 1.0 7 9;  fail T10_s41_c20_early houston_c20 20 isolate 7.5 "$ISO"
mk T11_s41_vic_late   600 1.0 7 9;  fail T11_s41_vic_late victoria 9,24 isolate 10 "$ISO"
mk T12_s20_c15        600 0.5 7 9;  fail T12_s20_c15  houston_c15 15   isolate 8   "$ISO"
mk T13_s61_vic_byp    750 1.0 7 9;  fail T13_s61_vic_byp victoria 9,24 bypass 8   "$BYP"
