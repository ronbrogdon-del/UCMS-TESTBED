"""Compare failure runs against the control: per-plant pressure drop, weakest-plant margin, projected time to the floor.
Usage: python3 -I compare_fail.py <control.out.json> <run.out.json> [...]"""
import json, sys
import numpy as np
FLOOR = 2901.3
ctl = json.load(open(sys.argv[1])); t = np.array(ctl["t_s"]) / 3600
pc = {k: np.array(v) for k, v in ctl["pressure_kPa"].items()}
wc = np.min(np.vstack(list(pc.values())), axis=0) - FLOOR
print(f"{'run':16s} {'first_rb_h':>10s} {'margin_end':>10s} {'ctl_margin':>10s} {'drop_vs_ctl':>11s} {'slope_kPa/h':>11s} {'proj_floor_h':>12s} worst plants (drop kPa)")
for f in sys.argv[2:]:
    r = json.load(open(f)); tr = np.array(r["t_s"]) / 3600
    pr = {k: np.array(v) for k, v in r["pressure_kPa"].items()}
    w = np.min(np.vstack(list(pr.values())), axis=0) - FLOOR
    n = min(len(w), len(wc))
    drop = {k: pc[k][n-1] - pr[k][n-1] for k in pr}
    worst = sorted(drop.items(), key=lambda kv: -kv[1])[:5]
    m = tr[:n] >= tr[n-1] - 3       # slope over the last 3 h
    slope = np.polyfit(tr[:n][m], w[:n][m], 1)[0]
    proj = tr[n-1] + w[n-1] / -slope if slope < 0 else float("inf")
    ev = r["events"]; rb = ev.get("first_runback_s"); rb = f"{rb/3600:.2f}" if rb else "-"
    name = f.split("/")[-1].replace(".out.json", "")
    print(f"{name:16s} {rb:>10s} {w[n-1]:10.1f} {wc[n-1]:10.1f} {wc[n-1]-w[n-1]:11.1f} {slope:11.2f} {proj:12.1f} " +
          ", ".join(f"{k}({v:.0f})" for k, v in worst))
