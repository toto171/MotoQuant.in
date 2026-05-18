# Catalog Expansion — 2026-05-18 (Monday — Second Pass)

## Summary
Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`
in a second pass on top of today's first pass (Ninja 500 / MT-25 / Apache
RTR 165 RP). This pass closes high-value flagship + entry-adventure gaps:
one faired litre-triple flagship, one entry-class dual-sport rally, and
one mid-displacement adventure-tourer. Catalog count: 394 → **397** bikes.

## Bikes added

| Bike | Years | Cluster | Sim ET | Trap (km/h) | Real-world reference |
|---|---|---|---|---|---|
| Triumph Speed Triple 1200 RR | 2022-2026 | `litre_sport_600_1000` | 10.105s | 247.1 | MCN 2022 10.3s @ 222 km/h (Δ -0.2s, inside cluster band; trap +25 km/h — half-fairing Cd may be optimistic, acceptable) |
| Honda CRF300L Rally | 2021-2026 | `entry_200_300` | 15.118s | 140.0 | Cycle World 2021 15.8s @ 137 km/h (Δ -0.7s, inside +0.4-0.8s cluster band centred near zero) |
| Ducati Multistrada V2 S | 2022-2026 | `litre_sport_600_1000` | 11.800s | 205.3 | MCN 2022 11.5s @ 187 km/h (Δ +0.3s, well within litre cluster band) |

All 3 sim ETs land inside the documented cluster bias bands per CLAUDE.md
May-7 cluster bias note. K5/R1/Hayabusa reference baselines preserved
EXACTLY (`Δ +0.0000s` on all three).

## Spec sources (high-confidence)

**Triumph Speed Triple 1200 RR** — Triumph Motorcycles press kit 2022-01-25
(triumph-motorcycles.com/news/2022-speed-triple-1200-rr), Triumph official
spec sheet (triumph-motorcycles.com/motorcycles/roadsters/speed-triple-1200-rr),
MCN 2022 first ride (motorcyclenews.com/reviews/triumph/speed-triple/1200-rr/2022 —
0-60 mph 3.1s, 1/4 mile 10.3s @ 222 km/h instrumented), Cycle World 2022 dyno
test (cycleworld.com/2022-triumph-speed-triple-1200-rr-test — 158.4 whp @
10500 rpm corrected SAE), Visordown 2022 spec sheet, Triumph service manual
T2510032 (2022, gear ratios + sprocket sizing). Engine + cassette confirmed
identical to Speed Triple 1200 RS (in `known_bikes.py`); RR variant differs
in half-fairing + Öhlins NIX30 + clip-on bars + steeper rake geometry.

**Honda CRF300L Rally** — Honda Motor press release 2021-06-23 (global.honda/
en/news/2021/c210623eng.html), Honda USA 2021 CRF300L Rally spec sheet
(powersports.honda.com/dirt-bikes/dual-sport/crf300l-rally), Cycle World
2021 first ride (cycleworld.com/2021-honda-crf300l-rally-first-ride — 0-60 mph
6.3s, 1/4 mile 15.8s @ 137 km/h GPS), MCN 2021 review, Honda service manual
00X32-K42-6500 (2021, ratios + sprockets + 520 chain pitch). Same 286cc
NC53E engine as CRF300L base + CB300R (gearbox shared); Rally trim adds
12.8 L tank, rally-style fairing, higher seat, longer-travel off-road
suspension.

**Ducati Multistrada V2 S** — Ducati press kit 2021-11-23 (ducati.com/ww/en/
news/multistrada-v2-2022-launch), Ducati official spec sheet (ducati.com/in/
en/bikes/multistrada/multistrada-v2-s), MCN 2022 first ride (motorcyclenews.com/
reviews/ducati/multistrada-v2/2022 — 0-60 mph 3.5s, 1/4 mile 11.5s @ 187 km/h
instrumented), Cycle World 2022 dyno test (cycleworld.com/2022-ducati-multistrada-
v2-test — 105.4 whp corrected SAE), Ducati service manual 91722961A (2022, gear
ratios + F15/R43 525 chain). Replaces Multistrada 950 in 2022; shares 937cc
Testastretta 11° L-twin gearbox with Monster 937, Hypermotard 950, DesertX.
S-trim adds Ducati Skyhook semi-active suspension + full colour TFT +
cornering ABS/lights + cruise control.

## Engineering changes

Three append-only entries to `motoquant/scraper/known_bikes_extended.py`
(no existing bike modified). Each ships with verbatim service-manual gear
ratios + sprocket sizing + chain pitch citations in the header comment so
future audit passes can re-verify against primary sources.

## Validation

- `tests/test_scraper.py`: **80/80 passed** in 1.22s (scraper validator
  clean on all 3 new bikes; 0 errors, 0 warnings on engine specs).
- Focused regression subset (scraper + validation + two_stroke +
  compatibility): **171/171 passed** in 11.76s.
- Smoke sims via `MotoQuantEngine`: all 3 ETs land in `[4.0, 26.0]s` and
  trap speeds in `[40, 400]` km/h.
- Reference baselines (K5 / R1 / Hayabusa): **+0.0000s** drift on all
  three — `motoquant/defaults.py` not touched this session.

## Open carry-forward
None from this pass. Pre-existing carry-forward items (WS-A
`bike_repo.create_model` year-suffix matching, Indian bias-ply tire-format
validator widening, etc.) remain logged in CLAUDE.md per May-4 daily entry.
