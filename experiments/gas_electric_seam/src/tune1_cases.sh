#!/bin/bash
# Tuning package 1 (gating rule v4-Tune-2). Exploratory, tuning set only; never part of the sealed set.
# Every case: 24 h = 6 h settled pre-window (baseline) + 18 h test window. Strain starts at 7 h (pre-window + 1 h).
# IC: long spin-up extended to 136 h (chunk 11). Capped supply, coupled loop, Uri mode.
set -e
cd /home/claude
IC=longspin/chunk11/ic_final.json; SRC=t7k_raw/Texas7k_Gas.json
P="tuning set; precedents in records/compressor_failure/precedents.md"
mk() { python3 -I scripts/make_case.py gts_t7k_k $IC $SRC tune1/$1 $2 $3 $4 $5 24 60 cap >/dev/null; }
fail() { python3 -I scripts/add_failure.py tune1/$1 $2 $3 $4 $5 300 "$P" >/dev/null; }
mk T01_control       0   0   7 7
mk T02_strain_low  500 1.0   7 9
mk T03_strain_med  600 1.0   7 9
mk T04_strain_high 700 1.0   7 9
mk T05_strain_slow 600 1.0   7 13
mk T06_strain_fast 600 1.0   7 7.25
mk T07_med_hou15_iso   600 1.0 7 9; fail T07_med_hou15_iso   houston_c15 15   isolate 8
mk T08_med_vic_byp     600 1.0 7 9; fail T08_med_vic_byp     victoria    9,24 bypass  8
mk T09_med_dal2_iso    600 1.0 7 9; fail T09_med_dal2_iso    dallas_c2   2    isolate 8
mk T10_med_perm_iso    600 1.0 7 9; fail T10_med_perm_iso    permian     11   isolate 8
mk T11_med_hou20_early 600 1.0 7 9; fail T11_med_hou20_early houston_c20 20   isolate 7.25
mk T12_med_vic_late    600 1.0 7 9; fail T12_med_vic_late    victoria    9,24 isolate 10
echo cases built
