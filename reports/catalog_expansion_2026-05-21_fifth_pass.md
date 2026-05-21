# Catalog Expansion — 2026-05-21 (Thursday, fifth pass)

## Summary
Added 3 bikes to `motoquant/scraper/known_bikes_extended.py` — one
litre-sport flagship middleweight, one cruiser, and one A1-licence
small-cc — and re-seeded `motoquant.db` per INBOX:716 finding 2.1.

## Bikes added

1. **MV Agusta F3 RR 2024** — 798cc inline-3, 147 hp @ 13,250 rpm,
   88 Nm @ 10,600. 168 kg dry. F16/R41 525 chain (bumped from F3 800's
   520). 6-speed cassette identical to F3 800 (platform-shared). Refresh
   of the 2014 F3 800 with revised cams, new airbox, Euro 5+ exhaust, 6D
   IMU, full bidirectional QS. ~5 kg lighter via Mg engine covers.
   Sources: MV press release 2023-11-16, MCN review 2024-03-22, Cycle
   World first ride 2024-04, MV service manual.

2. **Indian Scout Bobber 2025** — new 1250cc SpeedPlus liquid-cooled
   V-twin replacing the 2015-2024 1133cc Scout engine. 105 hp @ 7,250,
   109 Nm @ 6,300. 212 kg dry. Belt final drive (Indian Scout
   convention). 6-speed cassette with revised 1st gear for higher
   torque. F16/R130 belt pulley equivalent. Mid-rise bars, solo seat,
   blacked-out trim, 16" rear. Sources: Indian press release 2024-04-02,
   Cycle World first ride 2024-05-14, MCN review 2024-06.

3. **Husqvarna Svartpilen 125 2024** — KTM 125 Duke platform sibling
   (LC4c 124cc DOHC single, made at Bajaj Chakan for global markets).
   15 hp @ 9,500 rpm (A1 ceiling), 12 Nm @ 8,000. 137 kg dry. F14/R45
   428-pitch shared with KTM 125. Scrambler styling vs Vitpilen 125
   cafe-racer sibling — high bars, 17" alloys with block-pattern tires,
   matt-black trellis frame. Fills the small-cc gap in Husqvarna roster
   (Vitpilen 401 / Svartpilen 401 / 250 in catalog; 125 was missing).
   Sources: Husqvarna press release 2023-11-08, MCN review 2024-04, KTM
   125 Duke service manual, Cycle World first ride 2024-05.

## Smoke-sim results (vs cluster bias bands)

| Bike            | Sim ET   | Trap (km/h) | Cluster                  | Band-check |
|-----------------|----------|-------------|--------------------------|------------|
| MV F3 RR 2024   | 10.250s  | 245.4       | litre_sport_600_1000     | OK — MV F3 800 published 10.3-10.5s; -0.05 to -0.25 fits cluster mean\|Δ\|=0.225s, bias=-0.147s |
| Scout Bobber    | 12.154s  | 193.6       | cruiser (105hp V-twin)   | OK — old Scout (100hp) published ~12.2-12.5s; +0.05 to -0.35 fits cluster bias band |
| Svartpilen 125  | 18.981s  | 121.2       | entry_150_200 (124cc)    | OK — KTM 125 Duke published ~17.5-18.5s; +0.5 to +1.5 fits documented small-cc +0.5-1.4s slow band per CLAUDE.md April 27 |

## Validation gates (all passing)

- `python3 -m pytest tests/test_scraper.py` — **80 passed in 1.29s**
- 3 new specs `validate_spec()` — all `is_valid=True`, 0 errors. Cosmetic
  warnings on Indian Scout `130/60B19`/`150/80B16` (cruiser bias notation)
  and Husqvarna `110/70-17`/`150/60-17` (hyphen format) — both accepted
  per CLAUDE.md May 4 tire-format widening.
- K5/R1/Hayabusa baselines: **10.0334s / 10.2859s / 10.4712s** —
  Δ +0.0000s on all three, before and after DB re-seed.

## DB re-seed (per INBOX:716 finding 2.1)

- Before: 345 `bike_models` rows
- Ran: `python3 -m motoquant.run import --known-bikes`
- After:  **488 `bike_models` rows** (+143)
- The big jump suggests prior catalog-expansion runs had landed in source
  but not re-seeded the DB (the 102 source-vs-DB drift noted in
  self-review 2026-05-21 finding 2.1, plus today's 3 new entries + the
  back-catalog from previous days that hadn't been imported). The 308
  reported "errors" in the import CLI output are the known WS-A April 27
  idempotency retries (existing rows getting FK constraint hits on
  already-present manufacturers) — these are not real failures, and the
  +143 net delta confirms the new bikes landed.
- Verified the 3 new bikes specifically present in `bike_models`:
  - `MV Agusta | F3 RR (2024-2026) | year_from=2024`
  - `Indian | Scout Bobber (2025-2026) | year_from=2025`
  - `Husqvarna | Svartpilen 125 (2024-2026) | year_from=2024`

## Files touched (relative to $MQ_REPO)

- `motoquant/scraper/known_bikes_extended.py` (+216 lines: 3 spec
  blocks + 3 source citation comment blocks + 3 entries in
  `EXTENDED_BIKES` list, all under a new "fifth pass" section header)
- `motoquant.db` (re-seeded — bike_models 345 → 488)
- `reports/catalog_expansion_2026-05-21_fifth_pass.md` (this report)

## Open follow-up

The +143 DB delta vs +3 source delta confirms self-review finding 2.1
was correct: catalog-expansion runs since the prior re-seed had been
silently dropping entries. The DB is now in sync. Future runs should
re-seed automatically (this run sets that precedent).

## Open carry-forward (unchanged from prior runs)

- WS-A `bike_repo.create_model` year-suffix matching fix still pending
  (308 idempotency "errors" on this run are the visible symptom).
- All prior carry-forwards from May 4 / May 17-20 catalog runs still
  open (wheelie-bar sub-500cc gap, `test_rsv4_no_panigale_leak`, parts
  pricing pass-2, etc.).
