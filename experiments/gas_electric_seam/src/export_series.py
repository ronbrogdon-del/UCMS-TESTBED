"""Export pressure series at the electric-load gas nodes for the control and shortfall runs.

Outputs (in <runs>/export/):
  plant_nodes.csv           gas node -> substation number, name, lat, lon, gas draw (std m3/h)
  control_pressure_kPa.csv  wide: elapsed_s, timestamp, one column per gas node
  shortfall_pressure_kPa.csv
  checks.json               consistency checks
Timestamps are nominal (start 2026-01-01T00:00, synthetic); elapsed_s is authoritative.
Usage: python3 -I export_series.py <runs_dir> <Texas7k_Gas.json> <Texas7k.AUX>
"""
import csv, json, os, shlex, sys, datetime

runs, src, aux = sys.argv[1:4]
out = os.path.join(runs, "export"); os.makedirs(out, exist_ok=True)
d = json.load(open(src))
el = [n for n in d["nodes"] if n["name"] == "Electric Load"]
subs = {}
lines = open(aux).read().splitlines()
for l in lines[18:4914]:
    if not l.strip() or l.strip() in "{}": continue
    r = shlex.split(l)
    if len(r) >= 5 and r[0].isdigit(): subs[int(r[0])] = r[1]

with open(os.path.join(out, "plant_nodes.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["gas_node", "substation", "substation_name", "lat", "lon", "gas_draw_std_m3_h"])
    for n in el:
        w.writerow([n["number"], n["sub"], subs.get(n["sub"], ""), n["lat"], n["lon"], round(n["qf"], 3)])

t0 = datetime.datetime(2026, 1, 1)
series = {}
for run in ("control", "shortfall"):
    r = json.load(open(os.path.join(runs, run + ".out.json")))
    t = r["time"]; series[run] = (t, r["nodes"])
    with open(os.path.join(out, run + "_pressure_kPa.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["elapsed_s", "timestamp_nominal"] + [str(n["number"]) for n in el])
        for i, ti in enumerate(t):
            w.writerow([round(ti, 1), (t0 + datetime.timedelta(seconds=round(ti))).isoformat()]
                       + [round(r["nodes"][str(n["number"])][i] / 1000, 4) for n in el])

tc, nc = series["control"]; tsr, ns = series["shortfall"]
pre = [i for i, x in enumerate(tc) if x <= 3600]
checks = {
    "time_points": len(tc), "same_time_axis": tc == tsr, "interval_s": tc[1] - tc[0],
    "plant_nodes": len(el), "missing_nodes": [n["number"] for n in el if str(n["number"]) not in nc],
    "nan_values": sum(1 for s in list(nc.values()) + list(ns.values()) for v in s if v is None or v != v),
    "max_abs_diff_before_ramp_kPa": max(abs(nc[k][i] - ns[k][i]) for k in nc for i in pre) / 1000,
    "control_max_drift_pct": max(abs(s[-1] - s[0]) / s[0] for s in nc.values()) * 100,
    "min_pressure_kPa": {"control": min(min(s) for s in nc.values()) / 1000,
                         "shortfall": min(min(s) for s in ns.values()) / 1000},
}
json.dump(checks, open(os.path.join(out, "checks.json"), "w"), indent=1)
print(json.dumps(checks, indent=1))
