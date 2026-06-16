# Section 1, Item 2 (proxy) — Reserve-Headroom Findings

**This is a static reserve-margin proxy, not a frequency response curve.**
See the docstring in `src/testbed/frequency_response_proxy.py` for why a true
Δf-vs-ΔP frequency response is not computable from ACTIVSg2000 (no inertia,
governor droop, or AGC parameters — RAMP_AGC confirmed 0 for all 544
generators, not just defaulted).

## What was computed

Fixed online generation capacity per area (sum of PMAX for GEN_STATUS==1
generators) compared against the real 2016 hourly area load profile
(8784 hours), giving a headroom-% trajectory per area and system-wide.

- System online capacity: 81,202 MW. Offline (non-spinning, excluded):
  15,090 MW.
- System-wide headroom across the year: min 18.38%, mean 54.30%, max 71.59%.
- **Tightest system-wide hour: August 11, 2016, 3:00 PM — 18.38% headroom.**
  This is a plausible result on its face: a Texas-summer-afternoon AC-load
  peak is exactly when a real ERCOT-like system would be tightest. Useful as
  a face-validity check on the dataset, not a claim about the real grid.

## The thing worth flagging: per-area headroom went negative for Area 5

| Area | Online capacity (MW) | Min headroom | Tightest hour |
|---|---|---|---|
| 1 | 3,012 | 56.6% | Jul 12, 3 PM |
| 2 | 3,213 | 54.1% | Aug 4, 2 PM |
| 3 | 4,068 | 59.7% | Aug 11, 3 PM |
| 4 | 7,824 | 13.3% | Aug 11, 2 PM |
| 5 | 15,570 | **-43.0%** | Aug 11, 3 PM |
| 6 | 15,373 | 20.2% | Aug 12, 3 PM |
| 7 | 26,237 | 30.7% | Aug 9, 2 PM |
| 8 | 5,905 | 46.0% | Aug 9, 2 PM |

Area 5's load exceeds its own online generation by 43% at peak — meaning it's
a structural net importer, leaning on inter-area transfer (which is exactly
what the coupling matrix and seam branches exist to carry). That's not a
flaw in the calculation; it's a real feature of how the areas were defined,
and it's the reason a per-area headroom number isn't standalone meaningful —
the **system-wide** figure (18.38% minimum) is the one that's physically
load-bearing, since the AC grid shares frequency response across the whole
interconnection, not per-area.

## Cross-check with the PV/QV result

This independently corroborates something the single-slack PV sweep also
flagged: Area 5 (and to a lesser extent Area 7) showed the least margin
there too — but for a *different and more legitimate* reason this time.
The PV-curve result was confounded by the single-slack-bus artifact; this
result is a direct, unconfounded read of installed capacity vs. real annual
demand. Both point to Area 5 being the system's load-bearing center of
gravity, which is now established two independent ways.

## Status
Reserve-headroom proxy complete for all 8784 hours, all 8 areas + system.
Explicitly NOT validated as a frequency-response measure — that remains
blocked pending a dynamics-capable case (inertia/governor data), out of
scope for this testbed unless that data becomes available.
