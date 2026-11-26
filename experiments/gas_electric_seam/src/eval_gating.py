"""Apply the v4-Tune-2 gating rule (supplied by the operator for this check) to engine outputs of a tuning package.
Reads only engine output series (SHIFT_z, STRESS_diameter_w24, RUPTURE_ratio via candidates, drift_step_distance).
Rule parameters are passed on the command line and are not stored here."""
import glob, json, sys, collections
import pandas as pd, numpy as np
root, K, PERSIST, LOOKBACK_MIN, WIN_H, SLOPE_STEPS, SLOPE_PERSIST, DRIFT_X, PRE_H = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), int(sys.argv[6]), int(sys.argv[7]), float(sys.argv[8]), float(sys.argv[9])
STRAIN_ONLY = sys.argv[10].split(",")
T0 = pd.Timestamp("2030-01-01") + pd.Timedelta(hours=PRE_H)
runs = collections.defaultdict(list)
for f in sorted(glob.glob(f"{root}/inputs/INPUT_*/measure_output/operators_by_step.csv")):
    d = f.split("/")[-3][6:]; cond, seed = d.rsplit("_s", 1)
    x = pd.read_csv(f, index_col=0, parse_dates=True); s = json.load(open(f.replace("operators_by_step.csv", "operators_summary.json")))
    z = x["SHIFT_z"][T0:]; below = (z < -K).astype(int); r = below.rolling(PERSIST).sum(); hit = r[r >= PERSIST]
    gate = hit.index[0] - pd.Timedelta(minutes=5 * (PERSIST - 1)) if len(hit) else None
    rup = [pd.Timestamp(c["timestamp"]) for c in s["RUPTURE_candidates"]]
    dl = s["SHIFT"].get("lock_in")
    runs[cond].append(dict(seed=int(seed), gate=gate, default_lock=pd.Timestamp(dl) if dl else None, stress=x["STRESS_diameter_w24"],
                           slope=x["STRESS_diameter_w24"].diff(SLOPE_STEPS), rup=rup, drift=x["drift_step_distance"]))
win = lambda r, s: s[r["gate"]:r["gate"] + pd.Timedelta(hours=WIN_H)]
print("STAGE 1: SHIFT gate (rule applied to engine SHIFT_z) and default engine lock-in")
for c, L in runs.items():
    g = [(r["gate"] - T0).total_seconds() / 3600 for r in L if r["gate"] is not None]
    dlk = [r for r in L if r["default_lock"] is not None]
    print(f"  {c:22s} gated {len(g):2d}/30" + (f"  gate at {min(g):.2f}-{max(g):.2f} h after 06:00 (median {np.median(g):.2f})" if g else "") + f" | default lock {len(dlk)}/30")
print("STAGE 2: peak 20-min STRESS rise inside [gate, gate+window], strain-only cases")
ceil_by = {}
for c in STRAIN_ONLY:
    v = [win(r, r["slope"]).max() for r in runs[c] if r["gate"] is not None]; ceil_by[c] = max(v) if v else np.nan
    print(f"  {c:22s} max {ceil_by[c]:.1f}  median {np.median(v):.1f}")
CEIL = np.nanmax(list(ceil_by.values())); print(f"  ceiling (max over strain-only) = {CEIL:.1f}")
print("STAGE 2: classification (slope > ceiling for persist steps); Tier A = RUPTURE in [gate-lookback, gate+window] or slope > 2x ceiling")
for c, L in runs.items():
    cls = tA = rupw = rup_strict = 0; first = []
    for r in L:
        if r["gate"] is None: continue
        s = win(r, r["slope"]); e = (s > CEIL).astype(int).rolling(SLOPE_PERSIST).sum(); h = e[e >= SLOPE_PERSIST]
        lo = r["gate"] - pd.Timedelta(minutes=LOOKBACK_MIN); hi = r["gate"] + pd.Timedelta(hours=WIN_H)
        rw = any(lo <= t <= hi for t in r["rup"]); rs = any(r["gate"] <= t <= hi for t in r["rup"])
        shock = (s > 2 * CEIL).any()
        if len(h) or rw or shock: cls += 1; first.append(((h.index[0] if len(h) else s.index[-1]) - r["gate"]).total_seconds() / 3600)
        tA += (rw or shock); rupw += rw; rup_strict += rs
    print(f"  {c:22s} classified {cls:2d}/30  TierA {tA:2d}  RUPTURE in look-back window {rupw:2d} (post-gate only {rup_strict:2d})")
print("STAGE 3: hourly DRIFT (sum of step distances) vs control ceiling x", DRIFT_X)
H = lambda r: r["drift"].resample("1h").sum()
cc = max(H(r)[T0:].max() for r in runs[[c for c in runs if "control" in c][0]])
print(f"  control hourly ceiling {cc:.1f}")
for c, L in runs.items():
    n = 0; t = []
    for r in L:
        if r["gate"] is None: continue
        h = H(r)[r["gate"].floor("h") + pd.Timedelta(hours=1):]; e = (h > DRIFT_X * cc).astype(int).rolling(2).sum(); k = e[e >= 2]
        if len(k): n += 1; t.append((k.index[0] - r["gate"]).total_seconds() / 3600)
    print(f"  {c:22s} confirmed {n:2d}/30" + (f"  at gate+{min(t):.1f}-{max(t):.1f} h" if t else ""))
