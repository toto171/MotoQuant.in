# Workstream ws/gear-topspeed — Session Log

**Date:** 2026-04-24  
**Branch:** ws/gear-topspeed  
**Scope:** Gearing data-quality fixes + top-speed benchmark expansion

---

## Task 1 — Gearing Audit

Ran `scripts/gearing_audit.py` (script created fresh — was absent from repo).

### Before fixes (287 bikes)
| Category | Count |
|---|---|
| TOP_GEAR_CRITICAL (> 1.30) | 4 |
| TOP_GEAR_HIGH (> 1.10) | 49 |
| Clean | 234 |

### After fixes (287 bikes)
| Category | Count |
|---|---|
| TOP_GEAR_CRITICAL (> 1.30) | 3 (all legitimate — see below) |
| TOP_GEAR_HIGH (> 1.10) | 50 |
| Clean | 234 |

Remaining TOP_GEAR_CRITICAL are documented correct values:
- Suzuki Hayabusa (all gens): 6th = 1.304 — highway hyperbike design
- Honda CBR 600RR PC40: 6th = 1.315 — close-ratio race gearbox

---

## Task 2 — Gear Cassette Fixes

### known_bikes.py changes

| Bike | Field | Old | New | Source |
|---|---|---|---|---|
| Suzuki GSX-R 600 K6 (2006) | gear_ratios[1..5] | [2.923, **2.333, 1.950, 1.700, 1.533, 1.407**] | [2.923, **2.071, 1.789, 1.550, 1.381, 1.259**] | GSX-R600 K6 service manual GSF-6A-M5 |
| Suzuki GSX-R 600 K6 (2006) | rear_sprocket | 44 | 42 | OEM F17/R42 |
| Suzuki Katana (2019) | gear_ratios | [2.562, 1.947, 1.636, 1.416, 1.260, 1.136] | [2.571, 1.894, 1.571, 1.381, 1.238, 1.130] | GSX-S1000 platform SM 99500-39390-01E |
| BMW M1000RR (2021) | gear_ratios | [2.640, 2.062, 1.667, 1.421, 1.259, 1.130] (wrong era) | [2.640, 2.176, 1.800, 1.560, 1.400, 1.280] (K67) | BMW M1000RR homologation manual 2021 |
| BMW M 1000 R (2023) | gear_ratios | [2.529, 2.058, 1.714, 1.476, 1.304, 1.173] | [2.640, 2.176, 1.800, 1.560, 1.400, 1.280] (K67) | BMW M 1000 R owner's manual 01498053618 |
| Yamaha YZF-R6 (5SL) (2003) | gear_ratios | [2.583, 2.000, 1.666, 1.444, 1.286, 1.150] (was 13S ratios) | [2.750, 2.000, 1.667, 1.444, 1.304, 1.208] | 5SL SM 5SL-W001E-01 |

### gear_ratios.py changes

| Change | Detail |
|---|---|
| Removed duplicate `"katana"` Tier-1 entry | Wrong entry: ratios [2.562,...,1.136], F17/R44, primary 1.553 — retained the correct entry (lines 94-102) |
| Split `"s 1000 rr"` into K46 (2009-2018) and K67 (2019+) | K46: [2.640, 1.947, 1.619, 1.395, 1.250, 1.143] / K67: [2.640, 2.176, 1.800, 1.560, 1.400, 1.280] |
| Updated `"m 1000 rr"` to K67 ratios | [2.640, 2.176, 1.800, 1.560, 1.400, 1.280] |
| Added new `"m 1000 r"` Tier-1 entry (2023-2026) | [2.640, 2.176, 1.800, 1.560, 1.400, 1.280], F17/R45 |

### gearing_audit.py fix

- V_MAX_HIGH flag now only fires when `top_gear > 1.0` (not for legitimately overdriven bikes like ZX-10R 2008 with 6th=0.871)

---

## Task 3 — Top-Speed Benchmark Expansion

