"""Physical ground truth for 'renewed worsening' (simulator only, no SCFL).
Erosion rate E(t) = drop in the weakest Houston plant margin over the previous hour (kPa/h), from noise-free coupled output.
A run shows renewed worsening if, inside [T_START, T_END], after E has fallen below DECL x its running peak,
E rises again by at least RISE x that peak above its lowest post-decline value, sustained for SUST minutes.
Usage: python3 -I truth_renewed.py <T_START_h> <T_END_h> <DECL> <RISE> <SUST_min> <run.out.json> ..."""
import json, sys
import numpy as np, pandas as pd
TS, TE, DECL, RISE, SUST = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
NODES = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,19,20,21,23,24,25,26,27,30,31,32,33,34,36,37,38]
for f in sys.argv[6:]:
    r = json.load(open(f)); t = pd.to_timedelta(np.array(r["t_s"]), unit="s")
    m = pd.Series(np.min(np.vstack([np.array(r["pressure_kPa"][str(n)]) for n in NODES]), axis=0), index=t)
    m = m.resample("5min").nearest()
    E = (m.shift(12) - m)[pd.Timedelta(hours=TS):pd.Timedelta(hours=TE)]
    pk = E.cummax(); dec = E < DECL * pk
    verdict, when = False, None
    if dec.any():
        p = dec.idxmax(); post = E[p:]; lift = post - post.cummin(); ok = (lift >= RISE * pk[p:]).astype(int)
        run = ok.rolling(int(SUST / 5)).sum(); hit = run[run >= SUST / 5]
        if len(hit): verdict, when = True, hit.index[0]
    name = f.split("/")[-1].replace(".out.json", "")
    print(f"{name:22s} peak erosion {E.max():6.1f} kPa/h  renewed worsening: {'YES at %.2f h' % (when.total_seconds()/3600) if verdict else 'no'}")
