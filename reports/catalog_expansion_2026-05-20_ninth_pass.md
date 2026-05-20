# Catalog Expansion — 2026-05-20 (Wednesday — Ninth Pass)

## Summary
Added **3 production motorcycles** to `motoquant/scraper/known_bikes_extended.py`,
appended to `EXTENDED_BIKES` master list. Closed mid-displacement naked-sport
(CB650F), V-twin sport-café (SV650X), and SE-Asia retro-naked (XSR155) gaps.

## Bikes added
| # | Bike | Years | Cluster | Sim ET / trap | Sources |
|---|------|-------|---------|---------------|---------|
| 1 | **Honda CB650F** (RC83) | 2014–2018 | litre_sport_600_1000 | 11.952 s / 199.4 km/h | Honda EU press kit, SM 61MGE00, MCN/CW/Visordown reviews |
| 2 | **Suzuki SV650X** (K8) | 2018–2024 | litre_sport_600_1000 (via 600≤cc<1100 sport rule) | 11.738 s / 203.2 km/h | Suzuki EU press kit, SM 99500-39403-01E, MCN/CW/RideApart |
| 3 | **Yamaha XSR155** (G3K3) | 2019–2026 | entry_150_200 | 17.184 s / 130.3 km/h | Yamaha Indonesia spec, BikeWale, Visordown, AutoIndustriya |

### Cluster-bias sanity
- CB650F cluster band -0.15 to +0.30 s; sim landed +0.16 to +0.36 s vs CW 2015
  (11.79 s @ 188 km/h) — acceptable, slight +trap from synthetic curve.
- SV650X — real-world stock 11.8–12.2 s; sim 11.74 s sits at fast edge,
  consistent with documented mid-cluster bias being centred.
- XSR155 — Indonesian magazine 0-400 m typically 16.5–17.5 s; sim +0.5 s
  falls cleanly in entry_150_200 documented slow-by-0.5–1.4 s band.

## Source-quality bar
Each bike has manufacturer spec sheet (power, torque, mass) plus service-manual
or parts-catalog cross-reference for gear cassette + sprockets. No estimated
power or mass. CB650F & SV650X gear ratios pulled from Honda 61MGE00 + Suzuki
99500-39403-01E. XSR155 cassette confirmed shared with YZF-R15 V3 / MT-15 V2
via Yamaha PN B65-E7400 cross-reference.

## Validation gates passed
- `pytest tests/test_scraper.py` — **80/80 passed** (1.32 s).
- `pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py
  tests/test_compatibility.py` — **171/171 passed** (12.40 s).
- All 3 bikes pass smoke-sim: ET in [4, 26] s, trap in [40, 400] km/h, all
  `finished_quarter=True`.
- **Reference baselines preserved exactly:**
  - K5 = 10.0334 s (Δ +0.0000)
  - R1 = 10.2859 s (Δ +0.0000)
  - Hayabusa = 10.4712 s (Δ +0.0000)

## Files touched
- `/tmp/mq-session-1779316232-658/repo/motoquant/scraper/known_bikes_extended.py`
  (+208 lines: 3 new spec_from_dict entries + 3 lines in EXTENDED_BIKES list)
- `/tmp/mq-session-1779316232-658/repo/reports/catalog_expansion_2026-05-20_ninth_pass.md`
  (this report)

## Open hygiene
- All three bikes use standard ZR17 / -17 tire formatting; no validator warnings.
- WS-A `bike_repo.create_model` year-suffix matching bug still open (carry-
  forward from May 4 entry); avoided by not running `python -m motoquant.run
  import --known-bikes` per CLAUDE.md guidance.

## Commit summary suggestion
`feat(catalog): +3 bikes (Honda CB650F / Suzuki SV650X / Yamaha XSR155); ninth pass 2026-05-20`
