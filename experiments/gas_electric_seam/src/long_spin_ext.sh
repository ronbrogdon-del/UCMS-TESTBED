#!/bin/bash
# Extension: chunks 7-11 x 12 h from chunk 6 (76 h -> 136 h simulated); tracks the 31 Houston plant nodes
export JULIA_DEPOT_PATH=/home/claude/tools/depot JULIA_PKG_SERVER=""
cd /home/claude
PREV=longspin/chunk6/ic_final.json
NODES=1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,19,20,21,23,24,25,26,27,30,31,32,33,34,36,37,38
for k in 7 8 9 10 11; do
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
