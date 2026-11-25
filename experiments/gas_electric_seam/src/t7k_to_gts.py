"""Convert Texas7k_Gas.json into GasTranSim input files (steady hold, no injection).

Modelling choices (all logged to conversion_log.json):
  - pressure: |p| (file solves in squared pressure; sign is an artifact), kPa -> Pa
  - flow: standard m3/h -> kg/s using rho_stp from the file's own STP constants
  - zero-length pipes: end nodes merged (union-find)
  - negative pipe lengths: absolute value
  - optional (arg 5 = "k"): friction factor re-derived from the file's resistance k,
    so the simulator reproduces the file's solved steady state
  - pipes shorter than LMIN: length set to LMIN, friction scaled by L/LMIN
    (keeps f*L/D, so the steady-state pressure drop is unchanged)
  - slack node: pressure control at its |p|; all others: flow control at qf
  - compressors: compression-ratio control at r
Usage: python3 -I t7k_to_gts.py <Texas7k_Gas.json> <out_dir> [LMIN_m] [hours]
"""
import json, math, os, sys

src, out = sys.argv[1], sys.argv[2]
LMIN = float(sys.argv[3]) if len(sys.argv) > 3 else 1000.0
HOURS = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
FROM_K = (sys.argv[5] == "k") if len(sys.argv) > 5 else False
os.makedirs(out, exist_ok=True)
d = json.load(open(src))
g = d["gas"]
rho_stp = g["pressure_stp"] * 1000 / (g["gas_constant"] * g["temp_stp"])
Q = rho_stp / 3600.0                      # kg/s per std m3/h
G = 8314.46 / (g["gas_constant"] * 28.9647)
a2 = g["z_nom"] * g["gas_constant"] * g["temp_nom"]
T_END = HOURS * 3600

nodes = {n["number"]: n for n in d["nodes"]}
parent = {k: k for k in nodes}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
slack = [k for k, n in nodes.items() if n["slack"]][0]
log = {"zero_length_merged": [], "negative_length_abs": [], "lengthened": 0,
       "LMIN_m": LMIN, "friction_from_k": 0, "kg_s_per_std_m3_h": Q, "G": G}
for b in d["branches"]:
    if b["dev_type"] == "pipe" and b["length"] == 0:
        a, c = find(b["n1"]), find(b["n2"])
        if a != c:
            keep, drop = (a, c) if a == slack or c != slack else (c, a)
            parent[drop] = keep
            log["zero_length_merged"].append([b["n1"], b["n2"]])

rep = {k: find(k) for k in nodes}
demand = {}
for k, n in nodes.items():
    r = rep[k]
    if k != slack:
        demand[r] = demand.get(r, 0.0) + n["qf"] * Q
pres = {}
for k, n in nodes.items():
    pres.setdefault(rep[k], abs(n["p"]) * 1000)

net = {"nodes": {}, "pipes": {}, "compressors": {}}
for r in sorted(set(rep.values())):
    n = nodes[r]
    net["nodes"][str(r)] = {"node_id": r, "node_name": n["name"], "x_coord": n["lon"],
        "y_coord": n["lat"], "min_pressure": 0, "max_pressure": 2e7,
        "min_injection": -1e9, "max_injection": 1e9, "slack_bool": int(r == slack)}

ic = {"initial_nodal_pressure": {}, "initial_pipe_flow": {}, "initial_compressor_flow": {}}
bc = {"boundary_pslack": {}, "boundary_nonslack_flow": {}, "boundary_compressor": {}}
pid = cid = 0
for b in d["branches"]:
    u, v = rep[b["n1"]], rep[b["n2"]]
    if b["dev_type"] == "pipe":
        if b["length"] == 0:
            continue
        L, f = b["length"], b["friction_factor"]
        if FROM_K and b["k"] > 0:
            D = b["diameter"]; A = math.pi * D * D / 4
            f_k = b["k"] * 1e6 / (Q * Q) * D * A * A / (abs(L) * a2)
            if abs(f_k / f - 1) > 0.02: log["friction_from_k"] += 1
            f = f_k
        if L < 0:
            log["negative_length_abs"].append(b["uid"] if False else [b["n1"], b["n2"], L]); L = -L
        if L < LMIN:
            f = f * L / LMIN; L = LMIN; log["lengthened"] += 1
        pid += 1
        net["pipes"][str(pid)] = {"pipe_id": pid, "pipe_name": f"p{pid}", "from_node": u,
            "to_node": v, "diameter": b["diameter"], "length": L, "friction_factor": f,
            "disc_seg": 0, "src": [b["n1"], b["n2"]]}
        ic["initial_pipe_flow"][str(pid)] = b["q"] * Q
    else:
        cid += 1
        net["compressors"][str(cid)] = {"comp_id": cid, "comp_name": f"c{cid}", "from_node": u,
            "to_node": v, "c_min": 1.0, "c_max": 2.0, "max_power": 1e12,
            "min_flow": -1e9, "max_flow": 1e9, "src": [b["n1"], b["n2"]]}
        ic["initial_compressor_flow"][str(cid)] = b["q"] * Q
        bc["boundary_compressor"][str(cid)] = {"time": [0, T_END], "control_type": [0, 0],
                                               "value": [b["r"], b["r"]]}

for r in net["nodes"]:
    ri = int(r)
    ic["initial_nodal_pressure"][r] = pres[ri]
    if ri == slack:
        bc["boundary_pslack"][r] = {"time": [0, T_END], "value": [pres[ri]] * 2}
    else:
        w = demand.get(ri, 0.0)
        bc["boundary_nonslack_flow"][r] = {"time": [0, T_END], "value": [w, w]}

params = {"simulation_params": {"Temperature (K):": g["temp_nom"], "Gas specific gravity (G):": G,
    "Specific heat capacity ratio": 1.4, "units (SI = 0, standard = 1)": 0.0,
    "Initial time": 0.0, "Final time": T_END, "Discretization time step": 1.0,
    "Courant number (must be between 0 and 1, recommended value is 0.9)": 0.9,
    "Output dt": 600.0, "Output dx": 1000.0, "Save final state": 0.0}}
# CFL: dt <= C * LMIN / a ; set below the limit
a = math.sqrt(1.25 * g["gas_constant"] * g["temp_nom"])
params["simulation_params"]["Discretization time step"] = round(0.8 * 0.9 * LMIN / a, 2)

for name, obj in [("network", net), ("ic", ic), ("bc", bc), ("params", params),
                  ("disruptions", {"disruption": {}})]:
    json.dump(obj, open(os.path.join(out, name + ".json"), "w"))
log.update(nodes=len(net["nodes"]), pipes=pid, compressors=cid,
           dt=params["simulation_params"]["Discretization time step"], slack=slack)
json.dump(log, open(os.path.join(out, "conversion_log.json"), "w"), indent=1)
print({k: (len(v) if isinstance(v, list) else v) for k, v in log.items()})
