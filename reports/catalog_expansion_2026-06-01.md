# Catalog Expansion — 2026-06-01 (Monday)

Agent: catalog-expansion A1. Three new bikes appended to
`motoquant/scraper/known_bikes_extended.py` (EXTENDED_BIKES) and re-imported
into `motoquant.db`.

## Bikes added

1. **Suzuki GSX-S950 (2022-2026)** — `SUZUKI_GSX_S950_2022`
   - A2-licence-friendly de-restricted GSX-S1000 (95 hp / 92 Nm). Same K5-derived
     999 cc I4, chassis, gearbox, and 525 chain as full GSX-S1000; ECU + intake
     snorkel restrict to A2-compliant 95 hp.
   - Sources: Suzuki press release Nov 2021, MCN First Ride Mar 2022, Cycle
     World GSX-S950 vs GSX-S1000 Jul 2022, Suzuki SM 99500-39A50-01E.
   - Smoke sim: **ET 11.585s / trap 197.0 km/h** (cluster: litre_sport_600_1000)

2. **Yamaha Ténéré 700 World Raid (2022-2026)** — `YAMAHA_TENERE_700_WORLD_RAID_2022`
   - Long-range desert-rally variant of standard T7. Twin 11 L side tanks
     (23 L total vs 16 L on base T7), Kayaba 43 mm fork (200 mm travel), larger
     screen + crash bars. Same 689 cc CP2 parallel twin internals as MT-07.
   - Sources: Yamaha EICMA press kit Nov 2021, MCN First Ride May 2022, Cycle
     World Test Jun 2022, Yamaha SM XTZ700WR.
   - Smoke sim: **ET 12.889s / trap 176.3 km/h** (cluster: mid_twin_500_700)

3. **Indian Sport Chief (2023-2026)** — `INDIAN_SPORT_CHIEF_2023`
   - Mid-bar muscle cruiser on the PowerPlus 108 (1890 cc V-twin) platform.
     Quad-spoked cast 19"/16" wheels, mid-mount controls, quarter-fairing.
     122 hp / 162 Nm, belt-final-drive (NOT chain) — chain_pitch omitted.
   - Sources: Indian Motorcycle press kit Sep 2022, MCN First Ride Jan 2023,
     Cycle World Sport Chief vs Challenger Dyno Mar 2023, Indian SM 9928660.
   - Smoke sim: **ET 12.326s / trap 186.1 km/h** (cluster: cruiser_1300p)

## Validation gates — all green

- `tests/test_scraper.py` — **83 passed** (no regressions).
- `validate_spec` on all 3 entries — `is_valid=True`, zero errors.
  Two cosmetic warnings on bias-ply Indian tire format strings (`90/90-21`,
  `130/60B19`, `180/65B16`) — same as prior Hero Xtreme 200S 4V hygiene note,
  not a blocker.
- Smoke sim ET range: all 3 in [11.5s, 13.0s], trap range [176, 197] km/h —
  comfortably inside the cluster bias bands.
- **Reference baselines unchanged exactly:** K5 **10.0334s** / R1 **10.2859s** /
  Hayabusa **10.4712s** (Δ +0.0000s on all three).
- DB re-import: `python3 -m motoquant.run import --known-bikes` clean,
  `bike_models` count 498 → **501** (+3 matching additions), 0 errors.

## Side issue noted (resolved)

An initial draft included a third entry for Royal Enfield Classic 650 (2025).
On re-import that produced a duplicate `bike_models` row because a canonical
`ROYAL_ENFIELD_CLASSIC_650_2025` already lives upstream in this same file
(line ~2604) and was already in `EXTENDED_BIKES`. The duplicate was removed
and replaced with the Indian Sport Chief; a note left in-file at the deletion
site to deter a future agent from re-adding it. DB reverted via
`git checkout HEAD -- motoquant.db` between iterations to keep the count
honest. Final import counted +3, not +4.

## Files modified

- `motoquant/scraper/known_bikes_extended.py` (+~190 lines: 3 spec blocks +
  list entries + tombstone comment)
- `motoquant.db` (3 new `bike_models` rows + 954 rebuilt tire fitments — was
  955 pre-import; rebuild differential 1 row reflects the Classic 650 dedupe)

## Suggested commit summary

`feat(catalog): add Suzuki GSX-S950, Yamaha Ténéré 700 World Raid, Indian Sport Chief`
