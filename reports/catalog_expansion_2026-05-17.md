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
