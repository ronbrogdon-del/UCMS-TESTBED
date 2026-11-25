"""Build SCFL engine inputs v4 (compressor-failure set) from coupled-run outputs. Exploratory, pre-freeze.
State series: gas pressure at the 31 gas-fired plant nodes within 80 km (great-circle) of downtown Houston
(29.7604 N, 95.3698 W), declared before reading SCFL output.
Conditions (30 h, capped supply, coupled loop, uri mode):
  control       no supply cut, no failure
  strain        100% cut of processing plants within 600 km of node 546, ramp 1-3 h (= cut41)
  strain_hou20  strain + Houston station (compressor 20) isolated at 2 h, 5 min valve closure
  strain_vic    strain + Victoria station (compressors 9, 24) isolated at 2 h, 5 min valve closure
Sampling: nearest coupling record (60 s apart) to each 5-min mark. Declared sensor noise sd 1.4 kPa; seeds 20261125.. (one per
replicate; the same seed gives the same noise realisation in all four conditions).
Usage: python3 -I build_scfl_inputs_v4.py <Texas7k_Gas.json> <coupling_data.json> <out_dir> <n_seeds> <commit> \
           control=<out.json> strain=<out.json> strain_hou20=<out.json> strain_vic=<out.json>
"""
import json, os, sys, math, zipfile, hashlib
import numpy as np, pandas as pd
src, cdf, out, NS, COMMIT = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]
runs = dict(a.split("=", 1) for a in sys.argv[6:])
NOISE_SD, SEED0, FLOOR = 1.4, 20261125, 2901.3
raw = json.load(open(src)); nodes = {n["number"]: n for n in raw["nodes"]}; cd = json.load(open(cdf))
def km(a, b, c, d):
    p1, p2 = math.radians(a), math.radians(c); dp, dl = p2 - p1, math.radians(d - b)
    return 2 * 6371 * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
grp = sorted(int(k) for k in cd["plants"] if km(29.7604, -95.3698, nodes[int(k)]["lat"], nodes[int(k)]["lon"]) <= 80)
cols = [f"P_node{n}" for n in grp]
START = pd.Timestamp("2030-01-01 00:00")
SOR = "GasTranSim.jl on Texas7k combined electric-gas test case, coupled loop (ucms-testbed commit %s)" % COMMIT
data = {}
for cond, f in runs.items():
    r = json.load(open(f)); t = np.array(r["t_s"])
    grid = np.arange(0.0, float(r["scenario"]["horizon_s"]) + 1.0, 300.0)   # 5-min marks
    keep = np.array([int(np.argmin(np.abs(t - g))) for g in grid])           # nearest coupling record (60 s apart)
    assert np.max(np.abs(t[keep] - grid)) < 60.0
    df = pd.DataFrame({c: np.array(r["pressure_kPa"][str(n)])[keep] for c, n in zip(cols, grp)})
    df.index = START + pd.to_timedelta(grid, unit="s"); df.index.name = "timestamp"
    data[cond] = (df, r.get("scenario", {}), r["events"])
n0 = {k: len(v[0]) for k, v in data.items()}; assert len(set(n0.values())) == 1, n0
folders = []
for s in range(NS):
    seed = SEED0 + s
    noise = np.random.default_rng(seed).normal(0.0, NOISE_SD, size=data["control"][0].shape)
    for cond, (df, scen, ev) in data.items():
        x = df + noise
        x["Weakest_plant_pressure"] = x[cols].min(axis=1); x["Min_delivery_pressure"] = FLOOR
        name = f"INPUT_{cond}_s{s+1:02d}"; d_ = os.path.join(out, "inputs", name); os.makedirs(d_, exist_ok=True)
        x.round(4).to_csv(os.path.join(d_, "series.csv"))
        base = {"System of record": SOR, "Units": "kPa", "Cadence": "5-min", "Start": "", "End": "", "Time zone": "UTC",
                "File": "series.csv", "Timestamp column": "timestamp"}
        rows = [dict(base, **{"Series": c, "What it measures": f"Gas pressure at plant gas node {n} (substation {nodes[n]['sub']}, {cd['plants'][str(n)]['sub_name']})",
                              "Role": "State series", "Notes": f"condition {cond}; noise sd {NOISE_SD} kPa seed {seed}", "Value column": c})
                for c, n in zip(cols, grp)]
        rows.append(dict(base, **{"Series": "Weakest_plant_pressure", "What it measures": f"Lowest gas pressure across the {len(grp)} Houston plant nodes at each step",
                                  "Role": "Load / driver", "Notes": f"derived: row minimum of the {len(grp)} state series", "Value column": "Weakest_plant_pressure"}))
        rows.append(dict(base, **{"Series": "Min_delivery_pressure", "What it measures": "Minimum gas-turbine fuel supply pressure (constant)", "Role": "Load / driver",
                                  "System of record": "OEM natural-gas fuel specification (PSO Comanche RFP, Appendix C Att. 4): 2.8-5 MPag at GT package inlet; low end used",
                                  "Notes": "2.8 MPag + 101.3 kPa = 2901.3 kPa abs", "Value column": "Min_delivery_pressure"}))
        pd.DataFrame(rows).to_csv(os.path.join(d_, "series_manifest.csv"), index=False)
        cfg = {"state_series": cols, "period": "D", "margin": {"plus": ["Weakest_plant_pressure"], "minus": ["Min_delivery_pressure"]},
               "shift": {"mode": "fixed", "baseline_start": "2030-01-01 00:00:00", "baseline_end": "2030-01-01 00:55:00",
                         "search_from": "2030-01-01 01:00:00"}}
        json.dump(cfg, open(os.path.join(d_, "scan_config.json"), "w"), indent=2)
        folders.append(name)
prov = {"package": "SCFL_prelim_gas_inputs_v4", "testbed_version": "seam-v0.3-compressor", "commit": COMMIT,
        "status": "exploratory, pre-freeze", "state_series_rule": "plant gas nodes within 80 km of downtown Houston (29.7604, -95.3698)",
        "state_nodes": grp, "noise_sd_kPa": NOISE_SD, "seeds": [SEED0, SEED0 + NS - 1], "cadence": "5-min",
        "conditions": {k: {"scenario": v[1], "events_s": v[2]} for k, v in data.items()},
        "source_sha256": {k: hashlib.sha256(open(f, "rb").read()).hexdigest() for k, f in runs.items()}}
json.dump(prov, open(os.path.join(out, "inputs", "PROVENANCE.json"), "w"), indent=1)
zp = os.path.join(out, "SCFL_prelim_gas_inputs_v4.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for p in ["inputs/PROVENANCE.json"] + [f"inputs/{n}/{fn}" for n in folders for fn in ("series.csv", "series_manifest.csv", "scan_config.json")]:
        zi = zipfile.ZipInfo(p, (2030, 1, 1, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, open(os.path.join(out, p), "rb").read())
print(len(grp), "state series; folders", len(folders), "; rows", n0)
print("zip sha256", hashlib.sha256(open(zp, "rb").read()).hexdigest())
