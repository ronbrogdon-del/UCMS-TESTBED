"""
Annual Bus Voltage Time Series Builder
========================================
Generates V_i(t) for all 2000 buses, t = 1..8784 hours, by running AC power
flow once per hour with that hour's real area load applied.

This is the prerequisite data for TIER1_CANDIDATE_SPEC_v1 (seam-coherence,
coupling stress, precursor windows, Δ1/Δ2/τ½/R) -- none of those operators
can be computed without an actual time series to operate on.

METHOD (state explicitly, this is a real modeling choice):

Load side: for each area a and hour t, lambda_load(a,t) =
  year_profile_area_a(t) / basecase_area_a_total. Every bus in area a has
  its PD and QD scaled by lambda_load(a,t) for that hour. This reproduces
  the exact real annual area totals at the bus level by uniform
  within-area scaling (we don't have bus-level hourly data, only area-level,
  so this is the standard zonal-to-nodal disaggregation assumption).

Generation side: unlike Section 1's PV/QV sweep (which deliberately used
single-slack absorption to stress-test loadability), this run uses
SYSTEM-WIDE PROPORTIONAL GENERATION SCALING: every online, non-reference
generator's Pg is scaled by lambda_gen(t) = total_system_load(t) /
total_system_load_basecase. This approximates uniform economic
redispatch as system load varies through the year and avoids forcing the
single slack bus to absorb the full demand swing (which, holding
generation fixed at near-peak base-case levels while real load drops to
~34% of that at its annual minimum, would require deeply unrealistic
negative slack generation). The slack bus absorbs only losses and any
residual mismatch from this approximation, not the bulk of the demand
variation. This is a DIFFERENT assumption from Section 1's PV/QV sweep,
used here because the goal is a representative annual operating
trajectory, not a stress-margin test -- stated explicitly so the two
are never conflated.

Output: experiments/annual_voltage_series.npz containing:
  - vm: (8784, 2000) float32 array of voltage magnitudes (p.u.), NaN for
    any hour that failed to converge
  - bus_ids: (2000,) array, column order reference for vm
  - hours: (8784,) array, hour index 1..8784
  - converged: (8784,) bool array
"""

import os
import sys
import time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from activsg2000_loader import load_case
from activsg2000_powerflow import case_to_ppc
from pypower.api import runpf, ppoption

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')
OPT = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)

BUS_PD_COL, BUS_QD_COL, BUS_AREA_COL, BUS_VM_COL = 2, 3, 6, 7
GEN_BUS_COL, GEN_PG_COL, GEN_STATUS_COL = 0, 1, 7


def main(start_idx=0, end_idx=None):
    t_start = time.time()
    cf = load_case()
    base_ppc = case_to_ppc(cf)
    bus0 = base_ppc['bus']
    gen0 = base_ppc['gen']
    bus_ids = bus0[:, 0].copy()
    n_buses = bus0.shape[0]

    area_of_bus = bus0[:, BUS_AREA_COL].astype(int)
    area_masks = {a: (area_of_bus == a) for a in range(1, 9)}

    ref_bus_id = bus0[bus0[:, 1] == 3, 0]
    gen_is_ref = np.isin(gen0[:, GEN_BUS_COL], ref_bus_id)
    gen_online = gen0[:, GEN_STATUS_COL] == 1
    gen_scale_mask = gen_online & ~gen_is_ref  # online, non-reference gens

    basecase_area_total = {a: bus0[area_masks[a], BUS_PD_COL].sum() for a in range(1, 9)}
    basecase_system_total = bus0[:, BUS_PD_COL].sum()

    yr = pd.read_csv(os.path.join(DATA_DIR, 'activsg2000_area_load_8784h.csv'))
    n_hours = len(yr)
    load_cols = [f'area_{a}' for a in range(1, 9)]
    yr['system_total'] = yr[load_cols].sum(axis=1)

    out_path = os.path.join(OUT_DIR, 'annual_voltage_series.npz')
    if os.path.exists(out_path):
        existing = np.load(out_path)
        vm = existing['vm'].copy()
        converged = existing['converged'].copy()
        print(f"Loaded existing partial results: {converged.sum()}/{n_hours} already converged.")
    else:
        vm = np.full((n_hours, n_buses), np.nan, dtype=np.float32)
        converged = np.zeros(n_hours, dtype=bool)

    if end_idx is None:
        end_idx = n_hours

    print(f"Running hours [{start_idx}, {end_idx}) of {n_hours}...")
    for idx in range(start_idx, end_idx):
        hour = int(yr.loc[idx, 'hour'])
        lam_gen = yr.loc[idx, 'system_total'] / basecase_system_total

        bus_t = bus0.copy()
        for a in range(1, 9):
            lam_load = yr.loc[idx, f'area_{a}'] / basecase_area_total[a]
            m = area_masks[a]
            bus_t[m, BUS_PD_COL] *= lam_load
            bus_t[m, BUS_QD_COL] *= lam_load

        gen_t = gen0.copy()
        gen_t[gen_scale_mask, GEN_PG_COL] *= lam_gen

        ppc_t = {**base_ppc, 'bus': bus_t, 'gen': gen_t}
        result, success = runpf(ppc_t, OPT)

        if success:
            vm[idx, :] = result['bus'][:, BUS_VM_COL]
            converged[idx] = True
        else:
            converged[idx] = False

        if (idx + 1 - start_idx) % 250 == 0 or idx == end_idx - 1:
            elapsed = time.time() - t_start
            print(f"  {idx+1}/{end_idx} done ({elapsed:.1f}s elapsed)")

    os.makedirs(OUT_DIR, exist_ok=True)
    np.savez_compressed(out_path, vm=vm, bus_ids=bus_ids, hours=yr['hour'].to_numpy(), converged=converged)

    n_done = int(converged.sum())
    n_fail = int((~converged[:end_idx]).sum()) if end_idx == n_hours else None
    print(f"\nChunk done in {time.time()-t_start:.1f}s. Total converged so far: {n_done}/{n_hours}.")
    if end_idx == n_hours:
        n_fail_total = int((~converged).sum())
        print(f"FINAL: {n_done}/{n_hours} converged, {n_fail_total} failed.")
        if n_fail_total:
            fail_hours = yr.loc[~converged, 'hour'].tolist()
            print(f"Failed hours: {fail_hours[:30]}{' ...' if n_fail_total > 30 else ''}")

    return vm, bus_ids, converged


if __name__ == '__main__':
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    e = int(sys.argv[2]) if len(sys.argv) > 2 else None
    main(s, e)
