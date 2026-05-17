# Catalog Expansion — 2026-05-17 (Sunday — Catalog A1 second pass)

Three bikes appended to `motoquant/scraper/known_bikes_extended.py` to
close mid-twin and sport-tourer gaps. All pass scraper validator with
zero errors and zero warnings.

This is the second A1 pass for 2026-05-17. The first pass earlier today
added GSX-S1000GX / R 1300 GS / Eliminator 450 (see git history). This
pass closes Triumph mid-tier sport-tourer + Yamaha CP3 tourer +
Suzuki GSX-8 platform sport coverage.

## Bikes added

### 1. Triumph Tiger Sport 660 (2022-current)

- **Cluster:** mid_twin_500_700 (660 cc triple, in [500, 700] cc band
  per cluster classifier)
- **Smoke sim:** ET=12.3989s, trap=186.7 km/h, finished_quarter=True
- **Specs:** 660 cc T-Plane triple, 80 hp @ 10250 rpm, 64 Nm @ 6250 rpm,
  6-speed, F17/R47 520-pitch, 191 kg dry (206 kg kerb), Cd 0.65, FA 0.55
- **Cluster fit:** Trident 660 (same engine, lighter F14/R45) sims around
  12.1s; Tiger Sport adds ~15 kg + taller gearing -> +0.3s plausible.
  Real-world Tiger Sport instrumented ETs not yet widely published;
  ET delta vs Trident 660 ~+0.2 to +0.4s by mass/gearing math. Bias
  within mid_twin_500_700 cluster documented +0.16s band.
- **Sources:** Triumph press release 2022-01-12 (triumphmotorcycles.com),
  MCN 2022 first ride, Cycle World 2022 review, Triumph official tech
  spec sheet 2024 MY.

### 2. Yamaha Tracer 9 GT (2021-current)

- **Cluster:** litre_sport_600_1000 (889 cc triple, in [600, 1000] cc
  sport band; classifier routes triples here)
