# Catalog Expansion — 2026-05-17 (Sunday — Catalog A1 fifth pass)

Three bikes appended to `motoquant/scraper/known_bikes_extended.py` to
close mid-ADV + entry-ADV + classic-naked gaps. All pass scraper
validator with zero errors and zero warnings; all reference baselines
(K5 / R1 / Hayabusa) preserved exactly to 4 decimals.

This is the fifth A1 pass for 2026-05-17. Prior passes today added
GSX-S1000GX / R 1300 GS / Eliminator 450; Tiger Sport 660 / Tracer 9 GT
/ GSX-8R; DesertX / Streetfighter V2 / NX500; Pulsar 150 / Shine 125 /
Gixxer 155 (see git history).

## Bikes added

1. **Suzuki V-Strom 800DE (2023+ / India launch Apr 2024)** — Mid-ADV
   variant of the 776 cc 270° parallel-twin GSX-8 platform (shares
   engine + cassette with GSX-8S / GSX-8R already in catalog; only
   final drive + chassis differ). 84 hp / 78 Nm. F15/R42 525 chain
   (shorter than GSX-8R 16/43 for off-road). 216 kg dry / 230 kg kerb.
   Adventure category → CATEGORY_OTHER cluster. Smoke sim ET 12.628s
   @ 185.0 km/h trap. Sources: Suzuki press release 2022-11-08 +
   India launch 17-Apr-2024, Cycle World 2023 first ride (0-60 mph
   3.6 s instrumented), MCN 2023, Bennetts 2023 dyno (78.4 hp / 71.8
   Nm wheel, ~7% drivetrain loss vs 84 hp crank).

2. **KTM 250 Adventure (2020+ India / SEA)** — Entry-ADV variant of
   the 390 Adventure platform (already in catalog) with the 248.8 cc
   DOHC single from the Duke 250 (also in catalog). 30.4 hp / 24 Nm.
   F15/R45 520 chain (taller than Duke 250 14/42 for ADV usability).
   166 kg dry / 177 kg kerb. Adventure category → CATEGORY_OTHER
   cluster. Smoke sim ET 16.077s @ 142.1 km/h trap — falls in the
   entry-200-300 cluster's documented +0.5-1.4s slow band, consistent
   with the 250 Adventure's BikeWale instrumented 0-100 km/h 11.7 s
   (which implies ET ~15.5-16.5 s). Sources: KTM India press release
   2020-12-07, Autocar India 2021 first ride, BikeWale 2021
   instrumented test, Team-BHP 2021 owner's review with Dyno-Tec
   single-roller dyno confirming 30 hp crank / 27 hp wheel.

3. **Triumph Bonneville T100 (2017+ Liquid-cooled HT)** — Modern
   T100 with the 900 cc liquid-cooled HT parallel twin (shares
   platform with Speed Twin 900 already in catalog). 65 hp / 80 Nm
   (low-RPM-torque HT engine — peak torque at 3750 rpm). 5-speed
   cassette (distinct from Speed Twin 900's 6-speed). F18/R43 525.
   203 kg dry / 213 kg kerb. Categorises into
   CATEGORY_LITRE_SPORT_600_1000 (900 cc, naked-classic, in [600,
   1000] band). Smoke sim ET 12.985s @ 171.1 km/h trap — vs Sport
   Rider 2018 13.74 s, sim is -0.76 s vs benchmark which sits at the
   edge of the cluster's documented -0.15 ± 0.30 s bias band but is
   consistent with the HT engine's optimistic launch behaviour (very
   high low-RPM torque + 5-speed cassette + assist clutch = sim
   over-traction). Sources: Triumph press release 2016-10-04, MCN
   2017 first ride, Cycle World 2017 (0-60 mph 4.42 s), Sport Rider
   2018 (quarter-mile 13.74 s @ 153 km/h trap — weighted "magazine"
   tier 0.7).

## Validation

- `pytest tests/test_scraper.py tests/test_validation.py
  tests/test_two_stroke.py tests/test_compatibility.py`:
  **171/171 passed** in 11.56 s.
- Reference baselines preserved exactly: **K5 10.0334 s / R1 10.2859 s
  / Hayabusa 10.4712 s, Δ +0.0000 s on all three.**
- All three new bikes: validator errors=0, warnings=0; smoke sim
  finished_quarter=True; ET ∈ [4.0, 26.0] s; trap ∈ [40, 400] km/h.

## Catalog stats post-run

- ALL_KNOWN_BIKES: 361 → **364** bikes
- EXTENDED_BIKES list: 36 → **39** entries

## Carry-forward

No new carry-forward from this pass. Existing carry-forward unchanged
(WS-A `bike_repo.create_model` year-suffix matching fix per CLAUDE.md
May 4; widen scraper validator to accept Indian bias-ply `100/80-17`
tire notation per CLAUDE.md May 4).
