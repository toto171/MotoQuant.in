# Catalog Expansion Report — 2026-05-07 (A1 Agent Pass)

**Session:** autonomous-ops A1 catalog-expansion agent  
**Date:** 2026-05-07  
**Bikes added:** 3  
**Catalog total:** 338 → 341 bikes  

---

## Bikes Added

### 1. Bajaj Pulsar NS160 (2017-2024)
- **Engine:** 160.3cc DTS-i oil-cooled SOHC single, 15.7 PS @ 8750 rpm, 14.6 Nm @ 6750 rpm
- **Gearbox:** 5-speed [2.733, 1.556, 1.158, 0.905, 0.737], F14/R49, 428 chain
- **Dry mass:** 138 kg (144 kg kerb − 6 kg fuel)
- **Smoke-sim ET:** 18.051s @ 119.7 km/h trap ✓
- **Cluster:** entry-150-200; 18.05s within known bias band (+0.255s slow per CLAUDE.md cluster metrics)
- **Validator:** valid=True, 0 errors, 2 cosmetic tire-format warnings (Indian `80/100-17` notation)
- **Sources:** Bajaj Auto official spec page (bajaj-auto.com/ns160); BikeWale spec table; Bajaj NS160 service manual Doc 45-3-21 (2021)

### 2. Honda CB Hornet 160R (2016-2022)
- **Engine:** 162.71cc oil-cooled SOHC single, 15.06 PS @ 8500 rpm, 14.52 Nm @ 5500 rpm
- **Gearbox:** 5-speed [3.308, 1.812, 1.227, 0.969, 0.786], F15/R44, 428 chain
- **Dry mass:** 127 kg (137 kg kerb − 10 kg fuel)
- **Smoke-sim ET:** 18.116s @ 119.0 km/h trap ✓
- **Cluster:** entry-150-200; 18.12s within known bias band
- **Validator:** valid=True, 0 errors, 2 cosmetic tire-format warnings (Indian `100/80-17` notation)
- **Sources:** Honda India official spec page (hondamotorcycle.co.in); Honda India service manual 00X38-K1R-6400 (2018); BikeWale spec table; ZigWheels 2020 long-term review

### 3. Hero Xtreme 250R (2024-2025)
- **Engine:** 249.1cc liquid-cooled DOHC single, 25.31 PS @ 9000 rpm, 22.0 Nm @ 7250 rpm
- **Gearbox:** 6-speed [2.846, 1.765, 1.333, 1.087, 0.931, 0.826], F15/R46, 520 chain
- **Dry mass:** 148 kg (157 kg kerb − 9 kg fuel)
- **Smoke-sim ET:** 15.844s @ 137.0 km/h trap ✓
- **Cluster:** entry-200-300; 15.84s within known bias band (+0.211s slow per CLAUDE.md cluster metrics)
- **Validator:** valid=True, 0 errors, 2 cosmetic tire-format warnings (Indian `110/70-17` notation)
- **Sources:** Hero MotoCorp official spec page (heromotocorp.com/xtreme-250r); Hero press kit December 2023; Autocar India first ride January 2024; MCN India launch coverage

---

## Validation Gates

| Gate | Result |
|---|---|
| `test_scraper.py` (80 tests) | ✓ 80 passed |
| `test_validation.py` + `test_two_stroke.py` + `test_compatibility.py` | ✓ 171 passed total |
| K5 baseline | ✓ 10.0334s (Δ +0.0000s) |
| R1 baseline | ✓ 10.2859s (Δ +0.0000s) |
| Hayabusa baseline | ✓ 10.4712s (Δ +0.0000s) |
| All 3 new bikes ET ∈ [4.0, 26.0]s | ✓ |
| All 3 new bikes trap ∈ [40, 400] km/h | ✓ |

---

## Rationale for Selection

All three bikes fill genuine Indian-market catalog gaps relevant to the entry-class drag scene:

- **NS160** is Bajaj's bestselling 160cc naked and the most common budget drag entry-class bike in Tier-2/Tier-3 Indian cities. Only the 6-speed NS200 was in catalog; the NS160 uses a completely separate 5-speed gearbox.
- **CB Hornet 160R** is Honda India's premium 160cc naked (2016-2022). It was absent despite the SP 160 (2024+) being present — the earlier Hornet 160R generation is common at drag events.
- **Hero Xtreme 250R** is Hero MotoCorp's brand-new 250cc premium model (launched Dec 2023), completing coverage of Hero's performance lineup alongside the Xtreme 200S 4V added on 2026-05-04.

---

## Notes

Tire-format warnings are cosmetic: Indian-market bikes use `100/80-17` (bias-ply) notation rather than the `100/80R17` radial form the validator expects. All three bikes pass `is_valid=True`. This is the same carry-forward from the Xtreme 200S 4V session — broadening the validator to accept Indian bias-ply notation is still an open item.
