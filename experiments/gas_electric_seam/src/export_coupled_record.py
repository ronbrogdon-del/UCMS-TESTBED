"""Export a coupled-run output to the public record format (no SCFL readings): system totals by minute,
events, and failed-station flow and pressures. Usage: python3 -I export_coupled_record.py <run.out.json> <prefix>"""
import json, sys
import pandas as pd
r = json.load(open(sys.argv[1])); pre = sys.argv[2]
keys = ["t_s", "lost_mw", "redisp_nongas_mw", "redisp_gas_mw", "shed_mw", "shed_frac", "supply_mult", "compressor_mult", "plants_runback", "plants_trip"]
df = pd.DataFrame({k: r[k] for k in keys})
P = pd.DataFrame(r["pressure_kPa"]); df["weakest_plant_margin_kPa"] = P.min(axis=1) - 2901.3
for c, v in r.get("failed_comp", {}).items():
    for k, x in v.items(): df[f"comp{c}_{k}"] = x
df.to_csv(pre + "_by_minute.csv", index=False, float_format="%.4f")
json.dump({"events_s": r["events"], "mode": r["mode"], "couple_dt_s": r["couple_dt_s"], "scenario": r["scenario"]}, open(pre + "_events.json", "w"), indent=1)
print(pre, len(df))
