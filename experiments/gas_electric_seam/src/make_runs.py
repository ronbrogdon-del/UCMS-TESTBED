"""Build the control and shortfall cases from the spun-up state.

Exploratory, illustrative shortfall (not protocol tiers):
  - region: processing plants within 250 km pipeline distance of node 546
  - cut: 50% of each plant's supply, linear ramp from t=1 h to t=3 h, then held
  - horizon 8 h, output every 300 s
Usage: python3 -I make_runs.py <base_case> <ic_final.json> <Texas7k_Gas.json> <out_root>
"""
import json, os, shutil, sys, heapq, collections

base, icf, src, root = sys.argv[1:5]
H, T0, T1, CUT, R = 8 * 3600, 3600, 3 * 3600, 0.5, 250e3
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
cut_nodes = [n["number"] for n in d["nodes"]
             if n["name"] == "Processing Plant" and n["qf"] < 0 and D.get(n["number"], 1e18) < R]

ic = json.load(open(icf))
for name in ("control", "shortfall"):
    out = os.path.join(root, name)
    shutil.rmtree(out, ignore_errors=True); shutil.copytree(base, out)
    json.dump(ic, open(os.path.join(out, "ic.json"), "w"))
    p = json.load(open(os.path.join(out, "params.json"))); sp = p["simulation_params"]
    sp["Final time"] = H; sp["Output dt"] = 300.0; sp["Save final state"] = 0.0
    json.dump(p, open(os.path.join(out, "params.json"), "w"))
    bc = json.load(open(os.path.join(out, "bc.json")))
    for sec in bc.values():
        for v in sec.values():
            v["time"] = [0, H]
            for key in ("value", "control_type"):
                if key in v: v[key] = [v[key][0], v[key][0]]
    if name == "shortfall":
        for n in cut_nodes:
            v = bc["boundary_nonslack_flow"][str(n)]
            w0 = v["value"][0]                      # negative = supply
            v["time"] = [0, T0, T1, H]
            v["value"] = [w0, w0, w0 * (1 - CUT), w0 * (1 - CUT)]
    json.dump(bc, open(os.path.join(out, "bc.json"), "w"))
json.dump({"cut_nodes": cut_nodes, "cut_fraction": CUT, "ramp_start_s": T0, "ramp_end_s": T1,
           "horizon_s": H, "region": "processing plants within 250 km pipeline distance of node 546",
           "label": "exploratory, illustrative; not protocol tiers"},
          open(os.path.join(root, "scenario.json"), "w"), indent=1)
print(len(cut_nodes), "plants cut:", cut_nodes)
