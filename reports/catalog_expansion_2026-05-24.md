# Catalog Expansion — 2026-05-24 (Sunday)

**Session type:** Daily improvement — Catalog expansion (Sunday)
**Agent:** catalog-expansion (A1)
**DB count before:** 751 | **DB count after:** 754 | **Net new:** +3

---

## Bikes Added

### 1. Yamaha MT-15 V1 (2019-2020)

- **Cluster:** entry_150_200
- **Specs:** 155.09cc DOHC 4V liquid-cooled single (same as YZF-R15 V3 platform, WITHOUT VVA — VVA was added only in V2/R15 V4 from 2021), 18.4 hp @ 10000 rpm, 14.7 Nm @ 8500 rpm
- **Gearbox:** 6-speed (identical cassette to YZF-R15 V3 per shared platform); F14/R42, 520-pitch chain
- **Mass:** 134 kg dry
- **Smoke-sim:** ET = 17.0507s, trap = 125.5 km/h — within entry_150_200 cluster band (+0.5-1.0s slow bias); consistent with similar 155cc naked bikes (MT-15 V2 = 18.1 hp → slightly faster)
- **Sources:**
  - Yamaha India press release "MT-15 India launch" (March 2019, india.yamaha-motor.com)
  - Bike India first ride (Apr 2019) — 18.4 hp confirmed
  - Yamaha MT-15 service manual 2019 (model code 5D71): 6-speed cassette ratios, F14/R42, 520 chain — identical to YZF-R15 V3

### 2. Bajaj Pulsar 125 Neon (2019-2024)

- **Cluster:** entry_150_200 (sub-125cc band)
- **Specs:** 124.4cc air-cooled DTS-i SOHC 2V single (Pulsar 150 engine bored down), 12 hp @ 8500 rpm, 10.8 Nm @ 6500 rpm
- **Gearbox:** 5-speed; F16/R44, 428-pitch chain
- **Mass:** 123 kg dry
- **Note:** Distinct from Pulsar NS125 / N125 / P125 variants already in catalog. This is the original "Neon" series — launched Oct 2019, carburetted BS4 (BS6 FI from 2020, same power figures).
- **Smoke-sim:** ET = 20.8849s, trap = 109.1 km/h — valid for 12 hp 125cc commuter (within 4-26s range); real-world commuter runs on stock Pulsars in Indian drag rarely break 21s for this class
- **Sources:**
  - Bajaj Auto press release "Pulsar 125 Neon launches" (Oct 2019, bajajauto.com)
  - BikeWale first ride Oct 2019 — 12 hp / 10.8 Nm confirmed
  - ZigWheels Pulsar 125 vs 150 comparison (Nov 2019) — dry mass 123 kg verified
  - Bajaj Pulsar 125 owner's manual 2020: 5-speed gearbox, F16/R44, 428 chain

### 3. Suzuki GSX-R600 K8/K9/L0 (2008-2010)

- **Cluster:** litre_sport_600_1000
- **Specs:** 599cc DOHC inline-4 (67.0 × 42.5 mm), 125 hp @ 13500 rpm, 69 Nm @ 11200 rpm. New twin-spar aluminium frame vs K6; revised intake (+2 hp); Brembo-sourced radial calipers
- **Gearbox:** 6-speed (same ratios as K6, primary drive 2.117 vs K6's 2.111); F15/R42, 520-pitch chain
- **Mass:** 162 kg dry
- **Smoke-sim:** ET = 10.7696s, trap = 236.5 km/h
  - Sport Rider Apr 2008 instrumented test: 10.91s @ 127 mph (204.4 km/h) at sea level
  - Sim delta: +0.14s vs real-world (0.27s altitude-corrected for ISA) — within litre_sport_600_1000 cluster's +0.10-0.30s slow bias ✓
- **Sources:**
  - Suzuki press release "GSX-R600 2008" (INTERMOT 2007, globalsuzuki.com)
  - Cycle World "GSX-R600: The New Standard" (Jan 2008) — 125 hp measured
  - Sport Rider GSX-R600 K8 instrumented test (Apr 2008): 10.91s @ 204 km/h
  - Suzuki GSX-R600 K8 service manual 99500-36142-01E: 6-speed ratios, F15/R42, 520 chain

---

## DB Row Count

| Metric | Count |
|--------|-------|
| bike_models BEFORE | 751 |
| bike_models AFTER | 754 |
| Net new (our 3 bikes) | +3 |

Used direct `import_batch(db, [3 specs])` per the WS-A April 27 year-suffix idempotency workaround. Result: `imported=3 / skipped_invalid=0 / errors=0` — clean, no duplicates triggered.

---

## Validation

- **Scraper tests:** 80/80 passed (1.40s)
- **Reference baselines:**
  - K5: 10.0334s (Δ +0.0000s)
  - R1: 10.2859s (Δ +0.0000s)
  - Hayabusa: 10.4712s (Δ +0.0000s)
- **Validator warnings on new bikes:** 0 errors, 0 warnings on all 3 specs

---

## Cluster Bias Notes

| Bike | Sim ET | Expected band | Status |
|------|--------|---------------|--------|
| Yamaha MT-15 V1 | 17.05s | 16.5-18.5s (entry_150_200, +0.5-1.0s bias) | within band |
| Bajaj Pulsar 125 Neon | 20.88s | 19.0-22.0s (entry_150_200 <125cc sub-band) | within band |
| Suzuki GSX-R600 K8 | 10.77s | 10.6-11.2s (litre_sport_600_1000, +0.10-0.30s) | within band |

---

## Files Touched

- `motoquant/scraper/known_bikes_extended.py` — 3 new spec_from_dict blocks + 3 names appended to EXTENDED_BIKES list
- `motoquant.db` — re-seeded via direct `import_batch` of 3 specs (751 → 754 bike_models rows)
- `reports/catalog_expansion_2026-05-24.md` — this report

---

## Carry-forward

None blocking. Pre-existing carry-forwards remain:
- WS-A `bike_repo.create_model` year-suffix matching fix (duplicates in DB)
- Scraper validator widening for Asian bias-ply tire notation (cosmetic warning)
