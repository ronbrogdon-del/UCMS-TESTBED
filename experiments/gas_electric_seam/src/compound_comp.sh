#!/bin/bash
cd /home/claude
export JULIA_DEPOT_PATH=/home/claude/tools/depot JULIA_PKG_SERVER=""
run() { tools/jl/bin/julia --project=tools/gtsenv scripts/coupled_run.jl comp/$1 elec/coupling_data.json comp/$1.out.json uri 60 > comp/$1.log 2>&1; }
run c_hou20 & run c_vic & wait; echo ALLDONE $(date +%T)
