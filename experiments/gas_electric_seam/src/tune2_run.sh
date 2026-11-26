#!/bin/bash
cd /home/claude
export JULIA_DEPOT_PATH=/home/claude/tools/depot JULIA_PKG_SERVER=""
run() { [ -f tune2/$1.out.json ] && return; tools/jl/bin/julia --project=tools/gtsenv scripts/coupled_run.jl tune2/$1 elec/coupling_data.json tune2/$1.out.json uri 60 > tune2/$1.log 2>&1; echo "done $1 $(date +%T)"; }
L=(C05_med_c23_iso C06_med_c27_iso C07_med_c21_iso C08_650_hou20_late C09_550_hou15_early C02_strain_550 C03_strain_650_r1h C04_strain_600_r4h C10_med_c3_iso C11_med_c1_iso)
for ((i=0;i<${#L[@]};i+=2)); do run ${L[i]} & run ${L[i+1]} & wait; done
echo ALLDONE $(date +%T)
