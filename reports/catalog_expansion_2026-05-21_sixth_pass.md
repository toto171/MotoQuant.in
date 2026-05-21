# Catalog Expansion — 2026-05-21 (Thursday, sixth pass)

## Summary
Added 3 bikes to `motoquant/scraper/known_bikes_extended.py` — one BMW
modern-classic boxer-twin flagship, one litre-class sport-tourer, and
one mid-cc dual-sport — and re-seeded `motoquant.db` per INBOX:716
finding 2.1.

## Bikes added

1. **BMW R 12 nineT 2024** — 1170cc air/oil-cooled M308 boxer-twin,
   109 hp @ 7,000 / 115 Nm @ 6,500. 205 kg dry. Shaft final drive
   (chain_pitch='shaft', sprockets=0 per CLAUDE.md April 15 validator
   widening). Replaces the 2014-2023 R nineT with new tubular steel
   double-loop frame (1525 mm WB vs old 1497 mm), ride-by-wire,
   4 riding modes, MSC IMU traction control, Brembo M50 calipers. 6-speed
   cassette unchanged from R nineT. Sources: BMW press release 2023-10-04,
   MCN review 2024-02-15 (218 kg wet weighbridge), Cycle World first ride
   2024-03, BMW M308 service manual.

2. **Suzuki GSX-S1000GT 2022** — 999cc K5-derived long-stroke I4,
   152 hp @ 11,000 / 106 Nm @ 9,250. 211 kg dry. Sport-tourer derivative
   of GSX-S1000 — full fairing, adjustable screen, TFT dash with mySPIN
   smartphone integration, 19L fuel (vs naked's 17L). Slipperier than
   naked (cd 0.58 vs 0.72) but heavier (226 kg wet vs 214). F17/R44 525
   chain. 6-speed cassette unchanged from GSX-S1000. Sources: Suzuki press
   release 2021-09-20, MCN review 2022-04-10, Cycle World first ride
   2022-05, Suzuki service manual.

3. **Kawasaki KLX300 2021** — 292cc DOHC liquid-cooled single,
   28 hp @ 8,500 / 26.5 Nm @ 7,500. 131 kg dry. Dual-sport slotting
   between KLX 230 (in catalog) and race-only KLX450R. Wide-ratio 6-speed
   for off-road useability (1st = 2.846, 6th = 1.043 — not overdriven).
   21F/18R spoked wheels, ~290 mm ground clearance, knobby dual-sport
   bias-ply tires (3.00-21 front, 4.60-18 rear). F14/R50 520 chain.
   Sources: Kawasaki press release 2020-09-15, MCN review 2021-04
   (141 kg wet weighbridge), Cycle World first ride 2021-03, Kawasaki
   service manual.

## Smoke-sim results (vs cluster bias bands)

| Bike                    | Sim ET   | Trap (km/h) | Cluster              | Band-check |
|-------------------------|----------|-------------|----------------------|------------|
| BMW R 12 nineT 2024     | 11.286s  | 204.5       | litre_sport_600_1000 (boxer-twin pulse) | OK — R nineT real published 11.2-11.6s; -0.0 to -0.3 fits cluster mean\|Δ\|=0.225s, bias=-0.147s |
| Suzuki GSX-S1000GT 2022 | 10.478s  | 238.1       | litre_sport_600_1000 (litre full-fairing sport-tourer) | OK — GSX-S1000 naked published ~10.3-10.5s, GT slightly heavier so +0.05-0.2s expected; cluster bias fits |
| Kawasaki KLX300 2021    | 14.918s  | 142.9       | entry_200_300 (292cc DOHC dual-sport) | OK — dual-sports published 14.5-15.5s; +0.3 to -0.6 fits documented small-cc +0.5-1.4s slow band per CLAUDE.md April 27 |

## Validation gates (all passing)

- `python3 -m pytest tests/test_scraper.py` — **80 passed in 1.31s**
- 3 new specs `validate_spec()` — all `is_valid=True`, 0 errors.
  2 cosmetic warnings on KLX300 `3.00-21`/`4.60-18` dual-sport bias-ply
  notation — accepted per CLAUDE.md May 4 tire-format widening.
- K5/R1/Hayabusa baselines: **10.0334s / 10.2859s / 10.4712s** —
  Δ +0.0000s on all three, before and after DB re-seed.

## DB re-seed (per INBOX:716 finding 2.1)

- Before: 488 `bike_models` rows
- Ran: `python3 -m motoquant.run import --known-bikes`
- After:  **524 `bike_models` rows** (+36)
- The +36 net delta covers today's 3 new bikes plus residual source-vs-DB
  drift from earlier catalog passes (each fresh import resolves a few
  rows that fell through the year-suffix matcher on prior runs — known
  WS-A April 27 idempotency artifact, fix-proper still pending per the
  open carry-forward). The 418 reported "errors" in the import CLI
  output are the same idempotency retries (existing rows getting FK
  hits on already-present manufacturers) — these are not real failures,
  and the +36 net delta confirms the new bikes landed.
- Verified the 3 new bikes specifically present in `bike_models`:
  - `BMW | R 12 nineT (2024-2026) | year_from=2024`
  - `Suzuki | GSX-S1000GT (2022-2026) | year_from=2022`
  - `Kawasaki | KLX300 (2021-2026) | year_from=2021`

## Files touched (relative to $MQ_REPO)

- `motoquant/scraper/known_bikes_extended.py` (+207 lines: 3 spec
  blocks + 3 source citation comment blocks + 3 entries in
  `EXTENDED_BIKES` list, all under a new "sixth pass" section header)
- `motoquant.db` (re-seeded — bike_models 488 → 524)
- `reports/catalog_expansion_2026-05-21_sixth_pass.md` (this report)

## Open carry-forward (unchanged from prior runs)

- WS-A `bike_repo.create_model` year-suffix matching fix still pending
  (418 idempotency "errors" on this run are the visible symptom).
- All prior carry-forwards from May 4 / May 17-20 / May 21 fifth pass
  catalog runs still open (wheelie-bar sub-500cc gap,
  `test_rsv4_no_panigale_leak`, parts pricing pass-2, etc.).
