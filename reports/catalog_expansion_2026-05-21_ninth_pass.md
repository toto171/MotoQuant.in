# Catalog Expansion Report — 2026-05-21 (Thursday — Ninth Pass)

## Bikes added (3)

1. **KTM 690 SMC R (2019-2024)** — Supermoto, single-cylinder LC4 platform
   - 693cc DOHC single, 74 hp @ 8000 rpm / 73.5 Nm @ 6500 rpm
   - 147 kg dry / 158 kg wet, 6-speed, F15/R45 520 chain
   - Cluster: mid_500_700 (single-engine 700-class adjacent to parallel-twin cluster)
   - **Smoke sim ET: 11.803s @ 188.0 km/h trap** — within reasonable bounds for a 74hp supermoto with high Cd
   - Sources: KTM 2019 press kit, MCN 2019 first ride, Cycle World 2019 first test

2. **Husqvarna 701 Supermoto (2016-2023)** — Sister bike to KTM 690 SMC R
   - 692.7cc SOHC single, 74 hp @ 8500 rpm / 72 Nm @ 6750 rpm (peaks 500 rpm higher than KTM)
   - 145 kg dry, 6-speed, F16/R42 520 chain (Husky taller geometry)
   - Cluster: mid_500_700
   - **Smoke sim ET: 11.764s @ 189.0 km/h trap** — 39 ms quicker than KTM, consistent with lighter chassis + taller gearing
   - Sources: Husqvarna press kit 2016 701 SM, MCN 2016 first ride, Visordown 2017 review

3. **Suzuki V-Strom SX 250 (2022-2026)** — Indian-market small ADV
   - 249cc air/oil-cooled SOHC single, 26.1 hp @ 9300 rpm / 22.2 Nm @ 7300 rpm
   - 155 kg dry, 5-speed, F14/R44 520 chain
   - Cluster: entry_200_300 (sub-30hp small ADV — sits adjacent to KTM 250 Adv + Himalayan 411)
   - **Smoke sim ET: 16.030s @ 133.7 km/h trap** — in the documented entry-200-300 cluster band
   - Sources: Suzuki India press release 2022, BikeWale spec sheet, BikeDekho review, Indian Autos long-term

## Validation

- `python3 -m pytest tests/test_scraper.py` — **80 passed**, 0 failed, 566 deprecation warnings (pre-existing `datetime.utcnow()` usage in `spec.py:101` — not introduced by this change)
- All 3 new bikes pass `spec_from_dict` validator; finished_quarter=True; ETs in [4.0, 26.0]s; traps in [40, 400] km/h
- **Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s on all three**

## DB re-seed

Ran `python3 -m motoquant.run --db motoquant.db import --known-bikes`:
- Imported: 37 (includes the 3 new bikes + a handful of other fresh entries from latest source pass)
- Errors: 427 (idempotency mismatches per the documented WS-A April 27 hygiene — pre-existing rows in `bike_models` with year-suffix mismatches against the lenient upsert fallback. NOT a regression from this session.)
- Total bikes in DB: 599
- Tire fitments rebuilt: 1126

Direct DB verification confirmed:
- 690 SMC R: row 2184 (manufacturer_id=8 KTM)
- 701 Supermoto: row 2185 (manufacturer_id=13 Husqvarna)
- V-Strom SX 250 (2022-2026): row 2186 (manufacturer_id=1 Suzuki) — coexists with 5 prior duplicate rows under year-range (2022-2024) per the same WS-A year-suffix matcher gap

## Carry-forward

- **WS-A year-suffix matcher** still produces V-Strom SX 250 duplicates across import passes. Same fix as previously documented: normalize `model_name` in `bike_repo.create_model` upsert (strip `(YYYY-YYYY)` suffix). Not in scope for this catalog session.
- All 3 new bikes available at `/api/bikes` post-Railway redeploy.

## Files touched

- `motoquant/scraper/known_bikes_extended.py` — appended 3 specs + 3 list entries
- `motoquant.db` — 37 fresh bike rows inserted + tire fitments rebuilt
- `reports/catalog_expansion_2026-05-21_ninth_pass.md` — this report
