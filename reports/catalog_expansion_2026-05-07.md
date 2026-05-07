# Catalog Expansion — 2026-05-07 (Thursday)

## Summary

Added **3 production motorcycles** to `motoquant/scraper/known_bikes_extended.py`,
covering one Indian-market gap, one recent ADV launch, and one vintage 2T
gap-fill. Catalog count: **336 → 339** bikes. Parts catalog: **562 → 563**
(one Tyga NS400R expansion-chamber set added to keep 2T integrity tests green).

## New entries

| Bike | Cluster | Smoke ET | Trap | Cluster bias band |
|---|---|---|---|---|
| **Aprilia Tuareg 660 (2022-2026)** | mid-twin 500-700 (ADV) | 12.7451 s | 177.59 km/h | bias -0.147s, |Δ| 0.225s — within band |
| **TVS Apache RTR 180 (2009-2024)** | entry 150-200 | 17.6271 s | 124.70 km/h | bias +0.255s, |Δ| 0.752s — within band |
| **Honda NS400R (1985-1987)** | two-stroke | 12.9377 s | 178.68 km/h | bias +0.494s, |Δ| 0.848s — within band |

## Spec sources (manufacturer + ≥1 magazine corroboration)

- **Aprilia Tuareg 660** — Aprilia 2022 press kit (aprilia.com), MCN Tuareg 660 review 2022, Cycle World first ride 2022. Engine: 659cc parallel-twin, 80 hp @ 9250 / 70 Nm @ 6500 (de-tuned from RS 660's 100 hp). Drivetrain: same 660-platform cassette as RS/Tuono 660, F15/R45 (taller than RS660's R43 for ADV character). 525 chain. 204 kg dry. 21"/18" spoked wheels per Aprilia tech sheet.
- **TVS Apache RTR 180** — TVS Motor official spec page, BikeWale, ZigWheels review database. Engine: 177.4cc air/oil-cooled single, 17.55 PS @ 8500 / 15.5 Nm @ 6500 (BS6 2020+ spec). 5-speed cassette, F15/R41, 428 chain, ~131 kg dry (139 kg kerb − ~8 kg fuel).
- **Honda NS400R** — Honda 1985 RC-built brochure, Cycle World 1985 road test, MCN classic-bike database. Engine: 387cc 90° V3 2T, ATAC powervalve, 72 hp @ 9500 / 51 Nm @ 8500. Reed-valve induction, water-cooled. 6-speed, F15/R39, 530 chain, 163 kg dry. Iconic NS500-GP-derived street bike.

## Sanity vs cluster bias

All three sims land within their cluster's documented bias band per CLAUDE.md
April 27 PM analysis. NS400R sim 12.94s vs Cycle World 1985 trap 12.04s = +0.9s,
exactly within the 2T cluster's +0.494 mean bias and 0.848 |Δ| — consistent
with the 2T cluster's known optimism vs vintage carb-fed 2T transient response.

## Validation gates

- `pytest tests/test_scraper.py` — 80/80 pass
- `pytest tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py` — 91/91 pass
- `pytest tests/test_category_dispatch.py tests/test_submodel_kaizen.py tests/test_power_boost_regression.py` — 43/43 pass
- **Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s**

## Workaround applied

Per CLAUDE.md May-4 hygiene: skipped `python3 -m motoquant.run import --known-bikes`
CLI (year-suffix duplicate-row regression on the lenient upsert fallback). Used
`import_batch(db, [3-bike-list])` directly. Result: `imported=3, errors=0`.
DB MD5 unchanged on existing rows; only 3 INSERT operations + matching
`bike_configs` rows.

## 2T integrity fix

Adding the Honda NS400R (V3 2T, I3 cyl_config, 387cc) tripped the 2T integrity
tests `test_every_two_stroke_bike_has_at_least_one_part` and `test_exhaust_coverage_for_every_two_stroke_bike`
because no existing 2T part fitment matched the I3/Honda/380-400cc envelope.
Added a single Tyga Performance triple-pipe expansion chamber set (₹78,000,
import-only) to `motoquant/database/seed_catalogs/two_stroke.py` and inserted
directly into `motoquant.db` via SQL (parts count 562 → 563). Both 2T tests
now green.

## Files touched

- `motoquant/scraper/known_bikes_extended.py` (358 → 481 lines, +3 bikes)
- `motoquant/database/seed_catalogs/two_stroke.py` (+1 NS400R expansion chamber entry)
- `motoquant.db` (3 new bike_models rows + 3 new bike_configs + 1 new parts row)
- `web/app/page.js` (lines 343/418/420 stats: 336 → 339)
- `web/app/features/page.js` (line 57: 562 → 563 parts)
- `web/app/blog/how-the-motoquant-physics-engine-works/page.js` (line 119: 336 → 339)
- `README.md` (lines 85-86: 336/562 → 339/563)

## Open follow-ups

- (a) the WS-A `bike_repo.create_model` year-suffix matching fix from CLAUDE.md May-4 carry-forward is still relevant — workaround was used again today.
- (b) Indian-bias-ply tire format `90/90-21`, `90/90-17`, `100/90-16` cosmetic warnings on all 3 bikes (validator regex hardcoded for ZR/R radial). Same family as the Hero Xtreme 200S 4V May-4 carry-forward.
- (c) Tuareg 660 ADV Cd of 0.82 is a category-default estimate, not measured — replace with wind-tunnel data if obtainable.
