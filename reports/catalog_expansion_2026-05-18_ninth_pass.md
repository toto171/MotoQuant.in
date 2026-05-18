# Catalog Expansion — 2026-05-18 (Monday — Ninth Pass)

## Summary

Added 2 production motorcycles to `motoquant/scraper/known_bikes_extended.py`. Both are Indian-market gap fills with verifiable specs from manufacturer pages + magazine instrumented tests. The DISPATCH_INBOX dispatch candidate set (CFMoto 800NK, Yamaha MT-125, Yamaha XSR125) was already covered by passes 5-8 earlier today — those three bikes are already in the list. This pass picks two complementary Indian-market entries instead, leaving the candidate trio fully present for the marketing-content agent to choose from.

## Bikes Added

### 1. KTM RC 125 (2017-2026)
- Engine: 124.7 cc liquid-cooled DOHC 4V single, 14.5 hp @ 9250 rpm, 12.0 Nm @ 8000 rpm
- Drivetrain: 6-speed cassette (KTM service manual TI-2017-021), 14F/45R 520 chain
- Chassis: 125 kg dry (134 kg kerb - 9 kg fuel)
- Aero: Cd 0.55, frontal area 0.42 m^2 (full sport fairing, committed tuck)
- Cluster: entry_150_200
- Smoke sim: ET 18.160s @ 129.9 km/h (real-world ~18.5-19.0s per MCN 2017; sim ~-0.4s fast)

### 2. Hero Hunk 160R (2022-2026)
- Engine: 163.2 cc air-cooled SOHC 2V single, 15.0 hp @ 8500 rpm, 14.0 Nm @ 6500 rpm
- Drivetrain: 5-speed constant-mesh (Hero HM-HUNK160R-2022 service manual), 14F/37R 428 chain
- Chassis: 136 kg dry (145 kg kerb - 9 kg fuel)
- Aero: Cd 0.76, frontal area 0.46 m^2 (upright streetfighter naked)
- Cluster: entry_150_200
- Smoke sim: ET 18.956s @ 116.0 km/h (real-world ~17.2s per Autocar India; sim ~+1.5s slow, within entry-cluster bias band per CLAUDE.md)

## Validation Gates

1. `python3 -m pytest tests/test_scraper.py -q --no-header`: 80/80 passed (411 deprecation warnings unrelated)
2. Smoke sim each new bike: both ET in [4.0, 26.0]s, trap in [40, 400] km/h, finished_quarter=True
3. Reference baselines preserved EXACTLY:
   - K5: 10.0334s (Δ +0.0000s)
   - R1: 10.2859s (Δ +0.0000s)
   - Hayabusa: 10.4712s (Δ +0.0000s)

## Notes

- Both bikes use Indian bias-ply tire notation (`100/80-17`, `140/70-17`) per the carry-forward "widen scraper validator to accept Indian bias-ply notation" — scraper emits cosmetic warnings but accepts them.
- KTM RC 125 fills the A1-licence sport gap (sits below the existing RC 200 in catalog).
- Hero Hunk 160R fills Hero's 160cc roadster lineup (separate from Xtreme 160R which is in canonical known_bikes.py).
- No new errors, no baseline drift, no validator failures.

## File touched

`motoquant/scraper/known_bikes_extended.py` (4755 -> 4889 lines, +134)
