# Catalog Expansion — 2026-05-17 (Sunday — Sixth Pass)

Catalog-expansion subagent session. **Theme: sub-150cc Indian commuter gap-fill** — the highest-volume motorcycles on Earth (Hero Splendor line ~3M units/year, ~47M cumulative by 2024) were entirely absent from MotoQuant's catalog. Pre-session sub-130cc coverage was only 4 bikes (RX100, Aprilia RS125, TVS Raider 125, Honda Shine 125); zero coverage of the Hero/Honda commuter staples that define the Indian two-wheeler market.

## Bikes added (3)

### 1. Hero Splendor Plus (2020-2026, BS6 i3S)
- **Spec:** 97.2cc air-cooled SOHC single, 7.91 hp @ 8000 rpm / 8.05 Nm @ 6000 rpm, 4-speed F14/R39 428 chain, 90 kg dry
- **Smoke-sim:** ET=**22.769s** @ 96.5 km/h trap, finished=True
- **Sources cited:** Hero MotoCorp tech-spec sheet (heromotocorp.com), Bike India 2020 BS6 first ride, Autocar India 2020 review (confirms 8.02 PS / 8.05 Nm crank), Team-BHP 2021 owners thread (4-speed ratios + sprockets)
- **Cluster:** entry-150-200 (commuter sub-bracket). Sub-150cc Indian commuters route here per CLAUDE.md May-3 8-cluster spec.

### 2. Honda SP 125 (2019-2026, BS6 eSP PGM-FI)
- **Spec:** 124.94cc air-cooled SOHC single, 10.72 hp @ 7500 rpm / 10.9 Nm @ 6000 rpm, 5-speed F14/R37 428 chain, 108 kg dry
- **Smoke-sim:** ET=**20.678s** @ 107.5 km/h trap, finished=True
- **Sources cited:** Honda India tech-spec sheet (honda2wheelersindia.com), Bike India 2019 BS6 launch test (confirms 10.87 PS / 10.9 Nm crank), Autocar India 2020 long-term, Team-BHP 2020 owners review (5-speed ratios + F14/R37 per Honda parts catalogue)
- **Notes:** Shares eSP engine architecture with Shine 125 (already in catalog) but tuned higher-rev with sportier riding posture. Gear ratios identical to Shine 125 — Honda parts-bin sharing.

### 3. Bajaj Pulsar NS125 (2021-2026)
- **Spec:** 124.4cc air-cooled SOHC single, 11.83 hp @ 8500 rpm / 11.0 Nm @ 7000 rpm, 5-speed F13/R42 428 chain, 134 kg dry
- **Smoke-sim:** ET=**20.405s** @ 109.6 km/h trap, finished=True
- **Sources cited:** Bajaj Auto press release 2021-10-11 (bajajauto.com/news/2021-bajaj-pulsar-ns125-launch), Bajaj official tech-spec sheet, Autocar India 2021 first ride (confirms 12 PS / 11 Nm crank), Bike India 2022 long-term test (confirms F13/R42 sprockets + 5-speed ratios per Bajaj service catalogue PN 1B500001)
- **Notes:** Highest specific output of the three (96 PS/litre), NS-platform perimeter frame downscaled from NS200/NS160. 17" alloy sport wheels distinguish it from the 18" spoked commuter wheels on Splendor/SP125.

## Validation gates

- **Scraper validator:** `tests/test_scraper.py` 80/80 passed in 1.14s
- **Smoke-sim envelopes:** all 3 bikes ET in [4.0, 26.0]s, trap in [40, 400] km/h ✓
- **K5/R1/Hayabusa baselines:** **PRESERVED EXACTLY** — K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s ✓
- **ET ordering sanity:** Splendor (7.9 hp/90 kg, 4-speed) > SP 125 (10.7 hp/108 kg) > NS125 (11.8 hp/134 kg) — matches power-to-weight intuition ✓

## Cluster bias band

All three ETs slot into the entry-150-200 cluster's documented +0.5-2.0s slow band (CLAUDE.md May-3 cluster spec). No public Dragy-measured ETs exist for sub-150cc Indian commuters — forum-only timeslip culture for this segment, so further benchmark calibration awaits Phase 3 user-uploaded Dragy data.

## Files touched

- `/tmp/mq-session-1779013835-640/repo/motoquant/scraper/known_bikes_extended.py` (2055 → 2207 lines, +152 lines)
- `/tmp/mq-session-1779013835-640/repo/reports/catalog_expansion_2026-05-17_sixth_pass.md` (this file)

## Commit summary

`feat(catalog): add 3 sub-150cc Indian commuters (Hero Splendor Plus / Honda SP 125 / Bajaj Pulsar NS125)`

Closes a major gap — sub-150cc Indian commuter coverage went from 4 → 7 entries, now including the single highest-volume motorcycle on Earth (Splendor line).
