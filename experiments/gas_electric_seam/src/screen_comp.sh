#!/bin/bash
# Screening: single compressor-station failures, capped supply, no supply cut, fail at 1 h, 12 h horizon, coupled (uri mode).
set -e
cd /home/claude
export JULIA_DEPOT_PATH=/home/claude/tools/depot JULIA_PKG_SERVER=""
IC=longspin/chunk6/ic_final.json
mk() { python3 -I scripts/make_case.py gts_t7k_k $IC t7k_raw/Texas7k_Gas.json comp/$1 0 0 1 1 12 60 cap >/dev/null; }
run() { tools/jl/bin/julia --project=tools/gtsenv scripts/coupled_run.jl comp/$1 elec/coupling_data.json comp/$1.out.json uri 60 > comp/$1.log 2>&1; }
P="screening; unit trips and station outages are routine reported pipeline events (precedent list in protocol)"
mk s_control
mk s_vic_iso;  python3 -I scripts/add_failure.py comp/s_vic_iso  victoria 9,24 isolate 1 300 "$P" >/dev/null
mk s_vic_byp;  python3 -I scripts/add_failure.py comp/s_vic_byp  victoria 9,24 bypass 1 300 "$P" >/dev/null
mk s_hou20_iso; python3 -I scripts/add_failure.py comp/s_hou20_iso houston_c20 20 isolate 1 300 "$P" >/dev/null
mk s_hou15_iso; python3 -I scripts/add_failure.py comp/s_hou15_iso houston_c15 15 isolate 1 300 "$P" >/dev/null
mk s_perm_iso; python3 -I scripts/add_failure.py comp/s_perm_iso permian 11 isolate 1 300 "$P" >/dev/null
for pair in "s_control s_vic_iso" "s_vic_byp s_hou20_iso" "s_hou15_iso s_perm_iso"; do
  set -- $pair
  run $1 & run $2 & wait
  echo "batch done: $pair $(date +%T)"
done
echo ALLDONE
