# Catalog Expansion — 2026-05-17 (Sunday, ninth pass)

## Summary
Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`,
extending coverage of (a) flagship cruiser segment, (b) the latest Royal Enfield
launch on the established 650-twin platform, and (c) a key middleweight
adventure-bike gap. Catalog count: 373 → **376** bikes.

## Bikes added

| Bike | Years | Cluster | Sim ET | Trap (km/h) | Real-world reference |
|---|---|---|---|---|---|
| BMW R 18 | 2020-2026 | `cruiser_1300p` | 13.385s | 168.5 | Cycle World 2020 ~13.4s @ 161 km/h ✓ |
| Royal Enfield Classic 650 | 2025-2026 | `mid_twin_500_700` | 14.252s | 155.3 | Interceptor 650 baseline ~13.5-14.5s ✓ |
| KTM 890 Adventure R | 2021-2024 | `other` (ADV) | 11.830s | 199.5 | MCN 2021 ~11.8s ✓ |

All 3 sim ETs land inside the expected cluster bias bands. K5/R1/Hayabusa
reference baselines preserved EXACTLY (`Δ +0.0000s` on all three).

## Spec sources (high-confidence)

**BMW R 18** — BMW Motorrad press kit 2020-04-03 (T0307956EN), official
spec page bmwmotorrad.com/en/models/heritage/r18/r18/specs, MCN 2020 review,
Cycle World 2020 first-ride. Gear ratios from BMW R 18 service manual (K34).
Shaft drive (paralever); routes to `front_sprocket=0, rear_sprocket=0`.

**Royal Enfield Classic 650** — Royal Enfield EICMA 2024 press release
(launch 2024-11-05), official spec page royalenfield.com/in/en/motorcycles/
classic-650/specifications/, Autocar India 2025 first-ride, MCN 2025 review.
Engine + transmission verified shared with Interceptor 650 (UCE 648 cc
platform) via Tier-1 gear_ratios.py lookup. F15/R45 525 chain.

**KTM 890 Adventure R** — KTM press release 2020-12-08, official spec
page ktm.com/en-us/motorcycles/travel/890-adventure-r, MCN 2021 review,
Cycle World 2021 first-ride, RevZilla 2024 review. Engine + gearbox shared
with 890 Duke R (Tier-1 entry `duke 890`) — same PASC slipper cassette,
F15/R45 520 chain (45T rear vs Duke R's 42T for taller off-road gearing).

## Engineering changes

- `motoquant/scraper/importer.py` — extended `_BMW_SHAFT_MODELS` to include
  `R 18`, `R18`, `R 1300`, `R1300`. `R 1300` was missing despite the
  R 1300 GS already shipping in the catalog (existing entry hard-coded
  `chain_pitch=None` on the spec, but the inference rule didn't cover it).
- `motoquant/scraper/known_bikes_extended.py` — appended 3 spec blocks +
  3 list entries under "ninth pass" comment.

## Validation gates

- `python3 -m pytest tests/test_scraper.py` → **80 passed**
- `python3 -m pytest tests/test_scraper.py tests/test_two_stroke.py tests/test_compatibility.py` → **140 passed**
- Baselines (asserts `< 0.001s` drift):
  - K5: 10.0334s (target 10.0334, drift 0.0000s)
  - R1: 10.2859s (target 10.2859, drift 0.0000s)
  - Hayabusa: 10.4712s (target 10.4712, drift 0.0000s)
- All 3 new bikes pass ET ∈ [4.0, 26.0]s and trap ∈ [40, 400] km/h gates.

## Open carry-forward / warnings

- None. Zero scraper validator warnings on the new entries.
- No new dispatch escalations.
