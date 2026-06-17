"""
TIER1_MULTISCENARIO_STRUCTURAL_v1 — Cross-Scenario Seam Structure Test
=========================================================================
EXPLICITLY SCOPED, READ BEFORE USING. This is NOT the same operator
family as tier1_candidate_operators.py (Delta1/Delta2/precursor/tau_half/
R). Those require an annual hourly time series (vm over 8784 hours) with
independently-defined load-peak events. The seven operating points
analyzed here -- the original ACTIVSg2000 baseline plus the six Series24
scenarios (data/series24_cases/) -- are each a SINGLE static power-flow
solution, not a time series. There is no time axis to take Delta1/Delta2/
precursor/tau_half/R over, and pretending otherwise would be exactly the
kind of unearned operator transplant this repo's own discipline (see
notes/, ledger/evidence_ledger.md) exists to prevent.

What IS well-posed on a single snapshot: stratifying bus PAIRS (not time
points) by whether they cross an area boundary (a "seam" pair) or not,
and asking whether seam-crossing pairs show systematically different
|Delta Vm| than same-area connected pairs. This is the single-snapshot
analog of this repo's open "Dimensional Audit ground-truth test" (see
README, next experiment #1): same area partition, same non-circularity
rule (seam set defined from topology alone, BEFORE looking at any
voltage data) -- but bus-PAIRS are the unit of observation here, not
hours, since each scenario gives many pairs but only one timepoint.

Per case:
  1. Load case (.m), run AC power flow (pypower), confirm convergence.
     FAIL LOUDLY (raise) if a case does not converge -- do not silently
     skip or impute a result for a non-converged case.
  2. Build EACH case's OWN seam-pair set from its OWN branch data. Areas
     are consistent across cases (verified: bus 1001 = area 1, 8 areas,
     in both the baseline and every Series24 case), but topology is NOT
     (branch counts range 3220-3913 across the six scenarios vs 3206 in
     the baseline), so the baseline's seam set is not reused unchanged.
  3. Two null comparisons, because they test different claims:
     (a) "connected non-seam" null: random SAME-area in-service branches
         (real physical connections, just not crossing an area boundary)
         -- the relevant test of "does crossing an area boundary matter,
         given that you're on a real line either way".
     (b) "generic pairs" null: random pairs of any two distinct in-
         service buses, not required to be a real branch at all -- a
         weaker, supplementary baseline.
  Both are bootstrapped (n_boot draws, same sample size as the true seam
  set, WITH replacement across draws / WITHOUT replacement within a
  draw) to get a permutation p-value, not just a point comparison.

Output: experiments/tier1_multiscenario_structural.csv (one row per
case) and experiments/tier1_multiscenario_structural_summary.md.
"""

import os
import sys
import numpy as np
import pandas as pd

if not hasattr(np, 'in1d'):  # pypower 5.1.19 / numpy>=2.0 compat shim
    np.in1d = np.isin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from matpowercaseframes import CaseFrames
from pypower.api import runpf, ppoption

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
OUT_DIR = os.path.join(REPO_ROOT, 'experiments')

CASES = {
    'baseline_ACTIVSg2000':       os.path.join(REPO_ROOT, 'data', 'ACTIVSg2000.m'),
    'case1_2016summerpeak':       os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case1_2016summerpeak', 'Texas2k_series24_case1_2016summerPeak.m'),
    'case2_2016lowload':          os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case2_2016lowload', 'Texas2k_series24_case2_2016lowload.m'),
    'case3_2024summerpeak':       os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case3_2024summerpeak', 'Texas2k_series24_case3_2024summerpeak.m'),
    'case4_2024lowload':          os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case4_2024lowload', 'Texas2k_series24_case4_2024lowload.m'),
    'case5_2024highrenewables':   os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case5_2024highrenewables', 'Texas2k_series24_case5_2024highrenewables.m'),
    'case6_2024lowloadwithgfm':   os.path.join(REPO_ROOT, 'data', 'series24_cases', 'case6_2024lowloadwithgfm', 'Texas2k_series24_case6_2024lowloadwithgfm.m'),
}

N_BOOT = 5000
RNG_SEED = 42


def _read_sanitized(path):
    """Some Series24 .m headers contain cp1252 smart-quote bytes (citation
    text) that break CaseFrames' UTF-8 read. Sanitize to a temp UTF-8 copy;
    only header comment bytes are touched, no numeric data is altered."""
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('cp1252')
    root, ext = os.path.splitext(path)
    tmp_path = root + '_utf8sanitized' + ext  # must keep '.m' ext -- CaseFrames dispatches on extension
    with open(tmp_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return tmp_path


def load_and_solve(path):
    safe_path = _read_sanitized(path)
    try:
        cf = CaseFrames(safe_path)
    finally:
        os.remove(safe_path)
    ppc = {
        'version': '2',
        'baseMVA': float(cf.baseMVA),
        'bus': cf.bus.to_numpy(dtype=float),
        'gen': cf.gen.to_numpy(dtype=float),
        'branch': cf.branch.to_numpy(dtype=float),
        'gencost': cf.gencost.to_numpy(dtype=float),
    }
    opt = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)
    result, success = runpf(ppc, opt)
    if not success:
        raise RuntimeError(f"Power flow did NOT converge for {path}")
    bus_ids = result['bus'][:, 0].astype(int)
    vm = result['bus'][:, 7]
    vm_by_bus = dict(zip(bus_ids, vm))
    return cf, vm_by_bus


