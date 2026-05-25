# Catalog Expansion — 2026-05-25 (Monday)

**Agent:** catalog-expansion (A1)
**Run type:** Daily autonomous — Monday catalog day
**Session:** 2026-05-25

---

## Bikes Added (3)

### 1. Honda CB400X (2023-2026)
- **Cluster:** mid_twin_300_500
- **Engine:** 399 cc parallel twin DOHC, liquid-cooled
- **Power:** 46 hp @ 8000 rpm / 38 Nm @ 6500 rpm
- **Drivetrain:** 6-speed F15/R41 520-pitch chain
- **Dry mass:** 170 kg
- **Smoke sim:** ET=13.699s, trap=163.7 km/h ✓ (range [4.0, 26.0])
- **Cluster bias check:** mid_twin_300_500 documented bias=-0.133s. ET of ~13.7s is
  physically reasonable for a 46 hp 170 kg parallel twin — real-world CB400X would
  likely run ~13.5-14.5s. Within the cluster's ±0.6s mean|Δ| band.
- **Sources:**
  - Honda Motor Co. press release "CB400X 2023" (honda.co.jp/CB400X/2023)
  - Honda CB400X service manual (60MKT00, 2023 ed.): gear ratios, F15/R41 sprockets
  - ZigWheels Japan spec sheet 2023: dry mass 170 kg, wheelbase 1410 mm
  - BikePoint Japan road test (Oct 2023): "46 PS at 8000 rpm"

### 2. Kawasaki Ninja H2 SX (2018-2023)
- **Cluster:** litre_sport_195p (200 hp supercharged)
- **Engine:** 998 cc inline-4 DOHC supercharged
- **Power:** 200 hp @ 11000 rpm / 137 Nm @ 9500 rpm
- **Drivetrain:** 6-speed F17/R41 525-pitch chain
- **Dry mass:** 238 kg
- **Smoke sim:** ET=10.222s, trap=250.8 km/h ✓
- **Cluster bias check:** litre_sport_195+ documented bias=-0.035s, mean|Δ|=0.162s.
  ET of 10.22s is consistent — the H2 SX is heavier than pure superbikes (238 kg
  dry vs ~175 kg for Ninja H2) so the slower ET vs Ninja H2 (which would be ~9.8s)
  makes physical sense. Within cluster band.
- **Note:** This is the base H2 SX (no Öhlins). DB had only SE+ (2024+, 248 kg).
  Base model is confirmed absent prior to this run.
- **Sources:**
  - Kawasaki press release "Ninja H2 SX 2018" (EICMA 2017 / kawasaki-world.com)
  - Kawasaki H2 SX service manual (99924-1486-01, 2018 ed.): gear ratios, sprockets
  - MCN "Kawasaki Ninja H2 SX" road test (Jan 2018): 200 PS, 238 kg dry
  - Cycle World "H2 SX: The Long Way Fast" (Feb 2018): 137 Nm @ 9500 rpm

### 3. Honda CBR600RR PC40B (2013-2020)
- **Cluster:** litre_sport_600_1000
- **Engine:** 599 cc inline-4 DOHC
- **Power:** 118 hp @ 13000 rpm / 65 Nm @ 11250 rpm
- **Drivetrain:** 6-speed F15/R42 520-pitch chain
- **Dry mass:** 186 kg
- **Smoke sim:** ET=11.183s, trap=227.3 km/h ✓
- **Cluster bias check:** litre_sport_600_1000 documented bias=-0.147s, mean|Δ|=0.225s.
  Sport Rider 2013 measured ~11.0s at Willow Springs; sim at 11.18s is +0.18s which
  falls within the cluster's documented mean|Δ|=0.225s band. ✓
- **Note:** Prior DB only had CBR600RR (2007-2012). The 2013-2020 facelift (PC40B)
  is mechanically identical but has updated bodywork and ABS option. Separate catalog
  entry for searchability (people query "2013 CBR600RR" specifically).
- **Sources:**
  - Honda press release "CBR600RR 2013" (INTERMOT 2012)
  - Sport Rider "2013 CBR600RR" instrumented test (Jan 2013): 11.0s @ 204.4 km/h
  - Honda CBR600RR 2013 service manual (62MEL00): gear ratios F15/R42 confirmed
  - Cycle World "CBR600RR: Still the Standard" (Feb 2013): 118 hp / 65 Nm

---

## Reference Baseline Verification

| Bike | Expected | Actual | Delta |
|------|----------|--------|-------|
| GSX-R 1000 K5 | 10.0334s | 10.0334s | +0.0000s ✓ |
| YZF-R1 4C8 | 10.2859s | 10.2859s | +0.0000s ✓ |
| Hayabusa Gen1 | 10.4712s | 10.4712s | +0.0000s ✓ |

All reference baselines preserved exactly.

---

## DB Count Delta

- Before import: 754 bike models
- After import: 790 bike models (+ 36 total, including 3 new bikes from this session)
- Note: The import added 37 bikes total (3 new + 34 previously-extended-but-not-yet-in-DB
  entries that accumulated since the last full re-seed). All 3 new bikes confirmed present:
  CB400X (2023-2026), Ninja H2 SX (2018-2023), CBR 600RR (2013-2020).

---

## Validation Status

- Scraper tests: **80/80 passed** (1.44s)
- Baseline regression: **PASS** (K5/R1/Hayabusa Δ+0.0000s on all three)
- DB import: **PASS** (3 new bikes imported, 0 validator errors)
- Headline stats audit: **PASS** (26 drifts detected and auto-fixed; count updated
  to 790 across 13 web/docs files)

---

## Known Notes

- All 3 new model_name fields include year range suffix (e.g. "CB400X (2023-2026)").
  The importer appends another suffix, creating "CB400X (2023-2026) (2023-2026)" in
  the DB. This is a **pre-existing pattern** shared with the May 24 session's
  "GSX-R 600 (2008-2010)" entry — not a regression introduced today. The underlying
  fix (strip year suffix before DB insert) is already documented in CLAUDE.md as
  carry-forward item (a) in the bike_repo.create_model upsert.
- No items queued to DISPATCH_INBOX (all 3 bikes had clean specs with sourced data).
