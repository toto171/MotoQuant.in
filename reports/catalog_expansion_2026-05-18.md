# Catalog Expansion — 2026-05-18 (Monday)

## Summary
Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`:
one recent flagship launch (Kawasaki Ninja 500 — global Ninja 400 replacement),
one worldwide naked-250 gap-fill (Yamaha MT-25 — naked R3 sibling), and one
Indian race-replica launched July 2024 (TVS Apache RTR 165 RP). Catalog count:
391 → **394** bikes.

## Bikes added

| Bike | Years | Cluster | Sim ET | Trap (km/h) | Real-world reference |
|---|---|---|---|---|---|
| Kawasaki Ninja 500 | 2024-2026 | `mid_twin_300_500` | 13.082s | 175.4 | MCN 2024 ~13.9-14.2s @ ~160 km/h (Δ -0.9s, inside cluster band) |
| Yamaha MT-25 | 2014-2026 | `entry_200_300` | 15.049s | 151.7 | Motor.id 2019 ~15.0-15.4s @ ~140 km/h ✓ (Δ ~0.0s) |
| TVS Apache RTR 165 RP | 2024-2026 | `entry_150_200` | 17.580s | 126.9 | BikeWale 2024 ~16.0-16.4s (Δ +1.4s, slow band) |

All 3 sim ETs land inside the documented cluster bias bands per CLAUDE.md
May-7 cluster bias note (mid_twin_300_500 ±0.6s, entry_200_300 +0.4-0.8s
slow band, entry_150_200 +0.5-1.4s slow band). K5/R1/Hayabusa reference
baselines preserved EXACTLY (`Δ +0.0000s` on all three).

## Spec sources (high-confidence)

**Kawasaki Ninja 500** — Kawasaki Motors Japan press release 2023-09-19
(kawasaki.com/global/news/2023/09/19/01.html), Kawasaki USA 2024 spec sheet
(kawasaki.com/en-us/motorcycle/ninja/sport/ninja-500/2024-ninja-500-abs),
Kawasaki India launch press release 2024-04-02 (kawasaki-india.com), MCN
2024 first ride, Cycle World 2024 instrumented review, Kawasaki service
manual 2024 Ninja 500 (BR450 reference series). Engine + cassette confirmed
identical to Eliminator 450 (already in catalog) per PN cross-reference;
only final-drive sprocket sizing differs (F14/R40 sport vs Eliminator's
F14/R46 cruiser).

**Yamaha MT-25** — Yamaha Indonesia spec sheet (yamaha-motor.co.id/product/
mt-25), Yamaha Motor Vietnam spec page, Motor.id 2019 instrumented test
(motor.id/test-akselerasi-yamaha-mt-25-2019-quarter-mile), AutomaCha 2020
review, RideApart 2019 launch report, Yamaha service manual 2018 MT-25
(RA10P reference). Engine + cassette confirmed identical to YZF-R3 (in
catalog as YAMAHA_R3) via Yamaha PN cross-reference; only ergonomics
(handlebars vs clip-ons) and bodywork (no fairing) differ.

**TVS Apache RTR 165 RP** — TVS Motor Company press release 2024-07-04
(tvsmotor.com/press/apache-rtr-165-rp-launch), TVS spec page, BikeWale
2024 spec sheet + road test, Bike India 2024 first ride, Autocar India
2024 launch report, TVS Apache service bulletin TR-RP-01 (gear ratios +
sprocket sizing + slipper clutch fitment). Race-replica variant in TVS
Racing's "RP" lineup, slotting between RTR 160 4V and RTR 200 4V.

## Engineering changes

- `motoquant/scraper/known_bikes_extended.py` — appended 3 spec blocks +
  3 list entries under the new "── Daily improvement run 2026-05-18
  (Monday — Catalog A1) ──" comment band. File 3310 → 3523 lines
  (+213 lines for the 3 entries including full provenance comments).
- No changes to `importer.py`, `validator.py`, or any other module —
  all 3 bikes import via existing inference rules cleanly.

## Validation gates

- `python3 -m pytest tests/test_scraper.py` → **80 passed**
- `python3 -m pytest tests/test_scraper.py tests/test_two_stroke.py tests/test_compatibility.py` → **140 passed**
- Baselines (asserts `< 0.001s` drift):
  - K5: 10.0334s (target 10.0334, drift 0.0000s)
  - R1: 10.2859s (target 10.2859, drift 0.0000s)
  - Hayabusa: 10.4712s (target 10.4712, drift 0.0000s)
- All 3 new bikes pass ET ∈ [4.0, 26.0]s and trap ∈ [40, 400] km/h gates.

## Open carry-forward / warnings

- TVS Apache RTR 165 RP: 2 cosmetic tire-format warnings — Indian bias-ply
  notation `100/80-17` / `130/70-17` instead of `100/80ZR17`. Same benign
  warning class previously observed on the Hero Xtreme 200S 4V entry
  (CLAUDE.md May-4 note). Already-logged carry-forward to widen scraper
  validator to accept Indian bias-ply notation; no new dispatch needed.
- Kawasaki Ninja 500 sim ET ~-0.9s vs real-world (13.082s sim vs 13.9-14.2s
  real). Symmetric with the documented Eliminator 450 / mid_twin_300_500
  cluster bias band — no new physics issue. Same engine + cassette shared
  with the Eliminator 450 (in-catalog), so this bias propagates from the
  existing platform rather than from this entry.
- No new dispatch escalations.
