#!/bin/bash
# Run the 13 T1 cases two at a time (coupled loop, Uri mode).
cd /home/claude
export JULIA_DEPOT_PATH=/home/claude/tools/depot JULIA_PKG_SERVER=""
run() { [ -f tune1/$1.out.json ] && return; tools/jl/bin/julia --project=tools/gtsenv scripts/coupled_run.jl tune1/$1 elec/coupling_data.json tune1/$1.out.json uri 60 > tune1/$1.log 2>&1; }
L=(T01_control T02_s20 T03_s41 T04_s61 T05_s41_slow T06_s41_fast T07_s41_c15 T08_s41_c2 T09_s41_c1 T10_s41_c20_early T11_s41_vic_late T12_s20_c15 T13_s61_vic_byp)
i=0
while [ $i -lt ${#L[@]} ]; do
  run ${L[$i]} & [ $((i+1)) -lt ${#L[@]} ] && run ${L[$((i+1))]} &
  wait; echo "done ${L[$i]} ${L[$((i+1))]} $(date +%T)"; i=$((i+2))
done
echo ALLDONE
