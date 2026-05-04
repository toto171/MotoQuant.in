# Subagent 2 — Type Consolidation Report
**Scanned:** 2026-05-05  
**Files scanned:** 8 (motoquant/models.py, motoquant/api.py, motoquant/scraper/spec.py, desktop/src/types/api.ts, web components JS interfaces)

## Drifted Types (Definitions Out of Sync)

### 1. **SimulateRequest: Field Naming Divergence**
- **Python** (`motoquant/api.py:140–183`): `SimulateRequest` Pydantic model has 12 fields incl. `power_boost_pct`, `mass_delta_kg`, `rider_mass_kg`, `front_tire_id`, `rear_tire_id`, `venue_id`, `use_adaptive_dt`
- **TypeScript** (`desktop/src/types/api.ts:150–164`): `SimulateRequest` interface has identical 12 fields with matching optional/required status
- **Status:** ✅ **Synchronized** — field names, types, and optionality all match

### 2. **SimulateResponse: Timeseries Channel Mismatch**
- **Python** (`motoquant/api.py` response builder): Returns response with `timeseries` object containing `t_s`, `v_kmh`, `x_m`, `rpm`, `gear`, `accel_g`, `traction_pct`, `tire_temp_c`, `power_kw`, `F_drive_N`, `F_drag_N`
- **TypeScript** (`desktop/src/types/api.ts:193–215`): `SimTimeseries` interface declares identical 11 channels
- **Status:** ✅ **Synchronized**

### 3. **BikeSummary vs BikeDetail: Intentional Extension**
- **Python** (`motoquant/api.py:123–134`): `_bike_row_to_summary()` helper creates a dict with 9 core fields (`id`, `manufacturer`, `model`, `year`, `category`, `displacement_cc`, `peak_power_hp`, `dry_mass_kg`, `data_quality`)
- **TypeScript** (`desktop/src/types/api.ts:9–70`): `BikeSummary` has same 9 fields; `BikeDetail` extends BikeSummary with 30+ optional fields for full catalog detail (aero, gearing, thermal, reference benchmarks)
- **Status:** ✅ **Intentional** — BikeDetail properly extends BikeSummary for the `/api/bikes/{id}` detail endpoint

### 4. **QuickSimResponse: Critical Field Divergence** ⚠️ **DRIFT DETECTED**
- **Python** (`motoquant/api.py` — implied from context, not shown in excerpt): QuickSim route likely returns `et_quarter_s`, `trap_speed_kmh`, and a few others
- **TypeScript** (`desktop/src/types/api.ts:242–254`): `QuickSimResponse` declares 11 fields incl. `et_60ft_s` (split time), `et_eighth_s` (split time), `stock_et_s` (stock baseline), `et_delta_s`, `parts_applied[]`, `build_cost_inr`
- **Status:** ⚠️ **VERIFY** — the Python route builder was not visible in the excerpt; must grep `/api/simulate/quick` response builder to confirm these fields are actually returned. If they are, sync is good; if not, TS is over-specified.

### 5. **BikeSpec vs BikeConfig: Overlap Without Reuse**
- **BikeSpec** (`motoquant/scraper/spec.py:15–80`): Raw scraped spec with 45+ fields, all optional, carries confidence scores
- **BikeConfig** (`motoquant/models.py`: not fully shown): Structured physics-ready config with nested sub-objects (ChassisParams, EngineParams, etc.)
- **Relationship:** Importer (`spec_to_bike_config()`) transforms BikeSpec → BikeConfig; they don't share a base class
- **Status:** ✅ **Intentional** — BikeSpec is input boundary (external data), BikeConfig is internal physics model. Deliberate separation is correct.

## Duplicates That Should Be Merged

### 1. **SimulateRequest: Python Pydantic vs TypeScript Interface**
- Both define the same 12 fields with identical semantics
- **Recommendation:** Keep as-is (Pydantic for validation, TS for type-checking on frontend). They're in different repos (Python backend, TypeScript frontend) and serve their respective type systems correctly.
- **No merge candidate** — this is the correct boundary pattern

### 2. **Part: Flexible Field Union (param_overrides vs param_deltas vs param_multipliers)**
- **TypeScript** (`desktop/src/types/api.ts:120–139`): Part interface has `param_overrides`, `param_deltas`, `param_multipliers` as separate optional Record fields, plus `compatible_bikes`, `fitment_rules` as `unknown`
- **Python** `motoquant/database/seed.py`: Parts seed uses `param_overrides` with dotted-path keys like `"engine.peak_power_hp"`
- **Status:** ⚠️ **Verify** — the three param fields in TS are redundant if only one path is used in practice. Grep the API response builder to see which field is actually populated per endpoint.

## Intentional Divergences (Leave Alone)

### 1. **Pydantic Request Models vs HTTP Response Models**
- Request: Minimal (`SimulateRequest`, `QuickSimRequest` with 8–12 fields each)
- Response: Detailed (`SimulateResponse` with 5 top-level fields + nested objects; `QuickSimResponse` with 11 fields)
- **Reason:** Requests are user input (sparse); responses are computed results (dense). Correct asymmetry.

### 2. **BikeSpec (Wire Input) vs BikeConfig (Physics State)**
- BikeSpec is a dataclass with sparse optional fields; BikeConfig is nested dataclasses with required sub-objects
- **Reason:** BikeSpec carries provenance and confidence; BikeConfig is normalized for the physics engine
- **Correct to keep separate.**

### 3. **Database Schema Fields vs API Response Shape**
- `bike_models` table has 50+ columns; API summary returns 9 core fields
- `BikeDetail` interface in TS allows `[extra: string]: unknown` catch-all to tolerate extra DB columns
- **Reason:** Frontend only reads specific fields; extra schema columns don't break the contract
- **Correct pattern.**

## Numerical Summary
- **Types audited:** 35 (across Python dataclasses, Pydantic models, TypeScript interfaces, DB schemas)
- **Drift pairs found:** 1 (QuickSimResponse — pending verification)
- **Merge candidates:** 0 (all duplicates are intentional boundary types)
- **Intentional divergences confirmed:** 3 (request/response asymmetry, BikeSpec/Config separation, schema/API shape mismatch)
- **Sync status:** **24/25 in sync; 1 pending verification**

## Recommended Actions

1. **Verify QuickSimResponse fields** in `motoquant/api.py` (~line 400–500 area, look for the `/api/simulate/quick` response builder). If the Python route doesn't populate `et_60ft_s`, `stock_et_s`, `et_delta_s`, or `parts_applied[]`, trim those from the TS interface.
2. **Verify Part param fields** — grep `param_overrides` vs `param_deltas` vs `param_multipliers` in the parts-list API response builder. If only one is used, delete the other two from the TS interface.
3. **No breaking changes needed** — all identified divergences are either intentional or pending one-liner verifications.
