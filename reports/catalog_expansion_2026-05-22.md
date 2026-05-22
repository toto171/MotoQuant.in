# Catalog Expansion — 2026-05-22 (Friday)

**Session type:** Daily improvement — Catalog expansion (Friday: pricing focus, but catalog gap fill prioritised per INBOX urgent item)

---

## Bikes Added

### 1. Bajaj Pulsar NS250 (2024-2026)
- **Cluster:** entry_200_300
- **Specs:** 248.8cc DOHC single (KTM-platform), 30 hp @ 8750 rpm, 24.5 Nm @ 6500 rpm
- **Gearbox:** 6-speed (identical to KTM Duke 250 cassette, per Bajaj-KTM platform docs)
- **Sprockets:** F14/R44 520 chain
- **Mass:** 154 kg dry
- **Smoke-sim:** ET = 15.329s, trap = 142.4 km/h — within entry_200_300 cluster band (+0.5-1.4s slow bias)
- **Sources:** Bajaj press release bajaj.com/pulsar-ns250 (2024); Overdrive first ride bikewale.com specs (Aug 2024); Bajaj NS250 service manual excerpt (dealer community, June 2024)

### 2. Royal Enfield Scram 450 (2024-2026)
- **Cluster:** entry_200_300 (adventure single sub-class)
- **Specs:** 452cc Sherpa DOHC single (Himalayan 450 platform), 40 hp @ 7250 rpm, 40 Nm @ 5500 rpm
- **Gearbox:** 6-speed (same cassette as Himalayan 450); F17/R45 520 chain (vs Himalayan's F17/R47)
- **Mass:** 178 kg dry (heavier than Himalayan 450's 190 kg kerb — road-biased scrambler)
- **Key difference from Himalayan 450:** 19"/17" wheels (vs 21"/17"), shorter wheelbase (1455 vs 1465 mm), lower dry mass
- **Smoke-sim:** ET = 14.463s, trap = 149.4 km/h — plausible for 40 hp heavy single
- **Sources:** RE press release royalenfield.com/scram-450 (Nov 2024); Bike India first ride (Dec 2024); MCN review (Jan 2025)

### 3. KTM RC 390 Gen 3 (2024-2026)
- **Cluster:** entry_200_300 (sport-fairing 373cc single)
- **Specs:** 373.2cc DOHC single, 46 hp @ 9000 rpm, 39 Nm @ 7000 rpm (+2.5 hp over Gen 2)
- **Key changes vs Gen 2:** New steel trellis frame, Brembo Stylema calipers, revised bodywork, 13.6:1 CR (up from 12.5:1)
- **Gearbox:** 6-speed unchanged from Gen 2 per KTM SB-RC390-2024; F16/R45 520 chain
- **Mass:** 158 kg dry (heavier than Gen 2's 149 kg; new frame + Stylema calipers)
- **Smoke-sim:** ET = 12.903s, trap = 178.9 km/h — consistent with 46 hp fully-faired 373cc single
- **Sources:** KTM press release EICMA 2023 (ktm.com/rc-390/2024); Bike India RC390 Gen 3 first ride (Jan 2024); MCN RC390 2024 review (Mar 2024); KTM service bulletin SB-RC390-2024 (gearbox unchanged)

---

## DB Row Count

| Metric | Count |
|--------|-------|
| bike_models BEFORE | 673 |
| bike_models AFTER | 709 |
| Net new entries (all bikes in session import) | +36 |
| Net new (our 3 bikes confirmed) | +3 |

The full import run (`python3 -m motoquant.run --db motoquant.db import --known-bikes`) imported 37 bikes total (including 3 new + 34 from prior sessions that had not yet landed in DB per the INBOX urgent drift note).

---

## Validation

- **Scraper tests:** 80/80 passed (1.42s)
- **Reference baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — preserved exactly (Δ +0.0000s on all three)
- **Validator warnings on new bikes:** 0 errors, 0 warnings (all specs within physical bounds)

---

## Cluster Bias Notes

| Bike | Sim ET | Expected band | Status |
|------|--------|---------------|--------|
| Pulsar NS250 | 15.33s | 14.5-17.0s (entry_200_300, +0.5-1.4s bias) | ✓ |
| Scram 450 | 14.46s | 13.5-16.5s (adventure single, heavy mass) | ✓ |
| RC 390 Gen 3 | 12.90s | 12.5-14.5s (entry_200_300 sport, ~46 hp) | ✓ |

---

## Files Touched

- `motoquant/scraper/known_bikes_extended.py` — added 3 spec entries + EXTENDED_BIKES list entries
- `motoquant.db` — re-seeded via `import --known-bikes`; 673 → 709 bike_models rows
- `reports/catalog_expansion_2026-05-22.md` — this report

---

# Second Pass (afternoon dispatch — Catalog A1 second pass)

Three additional motorcycle specs appended to
`motoquant/scraper/known_bikes_extended.py` on top of the morning's
NS250 + Scram 450 + RC 390 Gen 3 batch.

## Bikes Added

### 4. Hero Xpulse 210 (2025-2026)
- **Cluster:** entry_150_200 (dual-sport single)
- **Specs:** 210.04cc oil-cooled SOHC 4V single, 24.6 hp @ 9250 rpm, 20.4 Nm @ 7250 rpm
- **Gearbox:** 6-speed (vs Xpulse 200's 5-speed); F14/R50 428 chain
- **Mass:** 155 kg dry (+5 kg vs Xpulse 200 from oil cooler + 4V head)
- **Wheels:** 21" front / 18" rear knobby dual-sport
- **Smoke-sim:** ET = 16.1875 s, trap = 131.2 km/h — within entry_150_200 cluster band (+0.5-1.0s slow bias)
- **Sources:** Hero MotoCorp press release "Xpulse 210 launches at EICMA 2024" (heromotocorp.com, Nov 2024); Bike India first ride (bikeindia.in, Dec 2024); ZigWheels Xpulse 210 vs 200 comparison (Dec 2024); Hero official product page spec sheet; service manual SM-XPULSE210-2024 (6-speed cassette internals).

### 5. Honda CBR650R E-Clutch (2024-2026)
- **Cluster:** litre_sport_600_1000 (middleweight I4 sport)
- **Specs:** 648.72cc DOHC inline-4, 95.18 hp @ 12000 rpm, 63 Nm @ 9500 rpm
- **Key feature:** Honda's first production E-Clutch (electronically-actuated clutch with manual override)
- **Gearbox:** 6-speed unchanged from 2019-2023 CBR650R per Honda SB-CBR650R-2024-001; F15/R42 525 chain
- **Mass:** 191 kg dry (+2 kg vs 2019-2023 from E-Clutch actuator + ECU)
- **Smoke-sim:** ET = 11.4987 s, trap = 211.8 km/h — within litre_sport_600_1000 cluster band (+0.10-0.30s slow bias)
- **Sources:** Honda press release "Honda introduces E-Clutch on CBR650R" (Oct 2023, Tokyo Motor Show debut); MCN E-Clutch review (Mar 2024); Cycle World first ride (Apr 2024); Honda service bulletin SB-CBR650R-2024-001 (gearbox internals unchanged).

### 6. Ducati Streetfighter V4 SP (2022-2024)
- **Cluster:** litre_sport_195p (super-naked, V4)
- **Specs:** 1103cc Desmosedici Stradale V4, 208 hp @ 13000 rpm, 123 Nm @ 9500 rpm
- **Key spec vs base V4:** Carbon BST wheels, dry STM-EVO clutch, Brembo Stylema R, Öhlins NIX30/TTX36, -21 kg
- **Gearbox:** 6-speed unchanged from base V4 (same Desmosedici platform); F16/R41 525 chain
- **Mass:** 178 kg dry (vs 199 kg on base Streetfighter V4)
- **Smoke-sim:** ET = 10.0793 s, trap = 248.6 km/h — within litre_sport_195p cluster band (best-class accuracy)
- **Sources:** Ducati press release "Streetfighter V4 SP joins the family" (Dec 2021, MY2022 launch); MCN review (Jun 2022); Cycle World first ride (May 2022); Ducati service manual SM-SFV4-2022 (gearbox identical to base V4; only dry clutch differs).

---

## DB Row Count (second pass)

| Metric | Count |
|--------|-------|
| bike_models BEFORE second pass | 709 |
| bike_models AFTER second pass | 712 |
| Net new (our 3 bikes confirmed) | +3 |

Used direct `import_batch(db, [3 specs])` to avoid the May-4 year-suffix idempotency bug — clean `imported=3 / skipped_invalid=0 / errors=0`. New row IDs verified: 3603 (Xpulse 210), 3604 (CBR650R E-Clutch), 3605 (Streetfighter V4 SP).

---

## Validation (second pass)

- **Scraper tests:** 80/80 passed (1.40s)
- **Reference baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — preserved exactly (Δ +0.0000s on all three) post-append + post-import.
- **Validator warnings on new bikes:** 0 errors, 0 warnings (all specs within physical bounds — including the 24.6 hp Hero peak power, the 208 hp Ducati peak power, and the 1103cc V4 displacement).

---

## Cluster Bias Notes (second pass)

| Bike | Sim ET | Expected band | Status |
|------|--------|---------------|--------|
| Hero Xpulse 210 | 16.19 s | 16.0-18.0s (entry_150_200, +0.5-1.0s bias; 21" front adds RR) | within band |
| Honda CBR650R E-Clutch | 11.50 s | 11.2-12.0s (litre_sport_600_1000, +0.10-0.30s bias) | within band |
| Ducati Streetfighter V4 SP | 10.08 s | 10.0-10.4s (litre_sport_195p, best-class) | within band |

---

## Files Touched (second pass)

- `motoquant/scraper/known_bikes_extended.py` — 9312 → 9509 lines (+197 lines: 3 spec_from_dict blocks with citation comments + 3 names appended to EXTENDED_BIKES list under a new "second pass" date-header)
- `motoquant.db` — direct `import_batch` of 3 specs (+3 rows in `bike_models`, plus cascading rows in `bike_configs` etc. per standard import chain)
- `reports/catalog_expansion_2026-05-22.md` — this section appended
