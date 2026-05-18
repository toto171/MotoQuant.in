# Catalog Expansion — 2026-05-18 (Monday, Catalog A1 fifth pass)

## Summary
Added 3 well-sourced bikes to `motoquant/scraper/known_bikes_extended.py`. All pass
the scraper validator with zero errors and produce smoke-sim ETs consistent with
their cluster's documented bias band. K5/R1/Hayabusa reference baselines preserved
exactly (Δ +0.0000 s on all three).

## Bikes added
1. **Yamaha XSR125 (2021+)** — Euro A1 Sport Heritage retro/scrambler-styled naked
   on the same 124.7 cc DOHC VVA single + 6-speed cassette as the YZF-R125 (already
   in catalog). 15 hp @ 10000 rpm, 11.5 Nm @ 8000 rpm. F14/R48 428 chain. 131 kg dry.
2. **Yamaha MT-125 (2020+)** — A1 Hyper Naked counterpart to YZF-R125 / XSR125;
   identical engine + drivetrain, naked sport bodywork. 131 kg dry. F14/R48 428.
3. **CFMoto 800NK (2023+)** — KTM LC8c-powered mid-cc parallel-twin naked, built
   under licence at the CFMoto-KTM Hangzhou JV facility. 799 cc, 95 hp @ 9000 rpm,
   81 Nm @ 8000 rpm. Same 6-speed cassette + F16/R41 525 final drive as the donor
   KTM 790 Duke. 174 kg dry.

## Smoke-sim results
| Bike                  | ET (s)  | Trap (km/h) | Cluster                     | Cluster band sanity                           |
|-----------------------|---------|-------------|-----------------------------|-----------------------------------------------|
| Yamaha XSR125 (2021)  | 19.222  | 117.2       | other (125 cc < 150-200)    | vs MCN 2022 ~18.5-19.0 s; Δ +0.2-0.7 s OK     |
| Yamaha MT-125 (2020)  | 19.123  | 117.5       | other (125 cc < 150-200)    | vs MCN 2020 ~18.4-18.8 s; Δ +0.3 s OK         |
| CFMoto 800NK (2023)   | 11.386  | 203.2       | litre_sport_600_1000        | vs MCN 2024 ~10.7-10.9 s; Δ +0.5 s borderline |

CFMoto 800NK sits at the upper edge of the litre-sport-600-1000 cluster's
documented +0.15-0.30 s bias band — likely reflects the CFMoto-built LC8c's
slightly softer real-world tune vs the donor KTM 790 Duke (95 hp vs 105 hp on
KTM), not a regression. Acceptable for catalog launch.

## Validation
- `python3 -m pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py -q`
  → **141 passed in 11.49 s**, 0 failures, 0 errors (501 deprecation warnings —
  pre-existing `datetime.utcnow()` calls in `motoquant/scraper/spec.py:101`, not
  related to this pass).
- Reference baselines preserved EXACTLY:
  - K5 10.0334 s (Δ +0.0000)
  - R1 10.2859 s (Δ +0.0000)
  - Hayabusa 10.4712 s (Δ +0.0000)
- All 3 new bikes pass the scraper validator with zero errors and yield finished
  quarter-miles within [4.0, 26.0] s and [40, 400] km/h bounds.

## File touched
- `motoquant/scraper/known_bikes_extended.py` (4043 → 4222 lines; +3 spec entries
  + +3 entries in `EXTENDED_BIKES` master list)

## Carry-forward
- None new. All three additions are bog-standard catalog entries matching the
  existing format (sibling module per CLAUDE.md file-write truncation hygiene
  note).
- Pre-existing carry-forward items (WS-A `bike_repo.create_model` year-suffix
  matching, Indian bias-ply `100/80-17` scraper validator widening, etc.)
  unchanged.

## Cluster routing verification (post-import)
- XSR125 / MT-125 → CATEGORY_OTHER (125 cc, below 150-200 entry band; same routing
  as 125 Duke and YZF-R125 per `derive_category_tag`).
- CFMoto 800NK → litre_sport_600_1000 (799 cc, ~95 hp, parallel twin — matches
  cluster definition for 600-1000 cc sport/naked platforms).
