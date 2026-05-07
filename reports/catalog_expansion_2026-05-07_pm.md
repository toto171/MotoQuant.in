# Catalog Expansion — 2026-05-07 (Thursday PM, A1 second-pass)

## Summary

Second autonomous catalog run today. The morning session (commit 577ac59)
already added 3 bikes (Tuareg 660 / Apache RTR 180 / NS400R) bringing
catalog 336 → 339. This PM pass adds **2 more well-validated bikes**,
filling one Indian-market gap and one mid-weight ADV gap. Catalog count:
**339 → 341** bikes.

## New entries

| Bike | Cluster | Smoke ET | Trap | Cluster bias band fit |
|---|---|---|---|---|
| **Hero Mavrick 440 (2024-2026)** | mid-twin 300-500 | 15.4778 s | 136.75 km/h | bias -0.133s, |Δ| 0.615s — within band |
| **Yamaha Ténéré 700 (2019-2026)** | mid-twin 500-700 (ADV) | 12.7776 s | 179.79 km/h | bias -0.147s, |Δ| 0.225s — within band |

## Spec sources (manufacturer + ≥1 magazine corroboration)

- **Hero Mavrick 440** — Hero MotoCorp official spec page (heromotocorp.com/mavrick),
  BikeWale spec table, ZigWheels review database, MCN India launch coverage Feb 2024.
  Engine: 440cc air/oil-cooled SOHC single, 27 PS @ 6000 / 36 Nm @ 4000.
  Drivetrain: same 6-speed cassette as Harley-Davidson X440 (joint Hero-Harley
  platform). F15/R44, 520 chain. ~178 kg dry (187 kg kerb − ~9 kg fuel).
  Differs from X440 in head/intake tuning (X440 = 38 Nm, Mavrick = 36 Nm) and
  ergonomics (Mavrick is naked roadster vs X440 cruiser).

- **Yamaha Ténéré 700** — Yamaha 2019 press kit (yamaha-motor.eu),
  Cycle World 2020 first ride, MCN long-term test 2021. Engine: 689cc
  CP2 270° crossplane parallel-twin (shared with MT-07/R7/Tracer 7),
  73 hp @ 9000 / 68 Nm @ 6500 rpm. Drivetrain: CP2 6-speed cassette,
  F15/R46 (ADV-tall vs MT-07's 16/43), 525 chain. 187 kg dry per
  Yamaha tech sheet. 21"/18" spoked wheels.

## Sanity vs cluster bias

Both sims land within their cluster's documented bias band per CLAUDE.md
April 27 PM final cluster metrics:
- Mavrick 440 → mid-twin-300-500 cluster (bias -0.133s, |Δ| 0.615s).
  Real-world Mavrick performance reports 0-100 ~6.6s, instrumented quarter
  ~15-15.5s. Sim 15.48s = +0.0-0.5s, within band.
- Ténéré 700 → mid-twin-500-700 cluster (bias -0.147s, |Δ| 0.225s).
  MCN instrumented Ténéré 700 quarter at 12.4-12.7s. Sim 12.78s = +0.1-0.4s,
  within band (slightly slow as expected for the cluster's centred-ish bias).

## Validation gates

- `pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py` — green
- `pytest tests/test_compatibility.py tests/test_category_dispatch.py` — green
  (193/193 across the focused subset)
- **Reference baselines preserved EXACTLY**: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s on all three

## Workaround NOT applied

Per CLAUDE.md May-4 hygiene, this run did NOT touch `motoquant.db`
(no DB-side `import_batch` invocation). The two new spec entries are
appended to `EXTENDED_BIKES` and will be picked up by the standard
`db seed` flow on the next deploy. This avoids re-triggering the WS-A
`bike_repo.create_model` year-suffix duplicate-row regression and stays
consistent with the May-7 morning session pattern (which used the
direct `import_batch(db, [...])` workaround).

## Files touched

- `motoquant/scraper/known_bikes_extended.py` (498 → 595 lines, +2 bikes)
- `reports/catalog_expansion_2026-05-07_pm.md` (this file)

## Open carry-forward

- (a) Mavrick tire format `110/70-17` and `150/60-17` still trip the
  Indian-bias-ply cosmetic warning (validator regex hardcoded for ZR/R radial).
  Same family as the May-4 Hero Xtreme 200S 4V and May-7 morning carry-forward.
  Not a regression; logged for the validator-widening instruction proposal.
- (b) The May-4 + morning May-7 WS-A `bike_repo.create_model` year-suffix
  fix is still pending and remains the single largest source of avoidable
  workaround friction in autonomous catalog runs.
- (c) DB-side seed of the 2 new bikes deferred to the next manual `db seed`
  pass. Not blocking — the spec entries are picked up by the test harness
  via `ALL_KNOWN_BIKES`.
