"""Build one GasTranSim case from the settled state.
Usage: python3 -I make_case.py <base_case> <ic.json> <Texas7k_Gas.json> <out_dir> <R_km> <cut_frac> <ramp_start_h> <ramp_end_h> <horizon_h> <output_dt_s>
cut_frac 0 gives a control. Region: processing plants within R_km pipeline distance of gas node 546.
"""
import json, os, shutil, sys, heapq, collections
base, icf, src, out = sys.argv[1:5]
R, CUT, T0, T1, H, ODT = float(sys.argv[5]) * 1e3, float(sys.argv[6]), float(sys.argv[7]) * 3600, float(sys.argv[8]) * 3600, float(sys.argv[9]) * 3600, float(sys.argv[10])
CAP = len(sys.argv) > 11 and sys.argv[11] == "cap"
d = json.load(open(src))
adj = collections.defaultdict(list)
for b in d["branches"]:
    L = abs(b["length"]) if b["dev_type"] == "pipe" else 0.0
    adj[b["n1"]].append((b["n2"], L)); adj[b["n2"]].append((b["n1"], L))
D = {546: 0.0}; h = [(0.0, 546)]
while h:
    dd, x = heapq.heappop(h)
    if dd > D[x]: continue
    for y, w in adj[x]:
        if dd + w < D.get(y, 1e18): D[y] = dd + w; heapq.heappush(h, (dd + w, y))
cut = [n["number"] for n in d["nodes"] if n["name"] == "Processing Plant" and n["qf"] < 0 and D.get(n["number"], 1e18) < R]
shutil.rmtree(out, ignore_errors=True); shutil.copytree(base, out)
shutil.copy(icf, os.path.join(out, "ic.json"))
p = json.load(open(os.path.join(out, "params.json"))); sp = p["simulation_params"]
sp["Final time"] = H; sp["Output dt"] = ODT; sp["Save final state"] = 0.0
json.dump(p, open(os.path.join(out, "params.json"), "w"))
bc = json.load(open(os.path.join(out, "bc.json")))
for sec in bc.values():
    for v in sec.values():
        v["time"] = [0, H]
        for key in ("value", "control_type"):
            if key in v: v[key] = [v[key][0], v[key][0]]
if CUT > 0:
    for n in cut:
        v = bc["boundary_nonslack_flow"][str(n)]; w0 = v["value"][0]
        v["time"] = [0, T0, T1, H]; v["value"] = [w0, w0, w0 * (1 - CUT), w0 * (1 - CUT)]
if CAP:   # supply cap: slack node becomes a fixed supply at the balancing rate of the settled state
    net = json.load(open(os.path.join(out, "network.json")))
    sl = [k for k, v in net["nodes"].items() if v["slack_bool"] == 1][0]
    net["nodes"][sl]["slack_bool"] = 0
    json.dump(net, open(os.path.join(out, "network.json"), "w"))
    w_other = sum(v["value"][0] for v in bc["boundary_nonslack_flow"].values())
    bc["boundary_nonslack_flow"][sl] = {"time": [0, H], "value": [-w_other, -w_other]}
    del bc["boundary_pslack"][sl]
    ic = json.load(open(os.path.join(out, "ic.json")))
    print("supply cap: node", sl, "fixed at %.3f kg/s" % w_other)
json.dump(bc, open(os.path.join(out, "bc.json"), "w"))
json.dump({"supply_cap": CAP, "region_km": R / 1e3, "cut_nodes": cut if CUT > 0 else [], "cut_fraction": CUT, "ramp_start_s": T0,
           "ramp_end_s": T1, "horizon_s": H, "output_dt_s": ODT}, open(os.path.join(out, "scenario.json"), "w"), indent=1)
print(out, "plants cut:", len(cut) if CUT > 0 else 0)
