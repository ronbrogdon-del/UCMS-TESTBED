"""Map the seam links: gas plant nodes -> gas-fired generators; compressor stations -> nearest substation/bus/area.
Writes elec/seam_map.json. Usage: python3 -I map_seam.py <raw_dir>"""
import json, re, shlex, math, collections, sys
import pandas as pd
from matpowercaseframes import CaseFrames
raw = sys.argv[1]
cf = CaseFrames(raw + "/Texas7k.m")
bus, gen = cf.bus, cf.gen
m = open(raw + "/Texas7k.m").read()
fuel = re.findall(r"'([^']*)'", m[m.index("mpc.genfuel = {"):m.index("};", m.index("mpc.genfuel = {"))])
names = re.findall(r"'([^']*)'", m[m.index("mpc.bus_name = {"):m.index("};", m.index("mpc.bus_name = {"))])
aux = open(raw + "/Texas7k.AUX").read().splitlines()
subs = {}
for l in aux[18:4914]:
    if not l.strip() or l.strip() in "{}": continue
    r = shlex.split(l)
    if len(r) >= 5 and r[0].isdigit(): subs[int(r[0])] = (r[1], float(r[3]), float(r[4]))
name2sub = {v[0]: k for k, v in subs.items()}
busnum = [int(x) for x in bus["BUS_I"]]
bus2sub = {b: name2sub.get(n.rsplit(" ", 1)[0]) for b, n in zip(busnum, names)}
area = dict(zip(busnum, bus["BUS_AREA"].astype(int)))
sub2buses = collections.defaultdict(list)
for b, s in bus2sub.items(): sub2buses[s].append(b)
g = gen.reset_index(drop=True)
gens = [dict(row=i, bus=int(g.loc[i, "GEN_BUS"]), pg=float(g.loc[i, "PG"]), pmax=float(g.loc[i, "PMAX"]),
             on=int(g.loc[i, "GEN_STATUS"]), fuel=fuel[i]) for i in range(len(g))]
d = json.load(open(raw + "/Texas7k_Gas.json"))
plants = {}
for n in d["nodes"]:
    if n["name"] != "Electric Load": continue
    gl = [x for x in gens if x["fuel"] == "ng" and bus2sub.get(x["bus"]) == n["sub"]]
    plants[n["number"]] = {"sub": n["sub"], "sub_name": subs[n["sub"]][0], "area": area[gl[0]["bus"]] if gl else None,
                           "gens": [x["row"] for x in gl], "pg_mw": sum(x["pg"] for x in gl if x["on"]),
                           "pmax_mw": sum(x["pmax"] for x in gl if x["on"])}
# compressor stations: nearest substation to the compressor's suction node
N = {n["number"]: n for n in d["nodes"]}
comps = {}
for i, b in enumerate([b for b in d["branches"] if b["dev_type"] == "compressor"]):
    nd = N[b["n1"]]
    best = min(subs.items(), key=lambda kv: (kv[1][1] - nd["lat"]) ** 2 + ((kv[1][2] - nd["lon"]) * math.cos(math.radians(nd["lat"]))) ** 2)
    km = 111 * math.hypot(best[1][1] - nd["lat"], (best[1][2] - nd["lon"]) * math.cos(math.radians(nd["lat"])))
    bl = sub2buses.get(best[0], [])
    comps[i + 1] = {"n1": b["n1"], "n2": b["n2"], "ratio": b["r"], "sub": best[0], "sub_name": best[1][0],
                    "km_to_sub": round(km, 1), "area": area[bl[0]] if bl else None}
json.dump({"plants": plants, "compressors": comps}, open("elec/seam_map.json", "w"), indent=1)
ng_on = [x for x in gens if x["fuel"] == "ng" and x["on"]]
mapped = {r for p in plants.values() for r in p["gens"]}
print("gas-fired units in service:", len(ng_on), "| total gas Pg MW %.0f" % sum(x["pg"] for x in ng_on))
print("plant nodes:", len(plants), "| units linked:", len(mapped & {x["row"] for x in ng_on}), "| linked gas Pg MW %.0f" % sum(p["pg_mw"] for p in plants.values()))
print("system load MW %.0f | gas share of dispatch %.0f%%" % (bus["PD"].sum(), 100 * sum(x["pg"] for x in ng_on) / sum(x["pg"] for x in gens if x["on"])))
print("compressors:", len(comps), "| km to nearest substation: median %.1f max %.1f" % (sorted(c["km_to_sub"] for c in comps.values())[len(comps) // 2], max(c["km_to_sub"] for c in comps.values())))
print("areas with gas plants:", sorted(collections.Counter(p["area"] for p in plants.values()).items()))
print("areas with compressors:", sorted(collections.Counter(c["area"] for c in comps.values()).items()))
