"""
Baseline AC-Physics Characterization — Voltage Stability Curves (PV/QV)
=========================================================================
Section 1, item 1 of the SCFL validation test suite.

METHOD (deliberately simplified — read this before interpreting results):

This uses repeated single-shot AC power flow solves (Newton's method via
pypower), NOT continuation power flow (CPF). That means:
  - We trace the upper (stable) branch of the PV/QV curve only, up to
    the last load level that still converges.
  - The "nose point" reported is APPROXIMATE: the true nose sits
    somewhere between the last converged step and the first
    non-converged step, at a resolution set by the step size below.
  - We do NOT get the lower (unstable) branch — that requires CPF or
    a continuation parameter, which is out of scope for this baseline
    pass.

PV curve per area:
  Scale that area's total PD and QD together (constant power factor)
  by a multiplier lambda, stepping from 1.00 (nominal) upward in 0.05
  increments. All other areas held at nominal load. Generation
  dispatch is held FIXED except the slack bus, which absorbs whatever
  the power flow solve requires -- this is a load-stress-only sweep,
  not a generation-redispatched or generation-limited margin. Voltage
  is tracked at the area's highest-seam-degree "boundary bus" (the
  single most cross-area-interconnected bus in that area).

QV curve per area boundary:
  At nominal system load, additional reactive load (QD only, P held
  fixed) is added AT THE REPRESENTATIVE BOUNDARY BUS ONLY, in steps of
  5% of that area's total nominal Q (so step size scales sensibly
  across areas of very different size). This is a reactive-load-
  increment proxy for a QV curve -- it is NOT the conventional
  fictitious-synchronous-condenser, voltage-driven QV curve from the
  power systems literature. It answers a related but distinct
  question: how much extra local reactive demand can this boundary
  point absorb before voltage collapses locally, using the same
  load-to-divergence methodology as the PV sweep for consistency.

Both curves characterize the EXISTING (already-built) ACTIVSg2000 base
case under these specific stress assumptions. They are nominal-regime
margin estimates, not predictions about the real grid (this dataset is
synthetic, per its own header).
"""

import os
import sys
import copy
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from activsg2000_loader import load_case
from activsg2000_powerflow import case_to_ppc
from pypower.api import runpf, ppoption

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')
OPT = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)

BUS_COLS = ['BUS_I', 'BUS_TYPE', 'PD', 'QD', 'GS', 'BS', 'BUS_AREA', 'VM', 'VA',
            'BASE_KV', 'ZONE', 'VMAX', 'VMIN', 'LAM_P', 'LAM_Q', 'MU_VMAX', 'MU_VMIN']


def find_boundary_buses(cf):
    """Returns dict: area -> DataFrame of (bus_id, seam_degree) sorted desc."""
    branch = cf.branch[cf.branch['BR_STATUS'] == 1].copy()
    area_map = dict(zip(cf.bus['BUS_I'].astype(float), cf.bus['BUS_AREA'].astype(int)))
    branch['AF'] = branch['F_BUS'].map(area_map)
    branch['AT'] = branch['T_BUS'].map(area_map)
    seam = branch[branch['AF'] != branch['AT']]

    deg = {}
    for _, row in seam.iterrows():
        deg[(row['F_BUS'], row['AF'])] = deg.get((row['F_BUS'], row['AF']), 0) + 1
        deg[(row['T_BUS'], row['AT'])] = deg.get((row['T_BUS'], row['AT']), 0) + 1

    by_area = {a: [] for a in range(1, 9)}
    for (bus, area), d in deg.items():
        by_area[area].append((bus, d))
    for a in by_area:
        by_area[a] = sorted(by_area[a], key=lambda x: -x[1])
    return by_area


def get_vm(result_bus_df, bus_id):
    row = result_bus_df[result_bus_df['BUS_I'] == bus_id]
    return float(row['VM'].iloc[0]) if len(row) else np.nan


def pv_curve(cf, area, rep_bus, lam_max=3.0, lam_step=0.05):
    area_map = dict(zip(cf.bus['BUS_I'].astype(float), cf.bus['BUS_AREA'].astype(int)))
    base_ppc = case_to_ppc(cf)
    bus0 = base_ppc['bus'].copy()
    area_col = BUS_COLS.index('BUS_AREA')
    pd_col, qd_col = BUS_COLS.index('PD'), BUS_COLS.index('QD')
    area_rows = bus0[:, area_col].astype(int) == area

    records = []
    lam = 1.00
    while lam <= lam_max + 1e-9:
        ppc = copy.deepcopy(base_ppc)
        ppc['bus'][area_rows, pd_col] *= lam
        ppc['bus'][area_rows, qd_col] *= lam
        result, success = runpf(ppc, OPT)
        if not success:
            records.append({'area': area, 'lambda': round(lam, 3), 'converged': False, 'vm_rep_bus': np.nan})
            break
        rbus = pd.DataFrame(result['bus'], columns=BUS_COLS)
        vm = get_vm(rbus, rep_bus)
        records.append({'area': area, 'lambda': round(lam, 3), 'converged': True, 'vm_rep_bus': vm})
        lam += lam_step
    return records


