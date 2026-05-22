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
