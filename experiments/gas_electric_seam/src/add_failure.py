"""Add a compressor-station failure to a case's scenario.json.
Usage: python3 -I add_failure.py <case_dir> <station_name> <comp_ids comma-sep> <bypass|isolate> <t_fail_h> <ramp_s> <precedent>"""
import json, os, sys
case, name, comps, mode, tf, ramp, prec = sys.argv[1:8]
p = os.path.join(case, "scenario.json"); s = json.load(open(p))
s.setdefault("compressor_failures", []).append(dict(station=name, comps=[int(c) for c in comps.split(",")], mode=mode,
    t_fail_s=float(tf) * 3600, ramp_s=float(ramp), precedent=prec))
json.dump(s, open(p, "w"), indent=1); print(p, s["compressor_failures"][-1])
