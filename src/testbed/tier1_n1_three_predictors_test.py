"""
TIER1_N1_THREE_PREDICTORS_TEST_v1 — Stiffness, Generator/Inertia Mix,
and Topology Geometry as predictors of the N-1 Delta1 inversion
=========================================================================
Follows tier1_n1_redundancy_test.py, which found redundancy (tie-count)
explains <15% of the year2024 effect on N-1 Delta1. Tests the three
remaining candidate explanations against the SAME 1,235 seam-branch
trips (experiments/tier1_n1_redundancy_trips.csv), joined by branch_idx.

  1. STIFFNESS: |Z_ii| (Thevenin/driving-point impedance magnitude at
     each branch's two endpoint buses, from the network Ybus -- the
     textbook short-circuit-strength measure: S_sc ~ V^2/|Z_ii|, lower
     |Z_ii| = stiffer/stronger bus). NOT a true short-circuit study
     (would need generator sub-transient reactances from the .dyr
     files, not used here) -- this is the NETWORK-only stiffness proxy,
     stated explicitly as a limitation.
  2. GENERATOR / INERTIA MIX: parses each case's .dyr file to classify
     every generator bus as synchronous (GENROU/GENSAL), grid-following
     inverter (REGCA1), or grid-forming inverter (REGFMA1). Joined to
     cf.gen (online status + dispatched MW) to get AREA-level online
     inverter share of capacity. Branch covariate = average inverter
     share of the branch's two endpoint areas. Also reports system-wide
     online synchronous inertia (sum of H x MBASE, GENROU/GENSAL only)
     as a case-level premise check.
  3. TOPOLOGY GEOMETRY: (a) edge betweenness centrality of each seam
     branch in the full 2000-bus graph (global structural importance,
     NOT the same as local area-pair tie count); (b) alt_area_degree =
     how many OTHER areas each of the branch's two endpoint areas
     connect to, in the 8-node area-supergraph (local meshing /
     rerouting potential through the broader area mesh, distinct from
     direct-tie redundancy).

Final test: does adding all three (plus redundancy) to the regression
attenuate the year2024 coefficient more than redundancy alone did?
"""

import os
import re
import sys
import time
import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr, mannwhitneyu
import statsmodels.api as sm

if not hasattr(np, 'in1d'):
    np.in1d = np.isin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tier1_multiscenario_structural import CASES
from tier1_multiscenario_followups import load_solve_full, YEAR_2016, YEAR_2024
from pypower.api import makeYbus, ext2int
import scipy.sparse.linalg as spla

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
OUT_DIR = os.path.join(REPO_ROOT, 'experiments')
TRIPS_CSV = os.path.join(OUT_DIR, 'tier1_n1_redundancy_trips.csv')

DYR_PATHS = {
    'baseline_ACTIVSg2000':     None,  # baseline has no matching dyr file; excluded from generator-mix test
    'case1_2016summerpeak':     os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case1_2016summerpeak', 'dynamic_models_case1.dyr'),
    'case2_2016lowload':        os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case2_2016lowload', 'dynamic_models_case2.dyr'),
    'case3_2024summerpeak':     os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case3_2024summerpeak', 'dynamic_models_case3.dyr'),
    'case4_2024lowload':        os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case4_2024lowload', 'dynamic_models_case4.dyr'),
    'case5_2024highrenewables': os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case5_2024highrenewables', 'dynamic_models_case5.dyr'),
    'case6_2024lowloadwithgfm': os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case6_2024lowloadwithgfm', 'dynamic_models_case6.dyr'),
}

SYNC_MODELS = {'GENROU', 'GENSAL'}
GFL_MODELS = {'REGCA1'}
GFM_MODELS = {'REGFMA1'}


