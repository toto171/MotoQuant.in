# Catalog Expansion 2026-05-30 (Saturday Daily — A1 Catalog Slot)

## Summary

Added **3 production motorcycles** to `motoquant/scraper/known_bikes_extended.py`
covering one ADV/dual-sport refresh, one mid-ADV triple update, and one
Indian/SE-Asia small-cc dual-sport. All three pass `validate_spec` cleanly
(scores 0.82-0.88, zero errors) and smoke-sim within their expected cluster
bias bands.

## Bikes added

| Symbol | Manufacturer | Model | Years | Disp | HP | Dry kg | Source |
|---|---|---|---|---|---|---|---|
| `KAWASAKI_KLR_650_2022` | Kawasaki | KLR 650 | 2022-2024 | 651 cc I1 | 40 | 196 | Kawasaki press release Sep 2021 + Cycle World Oct 2021 + service manual 99924-1453 + MCN Nov 2021 |
| `TRIUMPH_TIGER_900_GT_PRO_2024` | Triumph | Tiger 900 GT Pro | 2024-2026 | 888 cc I3 | 108 | 198 | Triumph press kit EICMA Nov 2023 + MCN Mar 2024 + Cycle World May 2024 + service manual T0301460 |
| `HONDA_CRF250L_2021` | Honda | CRF250L | 2021-2024 | 249 cc I1 | 24.5 | 132 | Honda Global press release Oct 2020 + Honda Thailand spec Mar 2021 + Cycle World Jan 2021 + service manual SHOP-CRF250L-21 |

## Smoke-sim results vs cluster bias bands

| Bike | Sim ET | Sim trap | Real-world expected | Cluster | Cluster bias |
|---|---|---|---|---|---|
| KLR 650 2022 | 14.941 s | 147.0 km/h | Cycle World 14.5-15.0 s @ ~150 km/h (40 hp / 196 kg single) | adventure / "other" (mid-cc single) | sim Δ +0.0 to +0.5 s — within band |
| Tiger 900 GT Pro 2024 | 12.081 s | 196.5 km/h | MCN informal 11.8-12.0 s (108 hp / 219 kg wet) | litre_sport_600_1000 / mid_twin (sits on boundary) | bias -0.15 s mean |Δ| 0.22 s — sim sits at +0.10 s, within band |
| CRF250L 2021 | 15.776 s | 134.7 km/h | 14.5-15.5 s expected (24.5 hp / 140 kg wet) | entry_200_300 | +0.5 to +1.4 s slow band — sim Δ +0.3 to +1.3 s consistent |

## Validator results

- `KLR650`: valid=True score=0.82 errors=0 warnings=2 (tire-size bias-ply notation `90/90-21` + `130/80-17` — same caveat as May-4 Hero Xtreme 200S 4V entry; cosmetic only)
- `Tiger 900 GT Pro`: valid=True score=0.88 errors=0 warnings=0
- `CRF250L`: valid=True score=0.82 errors=0 warnings=2 (tire-size bias-ply notation `3.00-21` + `120/80-18`)

## Baseline preservation

K5 = 10.0334 s · R1 = 10.2859 s · Hayabusa = 10.4712 s — **Δ +0.0000 s on all three** (pre and post catalog edit).

## Test suite

`tests/test_scraper.py + tests/test_validation.py = 140 passed in 8.00s`
(zero failures, zero new warnings).

## DB import

Used `import_batch(db, [...])` directly per CLAUDE.md WS-A workaround.
First pass: `imported=3 / errors=0`.
`bike_models` row count: **793 -> 796** (+3).

New bike row IDs: KLR 650 = 4589 · Tiger 900 GT Pro = 4590 · CRF250L = 4591.

## Notes / carry-forward

- All three bikes inherit the doubled year-suffix model_name pattern seen on
  the May 24-26 entries — the WS-A `bike_repo.create_model` upsert fix still
  open per the multi-week carry-forward list. Cosmetic only; does not affect
  physics path.
- KLR 650 uses a 5-speed gearbox (not 6) — unchanged from the 1987-2018
  carb-era KLR. The importer's gear-count handling accepts 5 cleanly per the
  April-21 `tests/test_scraper.py` gear-count-minimum relaxation (5 -> 4 for
  the RX100 4-speed).
- CRF250L uses 21" front spoke wheel with bias-ply `3.00-21` tire-size
  notation — the validator warning is cosmetic; the rolling-radius regex in
  `importer.py` handles `21` correctly via the `(\d{2})\b` boundary.
- All three bikes are dual-sport / ADV-biased, which adds to the catalog's
  adventure-cluster coverage (previously dominated by sport / naked /
  cruiser). Tire mu and gearing are set per category default rather than
  hand-tuned per bike; future calibration pass may benefit from running a
  Dragy timeslip on a stock CRF250L to refine the entry_200_300 cluster's
  +0.5 to +1.4 s slow band toward zero.
