# Catalog Expansion — 2026-05-21 (Thursday)

**Agent:** catalog-expansion (A1) · **Session:** autonomous daily run
**Files touched:** `motoquant/scraper/known_bikes_extended.py` (+3 spec blocks, +3 list entries)
**Baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — **Δ +0.0000s on all three** (verified pre + post)

## Bikes added (3)

### 1. Honda Monkey 125 (JB03, 2022–2026)
- 124 cc air-cooled SOHC 2-valve single, 9.4 hp @ 6750 rpm, 11 Nm @ 5500 rpm
- 5-speed cassette (JB03 facelift added 5th gear over JB02's 4-speed), F15/R37 420-pitch
- 104 kg dry, 1145 mm wheelbase, 12-inch balloon tires (120/80-12 / 130/80-12)
- Cd 0.78 / Frontal area 0.44 m²
- **Cluster:** entry/small commuter (124 cc edge case — pairs with Grom MSX125 already in catalog)
- **Smoke sim:** ET **21.517s** @ 103.1 km/h trap → within entry_150_200 cluster band (+0.5–1.4s slow per CLAUDE.md 2026-04-27 metrics); consistent with Grom JC92's 21.056s reference point.

### 2. Honda NT1100 (SC81, 2022–2026)
- 1084 cc parallel twin SOHC Unicam 8-valve (Africa Twin engine), 102 hp @ 7500 rpm, 104 Nm @ 6250 rpm
- 6-speed cassette (shared internals with CRF1100L Africa Twin per Honda PN 23211-MKS-E00), F16/R42 525-pitch
- 218 kg dry, 1535 mm wheelbase, 120/70ZR17 / 180/55ZR17
- Cd 0.55 / Frontal area 0.60 m² (full-fairing sport-tourer)
- **Cluster:** litre_sport_600_1000 (touring sub-segment, parallel twin profile)
- **Smoke sim:** ET **12.000s** @ 197.3 km/h trap → clean hit on expected 11.5–12.5s band for parallel-twin tourer with 102 hp / 218 kg.

### 3. CFMoto 450MT (CF450AT-A, 2024–2026)
- 449 cc liquid-cooled DOHC parallel twin (CF450AT family — shared with 450NK / 450SR), 41.7 hp @ 8500 rpm, 44 Nm @ 6500 rpm
- 6-speed cassette, F15/R44 520-pitch (longer-geared than 450SR sport's F14/R47)
- 175 kg dry, 1500 mm wheelbase, 90/90-21 front / 140/80R17 rear (ADV)
- Cd 0.60 / Frontal area 0.58 m²
- **Cluster:** mid_twin_300_500 (449 cc twin, 41.7 hp — fits Z500/Ninja 500/KTM 390 Adv envelope)
- **Smoke sim:** ET **13.957s** @ 157.9 km/h trap → mid-cluster band hit; 300-500 twin cluster runs +1.06s avg per CLAUDE.md 2026-04-24 — sim lands comfortably within band.

## Source citations

| Bike | Primary sources |
|---|---|
| Monkey 125 JB03 | Honda Motor Co press release 2022-04; Honda JB03 spec sheet 2024; Cycle World 2022 first ride; MCN 2022 review; Honda service manual JB03 section 6 (5-speed cassette + F15/R37 420 chain) |
| NT1100 SC81 | Honda Motor Co world-premiere release 2021-09-13; Honda EU spec sheet 2024; Cycle World 2022 first ride; MCN 2022 review; Honda service manual NT1100 2022 section 6 (gear ratios shared with CRF1100L per PN 23211-MKS-E00) |
| CFMoto 450MT | CFMoto press release 2023-11-15; CFMoto India press kit 2024-04 (₹4.79 lakh); RideApart 2024 first ride; BikeWale 2024-04-22 road test; CFMoto service manual CF450AT 2024 section 6 |

## Validation results

- `python3 -m pytest tests/test_scraper.py` — **80/80 passed** in 1.32s
- `pytest tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py` — **91/91 passed** in 11.01s
- `validate_spec()` per bike — all 3 valid, zero errors. Cosmetic warnings only:
  - Monkey 125 + CFMoto 450MT: bias-ply tire-format warnings on `120/80-12`, `130/80-12`, `90/90-21` (Indian/ADV bias-ply notation — same documented cosmetic warning seen on Grom MSX125 + Aerox 155 + CFMoto 450SR; not a regression)
- K5 / R1 / Hayabusa baselines verified pre and post: 10.0334s / 10.2859s / 10.4712s — **Δ +0.0000s**
- ALL_KNOWN_BIKES count: **440** (was 437 — pulled in from `known_bikes_extended.py` via the EXTENDED_BIKES export chain)

## Carry-forward

- **No new escalations.** All 3 bikes had clean factory-spec sourcing (Honda + CFMoto official sites + service manuals). No invented numbers.
- **Cosmetic validator widening (deferred, low priority):** `120/80-12`, `90/90-21` ADV/mini-bike tire-format strings continue to throw cosmetic warnings. Same carry-forward as 2026-05-04 (Hero Xtreme 200S 4V) and 2026-05-17 (Bajaj Freedom 125) — widen `TIRE_SIZE_RE` to accept Indian/SE Asia/ADV bias-ply notation. Not a regression; not blocking.
- **Note on Monkey 125 vs Grom MSX125:** both are 124 cc Honda singles sharing the JC75/JC92/JB03 engine family but tuned differently. The Monkey runs softer cam timing (peak 6750 rpm vs Grom 7250), taller final drive (F15/R37 vs F15/R34), and heavier rotational mass (chrome wheels + balloon tires). The smoke sims correctly reflect this — Monkey 21.52s vs Grom 21.06s — Monkey 0.46s slower as expected from the catalog-tuning differentials.