def parse_dyr(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('cp1252')
    machine_type, h_by_bus = {}, {}
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)\s+'([A-Z0-9_]+)'\s+(\S+)\s+(.*)", line)
        if not m:
            continue
        bus_id, model, genid, rest = m.groups()
        bus_id = int(bus_id)
        if model in SYNC_MODELS:
            machine_type[bus_id] = 'sync'
            params = rest.replace('/', '').split()
            try:
                h_by_bus[bus_id] = float(params[4])
            except Exception:
                pass
        elif model in GFL_MODELS:
            machine_type.setdefault(bus_id, 'gfl')
        elif model in GFM_MODELS:
            machine_type[bus_id] = 'gfm'
    return machine_type, h_by_bus


def case_stiffness(cf, ppc, needed_bus_ids):
    ppc_int = ext2int(dict(ppc))
    Ybus, _, _ = makeYbus(ppc_int['baseMVA'], ppc_int['bus'], ppc_int['branch'])
    lu = spla.splu(Ybus.tocsc())
    e2i = ppc_int['order']['bus']['e2i']
    n = Ybus.shape[0]
    z_by_bus = {}
    for b in needed_bus_ids:
        i = int(e2i[b])
        e = np.zeros(n, dtype=complex)
        e[i] = 1.0
        x = lu.solve(e)
        z_by_bus[b] = abs(x[i])
    return z_by_bus


def case_generator_mix(cf, dyr_path):
    """Returns (area_inverter_share dict, system_online_inertia_MWs,
    coverage_stats dict)."""
    machine_type, h_by_bus = parse_dyr(dyr_path)
    bus_area = dict(zip(cf.bus['BUS_I'].astype(int), cf.bus['BUS_AREA'].astype(int)))
    gen = cf.gen[cf.gen['GEN_STATUS'] == 1].copy()
    gen['bus_id'] = gen['GEN_BUS'].astype(int)
    gen['mtype'] = gen['bus_id'].map(machine_type).fillna('unknown')
    gen['area'] = gen['bus_id'].map(bus_area)

    n_unknown = (gen['mtype'] == 'unknown').sum()
    pg_by_area_type = gen.groupby(['area', 'mtype'])['PG'].sum().unstack(fill_value=0.0)
    for col in ['sync', 'gfl', 'gfm']:
        if col not in pg_by_area_type.columns:
            pg_by_area_type[col] = 0.0
    pg_by_area_type['inverter'] = pg_by_area_type['gfl'] + pg_by_area_type['gfm']
    pg_by_area_type['total'] = pg_by_area_type[['sync', 'gfl', 'gfm', 'unknown']].sum(axis=1) \
        if 'unknown' in pg_by_area_type.columns else pg_by_area_type[['sync', 'gfl', 'gfm']].sum(axis=1)
    pg_by_area_type['inverter_share'] = pg_by_area_type['inverter'] / pg_by_area_type['total'].replace(0, np.nan)
    area_inverter_share = pg_by_area_type['inverter_share'].fillna(0.0).to_dict()

    sync_rows = gen[gen['mtype'] == 'sync'].copy()
    sync_rows['H'] = sync_rows['bus_id'].map(h_by_bus)
    sync_rows = sync_rows.dropna(subset=['H'])
    system_inertia_mws = float((sync_rows['H'] * sync_rows['MBASE']).sum())

    return area_inverter_share, system_inertia_mws, {
        'n_gen_online': len(gen), 'n_unknown': int(n_unknown),
        'total_pg': float(gen['PG'].sum()), 'inverter_pg': float(pg_by_area_type['inverter'].sum()),
    }


def case_topology(cf):
    branch = cf.branch[cf.branch['BR_STATUS'] == 1]
    G = nx.Graph()
    G.add_nodes_from(cf.bus['BUS_I'].astype(int))
    edge_key_to_idx = {}
    for idx, r in branch.iterrows():
        f, t = int(r['F_BUS']), int(r['T_BUS'])
        G.add_edge(f, t)
        edge_key_to_idx.setdefault(tuple(sorted((f, t))), []).append(idx)
    ebc = nx.edge_betweenness_centrality(G, normalized=True)
    # ebc keyed by frozenset-like edge tuple from networkx (order as added/canonical)
    ebc_by_pair = {tuple(sorted(e)): v for e, v in ebc.items()}

    area_map = dict(zip(cf.bus['BUS_I'].astype(int), cf.bus['BUS_AREA'].astype(int)))
    G_area = nx.Graph()
    for f, t in G.edges():
        af, at = area_map[f], area_map[t]
        if af != at:
            G_area.add_edge(af, at)
    area_degree = dict(G_area.degree())
    return ebc_by_pair, area_degree


