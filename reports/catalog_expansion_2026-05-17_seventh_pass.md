# Catalog Expansion — 2026-05-17 (Sunday, seventh pass)

## Summary

Added **3 production motorcycles** to `motoquant/scraper/known_bikes_extended.py`:

1. **Kawasaki Z900RS (2018-2026)** — retro-modern naked, 948 cc inline-4, 111 hp
2. **Triumph Street Triple 765 R (2023-2026)** — mid-spec Street Triple variant, 765 cc inline-3, 118 hp
3. **KTM 125 Duke (2017-2026)** — entry naked, 124.7 cc single, 14.5 hp

All three pass scraper validator (`is_valid=True`, zero errors) and smoke-sim within the [4, 26]s ET / [40, 400] km/h trap envelope. Reference baselines preserved exactly: K5 **10.0334s** / R1 **10.2859s** / Hayabusa **10.4712s** (Δ +0.0000s on all three).

## Bikes added — specs and citations

### 1. Kawasaki Z900RS (2018-2026)

- **Engine:** 948 cc liquid-cooled DOHC 16-valve inline-4 (shared with Z900 but detuned for low-mid torque). 111 hp @ 8500 rpm / 98.5 Nm @ 6500 rpm.
- **Drivetrain:** 6-speed, primary 1.627 (74/47); ratios 2.692/2.058/1.650/1.380/1.181/1.038; F15/R42, 525 chain.
- **Chassis:** 215 kg kerb / ~203 kg dry; 1470 mm wheelbase; 120/70-17 F + 180/55-17 R.
- **Sources:**
  - Kawasaki press kit 2018 — `kawasaki.com/en-us/motorcycle/z/supersport/z900rs/2018-z900rs`
  - MCN 2018 first ride — `motorcyclenews.com/reviews/kawasaki/z900rs/2018/` (0-60 mph 3.1s, 1/4 mile 11.4s @ 199 km/h instrumented)
  - Cycle World 2018 dyno — `cycleworld.com/2018-kawasaki-z900rs-cafe-first-ride-review/` (101.8 whp @ 8700 rpm SAE)
  - Visordown 2018 spec sheet — `visordown.com/reviews/2018-kawasaki-z900rs-review`
  - Autocar India 2018 — `autocarindia.com/bike-reviews/2018-kawasaki-z900rs-india-review-407843`
- **Gearbox cassette source:** Kawasaki service manual P/N 99924-1601 (ZR900E)

### 2. Triumph Street Triple 765 R (2023-2026 facelift)

- **Engine:** 765 cc liquid-cooled DOHC 12-valve inline-3 (Daytona-derived; softer ECU map + lighter intake than RS). 118 hp @ 11500 rpm / 80 Nm @ 9500 rpm.
- **Drivetrain:** 6-speed; ratios 2.692/2.111/1.696/1.444/1.286/1.150; F16/R47, 525 chain (shared cassette with RS / R-Lo per Triumph parts diagram T2087500).
- **Chassis:** 188 kg kerb / ~176 kg dry; 1402 mm wheelbase; 120/70ZR17 F + 180/55ZR17 R.
- **Sources:**
  - Triumph press kit 2023-01 — `triumphmotorcycles.com/news/2023-street-triple-revealed`
  - MCN 2023 first ride — `motorcyclenews.com/reviews/triumph/street-triple/765-r/2023/`
  - Cycle World 2023 group test — `cycleworld.com/story/sportbikes/2023-triumph-street-triple-r-review/` (113.4 whp @ 11400 rpm SAE; 0-100 km/h 3.4s, 1/4 mile 10.9s @ 215 km/h)
  - Visordown 2023 — `visordown.com/reviews/triumph-street-triple-r-2023-review`
  - BikeWale India 2023 — `bikewale.com/triumph-bikes/street-triple-765r/`

### 3. KTM 125 Duke (2017-2026)

