# Catalog Expansion — 2026-05-21 (Thursday, Catalog A1 twelfth pass)

## Bikes added (3)

1. **Triumph Bonneville Bobber 1200 (2017-2024)** — 1200cc HT parallel twin, 76.9 hp / 106 Nm, 228 kg dry, 6-speed F18/R44 525 chain. Solo-seat hardtail-look cruiser. Cluster: mid-twin 700-1300 cruiser.
2. **Moto Guzzi V100 Mandello S (2022-2026)** — 1042cc transverse-V twin (new CARC engine), 113 hp / 105 Nm, 215 kg dry, 6-speed shaft drive. First production motorcycle with adaptive aerodynamics (active winglets). Cluster: mid-twin sport-tourer.
3. **Aprilia Shiver 900 (2017-2024)** — 896cc 90° V-twin, 95 hp / 90 Nm, 198 kg dry, 6-speed F16/R44 525 chain. Aprilia's first ride-by-wire production bike (lineage from Shiver 750 / Dorsoduro 900). Cluster: litre-naked 700-1000.

## Source quality

Each spec cites manufacturer press kit + at least 2 independent magazine reviews (MCN, Cycle World, Visordown, BikeSocial, RideApart) + service-manual gear cassette verification. Mass is dry (not wet — kerb-fuel-fluids conversion documented inline).

## Smoke-sim results

| Bike                    | Sim ET    | Trap         | Bias band assessment |
|-------------------------|-----------|--------------|----------------------|
| Bonneville Bobber 1200  | 12.808 s  | 178.9 km/h   | Cycle World 2017 reports 12.5s; sim +0.31s within cruiser cluster bias |
| V100 Mandello S         | 11.552 s  | 210.3 km/h   | MCN test 2022 ~11.4-11.6s; sim within ±0.15s |
| Shiver 900              | 11.512 s  | 200.7 km/h   | Visordown 2018 comparison ~11.3s; sim +0.21s litre-naked band |

## Validation gates

- `python3 -m pytest tests/test_scraper.py` — **80/80 passed** in 1.42s
- `validate_spec()` on all 3: **valid=True** (Bobber: 2 cosmetic Indian-bias-ply tire warnings, same pattern as RTR 200)
- **Reference baselines locked exactly: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s** (Δ +0.0000 each, pre- and post-DB-reseed)
- ET in [4.0, 26.0]s ✓; trap in [40, 400] km/h ✓ for all 3

## DB re-seed

- Pre-import: 637 bike_models rows
- Post-import: 673 bike_models rows (+36 new — our 3 plus prior unseeded entries from earlier today's passes)
- Importer reported `Imported: 37 / Errors: 435 / Total: 673` — the 435 errors are the documented WS-A year-suffix-matcher idempotency hits from CLAUDE.md May-4 hygiene, NOT real failures. All 3 of our new bikes landed cleanly (IDs 3125 / 3126 / 3127). Fix-proper (already a carry-forward) is in `bike_repo.create_model` — strip `(YYYY-YYYY)` suffix before exact match.

## Files touched

- `motoquant/scraper/known_bikes_extended.py` (8909 → 9120 lines; +3 spec_from_dict blocks + 3 ALL_KNOWN_BIKES entries)
- `motoquant.db` (re-seeded; 637 → 673 bike_models)
- `reports/catalog_expansion_2026-05-21_twelfth_pass.md` (this file)

## Open carry-forward

(a) `bike_repo.create_model` year-suffix matcher fix (May-4 carry-forward, unchanged). (b) Scraper validator should accept Indian bias-ply tire notation (`100/90-19`, `150/80-16`) — currently 2 cosmetic warnings on the Bobber. (c) Source-vs-DB drift: catalog source now has 441 unique `spec_from_dict` blocks; DB at 673 (incl. prior-session entries + reference bikes). User to audit drift in next sync window.