def run_analysis(merged):
    m = merged.copy()
    m['year_group'] = m['year_group'].astype(str)  # CSV round-trip can silently coerce '2016'/'2024' to int
    m = m[m['converged']].copy()
    m['year2024'] = (m['year_group'] == '2024').astype(int)

    print("\n" + "=" * 70 + "\nPREMISE CHECKS (2016 vs 2024, per-branch, pooled)\n" + "=" * 70)
    for col in ['stiffness_avg_Zii', 'betweenness', 'alt_area_degree', 'inverter_share_branch']:
        d16 = m[m['year_group'] == '2016'][col].dropna()
        d24 = m[m['year_group'] == '2024'][col].dropna()
        mw = mannwhitneyu(d24, d16, alternative='two-sided', method='asymptotic')
        print(f"  {col:25s} median2016={d16.median():.5f}  median2024={d24.median():.5f}  "
              f"MW_p={mw.pvalue:.3e}  n16={len(d16)} n24={len(d24)}")

    print("\n" + "=" * 70 + "\nUNIVARIATE CORRELATIONS with Delta1 (pooled, converged)\n" + "=" * 70)
    for col in ['redundancy', 'stiffness_avg_Zii', 'betweenness', 'alt_area_degree', 'inverter_share_branch']:
        sub = m.dropna(subset=[col, 'delta1'])
        rho, p = spearmanr(sub[col], sub['delta1'])
        print(f"  {col:25s} rho={rho:+.4f}  p={p:.3e}  n={len(sub)}")

    print("\n" + "=" * 70 + "\nREGRESSION PROGRESSION\n" + "=" * 70)
    base = m.dropna(subset=['delta1', 'redundancy', 'stiffness_avg_Zii', 'betweenness',
                             'alt_area_degree', 'inverter_share_branch']).copy()
    print(f"  n used in full model (complete cases): {len(base)}")

    def fit(label, predictors):
        X = sm.add_constant(base[predictors])
        mod = sm.OLS(base['delta1'], X).fit()
        print(f"  {label}: R2={mod.rsquared:.4f}  year2024 coef={mod.params['year2024']:+.5f} "
              f"(p={mod.pvalues['year2024']:.3e})")
        for p in predictors:
            if p != 'year2024':
                print(f"      {p:25s} coef={mod.params[p]:+.6f}  p={mod.pvalues[p]:.3e}")
        return mod

    mA = fit('A: year only', ['year2024'])
    mB = fit('B: + redundancy', ['year2024', 'redundancy'])
    mC = fit('C: + stiffness', ['year2024', 'redundancy', 'stiffness_avg_Zii'])
    mD = fit('D: + inverter_share', ['year2024', 'redundancy', 'stiffness_avg_Zii', 'inverter_share_branch'])
    mE = fit('E: + topology', ['year2024', 'redundancy', 'stiffness_avg_Zii', 'inverter_share_branch',
                                'betweenness', 'alt_area_degree'])

    y0, yf = mA.params['year2024'], mE.params['year2024']
    print(f"\n  Total attenuation of year2024 coef, A->E: {100*(1 - yf/y0):.1f}%  "
          f"(R2: {mA.rsquared:.3f} -> {mE.rsquared:.3f})")
    print(f"  year2024 p-value: A={mA.pvalues['year2024']:.3e}  ->  E={mE.pvalues['year2024']:.3e}")
    return {'A': mA, 'B': mB, 'C': mC, 'D': mD, 'E': mE}


