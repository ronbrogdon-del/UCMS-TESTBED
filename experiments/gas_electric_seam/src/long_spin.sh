#!/bin/bash
# 6 chunks x 12 h from the 4 h spin state (total 76 h simulated)
export JULIA_DEPOT_PATH=/home/claude/tools/depot JULIA_PKG_SERVER=""
cd /home/claude
PREV=spin/ic_final.json
NODES=44,45,46,55,56,57,58,60,61,62,63,64,65,82,83,85,88,95,112
for k in 1 2 3 4 5 6; do
  D=longspin/chunk$k; rm -rf $D; cp -r gts_t7k_k $D; cp $PREV $D/ic.json
  python3 -I - "$D" <<'PY'
import json,sys
d=sys.argv[1]; H=12*3600
p=json.load(open(d+'/params.json')); sp=p['simulation_params']; sp['Final time']=H; sp['Save final state']=1.0; sp['Output dt']=1800.0
json.dump(p,open(d+'/params.json','w'))
bc=json.load(open(d+'/bc.json'))
for sec in bc.values():
    for v in sec.values():
        v['time']=[0,H]
        for key in ('value','control_type'):
            if key in v: v[key]=[v[key][0],v[key][0]]
json.dump(bc,open(d+'/bc.json','w'))
PY
  echo "chunk $k start $(date +%T)"
  tools/jl/bin/julia --project=tools/gtsenv scripts/spin_chunk.jl $D $NODES || { echo "chunk $k FAILED"; exit 1; }
  PREV=$D/ic_final.json
  echo "chunk $k end $(date +%T)"
done
echo ALL DONE
