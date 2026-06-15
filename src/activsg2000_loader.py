"""
ACTIVSg2000 Loader
==================
Loads the ACTIVSg2000 synthetic Texas grid case (MATPOWER format) into
pandas DataFrames using matpowercaseframes.

Source: Texas A&M Electric Grid Test Case Repository
        (Birchfield et al., 2017, IEEE Trans. Power Systems)
File:   ACTIVSg2000.m (uploaded 2026-06-15)

Status: WORKING. Loads cleanly. pandapower's full from_mpc() converter
has a bug in gencost handling (IndexError in _from_ppc_gencost, version-
specific) -- bypassed entirely by using matpowercaseframes directly,
which is sufficient for topology/Dimensional Audit work (we don't need
pandapower's full electrical network object for this).

Usage:
    from activsg2000_loader import load_case
    cf = load_case()
    cf.bus, cf.branch, cf.gen  -> DataFrames
"""

from matpowercaseframes import CaseFrames
import os

CASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'ACTIVSg2000.m')


def load_case(path=CASE_FILE):
    """Load ACTIVSg2000 case. Returns a CaseFrames object with
    .bus, .branch, .gen, .gencost DataFrames and .baseMVA."""
    cf = CaseFrames(path)
    return cf


if __name__ == '__main__':
    cf = load_case()
    print(f"baseMVA: {cf.baseMVA}")
    print(f"bus:    {cf.bus.shape}   (2000 buses expected)")
    print(f"branch: {cf.branch.shape} (3206 branches expected)")
    print(f"gen:    {cf.gen.shape}   (544 generators expected)")
