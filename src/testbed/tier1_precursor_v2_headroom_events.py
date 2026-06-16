"""
TIER1_CANDIDATE_SPEC_v1 — Precursor Null Test, v2 (better event definition)
=============================================================================
v1 (tier1_candidate_operators.py) used top-1% system load as the "event" --
the null test showed this was the wrong choice: routine peak demand is
approached smoothly (predictable diurnal ramp), so curvature was LOWER
before those events, not higher.

This version uses bottom-1% system-wide reserve headroom (from
reserve_headroom_proxy_8784h.csv, already computed) as the event
definition instead. Rationale: headroom is a direct proxy for proximity
to actual structural failure (how much margin is left before something
breaks), which is a meaningfully different and more rupture-adjacent
concept than "how much is currently being demanded." Still independently
defined before looking at any operator output -- same non-circularity
rule as before.

Imports the operator functions from tier1_candidate_operators.py rather
than duplicating them.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tier1_candidate_operators import precursor_operator, half_life, resilience_integral

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')


def main():
    ts = pd.read_csv(os.path.join(OUT_DIR, 'tier1_candidate_timeseries.csv'))
    headroom = pd.read_csv(os.path.join(OUT_DIR, 'reserve_headroom_proxy_8784h.csv'))

    coherence = ts['seam_coherence'].to_numpy()
    stress_norm = ts['coupling_stress_norm'].to_numpy()
    hours = ts['hour'].to_numpy()

    threshold = headroom['system_headroom_pct'].quantile(0.01)
    event_mask = headroom['system_headroom_pct'].to_numpy() <= threshold
    event_idx = np.where(event_mask)[0]
    print(f"Events (bottom 1% system headroom): {len(event_idx)} hours, "
          f"threshold {threshold:.2f}% headroom")
    print(f"Event headroom range: {headroom['system_headroom_pct'].to_numpy()[event_idx].min():.2f}% "
          f"to {headroom['system_headroom_pct'].to_numpy()[event_idx].max():.2f}%")

    P_coherence = precursor_operator(coherence, event_idx, tau=24)
    P_stress = precursor_operator(stress_norm, event_idx, tau=24)

    events_df = pd.DataFrame({
        'event_hour': hours[event_idx],
        'headroom_pct': headroom['system_headroom_pct'].to_numpy()[event_idx],
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
    events_df.to_csv(os.path.join(OUT_DIR, 'tier1_candidate_events_v2_headroom.csv'), index=False)

    # --- Null test ---
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

    print(f"\n=== NULL TEST v2 (headroom events, n_boot={n_boot}) ===")
    print(f"Coherence-curvature: true mean={true_mean_coh:.4f} | null mean={null_means_coh.mean():.4f} "
          f"(std {null_means_coh.std():.4f}) | true value at {pctile_coh:.1f}th percentile of null")
    print(f"Stress-curvature: true mean={true_mean_stress:.6f} | null mean={null_means_stress.mean():.6f} "
          f"(std {null_means_stress.std():.6f}) | true value at {pctile_stress:.1f}th percentile of null")

    n_censored = int(np.isnan(events_df['tau_half_stress_hours']).sum())
    print(f"\ntau_1/2: {n_events - n_censored}/{n_events} recovered within 168h, {n_censored} censored")

    null_df = pd.DataFrame({'null_mean_coherence_precursor': null_means_coh,
                             'null_mean_stress_precursor': null_means_stress})
    null_df.to_csv(os.path.join(OUT_DIR, 'tier1_candidate_null_test_v2_headroom.csv'), index=False)

    return events_df, null_df, pctile_coh, pctile_stress


if __name__ == '__main__':
    main()
