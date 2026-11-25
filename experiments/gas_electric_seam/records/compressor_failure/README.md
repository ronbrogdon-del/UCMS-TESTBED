# Compressor-station failure set (seam-v0.3-compressor), exploratory, pre-freeze

Physics results only. SCFL readings are not published here.

## Failure modes
- **isolate**: the station is valved off, as after a fire or a rupture near the station. Flow ramps to zero over 5 minutes.
- **bypass**: the compressor units trip and gas passes through the bypass. The ratio ramps to 1.0.

Every mode cites a real event (see `precedents.md`). Only 7 of the 32 Texas7k compressors boost pressure in the base case; the rest run at ratio 1.0, so for them only isolation changes anything.

Limitation: the bypass mode has no check valve, so a short reverse-flow surge (about 10 minutes) follows the trip.

## Screening: single station failure, normal supply (capped), failure at 1 h, 12 h runs
See `screening_summary.txt`. Margin is the weakest plant pressure minus 2,901.3 kPa (2.8 MPag).

| Station | Mode | Weakest-plant margin lost vs control at 12 h | Projected time to floor |
|---|---|---|---|
| Houston, compressor 20 | isolate | 88 kPa (133 kPa at plant 37) | about 148 h |
| Houston, compressor 15 | isolate | 84 kPa | about 186 h |
| Victoria, compressors 9 and 24 | isolate | 51 kPa | about 131 h |
| Victoria, compressors 9 and 24 | bypass | 24 kPa | about 376 h |
| Permian, compressor 11 | isolate | 1 kPa | none in view |

No single station failure caused a runback within 12 hours. The network reroutes gas around a lost station.

## Compound: supply strain plus a station failure, 30 h runs
Strain is the earlier cut41 case: 100% loss at processing plants within 600 km of node 546 (41% of state supply), ramped 1–3 h, capped supply, coupled loop in Uri mode. Station isolated at 2 h.

| Case | First plant runback | Non-gas headroom used up | Plants in runback at 24 h | MW lost at 30 h | Load shed by 30 h |
|---|---|---|---|---|---|
| Strain only (cut41) | 20.08 h | 26.83 h | 22 | 10,445 | none |
| Strain + Houston c20 isolated | 17.47 h | 27.48 h | 25 | 9,291 | none |
| Strain + Victoria isolated | 17.35 h | 23.43 h | 38 | 11,410 | none |

A station failure at the onset of strain brings the first plant runback about 2.6–2.7 hours sooner. With Victoria lost, non-gas backup runs out 3.4 hours sooner. The onset is still slow (more than 17 hours), and no load is shed within 30 hours because gas plants still have spare capacity.

The first plants to run back are the same Houston plants in all three cases (gas nodes 14, 27, 1, 16).