def main():
    trips = pd.read_csv(TRIPS_CSV)
    print(f"Loaded {len(trips)} trip records from {TRIPS_CSV}")

    rows_extra = []
    premise_rows = []
    for name, path in CASES.items():
        t0 = time.time()
        cf, ppc, result0 = load_solve_full(path)
        case_trips = trips[trips['case'] == name]
        needed_buses = sorted(set(case_trips['f_bus']) | set(case_trips['t_bus']))

        z_by_bus = case_stiffness(cf, ppc, needed_buses)
        ebc_by_pair, area_degree = case_topology(cf)

        dyr_path = DYR_PATHS[name]
        if dyr_path is not None:
            area_inv_share, sys_inertia, cov = case_generator_mix(cf, dyr_path)
        else:
            area_inv_share, sys_inertia, cov = {}, np.nan, {'n_gen_online': np.nan, 'n_unknown': np.nan,
                                                              'total_pg': np.nan, 'inverter_pg': np.nan}

        for _, r in case_trips.iterrows():
            f_bus, t_bus = int(r['f_bus']), int(r['t_bus'])
            area_f = cf.bus.loc[cf.bus['BUS_I'] == f_bus, 'BUS_AREA'].iloc[0]
            area_t = cf.bus.loc[cf.bus['BUS_I'] == t_bus, 'BUS_AREA'].iloc[0]
            stiffness_avg = 0.5 * (z_by_bus.get(f_bus, np.nan) + z_by_bus.get(t_bus, np.nan))
            betweenness = ebc_by_pair.get(tuple(sorted((f_bus, t_bus))), np.nan)
            alt_area_degree = (area_degree.get(area_f, 1) - 1) + (area_degree.get(area_t, 1) - 1)
            inv_share = np.nan
            if area_inv_share:
                s_f = area_inv_share.get(area_f, np.nan)
                s_t = area_inv_share.get(area_t, np.nan)
                inv_share = np.nanmean([s_f, s_t])

            rows_extra.append({
                'case': name, 'branch_idx': r['branch_idx'],
                'stiffness_avg_Zii': stiffness_avg,
                'betweenness': betweenness,
                'alt_area_degree': alt_area_degree,
                'inverter_share_branch': inv_share,
            })

        premise_rows.append({
            'case': name, 'year_group': 'unknown' if name == 'baseline_ACTIVSg2000' else ('2016' if name in YEAR_2016 else '2024'),
            'system_online_inertia_MWs': sys_inertia,
            'n_gen_online': cov['n_gen_online'], 'n_unknown_gentype': cov['n_unknown'],
            'total_online_pg_MW': cov['total_pg'], 'inverter_online_pg_MW': cov['inverter_pg'],
            'median_betweenness_seam': np.median([ebc_by_pair.get(tuple(sorted((int(r['f_bus']), int(r['t_bus']))))) for _, r in case_trips.iterrows()]),
            'median_alt_area_degree_seam': np.median([(area_degree.get(cf.bus.loc[cf.bus['BUS_I']==int(r['f_bus']),'BUS_AREA'].iloc[0],1)-1)+(area_degree.get(cf.bus.loc[cf.bus['BUS_I']==int(r['t_bus']),'BUS_AREA'].iloc[0],1)-1) for _, r in case_trips.iterrows()]),
        })
        print(f"  {name}: done [{time.time()-t0:.1f}s]")

    extra_df = pd.DataFrame(rows_extra)
    merged = trips.merge(extra_df, on=['case', 'branch_idx'], how='left')
    merged_path = os.path.join(OUT_DIR, 'tier1_n1_three_predictors_merged.csv')
    merged.to_csv(merged_path, index=False)
    print(f"\nWrote merged dataset: {merged_path}  (n={len(merged)})")

    premise_df = pd.DataFrame(premise_rows)
    premise_path = os.path.join(OUT_DIR, 'tier1_n1_three_predictors_premise.csv')
    premise_df.to_csv(premise_path, index=False)
    print(f"Wrote premise checks: {premise_path}")
    print("\n" + premise_df.to_string(index=False))

    models = run_analysis(merged)

    return merged, premise_df, models


if __name__ == '__main__':
    main()
