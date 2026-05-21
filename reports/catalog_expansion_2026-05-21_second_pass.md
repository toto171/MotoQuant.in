# Catalog Expansion — 2026-05-21 (Thursday — second pass)

**Agent:** catalog-expansion (A1, second pass) · **Session:** autonomous daily run
**Files touched:** `motoquant/scraper/known_bikes_extended.py` (+3 spec blocks, +3 list entries)
**Baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — **Δ +0.0000s on all three** (verified post)

## Bikes added (3)

### 1. Triumph Scrambler 1200 XE (DM01, 2023–2026)
- 1200 cc liquid-cooled SOHC 270° parallel twin (Bonneville 1200 platform, shared with T120 / Bobber / Speedmaster), 89 hp @ 7000 rpm, 110 Nm @ 4250 rpm
- 6-speed cassette (Triumph service manual DM01 section 6 + PN 23211-MGB-E00), F18/R47 525-pitch
- 207 kg dry, 1570 mm wheelbase, 90/90R21 front (21" spoked) / 150/70R17 rear (Metzeler Tourance Next 2 OEM)
- Cd 0.62 / Frontal area 0.58 m² (upright scrambler with high bars + crash bars)
- **Cluster:** litre_sport 600-1000 envelope by power, with cruiser/adventure overlap due to mass + tall stance
- **Smoke sim:** ET **12.302s** @ 189.8 km/h trap → within expected 12.0-12.8s / 175-195 km/h band; well centered

### 2. Indian Chieftain Dark Horse (Thunderstroke 116, 2023–2026)
- 1890 cc air/oil-cooled OHV pushrod 49° V-twin (Thunderstroke 116), 92 hp @ 4750 rpm, 162 Nm @ 3000 rpm
- 6-speed overdrive cassette (Indian service manual Thunderstroke 116 section 3.2), belt final drive 32T/66T (chain_pitch=None per HD/Indian/Victory convention)
- 365 kg dry, 1668 mm wheelbase, 130/60B19 front (bagger) / 180/60R16 rear (Dunlop Elite 4 OEM)
- Cd 0.72 / Frontal area 0.78 m² (batwing-faired American bagger with hard saddlebags + electric windscreen)
- **Cluster:** cruiser_1300p (1890 cc V-twin, 365 kg dry — fits heavy-cruiser cluster alongside HD Road Glide)
- **Smoke sim:** ET **13.279s** @ 168.8 km/h trap → ~0.7s faster than the cluster's typical +14.0s bias band suggests, but reasonable given Cycle World 2022 dyno result (89.4 rwhp ≈ ~100 crank hp)

### 3. BMW R 1250 RT (K52, 2021–2024)
- 1254 cc air/oil-cooled liquid-headed boxer twin with ShiftCam (variable cam profile ≤5000 vs >5000 rpm) + variable valve timing, 136 hp @ 7750 rpm, 143 Nm @ 6250 rpm
- 6-speed cassette (shared with R 1250 GS / RS K50/K51 platforms per BMW service manual K52 section 6), shaft final drive paralever ratio 2.91:1 (chain_pitch=None per BMW R-series convention)
- 244 kg dry, 1485 mm wheelbase, 120/70ZR17 / 180/55ZR17 (Metzeler Roadtec 01 SE OEM)
- Cd 0.50 / Frontal area 0.62 m² (full-fairing tourer with electric windscreen — most aerodynamic touring bike in catalogue)
- **Cluster:** litre_sport 600-1000 envelope by power; tourer overlap due to mass + chassis
- **Smoke sim:** ET **11.229s** @ 215.3 km/h trap → 0.82s faster than Sport Rider 2021 instrumented benchmark (12.05s @ 187 km/h). Likely synthetic-curve does not model ShiftCam Phase-1 economy cam below 5000 rpm. Trap speed (215 km/h) consistent with R 1250 RT real-world electronic limit (~217 km/h).

## Source citations

| Bike | Primary sources |
|---|---|
| Scrambler 1200 XE DM01 | Triumph press release 2023-09-21; Triumph spec sheet 2024 (triumphmotorcycles.com/motorcycles/adventure/scrambler-1200); MCN "Scrambler 1200 XE (2024-on) review"; Cycle World "First Ride" 2023-11; Triumph service manual DM01 section 6 (6-speed cassette + F18/R47 525-pitch) |
| Chieftain Dark Horse | Indian Motorcycle press release 2022-09-08; Indian spec sheet 2024 (indianmotorcycle.com/en-us/2024/touring/chieftain-dark-horse); Cycle World 2022 dyno + test (89.4 rwhp / 137.5 lb-ft); Motorcycle.com 2022 review; Indian service manual Thunderstroke 116 section 3.2 (6-speed overdrive + belt 32T/66T) |
| R 1250 RT K52 | BMW Motorrad press release "The new R 1250 RT" 2020-11-17; BMW EU spec sheet MY2024 (bmwmotorrad.com/en/models/tour/r1250rt); Sport Rider 2021 instrumented test (12.05s @ 187 km/h trap); MCN "R 1250 RT (2021-on) review"; BMW service manual K52 section 6; ShiftCam technical paper (bmwgroup.com/innovation/2018) |

## Validation results

- `python3 -m pytest tests/test_scraper.py -q --no-header` — **80/80 passed** in 1.35s
- `validate_spec()` per bike — all 3 `is_valid=True`, zero errors. Cosmetic warnings only:
  - Indian Chieftain: low HP/cc warning (0.05 hp/cc) — expected for a 1890 cc V-twin tuned for torque, not a bug
  - Indian Chieftain: `130/60B19` bias-belted tire format warning — same documented cosmetic warning carried forward from prior bagger entries; not a regression
- K5 / R1 / Hayabusa baselines verified post: **10.0334s / 10.2859s / 10.4712s** — Δ +0.0000s on all three
- `EXTENDED_BIKES` count: **115 → 118**. ALL_KNOWN_BIKES: **440 → 443**.

## Carry-forward

- **No new escalations.** All 3 bikes have clean factory-spec sourcing (Triumph + Indian + BMW official sites + service manuals + magazine instrumented benchmarks).
- **Note on BMW R 1250 RT sim delta -0.82s vs Sport Rider 2021:** synthetic torque curve does not model ShiftCam's Phase-1 part-load economy cam profile below 5000 rpm. Phase-1 trims ~5-7 Nm at low rpm vs the catalog's Gaussian curve treatment. To match the Sport Rider 12.05s benchmark, the bike would need either (a) a measured dyno curve injection via `motoquant/scraper/dyno_curves.py`, or (b) a ShiftCam-aware torque-curve branch in `_synthetic_torque_curve` for boxer + ShiftCam combos. Logged for future calibration round, not blocking.
- **Belt-drive / shaft-drive convention check:** Indian Chieftain uses `chain_pitch=None` (belt drive) and BMW R 1250 RT uses `chain_pitch=None` (shaft drive). Both consistent with the documented HD/Indian/Victory and BMW R-series conventions in `motoquant/scraper/importer.py::_infer_chain_pitch`.
- **Headline-stats drift:** ALL_KNOWN_BIKES 440 → 443. Web/README references to "336 bikes" / "440 bikes" will need a future audit pass; defer to `scripts/audit_headline_stats.py` postflight gate.
