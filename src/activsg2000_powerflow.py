"""
ACTIVSg2000 Power Flow Runner
==============================
Builds on activsg2000_loader.py. Converts CaseFrames -> pypower ppc dict
(numpy arrays) and runs AC power flow via pypower.

Status: WORKING. Base case converges (Newton's method, 3 iterations).

This is the prerequisite for:
  - Stress-hour testing (apply scenario loads, re-solve, compare states)
  - N-1/N-k contingency sweeps (trip branches, re-solve, look for
    non-convergence / voltage collapse / overload -- synthetic rupture
    conditions per the "Texas2k synthetic rupture sweep v0.1" plan)

NOT YET DONE (next session):
  - Apply scenarios_ACTIVSg2000.m area loads to bus.PD/QD before solving
  - N-1 branch trips using contab_ACTIVSg2000.m
  - Define stress hours independently (e.g. top-1% area load) BEFORE
    looking at any operator output (non-circular event definition,
    per evening's discussion)
"""

import os
import numpy as np
from matpowercaseframes import CaseFrames
from pypower.api import runpf, ppoption


def case_to_ppc(cf):
    """Convert a CaseFrames object to a pypower ppc dict of numpy arrays."""
    return {
        'version': '2',
        'baseMVA': float(cf.baseMVA),
        'bus': cf.bus.to_numpy(dtype=float),
        'gen': cf.gen.to_numpy(dtype=float),
        'branch': cf.branch.to_numpy(dtype=float),
        'gencost': cf.gencost.to_numpy(dtype=float),
    }


def run_base_case(case_file=None, verbose=False):
    """Load the case and run AC power flow. Returns (result_ppc, success)."""
    if case_file is None:
        case_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'ACTIVSg2000.m')
    cf = CaseFrames(case_file)
    ppc = case_to_ppc(cf)
    opt = ppoption(VERBOSE=1 if verbose else 0, OUT_ALL=0, PF_TOL=1e-6)
    result, success = runpf(ppc, opt)
    return result, success


if __name__ == '__main__':
    result, success = run_base_case(verbose=True)
    print("\nConverged:", bool(success))
    if success:
        bus = result['bus']
        print(f"Bus voltage range: {bus[:,7].min():.4f} - {bus[:,7].max():.4f} p.u.")
