"""
TIER1_CANDIDATE_SPEC_v1 — Seam-Coherence, Coupling Stress, Precursor
Windows, and the Δ1/Δ2/τ½/R Operator Families
=========================================================================
EXPLICITLY LABELED CANDIDATE, NOT CANON. These mathematical forms came
from a third-party draft (not Ronald's published Zenodo canon, which
remains un-located). Treat every result in this file as provisional
until reconciled against the actual canon definitions. See chat history
for the critique applied before implementing: operator A is a z-scored
deviation index, not coherence in the rigorous (correlation/cross-
spectral) sense; operator C requires an independently-defined event set
or it becomes circular; τ½ needs a censoring rule for non-recovery.
Those fixes are applied below.

Inputs:
  - experiments/annual_voltage_series.npz (V_i(t), 8784 hours x 2000 buses)
  - The 8-area partition (BUS_AREA) and the seam branch set

Method notes specific to this implementation (deviations/choices made
explicit, since the spec left them open):
  - Seam set S: DEDUPLICATED to 127 unique (i,j) bus-pairs (matches the
    established ground-truth seam count). Where multiple parallel
    circuits exist between the same pair, their series-admittance
    magnitudes are SUMMED into one K_ij -- the voltage-based terms
    (A, B) depend only on the bus pair, not circuit count, so using the
    raw 131 branch records would silently double-weight the 4 pairs that
    have a parallel duplicate.
  - Event definition for the precursor operator (C): independently
    defined as the top 1% system-load hours of the year (88 hours),
    BEFORE looking at any operator output -- same non-circularity rule
    already stated in this repo's README for the (not-yet-run) stress-
    hour test. This is a choice, not a canon-derived definition; stated
    explicitly so it isn't mistaken for one.
  - Precursor lookback window τ = 24 hours (one day). Arbitrary, stated
    explicitly, not tuned.
  - τ½ censoring rule: if X never recovers to half its event-peak value
    within a 168-hour (1 week) window, τ½ is recorded as NaN ("not
    recovered within window"), not silently dropped.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from activsg2000_loader import load_case

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')


def build_seam_pairs(cf):
    """Deduplicated (i,j) seam pairs with aggregated coupling weight K_ij = sum|y|."""
    branch = cf.branch[cf.branch['BR_STATUS'] == 1].copy()
    area_map = dict(zip(cf.bus['BUS_I'].astype(float), cf.bus['BUS_AREA'].astype(int)))
    branch['AF'] = branch['F_BUS'].map(area_map)
    branch['AT'] = branch['T_BUS'].map(area_map)
    seam = branch[branch['AF'] != branch['AT']].copy()

    Z = seam['BR_R'].to_numpy(dtype=float) + 1j * seam['BR_X'].to_numpy(dtype=float)
    Z[np.abs(Z) < 1e-9] = 1e-9
    seam['absY'] = np.abs(1.0 / Z)

    pair_key = seam.apply(lambda r: tuple(sorted((r['F_BUS'], r['T_BUS']))), axis=1)
    seam['pair'] = pair_key
    agg = seam.groupby('pair')['absY'].sum()
    pairs = [(p[0], p[1], k) for p, k in agg.items()]
    return pairs  # list of (bus_i, bus_j, K_ij)


def seam_coherence_and_stress(vm, bus_ids, pairs):
    bus_idx = {b: i for i, b in enumerate(bus_ids)}
    Vbar = vm.mean(axis=0)
    Vtilde = vm - Vbar  # (8784, 2000)

    n_t = vm.shape[0]
    C_terms = np.zeros((n_t, len(pairs)))
    diff_terms = np.zeros((n_t, len(pairs)))
    K = np.array([k for (_, _, k) in pairs])

    for idx, (bi, bj, k) in enumerate(pairs):
        ii, jj = bus_idx[bi], bus_idx[bj]
        diff = Vtilde[:, ii] - Vtilde[:, jj]
        sigma = diff.std()
        diff_terms[:, idx] = diff
        C_terms[:, idx] = 1.0 - np.abs(diff) / sigma if sigma > 1e-12 else np.nan

    coherence = np.nanmean(C_terms, axis=1)
    stress_raw = (np.abs(diff_terms) * K[None, :]).sum(axis=1)
    stress_norm = stress_raw / K.sum()

    return coherence, stress_raw, stress_norm


def delta1(x):
    """Δ1 drift: x(t) - x(t-1). First entry NaN."""
    d = np.full_like(x, np.nan, dtype=float)
    d[1:] = x[1:] - x[:-1]
    return d


def delta2(x):
    """Δ2 curvature: x(t+1) - 2x(t) + x(t-1). First/last entries NaN."""
    d = np.full_like(x, np.nan, dtype=float)
    d[1:-1] = x[2:] - 2 * x[1:-1] + x[:-2]
    return d


def precursor_operator(x, event_idx, tau=24):
    """P(t_e) = max_{t in [t_e-tau, t_e)} |Δ2 x(t)|."""
    d2 = delta2(x)
    results = []
    for te in event_idx:
        lo = max(0, te - tau)
        window = d2[lo:te]
        window = window[~np.isnan(window)]
        results.append(np.max(np.abs(window)) if len(window) else np.nan)
    return np.array(results)


def half_life(x, t0, max_window=168):
    """tau_1/2 = min dt such that x(t0+dt) <= x(t0)/2. NaN if not reached within max_window."""
    peak = x[t0]
    if peak <= 0:
        return np.nan
    target = peak / 2.0
    end = min(len(x), t0 + max_window + 1)
    for dt in range(1, end - t0):
        if x[t0 + dt] <= target:
            return dt
    return np.nan


def resilience_integral(x, t0, baseline, t_end):
    """R = sum_{t=t0}^{t_end} |x(t) - baseline|."""
    return np.sum(np.abs(x[t0:t_end + 1] - baseline))


def main():
    cf = load_case()
    d = np.load(os.path.join(OUT_DIR, 'annual_voltage_series.npz'))
    vm, bus_ids, hours = d['vm'], d['bus_ids'], d['hours']

    pairs = build_seam_pairs(cf)
    print(f"Seam pairs (deduplicated): {len(pairs)}")

    coherence, stress_raw, stress_norm = seam_coherence_and_stress(vm, bus_ids, pairs)

    out = pd.DataFrame({
        'hour': hours,
        'seam_coherence': coherence,
        'coupling_stress_raw': stress_raw,
        'coupling_stress_norm': stress_norm,
    })
    out['delta1_coherence'] = delta1(coherence)
    out['delta2_coherence'] = delta2(coherence)
    out['delta1_stress_norm'] = delta1(stress_norm)
    out['delta2_stress_norm'] = delta2(stress_norm)
    out.to_csv(os.path.join(OUT_DIR, 'tier1_candidate_timeseries.csv'), index=False)

    print("\nSeam coherence C(t): min={:.4f} mean={:.4f} max={:.4f}".format(
        coherence.min(), coherence.mean(), coherence.max()))
    print("Coupling stress (normalized): min={:.4f} mean={:.4f} max={:.4f}".format(
        stress_norm.min(), stress_norm.mean(), stress_norm.max()))

    # --- Event definition: top 1% system load hours, independent of any operator ---
    yr = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', 'data', 'activsg2000_area_load_8784h.csv'))
    load_cols = [f'area_{a}' for a in range(1, 9)]
    yr['system_total'] = yr[load_cols].sum(axis=1)
    threshold = yr['system_total'].quantile(0.99)
    event_idx = np.where(yr['system_total'].to_numpy() >= threshold)[0]
    print(f"\nEvents (top 1% system load, independently defined): {len(event_idx)} hours, "
          f"threshold {threshold:.0f} MW")

    P_coherence = precursor_operator(coherence, event_idx, tau=24)
    P_stress = precursor_operator(stress_norm, event_idx, tau=24)

    events_df = pd.DataFrame({
        'event_hour': hours[event_idx],
        'system_load_mw': yr['system_total'].to_numpy()[event_idx],
        'precursor_coherence_curvature': P_coherence,
        'precursor_stress_curvature': P_stress,
    })

    # tau_1/2 and R for the stress series, anchored at each event (peak = event itself)
    baseline_stress = np.median(stress_norm)
    tau_half_list, resilience_list = [], []
    for te in event_idx:
        th = half_life(stress_norm, te, max_window=168)
        tau_half_list.append(th)
        t_end = te + (th if not np.isnan(th) else 168)
        t_end = min(t_end, len(stress_norm) - 1)
        resilience_list.append(resilience_integral(stress_norm, te, baseline_stress, t_end))
    events_df['tau_half_stress_hours'] = tau_half_list
    events_df['resilience_R_stress'] = resilience_list

    events_df.to_csv(os.path.join(OUT_DIR, 'tier1_candidate_events.csv'), index=False)

    n_censored = int(np.isnan(events_df['tau_half_stress_hours']).sum())
    print(f"\nPer-event tau_1/2: {len(event_idx) - n_censored}/{len(event_idx)} recovered within "
          f"168h, {n_censored} censored (did not recover within window)")
    print(events_df.head(10).to_string(index=False))

    # --- Null test: is precursor curvature at real events different from random hours? ---
    # Required by this project's own established discipline (see
    # notes/intervention_windows_note.md, notes/session_scope_notes.md --
    # Δ2 windows explicitly flagged as "pending null-tested validation").
    # Without this, reporting the numbers above would be exactly the
    # mistake those notes warn against.
    rng = np.random.default_rng(42)
    n_boot = 2000
    n_events = len(event_idx)
    valid_range = np.arange(24, len(coherence))  # need room for the tau=24 lookback

    null_means_coh, null_means_stress = [], []
    for _ in range(n_boot):
        draw = rng.choice(valid_range, size=n_events, replace=False)
        null_means_coh.append(np.nanmean(precursor_operator(coherence, draw, tau=24)))
        null_means_stress.append(np.nanmean(precursor_operator(stress_norm, draw, tau=24)))
    null_means_coh = np.array(null_means_coh)
    null_means_stress = np.array(null_means_stress)

    true_mean_coh = np.nanmean(P_coherence)
    true_mean_stress = np.nanmean(P_stress)
    pctile_coh = (null_means_coh < true_mean_coh).mean() * 100
    pctile_stress = (null_means_stress < true_mean_stress).mean() * 100

    print(f"\n=== NULL TEST (n_boot={n_boot} random 88-hour draws) ===")
    print(f"Coherence-curvature precursor: true mean={true_mean_coh:.4f} | "
          f"null mean={null_means_coh.mean():.4f} (std {null_means_coh.std():.4f}) | "
          f"true value is at the {pctile_coh:.1f}th percentile of the null distribution")
    print(f"Stress-curvature precursor: true mean={true_mean_stress:.6f} | "
          f"null mean={null_means_stress.mean():.6f} (std {null_means_stress.std():.6f}) | "
          f"true value is at the {pctile_stress:.1f}th percentile of the null distribution")

    null_df = pd.DataFrame({'null_mean_coherence_precursor': null_means_coh,
                             'null_mean_stress_precursor': null_means_stress})
    null_df.to_csv(os.path.join(OUT_DIR, 'tier1_candidate_null_test.csv'), index=False)

    return out, events_df, null_df


if __name__ == '__main__':
    main()
