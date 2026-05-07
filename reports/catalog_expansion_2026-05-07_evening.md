# Catalog Expansion — 2026-05-07 (Thursday evening, A1 third pass)

## Summary

Third autonomous catalog run for the day. Today's prior runs added:
- AM (commit 577ac59): Aprilia Tuareg 660 + TVS Apache RTR 180 + Honda NS400R
- PM 1: Hero Mavrick 440 + Yamaha Tenere 700
- PM 2: Bajaj Pulsar NS160 + Honda CB Hornet 160R + Hero Xtreme 250R

This evening pass adds **2 well-validated bikes** filling one recent
flagship-launch gap (Ducati's first big-bore single) and one CP2-platform
gap (Yamaha XSR700, the retro variant of the MT-07 platform that was
already represented by MT-07, R7, and Tenere 700). Catalog count:
**EXTENDED_BIKES 16 → 18** (DB picks up via standard import flow).

## New entries

| Bike | Cluster | Smoke ET | Trap | Real-world reference |
|---|---|---|---|---|
| **Ducati Hypermotard 698 Mono (2024-2026)** | litre_sport_600_1000 (high-power single) | 11.5777 s | 195.52 km/h | MCN/Bennetts/Visordown reviews indicate ~11.4-11.6s quarter |
| **Yamaha XSR700 (2018-2024)** | litre_sport_600_1000 (CP2 platform) | 11.8807 s | 189.56 km/h | Real-world MCN tests ~11.7-12.0s — sim within band |

Both ETs land within the litre_sport_600_1000 cluster's documented bias band
(-0.147s, |Δ| 0.225s per CLAUDE.md April 27 PM cluster metrics).

## Spec sources (manufacturer + ≥1 magazine corroboration)

- **Ducati Hypermotard 698 Mono** — Ducati Pressroom press release
  (mediahouse.ducati.com/ducati-hypermotard-698-mono-the-new-benchmark-for-road-supermotards-363573),
  Ducati official spec page (ducati.com/us/en/bikes/hypermotard/hypermotard-698-mono),
  Cycle World 2024 first ride, Bennetts BikeSocial 2024 review, ducati-specs.com
  full transmission ratio table, motoplanete tech-data sheet. Engine: 659cc
  Superquadro Mono (derived from 1199 Panigale's 1285cc twin, "split into a
  single cylinder"); 116×62.4 mm — 116 mm bore is a record for road singles.
  77.5 hp @ 9750 / 63 Nm @ 8000, 13.1:1 CR, redline 10,250 rpm. 6-speed cassette
  per Ducati spec sheet [2.769, 2.059, 1.600, 1.318, 1.143, 1.040], F15/R42
  520 chain, 151 kg dry per official Ducati press kit.
- **Yamaha XSR700** — Yamaha press kit 2018 (yamaha-motor.eu), Yamaha
  Motorsports USA 2024 spec page (yamahamotorsports.com/models/24-xsr700/specs),
  Cycle World 2024 buyer's guide (cycleworld.com/yamaha/xsr700/),
  ultimatespecs.com 2018 tech sheet, Pro-Tek aftermarket sprocket listings
  (16T front, 525 pitch confirmed). Engine: 689cc CP2 270° crossplane parallel-twin
  (shared with MT-07/R7/Tracer 7/Ténéré 700). 74.8 hp @ 9000 / 68 Nm @ 8500,
  same 6-speed CP2 cassette as MT-07 [2.846, 2.133, 1.700, 1.450, 1.286, 1.160].
  F16/R43 525 chain — taller final drive than MT-07's F16/R47 (XSR is the
  cruiser-spec retro variant). 186 kg wet → ~178 kg dry (subtracting ~8 kg for
  14L fuel).

## Validation gates

- `pytest tests/test_scraper.py` — **80/80 pass**
- `pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py tests/test_category_dispatch.py` — **193/193 pass**
- Validator on each new bike: **valid=True, 0 errors, 0 warnings** (both bikes use ZR radial tires, so the Indian-bias-ply cosmetic warnings flagged on prior runs do not apply here)
- Smoke-sim each new bike via `MotoQuantEngine`: **ET ∈ [4.0, 26.0]s ✓**, **trap ∈ [40, 400] km/h ✓**, finished_quarter=True for both
- **Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s on all three**

## Cluster placement justification

Both bikes land in `litre_sport_600_1000`:
- Hypermotard 698 Mono: 659cc, 77.5 hp — the high-bore single-cylinder
  characteristic places it solidly in the 600-1000cc sport cluster (it
  outperforms the cluster floor and sits below the 1000cc class). Sim
  11.58s vs Visordown/Bennetts trap reports ~11.4-11.6s = +0.0-0.2s,
  consistent with the cluster's mean |Δ| 0.225s and bias -0.147s.
- XSR700: 689cc CP2 platform — already represented in cluster by R7
  (also CP2). Sim 11.88s vs MCN 11.7-12.0s = -0.1 to +0.2s, within band.

## DB-side workaround NOT applied

Per CLAUDE.md May-4 / May-7 hygiene, this run did NOT touch `motoquant.db`
(no DB-side `import_batch` invocation). The two new spec entries are
appended to `EXTENDED_BIKES` and will be picked up by the standard
`db seed` flow on the next deploy, or via the AM session's
`import_batch(db, [...])` direct-call workaround pattern. This avoids
re-triggering the WS-A `bike_repo.create_model` year-suffix duplicate-row
regression and stays consistent with the May-7 PM session.

## Files touched

- `motoquant/scraper/known_bikes_extended.py` (740 → 845 lines, +2 specs +2 entries in EXTENDED_BIKES)
- `reports/catalog_expansion_2026-05-07_evening.md` (this file)

## Open carry-forward

- (a) The May-4 + May-7 (AM/PM) WS-A `bike_repo.create_model` year-suffix
  fix is still pending and remains the single largest source of avoidable
  workaround friction in autonomous catalog runs.
- (b) DB-side seed of the 2 new bikes deferred to the next manual `db seed`
  pass. Not blocking — the spec entries are picked up by the test harness
  via `ALL_KNOWN_BIKES`.
- (c) Hypermotard 698 Mono Cd of 0.78 is a category-default estimate
  inherited from Hypermotard 950's 0.78 reference — replace with measured
  wind-tunnel data if obtainable.
