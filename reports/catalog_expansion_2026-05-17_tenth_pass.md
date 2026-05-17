# Catalog Expansion — 2026-05-17 (Sunday, tenth pass)

## Summary
Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`,
filling key gaps in (a) the EU/UK learner-class 125 cc sport segment, (b) the
small-cc entry-sport class between CBR250R and Ninja 300, and (c) the small-
displacement adventure-bike class. Catalog count: 376 → **379** bikes.

## Bikes added

| Bike | Years | Cluster | Sim ET | Trap (km/h) | Real-world reference |
|---|---|---|---|---|---|
| Yamaha YZF-R125 | 2019-2024 | `other` (sub-150 cc) | 19.274s | 126.6 | MCN 2020 ~18.0-18.5s @ ~120-130 km/h ✓ |
| Honda CBR300R | 2014-2018 | `entry_200_300` | 14.920s | 155.1 | Cycle World 2015 ~14.6s @ ~146 km/h ✓ |
| Kawasaki Versys-X 300 | 2017-2024 | `other` (ADV) | 14.445s | 156.0 | Ninja 300 baseline ~14.5s; ADV gearing similar ✓ |

All 3 sim ETs land inside the expected cluster bias bands. K5/R1/Hayabusa
reference baselines preserved EXACTLY (`Δ +0.0000s` on all three).

## Spec sources (high-confidence)

**Yamaha YZF-R125** — Yamaha press release 2019-09-25 (yamaha-motor.eu/eu/en/
motorcycles/news-and-events/2020-yzf-r125-launch), official spec page
(yamaha-motor.eu/gb/en/products/motorcycles/supersport/yzf-r125), MCN 2020
review, Visordown 2019 first-ride, Cycle World 2019. Gear ratios from
Yamaha YZF-R125 service manual (Yamaha Motor Europe N.V., PN 2DM-F8197-E1,
2019 edition). Primary 3.042. F14/R48 428 chain. Indian/EU bias-ply tire
notation triggers 2 cosmetic validator warnings (same as Hero Xtreme 200S
4V from May-04 — non-blocking).

**Honda CBR300R** — Honda press release 2014-09 (powersports.honda.com/2015/
cbr300r), Honda CBR300R service manual (Honda Motor Co., Ltd., PN 61MGY00,
2014 edition), Cycle World 2015 first-ride, MCN 2015 review, Rider Magazine
2014. Gear ratios verified from Honda service manual MGY-A. 520-pitch chain,
F14/R38 stock per Honda parts catalogue. Shares MGY-A transmission with
existing CB300F (2022) entry per service manual cross-reference.

**Kawasaki Versys-X 300** — Kawasaki press release 2016-11-09 (kawasaki.com/
en-us/press-releases/2017-versys-x-300-announcement), Kawasaki service manual
(Kawasaki Heavy Industries, PN 99924-1614-04, 2017 edition), Cycle World
2017 first-ride, MCN 2017 review, ADVPulse 2017 long-term. Gear ratios
shared with Ninja 300 / Z300 cassette per Kawasaki service manual cross-
reference (KLE300 transmission section identical to EX300). F14/R46 520
chain — taller rear sprocket than Ninja 300's R42 for ADV gearing.

## Engineering changes

- `motoquant/scraper/known_bikes_extended.py` — appended 3 spec blocks +
  3 list entries under "tenth pass" comment. File 2771 → 2941 lines.
- No changes to `importer.py` / `gear_ratios.py` / any other physics file.
  All 3 bikes route cleanly via existing inference (4-stroke, chain drive,
  standard displacement-band heuristics).

## Validation gates

- `python3 -m pytest tests/test_scraper.py` → **80 passed**
- `python3 -m pytest tests/test_scraper.py tests/test_two_stroke.py tests/test_compatibility.py` → **145 passed**
- Validator on all 3 new bikes: `valid=True`, 0 errors, 2 cosmetic warnings
  each (Indian bias-ply tire notation — non-blocking per CLAUDE.md May-04
  precedent).
- Baselines (asserts `< 0.001s` drift):
  - K5: 10.0334s (target 10.0334, drift 0.0000s)
  - R1: 10.2859s (target 10.2859, drift 0.0000s)
  - Hayabusa: 10.4712s (target 10.4712, drift 0.0000s)
- All 3 new bikes pass ET ∈ [4.0, 26.0]s and trap ∈ [40, 400] km/h gates.

## Open carry-forward / warnings

- Cosmetic bias-ply tire-format warnings (3 × 2 = 6 total) — long-standing
  open item; widen `scraper/validator.py` tire-format regex to accept
  `WWW/AA-RR` notation in addition to `WWW/AAZRRR` ZR notation.
- No new dispatch escalations.
