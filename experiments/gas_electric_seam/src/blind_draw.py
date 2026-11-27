"""Draw the sealed blind-test scenarios from the NIST Randomness Beacon (protocol Section 2C).
Usage: python3 -I blind_draw.py <beacon_outputValue_hex> <out_dir>
Everything below is fixed before the beacon pulse exists; the pulse value alone decides the draw."""
import hashlib, json, os, sys
import numpy as np
POOL = {
    "radius_km": [475, 500, 550, 575, 600, 650, 675, 700],          # 19.1-53.5% of processing-plant supply
    "ramp_h": [0.25, 0.5, 1, 2, 4, 6],
    "strain_start_h": [6.5, 7.0, 7.5, 8.0, 8.5, 9.0],
    "failure": [None] * 10 + [                                        # half of scenarios have no failure
        ("houston_c15", [15], "isolate"), ("houston_c20", [20], "isolate"), ("victoria", [9, 24], "isolate"),
        ("victoria", [9, 24], "bypass"), ("station_c21", [21], "isolate"), ("station_c23", [23], "isolate"),
        ("station_c27", [27], "isolate"), ("station_c1", [1], "isolate"), ("dallas_c2", [2], "isolate"),
        ("permian", [11], "isolate")],
    "failure_delay_h": [0.5, 1, 2, 3, 4, 6],
}
N_STRAIN, N_CONTROL_LABELS, N_SEEDS = 16, 4, 10
PRE_H, WINDOW_H = 6, 30
ACUTE_STATIONS = {"houston_c15", "houston_c20"}   # isolations at these stations were acute in every tuning and confirmation case
beacon, out = sys.argv[1].strip().upper(), sys.argv[2]
seed = int.from_bytes(hashlib.sha256(("SCFL-seam-blind-1|" + beacon).encode()).digest()[:8], "big")
rng = np.random.default_rng(seed)
scen = []
for i in range(N_STRAIN):
    f = POOL["failure"][rng.integers(len(POOL["failure"]))]
    s = dict(kind="strain", radius_km=int(rng.choice(POOL["radius_km"])), ramp_h=float(rng.choice(POOL["ramp_h"])),
             strain_start_h=float(rng.choice(POOL["strain_start_h"])))
    if f is None: s["failure"] = None
    else:
        d = float(rng.choice(POOL["failure_delay_h"]))
        s["failure"] = dict(station=f[0], comps=f[1], mode=f[2], t_fail_h=s["strain_start_h"] + d, delay_h=d,
                            acute_class=(f[0] in ACUTE_STATIONS and f[2] == "isolate"))
    scen.append(s)
scen += [dict(kind="control") for _ in range(N_CONTROL_LABELS)]
for j, s in enumerate(scen): s["scenario_id"] = f"S{j+1:02d}"
inputs = []
for s in scen:
    for k in range(N_SEEDS):
        inputs.append(dict(scenario_id=s["scenario_id"], noise_seed=int(rng.integers(1, 2**31 - 1))))
codes = set()
for x in inputs:
    while True:
        c = "".join(rng.choice(list("ABCDEFGHJKMNPQRSTUVWXYZ23456789"), 6))
        if c not in codes: codes.add(c); x["code"] = c; break
order = rng.permutation(len(inputs)); inputs = [inputs[i] for i in order]
os.makedirs(out, exist_ok=True)
draw = dict(beacon_outputValue=beacon, derived_seed=seed, pool=POOL, pre_h=PRE_H, window_h=WINDOW_H, scenarios=scen, inputs=inputs)
json.dump(draw, open(os.path.join(out, "SEALED_answer_key.json"), "w"), indent=1)
print("scenarios", len(scen), "inputs", len(inputs))
print("answer key sha256", hashlib.sha256(open(os.path.join(out, "SEALED_answer_key.json"), "rb").read()).hexdigest())
