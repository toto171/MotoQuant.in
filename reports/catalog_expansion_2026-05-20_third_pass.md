# Catalog Expansion — 2026-05-20 Third Pass (Wednesday)

## Session summary

Third-pass catalog expansion for 2026-05-20. Previous passes added MT-09 SP /
KTM 890 SMT / CRF1100L AS (morning) and Honda CB1000 Hornet / Triumph Speed
Twin 1200 RS / Jawa 42 Bobber (PM). This pass targets three distinct gaps:
a popular retro naked missing from the Kawasaki lineup, Yamaha's premium
MT-07 variant, and Suzuki's 125cc sportsnaked for the Indian/EU small-cc segment.

Added 3 production motorcycles to `motoquant/scraper/known_bikes_extended.py`.

---

## Bikes added

### 1. Kawasaki Z650RS (2022+) — `KAWASAKI_Z650RS_2022`

- **Cluster:** mid_twin_500_700 (naked retro, 649cc ER650 parallel-twin, 68 hp)
- **Specs:** 649cc DOHC liquid-cooled I2, 68 hp @ 8,000 rpm, 65.7 Nm @ 6,700 rpm,
  171 kg dry, ER650 6-speed (2.438/1.714/1.333/1.111/0.966/0.852) F15/R46, 520-pitch
- **Smoke-sim ET:** 12.051s @ 186.3 km/h trap
- **Cluster bias expectation:** Z650 (same engine, 169 kg) measured ~12.3-12.8s
  real-world. Z650RS at 2 kg heavier + slightly more upright position → 12.1-12.5s
  expected. Sim 12.051s within mid_twin_500_700 cluster's documented -0.13s bias band.
- **Sources:** Kawasaki EU press release "Z650RS Reveal" EICMA Nov 2021
  (kawasaki.eu/Z650RS/2022); MCN first ride Dec 2021 (confirming 68 hp / 65.7 Nm /
  171 kg dry ABS spec); Visordown Dec 2021 review (confirming identical cassette/chain
  to Z650); Kawasaki service manual EX650P (2022) for gear ratios.
- **Validator:** is_valid=True, 0 warnings, 0 errors.

### 2. Yamaha MT-07 SP (2021+) — `YAMAHA_MT07_SP_2021`

- **Cluster:** mid_twin_500_700 (naked, 689cc CP2 parallel-twin, 73.4 hp)
- **Specs:** 689cc DOHC LC I2, 73.4 hp @ 8,750 rpm, 68 Nm @ 6,500 rpm,
  175 kg dry, CP2 6-speed (2.846/2.125/1.631/1.333/1.167/1.043) F15/R45, 520-pitch.
  Adds Öhlins TRRS shock + KYB USD fork vs standard MT-07; −2 kg vs 2021 standard.
- **Smoke-sim ET:** 11.918s @ 189.7 km/h trap
- **Cluster bias expectation:** MT-07 standard (73 hp, ~177 kg dry) measured
  ~11.8-12.2s real-world. SP at 2 kg lighter → 11.7-12.0s expected. Sim 11.918s
  is within the cluster's -0.13s bias band.
- **Sources:** Yamaha Motor EU press release "MT-07 SP Reveal" 2020-11-20
  (yamaha-motor.eu/mt-07-sp/2021); MCN first ride 2021-02-15 (189 kg wet / 73.4 hp);
  Cycle World MT-07 SP first look 2020-11-20 (Öhlins TRRS confirmed); Yamaha service
  manual 1WS (2021 MT-07/MT-07 SP) for gear ratios.
- **Validator:** is_valid=True, 0 warnings, 0 errors.

### 3. Suzuki GSX-S125 (2017+) — `SUZUKI_GSXS125_2017`

- **Cluster:** entry_150_200 (sportsnaked 124cc, 14.8 hp — same cluster as CB125R/KTM 125 Duke)
- **Specs:** 124.4cc DOHC LC single, 14.8 hp @ 10,500 rpm, 11.2 Nm @ 8,000 rpm,
  134 kg dry, 6-speed (2.923/1.882/1.409/1.130/0.958/0.838) F15/R43, 428-pitch
- **Smoke-sim ET:** 20.232s @ 115.4 km/h trap
- **Cluster bias expectation:** CB125R (14.7 hp, 126 kg) benchmarks at ~18-20s.
  GSX-S125 at 134 kg and same power class → 19-21s expected. Sim 20.2s is within
  the entry_150_200 cluster's documented +0.25-0.75s slow bias band.
- **Sources:** Suzuki India product page (14.8 hp / 11.2 Nm / 134 kg dry, accessed
  2020-11-14); Suzuki Japan tech sheet GSX-S125L7 (2017) for bore/stroke/gear ratios;
  Visordown GSX-S125 first ride 2016-10-19 (15F/43R, 428-pitch confirmed).
- **Validator:** is_valid=True, 0 warnings, 0 errors.

---

## Validation results

### Scraper tests
```
80 passed in 1.28s
```

### K5 / R1 / Hayabusa baselines
```
K5:       10.0334  target=10.0334  delta=+0.0000
R1:       10.2859  target=10.2859  delta=+0.0000
Hayabusa: 10.4712  target=10.4712  delta=+0.0000
```

### Smoke-sim summary
| Bike | ET (s) | Trap (km/h) | Finished | In-bounds |
|------|--------|-------------|---------|-----------|
| Kawasaki Z650RS 2022 | 12.051 | 186.3 | True | True |
| Yamaha MT-07 SP 2021 | 11.918 | 189.7 | True | True |
| Suzuki GSX-S125 2017 | 20.232 | 115.4 | True | True |

---

## Files modified

- `motoquant/scraper/known_bikes_extended.py`
  — Added 3 spec entries (5369 → 5545 lines) + appended to EXTENDED_BIKES list

---

## Commit message suggestion

```
feat(catalog): add Kawasaki Z650RS + Yamaha MT-07 SP + Suzuki GSX-S125
```

---

## Carry-forward / escalations

None. All three bikes validate clean with zero warnings/errors, finish quarter-mile
within the valid ET window, and fall within their respective cluster bias bands.
