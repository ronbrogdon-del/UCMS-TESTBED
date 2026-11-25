"""Prepare electric-side data for the coupled driver -> elec/coupling_data.json"""
import json, re, random
from matpowercaseframes import CaseFrames
cf = CaseFrames("t7k_raw/Texas7k.m"); g = cf.gen.reset_index(drop=True)
m = open("t7k_raw/Texas7k.m").read()
fuel = re.findall(r"'([^']*)'", m[m.index("mpc.genfuel = {"):m.index("};", m.index("mpc.genfuel = {"))])
sm = json.load(open("elec/seam_map.json"))
on = [i for i in range(len(g)) if int(g.loc[i, "GEN_STATUS"]) == 1]
linked = {r for p in sm["plants"].values() for r in p["gens"]}
plants = {}
for node, p in sm["plants"].items():
    rows = [r for r in p["gens"] if r in on]
    plants[node] = {"pg": float(sum(g.loc[r, "PG"] for r in rows)), "pmin": float(sum(max(g.loc[r, "PMIN"], 0) for r in rows)),
                    "pmax": float(sum(g.loc[r, "PMAX"] for r in rows)), "sub_name": p["sub_name"]}
nongas_headroom = float(sum(g.loc[i, "PMAX"] - g.loc[i, "PG"] for i in on if fuel[i] != "ng"))
unlinked_gas_headroom = float(sum(g.loc[i, "PMAX"] - g.loc[i, "PG"] for i in on if fuel[i] == "ng" and i not in linked))
d = json.load(open("t7k_raw/Texas7k_Gas.json"))
processing = [n["number"] for n in d["nodes"] if n["name"] == "Processing Plant" and n["qf"] < 0]
rng = random.Random(20261124)
comps = sorted(int(k) for k in sm["compressors"])
electric = sorted(rng.sample(comps, max(1, round(0.10 * len(comps)))))
out = {"plants": plants, "nongas_headroom_mw": nongas_headroom + unlinked_gas_headroom, "total_load_mw": float(cf.bus["PD"].sum()),
       "processing_nodes": processing, "electric_compressors": electric,
       "compressor_ratio": {str(k): sm["compressors"][str(k)]["ratio"] for k in comps},
       "floor_pa": 2901.3e3, "trip_pa": 0.9 * 2.8e6 + 101.3e3,
       "notes": {"electric_compressor_share": "10% placeholder (NERC: electric compressor stations not a large share in Texas), seed 20261124",
                 "trip_rule": "runback to Pmin at 2.8 MPag; trip at 2.52 MPag (10% further below floor, gauge) - declared assumption",
                 "load_shed": "pro rata statewide; copper-plate balance (no network constraints) in v1"}}
json.dump(out, open("elec/coupling_data.json", "w"), indent=1)
print("plants", len(plants), "| linked gas Pg %.0f MW, Pmin %.0f MW" % (sum(p["pg"] for p in plants.values()), sum(p["pmin"] for p in plants.values())),
      "| non-gas headroom %.0f MW | processing nodes %d | electric compressors %s" % (out["nongas_headroom_mw"], len(processing), electric))