def qv_curve(cf, area, rep_bus, area_total_q, step_frac=0.05, max_steps=60):
    base_ppc = case_to_ppc(cf)
    bus0 = base_ppc['bus']
    bus_col = BUS_COLS.index('BUS_I')
    qd_col = BUS_COLS.index('QD')
    rep_row = np.where(bus0[:, bus_col] == rep_bus)[0][0]
    q_step = step_frac * area_total_q

    records = []
    for k in range(max_steps + 1):
        delta_q = k * q_step
        ppc = copy.deepcopy(base_ppc)
        ppc['bus'][rep_row, qd_col] += delta_q
        result, success = runpf(ppc, OPT)
        if not success:
            records.append({'area': area, 'delta_q_mvar': round(delta_q, 2), 'converged': False, 'vm_rep_bus': np.nan})
            break
        rbus = pd.DataFrame(result['bus'], columns=BUS_COLS)
        vm = get_vm(rbus, rep_bus)
        records.append({'area': area, 'delta_q_mvar': round(delta_q, 2), 'converged': True, 'vm_rep_bus': vm})
    return records


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cf = load_case()
    boundary = find_boundary_buses(cf)

    area_q = cf.bus.copy()
    area_map = dict(zip(cf.bus['BUS_I'].astype(float), cf.bus['BUS_AREA'].astype(int)))
    area_q['AREA'] = area_q['BUS_I'].map(area_map)
    q_by_area = area_q.groupby('AREA')['QD'].sum()

    rep_bus_by_area = {}
    print("Representative boundary bus per area (highest seam-degree):")
    for area in range(1, 9):
        if not boundary[area]:
            print(f"  Area {area}: NO boundary buses found (isolated?) -- skipping")
            continue
        bus_id, degree = boundary[area][0]
        rep_bus_by_area[area] = bus_id
        print(f"  Area {area}: bus {int(bus_id)} (seam degree {degree}, "
              f"{len(boundary[area])} total boundary buses)")

    all_pv, all_qv = [], []
    for area, rep_bus in rep_bus_by_area.items():
        print(f"\n--- PV sweep, area {area}, rep bus {int(rep_bus)} ---")
        pv_recs = pv_curve(cf, area, rep_bus)
        all_pv.extend(pv_recs)
        last = pv_recs[-1]
        n_conv = sum(1 for r in pv_recs if r['converged'])
        max_lam_ok = max((r['lambda'] for r in pv_recs if r['converged']), default=None)
        print(f"  Converged steps: {n_conv}/{len(pv_recs)} | "
              f"approx loadability margin: lambda <= {max_lam_ok}")

        print(f"--- QV sweep, area {area}, rep bus {int(rep_bus)} ---")
        qv_recs = qv_curve(cf, area, rep_bus, area_total_q=float(q_by_area.get(area, 100.0)))
        all_qv.extend(qv_recs)
        n_conv_q = sum(1 for r in qv_recs if r['converged'])
        max_dq_ok = max((r['delta_q_mvar'] for r in qv_recs if r['converged']), default=None)
        print(f"  Converged steps: {n_conv_q}/{len(qv_recs)} | "
              f"approx reactive margin at boundary bus: +{max_dq_ok} MVAr")

    pv_df = pd.DataFrame(all_pv)
    qv_df = pd.DataFrame(all_qv)
    pv_df.to_csv(os.path.join(OUT_DIR, 'pv_curves_by_area.csv'), index=False)
    qv_df.to_csv(os.path.join(OUT_DIR, 'qv_curves_by_area.csv'), index=False)

    # Summary table: approx loadability margin & reactive margin per area
    summary_rows = []
    for area, rep_bus in rep_bus_by_area.items():
        pv_a = pv_df[pv_df['area'] == area]
        qv_a = qv_df[qv_df['area'] == area]
        margin_lam = pv_a.loc[pv_a['converged'], 'lambda'].max() if pv_a['converged'].any() else np.nan
        margin_dq = qv_a.loc[qv_a['converged'], 'delta_q_mvar'].max() if qv_a['converged'].any() else np.nan
        v_nominal = pv_a.loc[pv_a['lambda'] == 1.0, 'vm_rep_bus']
        summary_rows.append({
            'area': area, 'rep_bus': int(rep_bus),
            'v_nominal_pu': float(v_nominal.iloc[0]) if len(v_nominal) else np.nan,
            'approx_loadability_margin_lambda': margin_lam,
            'approx_reactive_margin_mvar': margin_dq,
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(os.path.join(OUT_DIR, 'voltage_stability_summary.csv'), index=False)
    print("\n=== Summary (approximate margins, single-slack-absorbs-load assumption) ===")
    print(summary_df.to_string(index=False))

    return pv_df, qv_df, summary_df


if __name__ == '__main__':
    main()
