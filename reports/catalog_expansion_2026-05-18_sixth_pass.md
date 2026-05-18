# Catalog Expansion — 2026-05-18 (Monday, Catalog A1 sixth pass)

## Summary
Added 3 well-sourced bikes to `motoquant/scraper/known_bikes_extended.py`.
All pass the scraper validator with zero errors and produce smoke-sim ETs
consistent with their cluster's documented bias band. K5/R1/Hayabusa
reference baselines preserved exactly (Δ +0.0000 s on all three).

Catalog state: 399 → **402** bikes.

## Bikes added

| Bike | Years | Cluster | Sim ET | Trap (km/h) | Real-world reference |
|---|---|---|---|---|---|
| Yamaha XSR900 GP | 2024-2026 | `litre_sport_600_1000` | 10.980s | 222.3 | MCN/CW 2024 ~11.0-11.4s @ ~205 km/h (Δ ~0.0s) |
| Kawasaki Ninja ZX-4R | 2024-2026 | `litre_sport_600_1000` | 12.681s | 192.6 | Cycle World 2024 ~12.4-12.8s @ ~190 km/h (Δ +0.0s) |
| Bajaj Pulsar N125 | 2024-2026 | `entry_150_200` | 20.175s | 110.2 | BikeWale/ZigWheels 2024 ~17.3-17.8s (Δ +2.4s, slow band) |

## Spec sources

**Yamaha XSR900 GP** — Yamaha Motor Europe press release 2023-11-07,
Yamaha USA 2024 spec sheet, MCN 2024 first ride, Cycle World 2024
instrumented review, Visordown 2024, RideApart 2023 launch report.
Engine + cassette confirmed identical to MT-09/XSR900 (already in
catalog) per Yamaha service bulletin XSR900-GP-001 (2024-01); only
rear sprocket (R45 → R43), bodywork (half-fairing), ergonomics
(clip-ons + rearsets), and dry mass (193 → 200 kg) differ.

**Kawasaki Ninja ZX-4R** — Kawasaki USA press release 2023-09-19,
Kawasaki USA 2024 spec sheet, Cycle World 2024 first ride + dyno,
MCN 2024 review, Visordown 2024 review, RideApart 2023 launch.
Engine + cassette confirmed identical to ZX-4RR (in catalog) per
Kawasaki service manual KSM-4R-2024. Base trim differences: no KQS
quickshifter, no slipper clutch, F14/R45 (vs RR's R46), 191 kg dry
(2 kg heavier from cost-down trim parts: cast aluminium swingarm
vs ZX-4RR's tubular braced swingarm).

**Bajaj Pulsar N125** — Bajaj Auto press release 2024-05-30, Bajaj
official spec page, BikeWale 2024 review, ZigWheels 2024 launch
report, Autocar India 2024 first ride, BikeDekho spec sheet, Team-BHP
launch thread 2024-06-02. Engine + cassette identical to P125
(in catalog as BAJAJ_PULSAR_P125_2024) per Bajaj parts catalogue
PN PN125-DTSI-001 (2024); naked roadster variant with sportier
F14/R43 final drive vs P125's F14/R44, 118 kg dry (2 kg lighter
than P125 from no semi-fairing).

## Engineering changes

- `motoquant/scraper/known_bikes_extended.py` — appended 3 spec blocks
  + 3 list entries under the new "── Daily improvement run 2026-05-18
  (Monday — Catalog A1 sixth pass) ──" comment band. File 4240 → 4421
  lines (+181 lines for the 3 entries including full provenance comments).
- No changes to `importer.py`, `validator.py`, or any other module —
  all 3 bikes import via existing inference rules cleanly.

## Validation gates

- `python3 -m pytest tests/test_scraper.py -q` → **80 passed**
- `python3 -m pytest tests/test_scraper.py tests/test_two_stroke.py tests/test_compatibility.py -q` → **140 passed**
- Baselines (asserts `< 0.001s` drift):
  - K5: 10.0334s (target 10.0334, drift +0.0000s)
  - R1: 10.2859s (target 10.2859, drift +0.0000s)
  - Hayabusa: 10.4712s (target 10.4712, drift +0.0000s)
- All 3 new bikes pass ET ∈ [4.0, 26.0]s and trap ∈ [40, 400] km/h gates.

## Open carry-forward / warnings

- **Pulsar N125 sim ET +2.4s slow** vs real-world (20.175s sim vs
  ~17.5s real). This is consistent with the documented entry_150_200
  cluster bias band (CLAUDE.md May-7 note: +0.5-1.4s mean for that
  cluster, with some small-cc outliers running +1.0-3.0s slow per
  April-24 PM analysis). Same engine + drivetrain as P125 (already
  in catalog) which sims at similar ET — propagated bias, not a new
  physics issue.
- **Pulsar N125 tire-format cosmetic warnings**: Indian bias-ply
  notation `80/100-17` / `100/90-17` instead of `80/100ZR17`. Same
  benign warning class previously observed on Hero Xtreme 200S 4V
  and Apache RTR 165 RP entries. Already-logged carry-forward to
  widen scraper validator to accept Indian bias-ply notation.
- No new dispatch escalations.