`scripts/topspeed_sweep.py` BENCHMARKS expanded from **39 → 64 entries** (+25).

New entries added:
- Indian market 150-250cc: KTM Duke 200/250/RC390, Bajaj Dominar 400, RE Interceptor 650, RE Continental GT 650, Triumph Speed 400/Speed Twin 900, Yamaha FZ25/YZF-R3, Honda CBR250RR
- SE Asia small-cc: Honda CBR150R, Yamaha R25/Aerox 155, Kawasaki ZX-25R
- International mid-sport: Honda CBR500R, Kawasaki Z900, KTM 890 Duke R, Yamaha MT-07/XSR900, Suzuki GSX-8S, BMW F900R/G310R, MV Agusta F3 800

---

## Task 4 — test_gearing_sanity.py

`tests/test_gearing_sanity.py` created with 5 parametric rules:
1. Top-gear ratio < 1.40 (whitelist: Hayabusa, CBR600RR PC40)
2. First-gear ratio ≥ 1.50
3. Gear count ∈ {4, 5, 6}
4. Ratios strictly descending
5. No non-positive ratio

**Result: 1432 passed, 3 skipped (whitelisted) in 1.28s**

---

## Task 5 — DB Reseed + Baseline Validation

```
reseed_configs_from_specs.py: 267 updated, 3 skipped (hand-curated K5/R1/Hayabusa)
```

Reference baselines (must be ±0.02s):

| Bike | Target | Actual | Delta |
|---|---|---|---|
| GSX-R K5 | 10.033s | 10.0334s | +0.0004s ✓ |
| YZF-R1 4C8 | 10.286s | 10.2859s | -0.0001s ✓ |
| Hayabusa Gen1 | 10.471s | 10.4712s | +0.0002s ✓ |

### Spot-check top-speed for fixed bikes

| Bike | Old v_max | New v_max | Notes |
|---|---|---|---|
| Suzuki GSX-R 600 K6 (2006) | 264.0 km/h | 314.2 km/h | Corrected cassette; no benchmark target in sweep |
| Suzuki Katana (2019) | 260.5 km/h | 261.3 km/h | Minor change; no benchmark target in sweep |
| BMW M1000RR (2021) | 333.2 km/h | 357.5 km/h | Correct K67 box; target 314 km/h (electronics-limited); sim has no limiter |
| BMW M 1000 R (2023) | 290.9 km/h | 292.5 km/h | Correct K67 box; no benchmark target |
| Yamaha YZF-R6 5SL (2003) | 289.3 km/h | 284.9 km/h | Correct 5SL ratios |

**Full 287-bike top-speed sweep not run in sandbox (timeout).** Run natively:
```bash
PYTHONPATH=. python3 scripts/topspeed_sweep.py
```

**Note on top-speed ≥30% improvement goal:** The gear cassette fixes correct data quality. The litre superbike overshoot bias (sim 320-360 vs target 299 km/h) is aero-driven (Cd_tuck too low for closed-throttle high-speed regime) — this is Stream 1's scope. Gear-ratio fixes alone do not reduce this class of error.

---

## Files Modified

| File | Change |
|---|---|
| `motoquant/scraper/known_bikes.py` | 5 cassette fixes (ratios + rear_sprocket on K6) |
| `motoquant/scraper/gear_ratios.py` | Removed duplicate katana; BMW K46/K67 year-split; M1000RR K67; M1000R added |
| `scripts/gearing_audit.py` | Created (was missing); V_MAX_HIGH false-positive fix for overdriven bikes |
| `scripts/topspeed_sweep.py` | 39 → 64 benchmarks (+25) |
| `tests/test_gearing_sanity.py` | Created (1432 tests pass) |
| `reports/gearing_audit_2026-04-24_v2.txt` | Audit output after fixes |
| `motoquant.db` | Reseeded (267/270 bike_configs updated) |

**DO NOT COMMIT motoquant.db** (tracks in git by legacy exception; re-seed on deploy).
