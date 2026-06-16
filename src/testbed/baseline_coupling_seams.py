"""
Baseline AC-Physics Characterization — Area-to-Area Coupling Matrix
                                          & Seam Stress Baselines
====================================================================
Section 1, items 3-4 of the SCFL validation test suite.

Builds on:
  - activsg2000_loader.py   (case -> CaseFrames)
  - activsg2000_powerflow.py (case_to_ppc, run_base_case)
  - The established 8-area ground-truth partition (BUS_AREA column;
    95.7% intra-area branch connectivity per README.md)

Produces two artifacts:

1. Area-to-area coupling matrix (real + imaginary), derived from the
   series admittance y = 1/(R + jX) of each in-service branch.
   - G (real/conductance) and B (imaginary/susceptance) are each
     aggregated into an 8x8 symmetric matrix: off-diagonal [i,j] is
     the sum over branches connecting area i and area j; diagonal
     [i,i] is the sum over branches *within* area i.
   - NOTE: this uses series admittance only (R, X). Line charging
     susceptance (BR_B, the shunt term in the pi-model) is excluded
     deliberately -- it represents capacitive coupling to ground, not
     inter-bus coupling, and would conflate the two physically
     distinct effects if folded into the same number. If shunt
     coupling is wanted later it should be a separate matrix.

2. Seam stress baseline: for every cross-area ("seam") branch, the
   nominal-case (base-load, no perturbation) apparent power flow and
   loading fraction (S / RATE_A). This identifies which seams are
   already running closest to their thermal limits under nominal
   conditions -- i.e. the natural stress points in the topology,
   established BEFORE any stress/rupture sweep is run, per the
   non-circular event-definition discipline used elsewhere in this
   project (define baselines/thresholds before looking at perturbed
   results).

Status: FIRST RUN. Single base-case snapshot. Does not yet establish
variance/distribution of coupling or seam loading -- that requires
the year-long load profile (item 2, nominal-regime operator tests)
and is intentionally out of scope here.
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from activsg2000_loader import load_case
from activsg2000_powerflow import case_to_ppc
from pypower.api import runpf, ppoption

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'experiments')

# Branch column order in the post-solve ppc['branch'] numpy array
# (matches activsg2000_powerflow.case_to_ppc / pypower convention)
BR_COLS = ['F_BUS', 'T_BUS', 'BR_R', 'BR_X', 'BR_B', 'RATE_A', 'RATE_B',
           'RATE_C', 'TAP', 'SHIFT', 'BR_STATUS', 'ANGMIN', 'ANGMAX',
           'PF', 'QF', 'PT', 'QT', 'MU_SF', 'MU_ST', 'MU_ANGMIN', 'MU_ANGMAX']


def build_area_map(cf):
    """bus_id (float) -> area (int)"""
    return dict(zip(cf.bus['BUS_I'].astype(float), cf.bus['BUS_AREA'].astype(int)))


def build_coupling_matrices(branch_df, area_map, n_areas=8):
    """Returns (G_matrix, B_matrix, seam_mask, area_from, area_to) for
    in-service branches. G/B matrices are n_areas x n_areas, 1-indexed
    areas mapped to 0-indexed rows/cols (area i -> row/col i-1)."""
    G = np.zeros((n_areas, n_areas))
    B = np.zeros((n_areas, n_areas))

    in_service = branch_df['BR_STATUS'] == 1
    bdf = branch_df[in_service].copy()

    area_from = bdf['F_BUS'].map(area_map).astype(int).to_numpy()
    area_to = bdf['T_BUS'].map(area_map).astype(int).to_numpy()
    R = bdf['BR_R'].to_numpy(dtype=float)
    X = bdf['BR_X'].to_numpy(dtype=float)

    Z = R + 1j * X
    # Guard against zero-impedance branches (would blow up 1/Z)
    Z[np.abs(Z) < 1e-9] = 1e-9
    y = 1.0 / Z
    g = y.real
    b = y.imag

    seam_mask = area_from != area_to
    i_idx, j_idx = area_from - 1, area_to - 1

    # Intra-area branches (i==j): add once to the diagonal.
    # Cross-area branches (i!=j): add to [i,j], then mirror into [j,i] so
    # the matrix is symmetric (coupling between A and B is the same
    # number read either direction).
    np.add.at(G, (i_idx, j_idx), g)
    np.add.at(B, (i_idx, j_idx), b)
    np.add.at(G, (j_idx[seam_mask], i_idx[seam_mask]), g[seam_mask])
    np.add.at(B, (j_idx[seam_mask], i_idx[seam_mask]), b[seam_mask])

    return G, B, seam_mask, area_from, area_to, bdf, R, X


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    cf = load_case()
    area_map = build_area_map(cf)

    print("=== Area-to-Area Coupling Matrix (series admittance) ===")
    G, B, seam_mask, area_from, area_to, bdf, R, X = build_coupling_matrices(cf.branch, area_map)

    areas = list(range(1, 9))
    G_df = pd.DataFrame(G, index=areas, columns=areas)
    B_df = pd.DataFrame(B, index=areas, columns=areas)
    G_df.to_csv(os.path.join(OUT_DIR, 'coupling_matrix_G.csv'))
    B_df.to_csv(os.path.join(OUT_DIR, 'coupling_matrix_B.csv'))

    print("\nG (conductance, real part of series admittance), p.u.:")
    print(G_df.round(2))
    print("\nB (susceptance, imaginary part of series admittance), p.u.:")
    print(B_df.round(2))

    n_seam_branches = int(seam_mask.sum())
    n_intra_branches = int((~seam_mask).sum())
    print(f"\nIn-service branches: {len(bdf)} total | "
          f"{n_intra_branches} intra-area | {n_seam_branches} cross-area (seam)")

    # --- Run base-case AC power flow to get nominal branch flows ---
    print("\n=== Running base-case AC power flow for seam stress baseline ===")
    ppc = case_to_ppc(cf)
    opt = ppoption(VERBOSE=0, OUT_ALL=0, PF_TOL=1e-6)
    result, success = runpf(ppc, opt)
    if not success:
        print("Base case did not converge -- aborting seam stress baseline.")
        return

    branch_result = pd.DataFrame(result['branch'], columns=BR_COLS)
    in_service = branch_result['BR_STATUS'] == 1
    bres = branch_result[in_service].reset_index(drop=True)

    bres['AREA_F'] = bres['F_BUS'].map(area_map).astype(int)
    bres['AREA_T'] = bres['T_BUS'].map(area_map).astype(int)
    bres['IS_SEAM'] = bres['AREA_F'] != bres['AREA_T']
    bres['S_MVA'] = np.sqrt(bres['PF']**2 + bres['QF']**2)
    bres['LOADING_PCT'] = np.where(
        bres['RATE_A'] > 0, 100.0 * bres['S_MVA'] / bres['RATE_A'], np.nan
    )

    seams = bres[bres['IS_SEAM']].copy()
    intra = bres[~bres['IS_SEAM']].copy()

    seams_out = seams[['F_BUS', 'T_BUS', 'AREA_F', 'AREA_T', 'BR_R', 'BR_X',
                        'RATE_A', 'PF', 'QF', 'S_MVA', 'LOADING_PCT']].sort_values(
        'LOADING_PCT', ascending=False
    )
    seams_out.to_csv(os.path.join(OUT_DIR, 'seam_stress_baseline.csv'), index=False)

    rated = seams['RATE_A'] > 0
    rated_intra = intra['RATE_A'] > 0

    print(f"\nSeam branches with a defined rating: {int(rated.sum())} / {len(seams)}")
    print(f"Seam loading %% -- mean: {seams.loc[rated,'LOADING_PCT'].mean():.2f}  "
          f"median: {seams.loc[rated,'LOADING_PCT'].median():.2f}  "
          f"max: {seams.loc[rated,'LOADING_PCT'].max():.2f}")
    print(f"Intra-area loading %% -- mean: {intra.loc[rated_intra,'LOADING_PCT'].mean():.2f}  "
          f"median: {intra.loc[rated_intra,'LOADING_PCT'].median():.2f}  "
          f"max: {intra.loc[rated_intra,'LOADING_PCT'].max():.2f}")

    print("\nTop 10 most heavily loaded seam branches (nominal base case):")
    print(seams_out.head(10).to_string(index=False))

    return G_df, B_df, seams_out, seams, intra


if __name__ == '__main__':
    main()