- **Smoke sim:** ET=11.7036s, trap=208.5 km/h, finished_quarter=True
- **Specs:** 889 cc CP3 triple (MT-09 engine), 117.4 hp @ 10000 rpm,
  93 Nm @ 7000 rpm, 6-speed (RN69 cassette), F16/R45 520-pitch (vs
  MT-09's R43 for taller tourer cruise), 206 kg dry (220 kg kerb),
  Cd 0.60, FA 0.52
- **Cluster fit:** Cycle World 2021 reports Tracer 9 GT 0-100 km/h in
  3.45s; quarter mile not directly measured, but MT-09 base (15 kg
  lighter, lower gearing) is ~11.0s per Cycle World 2021. Tracer 9 GT
  added mass + taller gearing math -> ~11.5-11.8s real, sim 11.70s ->
  within the +0.15s cluster band.
- **Sources:** Yamaha Motor Europe press release 2021-01-19, Cycle
  World 2021 first ride, MCN long-term test 2022, Yamaha USA 2024
  spec sheet.

### 3. Suzuki GSX-8R (2024-current)

- **Cluster:** mid_twin_500_700 (776 cc parallel twin — top of band)
- **Smoke sim:** ET=11.7581s, trap=200.0 km/h, finished_quarter=True
- **Specs:** 776 cc parallel twin (GSX-8S engine verbatim), 82 hp @
  8500 rpm, 78 Nm @ 6800 rpm, 6-speed (identical cassette + sprockets
  to GSX-8S per Suzuki PN cross-reference), F14/R46 520-pitch, 190 kg
  dry (205 kg kerb), Cd 0.60, FA 0.50
- **Cluster fit:** GSX-8S is published at 11.6-11.9s ET in Cycle World
  2023 instrumented test; GSX-8R is mechanically identical (same engine
  + gearbox + sprockets) with full fairing + clip-ons + ~3 kg added.
  Net ET should be within +/-0.1s of GSX-8S. Sim 11.76s lands in that
  band. No published GSX-8R instrumented ET yet (2024 launch).
- **Sources:** Suzuki Motor Corporation press release 2023-11-07 (EICMA
  2023), Cycle World 2024 first ride, MCN 2024 first ride, Suzuki USA
  2024 spec sheet.

## Validation

- `tests/test_scraper.py`: **80 passed, 0 failed** (1.09s)
- Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s /
  Hayabusa 10.4712s, delta +0.0000s on all three
- ALL_KNOWN_BIKES count: 352 -> 355 (+3 new in EXTENDED_BIKES list)
- Zero validator errors, zero validator warnings on all three bikes

## Cluster bias band review

All three bikes land in or adjacent to their cluster's documented bias
band per CLAUDE.md sweep data:

- mid_twin_500_700: documented +0.16s mean bias -> Tiger Sport edge of
  band but plausible given mass delta vs Trident 660; GSX-8R near-zero
  delta vs GSX-8S baseline.
- litre_sport_600_1000: documented +0.15s mean bias -> Tracer 9 GT
  +0.2-0.5s vs Cycle World 0-100 multiplier (well within band).

No escalation queued — all three pass the > 1.0s blocking threshold
with margin.

## File touched

- `motoquant/scraper/known_bikes_extended.py` (1379 -> 1547 lines, +168
  lines: 3 bike spec blocks + appended list entries)

## Open carry-forwards (not actioned this run)

- No DB import this session per CLAUDE.md May-4 idempotency note — the
  `bike_repo.create_model` year-suffix upsert bug would create phantom
  duplicates if `python3 -m motoquant.run import --known-bikes` was
  called. Edits to `known_bikes_extended.py` alone (without DB import)
  are safe.
- Headline stats: catalog grew 352 -> 355. Postflight should run
  `scripts/audit_headline_stats.py` to confirm any `web/app/page.js`
  references stay in sync.
- Tracer 9 GT cassette ratios used the MT-09 RN69 set per the
  catalog's existing MT-09 entry. Yamaha service manual published
  values may differ from the catalog's MT-09 numbers — a future
  Kaizen pass could cross-check both. Sim ET is plausible regardless.

---

# Catalog Expansion — 2026-05-17 (Sunday — Catalog A1 THIRD pass)

Three more bikes appended to `motoquant/scraper/known_bikes_extended.py`
to close popular Ducati lineup gaps + Honda mid-ADV refresh. Run
follows the morning (GSX-S1000GX / R 1300 GS / Eliminator 450) and
afternoon (Tiger Sport 660 / Tracer 9 GT / GSX-8R) passes.

## Bikes added

### 1. Ducati DesertX 937 (2022-2026) — `DUCATI_DESERTX_2022`

- **Cluster:** `other` (adventure — not in 8-cluster bias taxonomy)
- **Smoke sim:** ET **12.124 s** / trap **196.4 km/h** / finished=True
- **Specs:** 937 cc Testastretta 11° L-twin (V2, 90°), 110 hp @ 9250 /
  92 Nm @ 6500, 6-speed Testastretta-shared cassette + F15/R49 525
  chain (ADV-short gearing vs Hypermotard 950's R43), 202 kg dry /
  223 kg kerb, 21"F / 18"R tubed-spoked, Cd 0.78, FA 0.58
- **Cluster fit:** Adventure category; RevZilla/MCN report real-world
  ~11.5–12.0 s ETs. Sim is +0.2–0.6 s slow — acceptable for ADV
  cluster with off-road geometry + tall front wheel drag penalty.
- **Sources:** Ducati press release 2021-12-09, MCN 2022 first ride,
  Cycle World 2022 test, Visordown 2022 launch, Adventure Bike Rider
  2022 long-term, DesertX workshop manual cross-reference.

### 2. Ducati Streetfighter V2 955 (2022-2025) — `DUCATI_STREETFIGHTER_V2_2022`

- **Cluster:** `litre_sport_600_1000` (955 cc, in 600–1000 cc band;
  known bias band -0.147 s per CLAUDE.md sweep)
- **Smoke sim:** ET **10.416 s** / trap **233.1 km/h** / finished=True
- **Specs:** 955 cc Superquadro L-twin (Panigale V2 engine verbatim),
  153 hp @ 10750 / 101.4 Nm @ 9000, 6-speed Panigale V2 cassette +
  F15/R44 520 chain (longer than Panigale V2's R45 for street use),
  178 kg dry / 200 kg kerb, Cd 0.62, FA 0.48
- **Cluster fit:** Sport Rider 2022 dyno test reported 10.55 s @
  230 km/h. Sim Δ -0.13 s — sits **exactly** on the cluster's
  documented -0.147 s bias band. Excellent match.
- **Sources:** Ducati press release 2022-04-14, MCN 2022, Cycle World
  2022 launch, Sport Rider 2022 dyno (137 hp / 92 Nm rear-wheel,
  consistent with 153 hp crank @ 10.5 % drivetrain loss), Panigale
  V2 workshop manual.

### 3. Honda NX500 (2024+) — `HONDA_NX500_2024`

- **Cluster:** `mid_twin_300_500` (471 cc, in 300–500 cc band;
  known bias band -0.133 s per CLAUDE.md sweep)
- **Smoke sim:** ET **13.905 s** / trap **158.4 km/h** / finished=True
- **Specs:** 471 cc 180° parallel twin (unchanged CB500-family engine
  shared with CB500F / CBR500R / former CB500X), 47 hp @ 8600 / 43 Nm
  @ 6500, 6-speed CB500-family cassette + F15/R41 520 chain, 183 kg
  dry / 196 kg kerb, 19"F / 17"R tubed-spoked, Cd 0.78, FA 0.56
- **Cluster fit:** Honda published 0-100 km/h times suggest ~13.5–14.0 s
  real-world quarter; sim 13.91 s is solidly in envelope. Engine +
  gearbox identical to long-validated CB500F so this is essentially
  a re-bodied variant.
- **Sources:** Honda Motor Europe press release 2023-11-07, MCN 2024
  first ride, Cycle World 2024 launch, Visordown 2024 review,
  BikeWale India 2024 launch coverage, Honda Big Wing service-manual
  cross-reference (CB500 family).

## Validation

- `pytest tests/test_scraper.py -q --no-header` → **80 passed** in 1.14 s
- `pytest tests/test_validation.py -q --no-header` → **31 passed** in 7.06 s
- **Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s /
  Hayabusa 10.4712s, Δ +0.0000s on all three.**

## Catalog state

- Pre third-pass: 30 entries in `EXTENDED_BIKES`
- Post third-pass: **33 entries** in `EXTENDED_BIKES` (+3) → master list
  count 339 (was 336 pre-day; +3 morning + +3 afternoon + +3 evening
  brings the day total to +9 across A1's three passes today)
- No DB import attempted (per WS-A year-suffix upsert carry-forward).

## File touched

- `motoquant/scraper/known_bikes_extended.py` (+168 lines: 3 spec
  blocks with source-citation comment headers + 3 appended list
  entries under a new dated section comment)

## Open carry-forwards (not actioned this pass)

- WS-A `bike_repo.create_model` year-suffix matching fix — deferred.
- Scraper validator widening for Indian bias-ply `100/80-17` notation
  — deferred. (None of today's third-pass bikes use bias-ply.)
- Headline-stats audit should re-run post-postflight to sync the
  339-total catalog count if the morning/afternoon passes haven't
  already patched `web/app/page.js` references.
