# Catalog Expansion — 2026-05-18 (Monday, fourth pass)

## Summary
Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`,
extending coverage of (a) Bajaj's freshest 125cc Pulsar-branded entry,
(b) Suzuki's faired sport-commuter sibling to the Gixxer 155 naked, and
(c) Kawasaki's middleweight dual-sport (a previously empty middle-ground
between KLX 140 and KLX 300). Catalog count: +3 bikes.

## Bikes added

| Bike | Years | Cluster | Sim ET | Trap (km/h) | Real-world reference |
|---|---|---|---|---|---|
| Bajaj Pulsar P125 | 2024-2026 | `other` (sub-150) | 20.154s | 110.1 | BikeWale ~19-20s, AutocarIndia 0-60 km/h ~6.5s ✓ |
| Suzuki Gixxer SF 150 | 2019-2026 | `entry_150_200` | 18.214s | 123.3 | Motoroids/PowerDrift 2020 ~17.5-18.0s ✓ |
| Kawasaki KLX 230 | 2020-2026 | `entry_200_300` | 16.695s | 125.0 | Cycle World 2020 / RevZilla 2021 ~16.5-17.5s ✓ |

All 3 sim ETs land inside expected cluster bias bands (entry-150-200 and
entry-200-300 carry documented +0.5–1.4 s slow tendencies per CLAUDE.md
April-27 cluster-bias-precision notes; sub-150cc `other` cluster has no
formal band but empirically matches Splendor/SP125/Shine 125 already in
catalog). K5/R1/Hayabusa reference baselines preserved EXACTLY
(`Δ +0.0000s` on all three).

## Spec sources (high-confidence)

**Bajaj Pulsar P125** — Bajaj Auto press release 2024-05-30
(bajajauto.com/news/pulsar-p125-launch), Bajaj official Pulsar P125
spec page, BikeWale, ZigWheels, Autocar India 2024 first ride, BikeDekho
spec sheet, Team-BHP launch thread. Engine = 124.4cc DTS-i air-cooled
SOHC 2-valve single, 11.64 hp @ 8500 rpm / 11 Nm @ 6000 rpm. 5-speed
cassette inherits Pulsar 150 internals per Bajaj parts catalogue.
F14/R44 428 chain (taller than P150's F14/R45 for economy tune).

**Suzuki Gixxer SF 150** — Suzuki Motorcycle India press release
2019-12-12 (BS6 launch), Suzuki India official spec page, Motoroids
2020 first ride, PowerDrift, Bike India December 2019 (wind-tunnel Cd
citation), Cycle World 2020 India coverage, Suzuki Gixxer SF service
manual 99500-26880-01E. Engine identical to in-catalog Gixxer 155
naked (154.9cc air-cooled SOHC, 13.6 hp / 13.8 Nm); only bodywork
differs — Cd 0.66 (half-fairing) vs naked's 0.78. F14/R45 428 chain.

**Kawasaki KLX 230** — Kawasaki Motors Corp USA press release
2019-09-04 (MY2020 launch), Kawasaki official spec page, Cycle World
2020 first ride (16.4 whp SAE J1349 corrected dyno cited), RevZilla
2021 review, Kawasaki KLX 230 service manual 99924-1517-01,
Adventure Rider long-term test, India Today 2023 India-launch coverage,
Kawasaki India spec page. Engine = 233cc KX-series-derived air-cooled
SOHC 2-valve single (NOT the Bajaj-built KLX 110/140 mill), 19 hp @
7600 rpm / 19.8 Nm @ 6100 rpm. True dual-sport sizing: 21" front /
18" rear knobby wheels.

## Engineering changes

- `motoquant/scraper/known_bikes_extended.py` — appended 3 spec blocks
  (lines after RE_BULLET_350_J_2023) + 3 list entries under "fourth pass"
  comment.
- No `importer.py`, no `defaults.py`, no scraper-validator changes
  required. All three specs slot in cleanly with existing infrastructure.

## Validation gates

- `python3 -m pytest tests/test_scraper.py` → **80 passed** (498 warnings
  are pre-existing `datetime.utcnow()` DeprecationWarnings).
- Baselines (asserts `< 0.001s` drift):
  - K5: 10.0334s (target 10.0334, drift 0.0000s)
  - R1: 10.2859s (target 10.2859, drift 0.0000s)
  - Hayabusa: 10.4712s (target 10.4712, drift 0.0000s)
- All 3 new bikes pass ET ∈ [4.0, 26.0]s and trap ∈ [40, 400] km/h gates.
- Validator: 0 errors. Cosmetic tire-size warnings on Indian bias-ply
  notation (`80/100-17`, `100/90-17`, `2.75-21`, `4.10-18`) — documented
  as expected per CLAUDE.md May-4 Xtreme 200S 4V hygiene note.

## Open carry-forward / warnings

- None. Same validator-widening carry-forward for Indian bias-ply tire
  notation remains open from prior sessions; not a new escalation.
- No new dispatch escalations.
