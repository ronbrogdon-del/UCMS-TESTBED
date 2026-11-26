#!/bin/bash
# Confirmation package (tune2). Fresh seeds; new severities/ramps; failures at stations not used in tuning.
# Reuses tuning-package physics for the control (T01) and medium strain (T03): same deterministic runs.
set -e
cd /home/claude
IC=longspin/chunk11/ic_final.json; SRC=t7k_raw/Texas7k_Gas.json
P="confirmation set; precedents in records/compressor_failure/precedents.md"
mk() { python3 -I scripts/make_case.py gts_t7k_k $IC $SRC tune2/$1 $2 $3 $4 $5 24 60 cap >/dev/null; }
fail() { python3 -I scripts/add_failure.py tune2/$1 $2 $3 $4 $5 300 "$P" >/dev/null; }
mk C02_strain_550        550 1.0 7 9
mk C03_strain_650_r1h    650 1.0 7 8
mk C04_strain_600_r4h    600 1.0 7 11
mk C05_med_c23_iso       600 1.0 7 9;  fail C05_med_c23_iso       station_c23 23 isolate 8.5
mk C06_med_c27_iso       600 1.0 7 9;  fail C06_med_c27_iso       station_c27 27 isolate 9
mk C07_med_c21_iso       600 1.0 7 9;  fail C07_med_c21_iso       station_c21 21 isolate 8
mk C08_650_hou20_late    650 1.0 7 8;  fail C08_650_hou20_late    houston_c20 20 isolate 10
mk C09_550_hou15_early   550 1.0 7 9;  fail C09_550_hou15_early   houston_c15 15 isolate 7.5
mk C10_med_c3_iso        600 1.0 7 9;  fail C10_med_c3_iso        station_c3  3  isolate 8
mk C11_med_c1_iso        600 1.0 7 9;  fail C11_med_c1_iso        station_c1  1  isolate 8
echo cases built
