#!/bin/bash
cd /home/claude
export JULIA_DEPOT_PATH=/home/claude/tools/depot JULIA_PKG_SERVER=""
run() { [ -f tune1/$1.out.json ] && return; tools/jl/bin/julia --project=tools/gtsenv scripts/coupled_run.jl tune1/$1 elec/coupling_data.json tune1/$1.out.json uri 60 > tune1/$1.log 2>&1; echo "done $1 $(date +%T)"; }
L=(T01_control T02_strain_low T03_strain_med T04_strain_high T05_strain_slow T06_strain_fast T07_med_hou15_iso T08_med_vic_byp T09_med_dal2_iso T10_med_perm_iso T11_med_hou20_early T12_med_vic_late)
for ((i=0;i<${#L[@]};i+=2)); do run ${L[i]} & run ${L[i+1]} & wait; done
echo ALLDONE $(date +%T)
