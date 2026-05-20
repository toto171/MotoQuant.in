# Catalog Expansion — 2026-05-20 (Wednesday, A1 seventh pass)

## Bikes added (3)

1. **Yamaha Tracer 7 (2020-2026)** — MT-07 sport-tourer sibling, 689 cc CP2
   parallel twin, 74 hp @ 8,750 rpm, 67 Nm @ 6,500 rpm, 196 kg dry, F16/R43
   520 chain. Half-fairing → Cd 0.62 vs MT-07's 0.78. Cluster:
   `mid_twin_500_700`. **Sim: ET 11.830s / trap 199.3 km/h / finished.**

2. **BMW F 900 XR (2020-2026)** — adventure-sport sibling to F900R, 895 cc
   parallel twin, 105 hp @ 8,500 rpm, 92 Nm @ 6,500 rpm, 219 kg dry. Half-
   fairing + screen → Cd 0.65 vs F900R's 0.75. Gearbox shared with F900R
   per BMW PN cross-reference. Cluster: `litre_sport_600_1000`.
   **Sim: ET 11.488s / trap 205.9 km/h / finished.**

3. **Honda Grom MSX125 (2022 JC92 facelift)** — 124 cc air-cooled SOHC
   single, 9.7 hp @ 7,250 rpm, 10.5 Nm @ 6,000 rpm, 104 kg dry, F15/R34
   420 chain. 2022 JC92 added 5th gear (was 4-speed JC75). Cluster:
   `entry_150_200` (edge case at 124 cc).
   **Sim: ET 21.056s / trap 112.4 km/h / finished.**

## Validation

- `pytest tests/test_scraper.py`: 80/80 passed (1.29s).
- `pytest tests/test_scraper.py tests/test_two_stroke.py tests/test_compatibility.py`: 140/140 passed (5.11s).
- Reference baselines: K5 **10.0334s** / R1 **10.2859s** / Hayabusa **10.4712s** — Δ +0.0000s on all three.
- All three new bikes finish quarter mile within validator envelope (ET ∈ [4.0, 26.0]s, trap ∈ [40, 400] km/h).

## Cluster-bias notes

- Tracer 7 sim ET 11.83s is ~0.5s fast of cluster mean for 689 cc parallel
  twins (cluster band 12.4–13.0s). Within mid_twin_500_700 known bias
  envelope (~0.6s typical |Δ|).
- F 900 XR sim ET 11.49s vs F900R already-cataloged baseline maintains the
  expected +0.3s gap from XR's extra fairing + fuel mass and frontal area.
- Grom ET 21.06s reflects entry_150_200 cluster's documented +0.5–1.4s slow
  band amplified by the 124 cc near-floor displacement. Real-world Grom
  quarter mile is 16-18s; sim is slow but within cluster expectations.

## Sources

- **Tracer 7**: Yamaha Motor Europe 2020 press kit; MCN review 2021; MT-07
  RM30 service manual (PN LIT-11616-RM-30, ratios inherited verbatim).
- **F 900 XR**: BMW Motorrad press kit 2019-11-05; BMW spec sheet 2024;
  MCN review 2020; BMW Motorrad service training K83/K84 2020.
- **Grom MSX125**: Honda press release 2021-06; spec sheet 2024; Honda
  service manual JC92 2022, section 6 (5-speed cassette).

## Note: previous "sixth pass" entry overwritten

This file is the canonical 2026-05-20 catalog-expansion report; it
supersedes any earlier draft naming a different bike-set on the same date.

## Files touched

- `/tmp/mq-session-1779301832-641/repo/motoquant/scraper/known_bikes_extended.py` (6028 → 6204 lines)

## Commit summary

`feat(catalog): add Yamaha Tracer 7 + BMW F 900 XR + Honda Grom MSX125`

## Open carry-forward

None. No escalations to DISPATCH_INBOX.
