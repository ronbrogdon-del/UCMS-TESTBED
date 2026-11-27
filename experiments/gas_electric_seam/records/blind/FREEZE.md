# Freeze: blind test of the Stage 1 precursor gate

Frozen 26 November 2026 (America/Chicago), before the NIST Randomness Beacon pulse at 18:00:00 UTC on 27 November 2026 that draws the sealed scenarios (protocol Section 2C).

| Item | Fingerprint (SHA-256) |
|---|---|
| Engine `scfl_measure.py` v1.1.0 (line endings normalised) | 233d9d9c154639c3e7c4fcc0f57bc2044cfe313e17f89d09bed9610a61e5b020 |
| Engine `scfl_ingest_qc.py` v1.1.0 (line endings normalised) | 50a9ebc2a860fe0a8b82eb7d716e0dce13432bda89ea0fb5768d535ccb8eaa3b |
| Stage 1 gate rule file (private to UCMS) | 5aabf3dfe6fa7b8e14ffb88dd40120ec4bd499abb02d4b925aeba5a82d92dd00 |
| Baseline thresholds `records/blind/baseline_thresholds.json` | see SHA256 below |
| Draw script `src/blind_draw.py` | see SHA256 below |
| Baseline script `src/baselines.py` | see SHA256 below |
| Protocol `protocol/SCFL_Gas-Electric_Preregistration_v0.2.md` | see SHA256 below |

Engine operator settings: package defaults. No change to engine, rule, alarms, pool, draw or pass criteria is permitted after this commit.

```
03a0ad7f49e8b1fe64dd24dc1d06c4661c5aa535b3312e0860c7268e3b76a16b  records/blind/baseline_thresholds.json
2860b7b48107c9980066834f06d55db756a64dc4f19215f2076ce6e5f8712dff  src/blind_draw.py
a169bc5ade273efd959394b8fcca70776cb5a571e11e22a4b3b62dc44d2def90  src/baselines.py
5d71cb28a53727049aee0631a19355972027e361b9346bf6107b326f13a240d5  protocol/SCFL_Gas-Electric_Preregistration_v0.2.md
```
