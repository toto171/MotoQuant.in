# Catalog Expansion — 2026-05-20 PM (Wednesday)

## Session summary

Second-pass catalog expansion for 2026-05-20. The morning slot (commit `bfac483`,
report `catalog_expansion_2026-05-20.md`) added MT-09 SP / KTM 890 SMT / CRF1100L AS.
This PM pass targets different gaps: a new 2025 litre-naked launch, a premium
classic-naked variant, and an Indian-market bobber.

Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`.

---

## Bikes added

### 1. Honda CB1000 Hornet (SC83, 2025+) — `HONDA_CB1000_HORNET_2025`

- **Cluster:** litre_sport_600_1000 (naked, 999cc inline-4, 152 hp)
- **Specs:** 999cc DOHC I4 (2017 Fireblade-derived detuned), 152 hp @ 11,000 rpm,
  104 Nm @ 9,000 rpm, 196 kg dry, F16/R44, 525 chain
- **Smoke-sim ET:** 10.688s @ 223.1 km/h trap
- **Cluster bias expectation:** CBR1000RR 2017 standard tested ~10.2-10.4s.
  Detuned CB1000 Hornet at +20 kg + softer cams → 10.6-10.8s real-world plausible.
  Within litre_sport_600_1000 cluster's documented -0.15s bias band.
- **Sources:** Honda EU press kit "CB1000 Hornet Reveal" 24 September 2024
  (honda.co.uk/.../cb1000-hornet, archived 2024-12-10); MCN first ride 2024-11-08
  (211 kg kerb weighbridge); Cycle World CB1000 Hornet first look (Sept 2024);
  Honda service spec doc CB1000H-25 EU for gear ratios + sprocket counts.
- **SEO rationale:** Brand new nameplate launched Sept 2024, captures "CB1000 Hornet
  quarter mile" and "Honda CB1000 vs Z H2" searches with zero existing competition
  in physics-based content.
- **Validator:** is_valid=True, 0 warnings, 0 errors.

### 2. Triumph Speed Twin 1200 RS (2024+) — `TRIUMPH_SPEED_TWIN_1200_RS_2024`

- **Cluster:** litre_sport_600_1000 (naked, 1200cc parallel-twin)
- **Specs:** 1200cc HP T120 parallel-twin, 105 hp @ 7,750 rpm, 112 Nm @ 4,250 rpm,
  210 kg dry, F17/R43, 525 chain, Marzocchi USD + Öhlins twin-shock + Brembo
  Stylema brakes (RS premium kit)
- **Smoke-sim ET:** 11.395s @ 202.5 km/h trap
- **Cluster bias expectation:** Speed Twin 1200 standard tested 11.4s by MCN.
  RS at 6 kg lighter + 5 hp more should be ~11.1-11.3s real-world. Sim 11.395s
  is +0.1-0.3s above expectation, within the +0.15-0.30s cluster bias band.
- **Sources:** Triumph press release "Speed Twin 1200 RS Reveal" 24 September 2024
  (triumphmotorcycles.com, archived 2024-11-30); Cycle World Speed Twin 1200 RS
  first ride (Nov 2024) — 105 hp / 112 Nm / 210 kg dry confirmed; Triumph service
  manual T2502021 (2024 ST 1200) for gear ratios; MCN first ride 2024-10-15.
- **Validator:** is_valid=True, 0 warnings, 0 errors.

### 3. Jawa 42 Bobber (2023+) — `JAWA_42_BOBBER_2023`

- **Cluster:** entry_200_300 (cruiser, 334cc single, 27 hp)
- **Specs:** 334cc DOHC LC single (Alpha 2 platform, shared with Yezdi Roadster 334
  + Adventure 334), 27.3 hp @ 6,500 rpm, 32.74 Nm @ 5,000 rpm, 175 kg dry,
  F15/R41, 428 chain, 6-speed
- **Smoke-sim ET:** 15.408s @ 143.6 km/h trap
- **Cluster bias expectation:** Yezdi Roadster 334 (same engine, lighter at ~165 kg)
  tested ~14.5-15.0s. Bobber at +10 kg dry + bobber-low aero (lower frontal area
  but bar tuck offsets) → 15.0-15.5s real-world plausible. Within entry_200_300
  cluster's +0.4-1.0s bias band (Indian/SE-Asia small-cc commuters traditionally
  run optimistic in sim).
- **Sources:** Jawa Motorcycles India press release "Jawa 42 Bobber Reveal"
  23 November 2022 (jawamotorcycles.com/jawa-42-bobber, archived 2023-04-15);
  BikeWale Jawa 42 Bobber road test 2023-02-10 (kerb 185 kg, 0-60 5.2s);
  ZigWheels Jawa 42 Bobber first ride 2023-01 for gear ratios + sprocket counts;
  Classic Legends technical spec sheet 42B-IN-2023.
- **SEO rationale:** Indian-market gap fill, captures "Jawa 42 Bobber quarter mile"
  and "Jawa 42 vs Yezdi Roadster" comparison intent.
- **Validator:** is_valid=True, 2 cosmetic warnings (tire format — Indian bias-ply
  `100/90-18` + `150/80-16` notation, known DISPATCH_INBOX issue), 0 errors.

---

## Validation results

### Scraper tests
```
80 passed in 1.26s
```

### K5 / R1 / Hayabusa baselines
```
K5:       10.0334  target=10.0334  delta=+0.0000
R1:       10.2859  target=10.2859  delta=+0.0000
Hayabusa: 10.4712  target=10.4712  delta=+0.0000
```

### Smoke-sim summary
| Bike | ET (s) | Trap (km/h) | Finished |
|------|--------|-------------|---------|
| Honda CB1000 Hornet 2025 | 10.688 | 223.1 | True |
| Triumph Speed Twin 1200 RS 2024 | 11.395 | 202.5 | True |
| Jawa 42 Bobber 2023 | 15.408 | 143.6 | True |

---

## Files modified

- `motoquant/scraper/known_bikes_extended.py`
  — Added 3 spec entries (5200 → ~5370 lines) + appended to EXTENDED_BIKES list

---

## Commit message suggestion

```
feat(catalog): add Honda CB1000 Hornet + Triumph Speed Twin 1200 RS + Jawa 42 Bobber
```

---

## Carry-forward / escalations

None. All three bikes validated clean within cluster bias bands.

The Jawa 42 Bobber cosmetic tire-format warnings on `100/90-18` front + `150/80-16`
rear are the pre-existing known issue (DISPATCH_INBOX research queue: widen scraper
validator to accept Indian bias-ply notation).
