"""
Baseline AC-Physics Characterization — Reserve-Headroom Proxy
                                         (stand-in for Section 1, item 2:
                                          "frequency response surfaces")
================================================================================
THIS IS NOT A FREQUENCY RESPONSE CURVE. Read this before using the output.

The original test-suite item asked for "how frequency responds to
incremental load changes across the year" -- a Δf-vs-ΔP relationship.
That requires generator inertia (H), governor droop (R), and AGC/primary-
frequency-response parameters. ACTIVSg2000 is a static MATPOWER power-flow
case: it has none of those. Confirmed directly -- RAMP_AGC is 0 for all
544 generators (not just unmodeled-as-zero by convention; genuinely absent
from this case). pypower's `runpf` has no frequency state at all. There is
no honest way to produce an actual frequency-response number from this
dataset with this tool.

What CAN be computed, and what this script computes instead: a STATIC
RESERVE-MARGIN PROXY. The reasoning for why this is a defensible stand-in
(not just "the only other thing we could think of"): a system's ability to
arrest a frequency excursion depends on having synchronized generation
headroom available to respond -- no headroom, no frequency response,
regardless of how good the governors are. So "how much online generation
headroom exists, relative to demand, at each hour of the year" is a
necessary precondition for frequency response capacity, even though it is
not a sufficient description of the dynamics themselves. It tells you
WHEN the system would have the least room to absorb a disturbance; it does
NOT tell you how big the resulting Δf would actually be.

Method:
  - Online generation capacity per area = sum(PMAX) over generators with
    GEN_STATUS==1 in that area, from the base case. OFFLINE capacity is
    reported separately as context (non-spinning, cannot respond to a
    frequency event on a relevant timescale) -- never added to the
    "available" headroom.
  - This capacity is held FIXED across all 8784 hours (we do not have an
    hourly re-dispatch; only the hourly LOAD profile is real per-hour
    data). The hourly variable is just the real 2016 load.
  - headroom_pct(area, hour) = (capacity_area - load_area(hour)) / capacity_area * 100
  - Same calculation done system-wide (sum of all areas' capacity and load).

Output: an 8784 x 8 (+ system column) reserve-headroom-% surface, plus a
summary identifying the tightest hours of the year per area and system-wide.
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from activsg2000_loader import load_case

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')


def main():
    cf = load_case()
    area_map = dict(zip(cf.bus['BUS_I'].astype(float), cf.bus['BUS_AREA'].astype(int)))

    gen = cf.gen.copy()
    gen['AREA'] = gen['GEN_BUS'].map(area_map)
    online = gen[gen['GEN_STATUS'] == 1]
    offline = gen[gen['GEN_STATUS'] == 0]

    cap_online = online.groupby('AREA')['PMAX'].sum().reindex(range(1, 9), fill_value=0.0)
    cap_offline = offline.groupby('AREA')['PMAX'].sum().reindex(range(1, 9), fill_value=0.0)

    print("Online (spinning) capacity by area (MW):")
    print(cap_online)
    print("\nOffline (non-spinning, NOT counted as available headroom) capacity by area (MW):")
    print(cap_offline)
    print(f"\nSystem online capacity: {cap_online.sum():.1f} MW | "
          f"offline: {cap_offline.sum():.1f} MW | "
          f"total installed: {cap_online.sum() + cap_offline.sum():.1f} MW")

    yr = pd.read_csv(os.path.join(DATA_DIR, 'activsg2000_area_load_8784h.csv'))
    load_cols = [f'area_{a}' for a in range(1, 9)]

    headroom_pct = pd.DataFrame({'hour': yr['hour']})
    for a in range(1, 9):
        cap = cap_online.loc[a]
        load = yr[f'area_{a}']
        headroom_pct[f'area_{a}_headroom_pct'] = (cap - load) / cap * 100.0 if cap > 0 else np.nan

    system_cap = cap_online.sum()
    system_load = yr[load_cols].sum(axis=1)
    headroom_pct['system_headroom_pct'] = (system_cap - system_load) / system_cap * 100.0

    base = datetime(2016, 1, 1, 0, 0)
    headroom_pct['datetime'] = [base + timedelta(hours=int(h) - 1) for h in yr['hour']]

    headroom_pct.to_csv(os.path.join(OUT_DIR, 'reserve_headroom_proxy_8784h.csv'), index=False)

    print("\n=== System-wide reserve headroom across the year ===")
    print(f"  min: {headroom_pct['system_headroom_pct'].min():.2f}%  "
          f"mean: {headroom_pct['system_headroom_pct'].mean():.2f}%  "
          f"max: {headroom_pct['system_headroom_pct'].max():.2f}%")
    tightest_idx = headroom_pct['system_headroom_pct'].idxmin()
    tightest = headroom_pct.loc[tightest_idx]
    print(f"  Tightest hour: {tightest['datetime']} "
          f"(hour {int(tightest['hour'])}) -- {tightest['system_headroom_pct']:.2f}% headroom")

    print("\n=== Per-area tightest hour of the year ===")
    summary_rows = []
    for a in range(1, 9):
        col = f'area_{a}_headroom_pct'
        idx = headroom_pct[col].idxmin()
        row = headroom_pct.loc[idx]
        summary_rows.append({
            'area': a,
            'online_capacity_mw': round(cap_online.loc[a], 1),
            'offline_capacity_mw': round(cap_offline.loc[a], 1),
            'min_headroom_pct': round(row[col], 2),
            'mean_headroom_pct': round(headroom_pct[col].mean(), 2),
            'tightest_hour': int(row['hour']),
            'tightest_datetime': str(row['datetime']),
        })
        print(f"  Area {a}: min {row[col]:.2f}% at {row['datetime']} "
              f"(capacity {cap_online.loc[a]:.0f} MW)")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(os.path.join(OUT_DIR, 'reserve_headroom_summary.csv'), index=False)

    return headroom_pct, summary_df


if __name__ == '__main__':
    main()
