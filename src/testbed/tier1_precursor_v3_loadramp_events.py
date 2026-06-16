"""
TIER1_CANDIDATE_SPEC_v1 — Precursor Null Test, v3 (genuinely different events)
================================================================================
v1 used top-1% load level. v2 ("bottom-1% headroom") turned out to be the
IDENTICAL set of hours, since headroom = fixed_capacity - load with fixed
capacity -- not actually a different test, caught and discarded.

v3 uses the largest hour-to-hour JUMPS in system load (top 1% of |ΔLoad|),
independent of absolute level. This is a meaningfully different concept:
a big ramp can happen from low to medium load, not just into the annual
peak. It's also the more theoretically apt comparison for a curvature
(Δ2) precursor operator -- testing whether there's a buildup before a
SUDDEN CHANGE, not before a merely-high level.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tier1_candidate_operators import precursor_operator, half_life, resilience_integral

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')


def main():
    ts = pd.read_csv(os.path.join(OUT_DIR, 'tier1_candidate_timeseries.csv'))
    coherence = ts['seam_coherence'].to_numpy()
    stress_norm = ts['coupling_stress_norm'].to_numpy()
    hours = ts['hour'].to_numpy()

    yr = pd.read_csv(os.path.join(DATA_DIR, 'activsg2000_area_load_8784h.csv'))
    load_cols = [f'area_{a}' for a in range(1, 9)]
    yr['system_total'] = yr[load_cols].sum(axis=1)
    yr['abs_delta_load'] = yr['system_total'].diff().abs()

    threshold = yr['abs_delta_load'].quantile(0.99)
    event_mask = yr['abs_delta_load'].to_numpy() >= threshold
    event_idx = np.where(event_mask)[0]
    print(f"Events (top 1% |hour-to-hour load ramp|): {len(event_idx)} hours, "
          f"threshold {threshold:.1f} MW/h")
    print(f"Ramp range at events: {yr['abs_delta_load'].to_numpy()[event_idx].min():.1f} to "
          f"{yr['abs_delta_load'].to_numpy()[event_idx].max():.1f} MW/h")

    # Confirm this is actually a different set from v1/v2
    ev1 = set(pd.read_csv(os.path.join(OUT_DIR, 'tier1_candidate_events.csv'))['event_hour'])
    ev3 = set(hours[event_idx])
    print(f"Overlap with v1 (top-1%-load) event set: {len(ev1 & ev3)}/{len(ev3)}")

    P_coherence = precursor_operator(coherence, event_idx, tau=24)
    P_stress = precursor_operator(stress_norm, event_idx, tau=24)

    events_df = pd.DataFrame({
        'event_hour': hours[event_idx],
        'abs_delta_load_mw': yr['abs_delta_load'].to_numpy()[event_idx],
        'system_load_mw': yr['system_total'].to_numpy()[event_idx],
        'precursor_coherence_curvature': P_coherence,
        'precursor_stress_curvature': P_stress,
    })

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
    events_df.to_csv(os.path.join(OUT_DIR, 'tier1_candidate_events_v3_loadramp.csv'), index=False)

    rng = np.random.default_rng(42)
    n_boot = 2000
    n_events = len(event_idx)
    valid_range = np.arange(24, len(coherence))

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

    print(f"\n=== NULL TEST v3 (load-ramp events, n_boot={n_boot}) ===")
    print(f"Coherence-curvature: true mean={true_mean_coh:.4f} | null mean={null_means_coh.mean():.4f} "
          f"(std {null_means_coh.std():.4f}) | true value at {pctile_coh:.1f}th percentile of null")
    print(f"Stress-curvature: true mean={true_mean_stress:.6f} | null mean={null_means_stress.mean():.6f} "
          f"(std {null_means_stress.std():.6f}) | true value at {pctile_stress:.1f}th percentile of null")

    n_censored = int(np.isnan(events_df['tau_half_stress_hours']).sum())
    print(f"\ntau_1/2: {n_events - n_censored}/{n_events} recovered within 168h, {n_censored} censored")

    null_df = pd.DataFrame({'null_mean_coherence_precursor': null_means_coh,
                             'null_mean_stress_precursor': null_means_stress})
    null_df.to_csv(os.path.join(OUT_DIR, 'tier1_candidate_null_test_v3_loadramp.csv'), index=False)

    return events_df, null_df, pctile_coh, pctile_stress


if __name__ == '__main__':
    main()
