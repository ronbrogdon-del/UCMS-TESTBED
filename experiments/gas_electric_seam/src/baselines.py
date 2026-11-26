"""Conventional baseline alarms for the gas-electric seam test (pre-registered before the blind draw).
All use only the input series (31 plant pressures, kPa, 5-min), the first PRE_H hours as baseline, search from PRE_H.
  B1 level alarm:    weakest-plant pressure below its baseline mean by >= THR1 kPa for 3 consecutive samples.
  B2 rate alarm:     least-squares slope of weakest-plant pressure over the last 1 h <= -THR2 kPa/h for 3 consecutive samples.
  B3 multivariate:   Hotelling T^2 of the 31 plant pressures against baseline mean and Ledoit-Wolf covariance,
                     >= THR3 for 3 consecutive samples, counted only when the mean pressure is below baseline (a drop).
Thresholds are calibrated on the 60 tuning control inputs only: the lowest value on a fixed grid that gives zero alarms.
Usage: calibrate:  python3 -I baselines.py calibrate <pre_h> <input_dir> [...]
       evaluate:   python3 -I baselines.py evaluate <pre_h> <thresholds.json> <input_dir>  -> CSV of first alarm time per input"""
import sys, json, glob, os
import numpy as np, pandas as pd
from sklearn.covariance import LedoitWolf
PERSIST = 3
def stats(folder, pre_h):
    df = pd.read_csv(os.path.join(folder, "series.csv"), index_col=0, parse_dates=True)
    cols = [c for c in df.columns if c.startswith("P_node")]; X = df[cols]
    t0 = df.index[0] + pd.Timedelta(hours=pre_h); base = X[X.index < t0]
    w = X.min(axis=1); wb = w[w.index < t0].mean()
    s1 = (wb - w)                                                       # kPa below baseline
    tt = (w.index - w.index[0]).total_seconds() / 3600
    s2 = -pd.Series(w.values, index=w.index).rolling(12).apply(lambda v: np.polyfit(np.arange(12) / 12.0, v, 1)[0], raw=True)  # kPa/h drop
    lw = LedoitWolf().fit(base.values); P = np.linalg.inv(lw.covariance_); dX = X.values - base.values.mean(axis=0)
    t2 = np.einsum("ij,jk,ik->i", dX, P, dX); drop = dX.mean(axis=1) < 0
    s3 = pd.Series(np.where(drop, t2, 0.0), index=X.index)
    return {k: v[v.index >= t0] for k, v in (("B1", s1), ("B2", s2), ("B3", s3))}
def persisted(s): return s.rolling(PERSIST).min()                     # value held for PERSIST samples
def first_alarm(s, thr):
    p = persisted(s); h = p[p >= thr]
    return None if not len(h) else h.index[0] - pd.Timedelta(minutes=5 * (PERSIST - 1))
GRID = {"B1": np.arange(0.5, 50.01, 0.5), "B2": np.arange(0.25, 30.01, 0.25), "B3": np.arange(10, 2000.1, 5)}
if sys.argv[1] == "calibrate":
    pre = float(sys.argv[2]); folders = [f for d in sys.argv[3:] for f in sorted(glob.glob(d))]
    mx = {"B1": 0, "B2": 0, "B3": 0}
    for f in folders:
        st = stats(f, pre)
        for k in mx: mx[k] = max(mx[k], float(persisted(st[k]).max()))
    thr = {k: float(GRID[k][np.argmax(GRID[k] > mx[k])]) for k in mx}
    print(json.dumps({"n_controls": len(folders), "max_control_stat": mx, "thresholds": thr}, indent=1))
else:
    pre = float(sys.argv[2]); thr = json.load(open(sys.argv[3]))["thresholds"]; rows = []
    for f in sorted(glob.glob(os.path.join(sys.argv[4], "INPUT_*"))):
        st = stats(f, pre); r = {"input": os.path.basename(f)}
        for k in thr:
            a = first_alarm(st[k], thr[k]); r[k] = "" if a is None else str(a)
        rows.append(r)
    pd.DataFrame(rows).to_csv(sys.stdout, index=False)
