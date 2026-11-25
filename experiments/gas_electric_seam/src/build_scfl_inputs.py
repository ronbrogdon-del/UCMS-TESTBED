"""Build SCFL engine inputs (series.csv, series_manifest.csv, scan_config.json) for the
preliminary gas-only run. Exploratory, not blind.
State series: pressure at the 19 gas-fired plant nodes within 250 km pipeline distance of node 546.
Neutral timestamps from 2030-01-01 00:00 UTC, 5-minute cadence (elapsed_s 0..28800).
Fixed SHIFT baseline: first hour (before the ramp), search from 01:00.
Usage: python3 -I build_scfl_inputs.py <runs_export_dir> <Texas7k_Gas.json> <out_dir>
"""
import json, os, sys, heapq, collections, zipfile, hashlib
import pandas as pd
exp, src, out = sys.argv[1:4]
NOISE_SD = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0   # kPa, one standard deviation of declared sensor noise
SEED = int(sys.argv[5]) if len(sys.argv) > 5 else 20261124
import numpy as np
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
nodes = [n["number"] for n in d["nodes"] if n["name"] == "Electric Load" and D.get(n["number"], 1e18) < 250e3]
pn = pd.read_csv(os.path.join(exp, "plant_nodes.csv")).set_index("gas_node")
cols = {n: f"P_node{n}" for n in nodes}
START = pd.Timestamp("2030-01-01 00:00")
FLOOR = 2901.3   # kPa abs = 2.8 MPag + 101.3 kPa; low end of OEM GT fuel-supply minimum (2.8-5 MPag at GT package inlet)
for run in ("control", "shortfall"):
    df = pd.read_csv(os.path.join(exp, f"{run}_pressure_kPa.csv"))
    s = df[[str(n) for n in nodes]].copy()
    s.columns = [cols[n] for n in nodes]
    s.index = START + pd.to_timedelta(df["elapsed_s"], unit="s")
    s.index.name = "timestamp"
    if NOISE_SD > 0:   # same seed for both runs: identical noise realisation, so control/shortfall differ only by physics
        rng = np.random.default_rng(SEED)
        s = s + rng.normal(0.0, NOISE_SD, size=s.shape)
    s["Weakest_plant_pressure"] = s[[cols[n] for n in nodes]].min(axis=1)
    s["Min_delivery_pressure"] = FLOOR
    dd_ = os.path.join(out, "inputs", f"INPUT_{run}")
    os.makedirs(dd_, exist_ok=True)
    s.round(4).to_csv(os.path.join(dd_, "series.csv"))
    rows = [{"Series": cols[n], "What it measures": f"Gas pressure at plant gas node {n} (substation {pn.loc[n,'substation']} {pn.loc[n,'substation_name']})",
             "System of record": "GasTranSim.jl on Texas7k combined electric-gas test case", "Units": "kPa",
             "Cadence": "5-min", "Start": "", "End": "", "Time zone": "UTC", "Role": "State series",
             "Notes": "", "File": "series.csv", "Timestamp column": "timestamp", "Value column": cols[n]} for n in nodes]
    base = {"System of record": "GasTranSim.jl on Texas7k combined electric-gas test case", "Units": "kPa",
            "Cadence": "5-min", "Start": "", "End": "", "Time zone": "UTC", "Role": "Load / driver",
            "File": "series.csv", "Timestamp column": "timestamp"}
    rows.append(dict(base, **{"Series": "Weakest_plant_pressure", "What it measures": "Lowest gas pressure across the 19 state-series plant nodes at each step",
                              "Notes": "derived: row minimum of the 19 state series", "Value column": "Weakest_plant_pressure"}))
    rows.append(dict(base, **{"Series": "Min_delivery_pressure", "What it measures": "Minimum gas-turbine fuel supply pressure (constant)",
                              "System of record": "OEM natural-gas fuel specification (PSO Comanche RFP, Appendix C Att. 4): 2.8-5 MPag at GT package inlet; low end used",
                              "Notes": "2.8 MPag + 101.3 kPa = 2901.3 kPa abs; network pressures assumed absolute", "Value column": "Min_delivery_pressure"}))
    pd.DataFrame(rows).to_csv(os.path.join(dd_, "series_manifest.csv"), index=False)
    cfg = {"state_series": [cols[n] for n in nodes], "period": "D",
           "margin": {"plus": ["Weakest_plant_pressure"], "minus": ["Min_delivery_pressure"]},
           "shift": {"mode": "fixed", "baseline_start": "2030-01-01 00:00:00",
                     "baseline_end": "2030-01-01 00:55:00", "search_from": "2030-01-01 01:00:00"}}
    json.dump(cfg, open(os.path.join(dd_, "scan_config.json"), "w"), indent=2)
zp = os.path.join(out, "SCFL_prelim_gas_inputs.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for run in ("control", "shortfall"):
        for fn in ("series.csv", "series_manifest.csv", "scan_config.json"):
            p = f"inputs/INPUT_{run}/{fn}"
            zi = zipfile.ZipInfo(p, (2030, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(zi, open(os.path.join(out, p), "rb").read())
print(len(nodes), "state series:", nodes, "| noise sd kPa", NOISE_SD, "seed", SEED)
print("zip sha256", hashlib.sha256(open(zp, "rb").read()).hexdigest())