def seam_and_nonseam_pairs(cf):
    """Returns (seam_pairs, nonseam_connected_pairs) as lists of (i, j)
    bus-id tuples, deduplicated, built from this case's OWN branch data."""
    branch = cf.branch[cf.branch['BR_STATUS'] == 1].copy()
    area_map = dict(zip(cf.bus['BUS_I'].astype(int), cf.bus['BUS_AREA'].astype(int)))
    branch['AF'] = branch['F_BUS'].astype(int).map(area_map)
    branch['AT'] = branch['T_BUS'].astype(int).map(area_map)

    pair_key = branch.apply(lambda r: tuple(sorted((int(r['F_BUS']), int(r['T_BUS'])))), axis=1)
    branch['pair'] = pair_key
    is_seam = branch['AF'] != branch['AT']

    seam_pairs = sorted(set(branch.loc[is_seam, 'pair']))
    nonseam_pairs = sorted(set(branch.loc[~is_seam, 'pair']))
    return seam_pairs, nonseam_pairs


def abs_dv(pairs, vm_by_bus):
    out = []
    for (i, j) in pairs:
        if i in vm_by_bus and j in vm_by_bus:
            out.append(abs(vm_by_bus[i] - vm_by_bus[j]))
    return np.array(out)


def bootstrap_null(candidate_pairs, n_seam, vm_by_bus, rng, n_boot=N_BOOT):
    candidate_pairs = list(candidate_pairs)
    n_avail = len(candidate_pairs)
    if n_avail < n_seam:
        n_seam = n_avail  # degrade gracefully, flagged in output via n_avail
    means = np.empty(n_boot)
    idx_pool = np.arange(n_avail)
    for b in range(n_boot):
        draw_idx = rng.choice(idx_pool, size=n_seam, replace=False)
        draw_pairs = [candidate_pairs[k] for k in draw_idx]
        means[b] = abs_dv(draw_pairs, vm_by_bus).mean()
    return means, n_avail


def all_bus_pairs_sample(bus_ids, n_seam, rng, n_draw_pool=20000):
    """Generic random-pair null: sample random distinct bus-id pairs not
    constrained to be real branches at all."""
    bus_ids = np.array(sorted(bus_ids))
    n = len(bus_ids)
    pool = set()
    attempts = 0
    while len(pool) < n_draw_pool and attempts < n_draw_pool * 5:
        i, j = rng.choice(n, size=2, replace=False)
        a, b = bus_ids[i], bus_ids[j]
        pool.add((min(a, b), max(a, b)))
        attempts += 1
    return list(pool)


def main():
    rng = np.random.default_rng(RNG_SEED)
    rows = []

    for name, path in CASES.items():
        print(f"\n=== {name} ===")
        cf, vm_by_bus = load_and_solve(path)
        print(f"  converged, n_bus={len(vm_by_bus)}")

        seam_pairs, nonseam_pairs = seam_and_nonseam_pairs(cf)
        n_seam = len(seam_pairs)
        seam_dv = abs_dv(seam_pairs, vm_by_bus)
        true_mean_seam = seam_dv.mean()

        # Null (a): connected non-seam branches
        null_a, n_avail_a = bootstrap_null(nonseam_pairs, n_seam, vm_by_bus, rng)
        pctile_a = (null_a < true_mean_seam).mean() * 100

        # Null (b): generic random bus pairs (not required to be real branches)
        generic_pool = all_bus_pairs_sample(cf.bus['BUS_I'].astype(int).to_numpy(), n_seam, rng)
        null_b, n_avail_b = bootstrap_null(generic_pool, n_seam, vm_by_bus, rng)
        pctile_b = (null_b < true_mean_seam).mean() * 100

        print(f"  n_seam_pairs={n_seam}  n_nonseam_connected_pairs={n_avail_a}")
        print(f"  true mean |dVm| (seam pairs)              = {true_mean_seam:.5f}")
        print(f"  null (connected, non-seam) mean +/- std    = {null_a.mean():.5f} +/- {null_a.std():.5f}  "
              f"(seam value at {pctile_a:.1f} pctile of null)")
        print(f"  null (generic random pairs) mean +/- std   = {null_b.mean():.5f} +/- {null_b.std():.5f}  "
              f"(seam value at {pctile_b:.1f} pctile of null)")

        rows.append({
            'case': name,
            'n_bus': len(vm_by_bus),
            'n_seam_pairs': n_seam,
            'n_nonseam_connected_pairs': n_avail_a,
            'mean_abs_dVm_seam': true_mean_seam,
            'null_connected_mean': null_a.mean(),
            'null_connected_std': null_a.std(),
            'seam_pctile_vs_connected_null': pctile_a,
            'null_generic_mean': null_b.mean(),
            'null_generic_std': null_b.std(),
            'seam_pctile_vs_generic_null': pctile_b,
        })

    out = pd.DataFrame(rows)
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, 'tier1_multiscenario_structural.csv')
    out.to_csv(out_path, index=False)
    print(f"\nWrote {out_path}")
    return out


if __name__ == '__main__':
    main()