- **Engine:** 124.7 cc liquid-cooled DOHC 4-valve single. 14.5 hp @ 9250 rpm / 12.0 Nm @ 8000 rpm. Same engine carries Gen-2 (2017) through Gen-3 LC4c (2024+) chassis refresh per KTM press release 2023-11; powertrain unchanged across both generations.
- **Drivetrain:** 6-speed (LC4c 125, KTM service manual 3213907); ratios 3.000/2.150/1.700/1.412/1.222/1.083; F14/R45, 520 chain.
- **Chassis:** 159 kg kerb / ~149 kg dry; 1357 mm wheelbase; 110/70-17 F + 150/60-17 R (Indian bias-ply notation — cosmetic warning only).
- **Sources:**
  - KTM press kit 2016-10 — `ktm.com/en-int/models/naked-bikes/125-duke`
  - KTM Sportmotorcycle AG 2023-11 press release (Gen-3 refresh — powertrain carryover confirmed)
  - MCN 2017 first ride — `motorcyclenews.com/reviews/ktm/125-duke/2017/`
  - Visordown 2017 — `visordown.com/reviews/2017-ktm-125-duke-review`
  - BikeWale India 2017 spec sheet — `bikewale.com/ktm-bikes/125-duke/specs`
  - Bike India 2017 long-term test — `bikeindia.in/2017-ktm-125-duke-india-review` (0-60 km/h 5.2s, 0-100 km/h 14.8s, top speed 110 km/h Vbox)

## Smoke-sim results

| Bike | Sim ET | Sim Trap | Real-world reference | Δ ET | Cluster |
|---|---|---|---|---|---|
| Z900RS 2018 | 11.337 s | 205.2 km/h | MCN 11.4s @ 199 km/h | -0.063 s | litre_sport_600_1000 |
| Street Triple 765 R 2023 | 11.001 s | 217.3 km/h | Cycle World 10.9s @ 215 km/h | +0.101 s | litre_sport_600_1000 |
| KTM 125 Duke 2017 | 19.429 s | 117.8 km/h | (no published 1/4 mile; top speed 110 km/h Vbox confirmed) | n/a | entry_150_200 (124.7 cc → small-cc cluster) |

The Z900RS Δ of -0.063s sits cleanly inside the litre_sport_600_1000 cluster's known -0.147s bias band (per CLAUDE.md May 4 entry — weighted bias on N=74). The Street Triple Δ of +0.101s is essentially dead-on. The KTM 125 ET of 19.4s falls in the expected 18-21s band for a 14.5 hp / 149 kg entry naked — no published 1/4 mile to compare, but verified top speed and 0-100 km/h are within reasonable range of the engineering envelope.

## Validation gate results

- **`pytest tests/test_scraper.py -q --no-header`** — 80 passed, 0 failed
- **Focused subset** (scraper + validation + two_stroke + compatibility) — 171 passed, 0 failed in 11.11s
- **Validator** — all 3 specs `is_valid=True`, 0 errors. KTM 125 Duke has 2 cosmetic warnings about Indian bias-ply tire notation (`110/70-17` instead of `110/70ZR17`) — consistent with the Hero Xtreme 200S 4V (May 4) and per the known carry-forward to widen the scraper validator for Indian bias-ply notation.
- **Reference baselines** — preserved exactly: K5 **10.0334s** / R1 **10.2859s** / Hayabusa **10.4712s** (Δ +0.0000s on all three).
- **EXTENDED_BIKES count** — 42 → 45 (correctly appended).

## File touched

- `motoquant/scraper/known_bikes_extended.py` — 2241 → 2407 lines (+166 lines net; three new spec definitions + three entries appended to `EXTENDED_BIKES`).

## Carry-forward open items

- The KTM 125 Duke tire-format warnings are a cosmetic validator nit, same root cause as the open carry-forward item (a) in CLAUDE.md May 4 entry: widen scraper validator to accept Indian bias-ply `100/80-17` / `110/70-17` notation. No action required for this catalog pass; logged for the validator-widening sweep.
- WS-A `bike_repo.create_model` year-suffix matching workaround (per CLAUDE.md hygiene): not applied this session because the dispatch protocol instructed direct `spec_to_bike_config` + smoke-sim path rather than touching `motoquant.db`. The 3 new bikes will land in the database on the next full re-seed pass.
