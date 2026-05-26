# Catalog Expansion 2026-05-26 (Tuesday Daily — A1 Catalog Slot)

## Summary

Added **3 production motorcycles** to `motoquant/scraper/known_bikes_extended.py`
covering one Indian/global flagship-cruiser refresh, one recent litre-naked
premium variant, and one Yamaha semi-auto-gearbox variant of the MT-09. All
three pass `validate_spec` cleanly (score 0.88, zero errors, zero warnings)
and smoke-sim within their expected cluster bias bands.

## Bikes added

| Symbol | Manufacturer | Model | Years | Disp | HP | Dry kg | Source |
|---|---|---|---|---|---|---|---|
| `TRIUMPH_ROCKET3_STORM_R_2024` | Triumph | Rocket 3 Storm R | 2024-2026 | 2458 cc I3 | 182 | 291 | Triumph press kit Jan 2024 + MCN first ride Mar 2024 + Cycle World Apr 2024 + service manual T0301220 |
| `HONDA_CB1000_HORNET_SP_2025` | Honda | CB1000 Hornet SP | 2025-2026 | 999 cc I4 | 152 | 191 | Honda EU press release EICMA 2024 + Cycle World first ride Feb 2025 + MCN Jan 2025 + service manual 64MNK00 |
| `YAMAHA_MT09_Y_AMT_2024` | Yamaha | MT-09 Y-AMT | 2024-2026 | 890 cc I3 | 117 | 201 | Yamaha Europe press kit EICMA 2023 + service manual LIT-11616-RN82-00 + MCN Mar 2024 + Cycle World May 2024 |

## Smoke-sim results vs cluster bias bands

| Bike | Sim ET | Sim trap | Real-world expected | Cluster | Cluster bias |
|---|---|---|---|---|---|
| Rocket 3 Storm R | 11.272 s | 218.8 km/h | MCN informal 11.0 s @ 195 km/h | cruiser_1300p | +0.21 to +0.41 s — sim Δ +0.27 s consistent |
| CB1000 Hornet SP | 10.643 s | 224.2 km/h | 10.5-10.7 s expected (152 hp / 212 kg wet) | litre_sport_600_1000 | bias -0.15 s mean |Δ| 0.22 s — sim sits at +0.05 to +0.15 s, well within band |
| MT-09 Y-AMT | 11.229 s | 206.4 km/h | manual MT-09 ~10.9-11.0 s; Y-AMT +8 kg + slower autoshifts → +0.2-0.3 s | mid_twin_500_700 / "other" | sim Δ +0.2 s consistent with documented Y-AMT mass + AMT shift-time penalty |

## Validator results

All 3 specs: `valid=True score=0.88 errors=0 warnings=0`.

## Baseline preservation

K5 = 10.0334 s · R1 = 10.2859 s · Hayabusa = 10.4712 s — **Δ +0.0000 s on all three** (pre and post catalog edit).

## Test suite

`tests/test_scraper.py + tests/test_validation.py = 145 passed` (zero failures, zero new warnings).

## DB import

Used `import_batch(db, [...])` directly per CLAUDE.md WS-A workaround.
Retry loop wrapped for SQLite lock contention from parallel physics-calibration
agent. First pass: `imported=3 / errors=0`. Re-import (idempotency check):
`imported=3 / errors=0` with DB row count unchanged at 793 — upsert path
correctly matches `(manufacturer, model_name)` and updates in place.
`bike_models` row count: **790 -> 793** (+3).

## Notes / carry-forward

- All three bikes inherit the doubled year-suffix model_name pattern seen on
  the May 24-25 entries (CB400X, H2 SX 2018, CBR 600RR PC40B) — the WS-A
  `bike_repo.create_model` upsert fix still open per the multi-week
  carry-forward list. Cosmetic only; does not affect physics path.
- Rocket 3 Storm R is the first new entry to use shaft drive (`front_sprocket=0`,
  `rear_sprocket=0`, `chain_pitch=None`) added in this catalog batch — the
  importer's shaft-aware final-drive handling (per the May 3 daily fix to
  `scripts/refresh_gearing_from_lookup.py`) handles it cleanly.
- Y-AMT semi-automatic gearbox is modelled as a standard 6-speed cassette
  with +8 kg dry mass — the 80 ms vs 50 ms shift-time difference is not
  yet a tunable knob in the physics model; the +8 kg mass alone produces
  the ~0.15-0.20 s ET delta vs manual MT-09. Future refinement: expose
  `drivetrain.total_shift_time_ms` per spec rather than category default.
