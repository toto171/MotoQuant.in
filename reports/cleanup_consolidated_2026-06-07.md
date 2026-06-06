# Cleanup pass — consolidated report — 2026-06-07

**Trigger:** operator-requested full-code audit (run early; normal cadence is last Sunday monthly).
**Scope:** 7 house subagents (scripts/subagents/01-07) + agent-0 truncation/parse sweep (167 py / 48 json / 11 yaml / 747 text files — zero failures; ci.yml was the last corrupted file, fixed 2026-06-06).

## Applied this pass (high-confidence mechanical)
- Deleted 11 dead files: 6 one-shot/orphaned scripts (_patch_physics_dispatch, patch_h2_h2r_2026_04_29, patch_2026_04_30_drag_fitments, pricing_audit_2026_04_27, audit_calibrator, sweep_batched), 2 orphaned binaries (calibrator_v2.pkl, calibration_v2_2k.npz), motoquant/scraper/parameter_sources.py (1,897 dead lines), 2 unimported web components (BikeSilhouette, SpecCorrectionForm).
- Blog factual fix: K5 baseline 10.2859→10.0334 (2 sites, documented drift).
- Privacy page: Railway/us-west2(Oregon) → Render/Singapore (legal accuracy).
- dragy.py: QUARTER_MILE_M/EIGHTH_MILE_M now import from constants.py (re-export preserved for ecu.py).
- build_optimizer._check_envelope: fail-SAFE on exception (full-sim fallback + warning; was silently "in envelope").
- roi._resolve_price + seed_recommended_fitments: silent except → logged warnings.
- api.py SurrogatePredictRequest: 3 Optional fields annotated honestly (int|None / float|None).

## Verification
test_dragy 56-pass · test_build_optimizer 14-pass · targeted fail-safe/logging probes pass · K5/R1/Hayabusa Δ+0.0000 ×3 · TestClient /api/health 200.

## Queued (medium-confidence)
See DISPATCH_INBOX.md instruction block 2026-06-07 (8 items + false-positive log).

---

# Subagent 1 — Deduplication Report
**Scanned:** 2026-05-05  
**Files scanned:** 120+ across motoquant/, tests/, web/, scripts/  

## High-confidence consolidations (apply these)

### 1. **Test Setup Boilerplate: _TestDB Class Duplication**
- **Files affected:** `tests/test_cli.py` (line 46–58), `tests/test_analysis.py` (line 58–83), `tests/test_recommendations.py` (line 55–76)
- **Issue:** Three near-identical `_TestDB` classes with 90% code overlap. All use the same pattern:
  - Create temp DB in `/tmp` with `NamedTemporaryFile`
  - Set `PRAGMA journal_mode=DELETE`
  - Call `seed_all(mdb)`
  - Cache in class variable `_mdb`
- **Suggested target:** Create `tests/conftest.py` with a shared `_TestDB` fixture
- **LOC saved:** ~60 lines (remove 2 class definitions, replace with fixture import)
- **Risk:** Low. All three classes are identical in function; simply centralizing doesn't change behavior.

### 2. **Seed Catalog Boilerplate**
- **Files affected:** All 6 seed catalog files in `motoquant/database/seed_catalogs/`
- **Issue:** Each `seed_*()` function follows identical pattern:
  ```python
  def seed_<name>(db) -> int:
      import logging
      logger = logging.getLogger(__name__)
      parts = []
      # ... parts.extend() calls ...
      count = 0
      for part in parts:
          try:
              db.parts.create(
                  category_name=part["category"],
                  brand=part["brand"],
                  model_name=part["model_name"],
                  # ... 10+ params ...
              )
              count += 1
          except Exception as e:
              logger.error(...)
      logger.info(f"... {count} parts seeded")
      return count
  ```
- **Suggested target:** Extract `_create_parts_batch(db, parts, source_name)` helper in `seed_catalogs/__init__.py`
- **LOC saved:** ~150 lines total (remove 6× 25-line boilerplate loops)
- **Risk:** Medium-low. Helper must preserve the exact `db.parts.create()` call signature; all catalogs follow it consistently.

## Worth investigating (medium confidence)

### 3. **Aero Parameter Lookups**
- **Pattern:** `CATEGORY_AERO` dict in `importer.py` (line 39–46) maps category → `{cd, frontal_area_m2, wheelie_tendency}`
- **Related code:** `category_profiles.py` has per-category physics knobs (launch_rpm_floor, over_clutch_factor, etc.)
- **Question:** Should these live together? Right now category dispatch is split across importer.py + category_profiles.py
- **Status:** Not a bug, but architectural smell. If the project adds more category-specific data (e.g., per-category tire mu defaults), this will become more painful.

### 4. **Engine Inertia Inference**
- **File:** `importer.py` has `_engine_inertia_from_spec()` (line 67–100+)
- **Related:** `CATEGORY_ENGINE_INERTIA` fallback dict (line 58–64) — used only by the inferred function
- **Question:** Should this live in `defaults.py` instead? Currently spread across two modules.

## False alarms (looks like dup, isn't)

### 1. **Validator bounds checks**
- Validator has many magic-number bounds (`compression_ratio 6.0–16.5`, `peak_torque_rpm 500–15000`). 
- **Looks repetitive but is correct:** Each bound is tuned for a different parameter with different physics constraints. Not consolidatable without introducing a confusing DSL.

### 2. **Seed catalog structure**
- All `parts.extend([{...}])` blocks LOOK the same, but each dict has different parameter combinations tied to specific bikes.
- **Correct as-is:** These are data, not logic. While boilerplate-consolidatable (see #2 above), merging them would hide the data structure.

## Numerical summary
- **Total dup blocks found:** 3 high-confidence + 2 medium-confidence
- **Recommended consolidations:** 2 (test fixture, seed helper)
- **Estimated LOC saved:** ~210 lines
- **Files to touch:** `tests/conftest.py` (new), `tests/test_cli.py` (remove _TestDB), `tests/test_analysis.py` (remove _TestDB), `tests/test_recommendations.py` (remove _TestDB), `motoquant/database/seed_catalogs/__init__.py` (add helper), all 6 seed catalog files (small refactor)
- **Risk:** Low–medium. Both consolidations are mechanical. Test fixture refactor is isolated. Seed helper must handle the exact `db.parts.create()` API (already consistent across all catalogs).
# Subagent 1 — Deduplication report
**Scanned:** 2026-06-07
**Files scanned:** 167 Python + ~35 JS/TS across motoquant/, tests/, scripts/, web/

---

## High-confidence consolidations (apply these)

### 1. `_wb_match` copied into `scripts/benchmark_sweep.py` and `scripts/sweep_with_clusters.py` — should import from `scripts/validation_sweep.py`
- **Files:** `scripts/benchmark_sweep.py:37–40`, `scripts/sweep_with_clusters.py:38–46`
- **Canonical:** `scripts/validation_sweep.py:2119` (`_model_match`, identical logic)
- `scripts/topspeed_sweep.py` already does this correctly (`from validation_sweep import _model_match`). The other two scripts predate that fix or were created by separate cron sessions.
- Also affects `_model_specificity_score`: defined identically in both `sweep_with_clusters.py:49–57` and `validation_sweep.py:2131–2143`; sweep_with_clusters even has a comment "Kept in sync with validation_sweep.py" — a sync comment is a reliable signal that the code should instead be imported.
- **Suggested target:** Extract both helpers from `validation_sweep.py` into `scripts/_sweep_utils.py`; have all four sweep scripts import from there. ~30 LOC saved, 3 divergence points eliminated.

### 2. `QUARTER_MILE_M = 402.336` re-defined in `motoquant/calibration/dragy.py` instead of imported from `motoquant/constants.py`
- **Files:** `motoquant/calibration/dragy.py:49`, `motoquant/constants.py:15`
- `motoquant/calibration/ecu.py` then imports the constant transitively from `dragy.py:51` rather than from the authoritative `constants.py`. If the value ever changes (e.g. metric vs NHRA-spec), `dragy.py` and `ecu.py` will silently diverge from the rest of the engine.
- **Fix:** Replace `QUARTER_MILE_M: float = 402.336` in `dragy.py` with `from motoquant.constants import QUARTER_MILE_M`; update `ecu.py` import to source from `constants.py` directly. ~2 LOC net change.

### 3. `API_URL` fallback inline-duplicated in three web client pages instead of importing `web/lib/api.js`
- **Files:** `web/app/login/page.js:22`, `web/app/pricing/page.js:21`, `web/app/account/page.js:22` — all define `process.env.NEXT_PUBLIC_API_URL || "https://motoquant-api.onrender.com"` inline.
- `web/components/AuthProvider.js:35` does the same with identical fallback.
- **Canonical:** `web/lib/api.js` exports `API_URL = process.env.NEXT_PUBLIC_API_URL || ''` (same-origin, the correct production default per the module's own inline comment about DNS filter workaround).
- The four inline copies all fall back to the full Render URL, bypassing the Vercel rewrite that prevents DNS filter failures. If the backend URL rotates again (Railway → Render already happened once), four files need patching instead of one.
- **Fix:** `import { API_URL } from '../../../lib/api';` in each page; remove the inline const. ~8 LOC saved.

---

## Worth investigating (medium confidence)

### 4. `_get_nested` / `_set_nested` in `motoquant/analysis/sobol.py:247–264` vs `motoquant/database/bridge.py:344–377`
- Logic is functionally identical (dotted-path attribute traversal). `bridge.py` version is a closure inside `apply_part_to_config` and adds user-facing `warnings.warn` with part-name context — that context is genuinely different.
- Not a drop-in replacement, but a shared `_traverse_nested_path` utility in `motoquant/utils.py` that both call would reduce drift risk. Medium confidence because the warning-message context in bridge.py would need threading through.

### 5. `_SURROGATE` lazy-load block copy-pasted into two routes in `motoquant/api.py`
- **Lines:** 2577–2584 (`surrogate_predict`) and 3044–3048 (`optimize_build_route`)
- The blocks are near-identical 6-line double-checked locking patterns. The key difference: `surrogate_predict` raises HTTP 503 if the surrogate is still None after load; `optimize_build_route` silently passes `None` to `optimize_build()` (which handles it gracefully via `make_predictor`).
- Extract a `_ensure_surrogate()` helper that loads and returns `(_SURROGATE, _SURROGATE_SOURCE)`, let callers decide on the 503 behaviour. ~10 LOC saved.

---

## False alarms (looks like dup, isn't)

- **`_run_et` in `roi.py` vs `sobol.py`**: Different return types (tuple vs float) and different error handling (sobol catches and returns NaN). Serve different callers.
- **`optimize_build` in `bayesian_opt.py` vs `build_optimizer.py`**: Completely different algorithms (BoTorch continuous-parameter Bayesian optimisation vs discrete 0/1 knapsack over catalog parts). Same name is the confusing part, not duplication.
- **Blog page structure (web/app/blog/*/page.js)**: ~40 pages share SLUG/TITLE/DESCRIPTION/CONTENT/metadata/export pattern. This is a content template, not code duplication — the rendered content is entirely distinct per post. No extraction needed.
- **`known_bikes_extended.py` splitting from `known_bikes.py`**: Intentional split to avoid file-write-tool truncation (documented in CLAUDE.md). The `EXTENDED_BIKES` list is imported and merged; no logic is duplicated.
- **`test_archetypes._seeded_db`**: Uses a minimal DB (`seed_archetypes` only), not the full catalog. Correctly does NOT use `tests/_helpers.SeededTestDB`, which would be over-seeding for that test scope.

---

## Numerical summary
```
{
  total_dup_blocks: 7,
  high_confidence_consolidations: 3,
  medium_confidence: 2,
  false_alarms: 5,
  estimated_LOC_saved: ~50
}
```
# Subagent 2 — Type consolidation report
**Scanned:** 2026-06-07
**Files scanned:** 293 (Python + TypeScript/TSX + JS across motoquant/, desktop/src/, web/)
**Key files:** motoquant/api.py (3090 lines), motoquant/llm/runner.py, motoquant/analysis/build_optimizer.py, desktop/src/types/api.ts (57 interfaces), web/lib/api.js

---

## Prior-art status

Both tech-debt reports from 2026-05-20 were **actioned and complete**:
- `SimDict` TypedDict family (runner.py:47–216) — confirmed present, correct.
- `FitmentRule` / `FitmentMatch` interfaces (api.ts) — confirmed present, correct.

---

## Drifted types (definitions out of sync)

### HIGH — `SurrogatePredictRequest` Python annotation vs runtime (api.py:2487–2496)
Three fields carry `Field(None)` defaults (nullable at runtime) but their Python annotations declare a non-nullable primitive:
```python
bike_id: int = Field(None, ...)           # should be int | None
aero_cd_override: float = Field(None, ...) # should be float | None
tire_mu_override: float = Field(None, ...) # should be float | None
```
Pydantic v2 accepts these today because `populate_by_name=True` relaxes coercion, but mypy/pyright will reject them and a future pydantic upgrade may break validation. The TS mirror (`SurrogatePredictRequest`) correctly marks all three optional (`?`). Fix: add `| None` to each annotation.

### HIGH — `ChatResponse.sim_result` typed opaquely despite concrete `SimDict` existing (api.py:2941, api.ts:425)
`ChatResponse` in api.py declares `sim_result: dict[str, Any] | None`. The corresponding TS interface uses `Record<string, unknown> | null`. Both erase the concrete field names (`et_quarter_s`, `trap_speed_kmh`, `trap_speed_mph`, `et_60ft_s`, `peak_accel_g`, `bike_name`). The runner already has the precise `SimDict` type. The erased type forces consumers (ChatBox.tsx:56–60, ChatPanel.js:73–76) to use unguarded runtime access. Fix: change api.py to `sim_result: SimDict | None` and TS to import a concrete `SimResultTiles` interface mirroring `SimDict`.

### MEDIUM — `OptimizeBuildRequest` has server-side fields absent from all clients (api.py:3006–3007, api.ts, web/lib/api.js)
Python `OptimizeBuildRequest` declares `power_boost_pct: float` and `mass_delta_kg: float` (defaulting to 0.0). Neither the TS `OptimizeBuildRequest` interface nor `web/lib/api.js` `optimizeBuild()` nor `desktop/src/lib/api.ts` sends these fields. The endpoint silently uses the 0.0 defaults, making the two sliders inaccessible from any shipping client. Clients cannot apply a pre-tuned power/mass mod before optimising. Fix: add both fields to TS interface and the web/desktop API helpers, or remove them from the Python model if the feature is intentionally deferred.

---

## Duplicates that should be merged

### MEDIUM — `RefreshSummary` dataclass defined twice with incompatible fields
- `motoquant/database/weather_refresh.py:40`: `{refreshed, skipped_fresh, no_coords, errors, venue_results, run_at}` — rich summary with per-venue detail.
- `motoquant/database/pricing_refresh.py:201`: `{total, urls_filled, check_stamps_updated, skipped_no_retailer}` — slim counter bag.

Same name, completely different shapes, no cross-import. Risk: a future `from motoquant.database import RefreshSummary` wildcard import will shadow one with the other. Rename to `WeatherRefreshSummary` and `PricingRefreshSummary` respectively (two-line change each + update the four call-sites in pricing_refresh.py).

---

## Intentional divergences (leave alone)

- **`ChatResult` (runner.py) vs `ChatResponse` (api.py)**: `ChatResult` holds `compare_result`, `rank_result`, `recommend_result`, `explain_result`; `ChatResponse` exposes only `sim_result`. Confirmed intentional: frontends render structured tiles only for the simulate/explain intents; all other intents surface output via `summary` text. The mapping is explicit in `chat()` (api.py:2964–2976). Do not expand `ChatResponse`.
- **`BikeSpec` (scraper/spec.py) vs `BikeConfig` (models.py)**: `BikeSpec` is the raw scrape shape (all nullable, unit-ambiguous, confidence-tracked); `BikeConfig` is the validated physics config (non-nullable, unit-normalised). The `spec_to_bike_config()` importer is the intentional translation layer. These should remain separate.
- **`BikeRowSummary` (Python TypedDict, api.py:129) vs `BikeSummary` (TS, api.ts)**: Fields match exactly and the docstring in `BikeRowSummary` cross-references the TS type explicitly. Correctly in sync.
- **`QuickSimResultDict` (Python TypedDict) vs `QuickSimResponse` (TS)**: Fields match exactly. Correctly in sync.
- **`CompareRequest`/`_build_summary` vs `CompareResponse`**: Python response dict and TS `CompareResponse` match. Confirmed in sync.

---

## Numerical summary

```
types_audited: 87   (30 Python Pydantic/TypedDict models in api.py + 57 TS interfaces)
drift_pairs: 3      (SurrogatePredictRequest annotation, ChatResponse.sim_result, OptimizeBuildRequest fields)
merge_candidates: 1 (RefreshSummary name collision)
prior_art_actioned: 2 (SimDict + FitmentRule/FitmentMatch — both confirmed complete)
intentional_divergences_confirmed: 5
```
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
# Subagent 3 — Dead code removal report
**Scanned:** 2026-06-07
**Files scanned:** 364 (167 Python + 197 JS/TS/TSX, excluding node_modules, __pycache__, .next)

---

## High-confidence dead (safe to delete)

### Applied one-shot patch scripts (changes already in codebase)
- `scripts/_patch_physics_dispatch.py:1` — patches `physics.py` to use `category_profiles`; physics.py already has `self._profile`, `over_clutch_factor`, `launch_floor_factor` at lines 230/543/563. Dead.
- `scripts/patch_h2_h2r_2026_04_29.py:1` — adds Ninja H2R to DB; DB already has `bike_id=328 Ninja H2R (2015-2026) 310 hp`. Dead.
- `scripts/patch_2026_04_30_drag_fitments.py:1` — adds drag_prep tire fitments for Hayabusa; DB already has `drag_prep=6` fitments for Hayabusa. Dead.

### Diagnostic scripts (never referenced by any playbook, agent, or schedule)
- `scripts/diagnose_r15_db_path.py:1` — 146-line diagnostic; not imported by any shell script or doc. One-shot debugging tool. Dead.
- `scripts/gearing_audit.py:1` — 199-line gear ratio auditor; not referenced by any shell script, agent prompt, or doc. Dead.
- `scripts/pricing_audit_2026_04_27.py:1` — 186-line one-shot Apr-27 pricing audit; not referenced anywhere. Dead.
- `scripts/audit_calibrator.py:1` — 172-line calibrator schema-v2 audit tool; not referenced anywhere; calibrator_v2 schema is not used in production code. Dead.
- `scripts/validation_run.py:1` — 214-line early validation harness; superseded by `scripts/validation_sweep.py` which is referenced by `docs/AUTONOMOUS_OPERATIONS_PLAYBOOK.md`. Dead.
- `scripts/train_surrogate_numpy.py:1` — 81-line training script; not referenced by any shell/doc/agent; `surrogate_numpy.npz` not present in `artifacts/surrogate/`. Dead.
- `scripts/sweep_batched.py:1` — 274-line sweep; only referenced internally by `topspeed_sweep` import and itself. No shell or doc calls it. Dead.

### Orphaned binary/pickle files (zero references in codebase)
- `calibrator_v2.pkl` (repo root) — `grep -r "calibrator_v2"` returns 0 hits in all .py/.sh/.md files. api.py loads `surrogate_dnn.pkl`/`surrogate.pkl`, never `calibrator_v2.pkl`. Dead.
- `calibration_v2_2k.npz` (repo root) — same: 0 references. Dead.

### Orphaned source module
- `motoquant/scraper/parameter_sources.py:1` — 1,897-line per-model parameter lookup table. Its own docstring says `from motoquant.scraper.parameter_sources import get_bike_params`, but `grep -r "parameter_sources"` across the full codebase returns zero hits outside the file itself. `importer.py` uses `gear_ratios.py` for this purpose instead. Dead.

### Orphaned web components
- `web/components/BikeSilhouette.js:1` — 428-line SVG superbike silhouette component. `grep -r "BikeSilhouette"` in `web/app/` returns 0 hits. Never imported. Dead.
- `web/components/SpecCorrectionForm.js:1` — 360-line modal correction form. `grep -r "SpecCorrectionForm"` in `web/app/` returns 0 hits. The backing API route (`/api/specs/correct`) exists in `api.py:2049` but the UI component is never imported into any page. Dead.

---

## Medium-confidence (verify before deleting)

- `motoquant/models.py:145 — EngineParams.afr_wot` — set in `defaults.py` (3×) and `importer.py`, but never read in `physics.py` or any `submodels/*.py`. Intended for future fuel-trim model. Not safe to remove without confirming no planned usage; flag for Phase 6.
- `motoquant/models.py:142 — EngineParams.crank_rotation_cw` — set in `defaults.py` (3×), but never read in physics. Note: `counter_rotating` (different field) IS used in `submodels/wheelie.py:39`. `crank_rotation_cw` itself is dead.
- `scripts/benchmark_sweep.py:1` — 274 lines; only reachable via `sweep_batched.py` which is itself dead. Cross-check: not referenced by any shell script or doc directly. Likely dead but `sweep_batched` might be resurrected.
- `scripts/patch_2026_04_30_fitment_normalize.py:1` — normalises `tier: "model"` → `tier: "family"` in DB. `seed_catalogs/indian_retailer_depth.py` still contains 34 `"tier": "model"` strings, meaning this patch was never applied to that file's DB seeds. Not dead — but clarify: if it runs idempotently on the live DB it's safe to delete after one final run; if it was skipped, seeds need direct fix.

---

## Looks dead but ISN'T (false positives caught)

- `motoquant/scraper/known_bikes_extended.py` — auto-flagged by my initial orphan scan (refs=2); actually imported at `known_bikes.py:12287` via `from .known_bikes_extended import EXTENDED_BIKES`.
- `motoquant/nlp.py` — scan flagged it (refs=1); actually imported by `run.py:2887` via lazy import inside `cmd_nl`.
- `web/components/TierBadge.js` — imported in `web/app/account/page.js` and one other page; not dead.
- `motoquant/analysis/bayesian_opt.py` — two `optimize_build` functions exist (`bayesian_opt.py` and `build_optimizer.py`); `run.py` uses the `bayesian_opt` version (CLI), `api.py` uses `build_optimizer` version (HTTP). Both are live.
- `calibration/calibrator.py` — no v2 schema in the Python code; `calibrator_v2.pkl` is the orphaned artifact, not the source module.

---

## Numerical summary

| Metric | Count |
|---|---|
| Files scanned | 364 |
| High-confidence dead items | 13 items (4,342 dead LOC in scripts + 2,297 in source/components) |
| Medium-confidence suspects | 4 items |
| False positives caught | 5 |
| Orphaned binary artifacts | 2 (calibrator_v2.pkl + calibration_v2_2k.npz) |
| Dead scripts (one-shot applied) | 3 |
| Dead scripts (diagnostic/superseded) | 7 |
| Dead Python module | 1 (parameter_sources.py, 1,897 lines) |
| Dead web components | 2 (BikeSilhouette.js 428 + SpecCorrectionForm.js 360 lines) |
| Dead dataclass fields (medium) | 2 (afr_wot, crank_rotation_cw) |

# Subagent 4 — Circular dependencies report
**Scanned:** 2026-06-07
**Module count:** 99 Python modules (motoquant/), 35 TypeScript modules (desktop/src/), 154 Next.js files (web/)

---

## True cycles (import-time loops)

**None found.**

Full DFS traversal of the top-level import graph across all 99 Python modules produced zero cycles. The TypeScript desktop layer (35 modules) and Next.js web layer (154 files) are likewise cycle-free.

---

## Deferred-import cycles (dodged via function-body import)

**None confirmed as cycle workarounds.**

Several deferred imports were inspected that *looked* like cycle dodges:

- **`physics.py:220` → `category_profiles`** (deferred inside `__init__`): `category_profiles` imports only `dataclass` — it has zero inbound motoquant imports. The deferral is unnecessary for cycle safety; it appears to be a late-initialization pattern from when the module was first wired in (April 30 session). Harmless but could be promoted to a top-level import.

- **`scraper/importer.py:953` and `submodels/parasitic.py:21` → `category_profiles`** (deferred): Same situation — `category_profiles` is fully standalone. Both can be promoted to top-level imports safely.

- **`database/connection.py` → repo modules** (deferred, in property accessors): This is the intentional lazy-facade pattern. `MotoQuantDB` properties (`bikes`, `parts`, `tires`, etc.) defer import of `BikeRepository`, `PartsRepository`, etc. No cycle exists because the repo files accept a raw `sqlite3.Connection` and do not import `MotoQuantDB`. Leave as-is.

- **`llm/runner.py:941,1110` → `llm/client.get_default_client`** (deferred): `client` is already imported at top level for `LLMClient`; the deferred calls get the factory function to avoid reading env vars at import time. Intentional lazy-load, not a cycle dodge.

- **`api.py` and `run.py`** — dozens of deferred imports of heavy subsystems (calibration, analysis, surrogate, llm, etc.) are all intentional lazy-loading to keep startup time low. Not cycle workarounds.

---

## Layer violations (no cycle, but bad direction)

### HIGH confidence

**`api.py:1331` and `run.py:1151` import `_enrich_bike_row_for_fitment` (private function)**

```
motoquant/api.py:1331   from .database.parts_repo import _enrich_bike_row_for_fitment
motoquant/run.py:1151   from .database.parts_repo import _enrich_bike_row_for_fitment
```

`_enrich_bike_row_for_fitment` is a module-private helper (leading underscore) in `database/parts_repo.py`. Both `api.py` and `run.py` call it directly to populate `chain_pitch`, `cylinder_config`, and `stroke_type` on a raw bike dict before passing it to `is_compatible()`.

`PartsRepository.list_compatible_for_bike()` (public method, line 235) already calls `_enrich_bike_row_for_fitment` internally — but `api.py` and `run.py` are running their own search query with different filters (pagination, search string, category filter) and then doing the enrich+compat loop themselves. The clean fix is to expose `enrich_bike_row_for_fitment` (drop the underscore) since it is genuinely reusable across layers. A one-character rename in `parts_repo.py` (remove the leading `_`) plus updating the two call sites removes the violation without any abstraction overhead.

**Proposal:** rename `_enrich_bike_row_for_fitment` → `enrich_bike_row_for_fitment` in `parts_repo.py` (line 18), update `api.py:1331` and `run.py:1151`. No logic change needed.

---

## Acceptable / leave alone

- `database/connection.py` lazy repo imports — intentional facade, no cycle, well-documented pattern.
- `calibration_ml/synthetic.py` deferred imports of `physics`, `defaults`, `scraper.importer` — training-time subpackage; deferring heavyweight imports to `generate_dataset()` is correct.
- `observability.py` deferred `from motoquant import __version__` inside a try/except — guards against import failure, not a cycle.
- `auth.py:408` deferred `from .database import subscriptions_repo` inside the `/me` route handler — avoids mutual top-level import between `auth` and `subscriptions`. `subscriptions.py` imports `auth` top-level; keeping `auth`'s reference to `subscriptions_repo` deferred is the right call.
- `physics.py`, `importer.py`, `parasitic.py` deferred `category_profiles` imports — not harmful, could be promoted to top-level, but not urgent.
- All deferred imports in `api.py` and `run.py` for heavy analysis/surrogate/calibration modules — intentional, correct lazy-loading.

---

## Numerical summary

```
modules_scanned:   99 Python + 35 TypeScript + 154 Next.js
true_cycles:       0
deferred_cycles:   0  (all deferred imports inspected; none are cycle workarounds)
layer_violations:  1  (private symbol exported across two callers: api.py + run.py)
actionable_items:  1  (rename _enrich_bike_row_for_fitment; low-risk, mechanical)
```
# Subagent 5 — Type strengthening report
**Scanned:** 2026-06-07
**Files scanned:** 99 Python (motoquant/ core + scraper + llm + db + calibration_ml), 3 TypeScript (desktop/src/lib/api.ts, types/api.ts, hooks/useApi.ts)

---

## Prior-art check

`reports/tech_debt_llm_db_typing_2026-05-20.md` confirms the prior pass closed all 13 `db: Any` annotations in `motoquant/llm/` (runner.py / parse_query.py / resolver.py). Those sites are now correctly `db: MotoQuantDB`. No duplicate work below.

TypeScript desktop/src — zero `any` or `as any` in the three API surface files. Strict mode is holding. No TS findings needed.

---

## High-confidence strengthenings (apply these)

1. **`motoquant/api.py:2941`** `ChatResponse.sim_result: dict[str, Any] | None` →
   `SimDict | None`
   Justification: `SimDict` is already defined and exported-ready in `motoquant/llm/runner.py:62`. The field is populated only from `result.sim_result` (api.py:2975) where `result` is a `ChatResult`; `ChatResult.sim_result` is already typed `SimDict | None` (runner.py:262). The Pydantic model just needs `from motoquant.llm.runner import SimDict` (add under `TYPE_CHECKING`) and `sim_result: SimDict | None = None`.

2. **`motoquant/llm/runner.py:282`** `_resolve_venue_env(...) -> Any` →
   `EnvironmentParams | None`
   Justification: the only return paths are `return None` and `return db.venues.to_environment(...)`. `VenueRepository.to_environment` is annotated `-> EnvironmentParams | None` (venue_repo.py:151). The `Any` return silently propagates throughout the three call sites (lines 390, 594, 1540).

3. **`motoquant/llm/runner.py:1037, 1050, 1299`** `config: Any` on `_apply_env_overrides`, `_apply_power_boost`, `_apply_archetype` → `config: BikeConfig`
   Justification: every caller guards `None` before the call (e.g., `if config is None: return …` at lines 1001–1003, 596–597, 1537–1539). The source is always `db.bikes.to_config(…)` which returns `BikeConfig | None` (bike_repo.py:415). Renaming to `BikeConfig` lets IDEs catch attribute misspells across these three mutation helpers.

4. **`motoquant/database/connection.py:336`** `stats() -> dict` →
   `stats() -> dict[str, int]`
   Justification: every value is a `COUNT(*)` integer (lines 343–350). The bare `dict` loses this contract.

5. **`motoquant/scraper/importer.py:989, 1075`** `db` (unannotated) on `import_spec` and `import_batch` → `db: MotoQuantDB`
   Justification: line 990 has `# MotoQuantDB` comment confirming developer intent. Both functions only call `db.bikes.*` and `db.manufacturers.*` — all `MotoQuantDB` attributes. Add `TYPE_CHECKING` guard identical to the pattern used in `llm/runner.py`.

6. **`motoquant/database/seed_archetypes.py:194, 220`** `db: Any` on `_resolve_base_bike_id` and `seed_archetypes` → `db: MotoQuantDB`
   Justification: both functions only access `db._conn` (lines 200, 240), which is the `sqlite3.Connection` private attribute on `MotoQuantDB`. Pattern matches the LLM-module fix from the May-20 prior pass.

---

## Medium-confidence (worth a closer look)

- **`motoquant/database/parts_repo.py:307`** `estimate_build_cost() -> dict[str, Any]` — the return shape is fully documented in the docstring (`total: float, currency: str, parts: list[...], unavailable_count: int`). A `BuildCostResult` TypedDict would make the contract machine-checkable. Moderate effort; no callers currently type-narrow on the fields.

- **`motoquant/database/parts_repo.py:18`** `_enrich_bike_row_for_fitment(bike_row: dict) -> dict` — should be `dict[str, Any]` minimum; a `BikeRowDict` TypedDict capturing the known keys (`id`, `manufacturer`, `cylinder_config`, `chain_pitch`, `stroke_type`) would be more precise. Cross-checks against schema.py cols needed before committing.

- **`motoquant/database/bike_repo.py:75, 187, 198`** `list_manufacturers()`, `get_model()`, `search()` return bare `list[dict]` / `dict | None`. The column set is stable (schema.py lines 34–93). A `BikeModelRow` TypedDict would help downstream callers (`llm/runner.py` dereferences `row["manufacturer_name"]` etc. with no type safety).

- **`motoquant/database/connection.py:370`** `connect(db_path)` — `db_path` is unannotated. Should be `db_path: str | None = None`.

- **`motoquant/database/weather_refresh.py:105`** `refresh_all_venues(db)` — `db` unannotated; callers always pass `MotoQuantDB`.

- **`motoquant/llm/client.py:193, 284`** `call_tool` and `call_text` — `system`, `user`, `tool_name`, `tool_schema` params unannotated; all are `str` / `dict[str, Any]` and straightforward to annotate.

---

## Boundary types where weak is correct (do NOT flag these)

- **`motoquant/calibration_ml/features.py:96–133`** `_safe_float(obj: Any)`, `_density_altitude_ft(env: Any)`, `extract_features(bike_config: Any)` — these use `getattr` with defaults throughout and are designed to tolerate partially-populated configs. `Any` is intentional defensive programming.
- **`motoquant/calibration_ml/calibrator.py`** `hyperparams: dict[str, Any]` — ML hyperparameter dicts are schema-free by design; XGB and sklearn have incompatible shapes.
- **`motoquant/llm/parse_query.py:108`** `TOOL_SCHEMA: dict[str, Any]` — Anthropic tool schema is a heterogeneous nested structure; `Any` is correct.
- **`motoquant/observability.py:117`** `_tag_app(event: dict[str, Any])` — Sentry event dict is open-ended by the SDK contract.
- **`motoquant/database/bridge.py:117`** `config_to_db_row() -> dict[str, Any]` — values are JSON strings, integers, and floats; `Any` is correct for a serialization helper.
- **`motoquant/api.py:674, 694, 881, 1311`** `params: list[Any]` — SQLite parameter lists accept `str | int | float | None`; `Any` is the standard idiom here.

---

## Numerical summary

```
functions_audited: 87
weak_signatures (Any where real type known): 12 (6 high + 6 medium)
untyped_dict_returns (bare dict / dict[str,Any] where shape is fixed): 4
ts_any: 0
ts_unknown: 0
boundary_correct (Any intentional, not flagged): 10
```

# Subagent 5 — Type Strengthening Report
**Scanned:** 2026-05-05  
**Files scanned:** 18 (Python + TypeScript)

## High-confidence strengthenings (apply these)

### Python

1. **`motoquant/api.py:123` — `_bike_row_to_summary`**
   - Current: `def _bike_row_to_summary(row: dict) -> dict:`
   - Proposed: `def _bike_row_to_summary(row: dict[str, Any]) -> dict[str, int | str | None]:`
   - Justification: Returns a fixed-shape dict with `id`, `manufacturer`, `model`, `year`, `category`, `displacement_cc`, `peak_power_hp`, `dry_mass_kg`, `data_quality`. Schema at `schema.py` `bike_models` table confirms all are nullable except `id`.

2. **`motoquant/database/bridge.py:150` — `extract_headline_specs`**
   - Current: `def extract_headline_specs(config: BikeConfig) -> dict[str, Any]:`
   - Proposed: Return type `HeadlineSpecsDict` (TypedDict with 13 fields: `displacement_cc`, `bore_mm`, `stroke_mm`, `compression_ratio`, `peak_power_hp`, `peak_power_rpm`, `peak_torque_nm`, `peak_torque_rpm`, `cylinder_count`, `cylinder_config`, `dry_mass_kg`, `wheelbase_mm`, `seat_height_mm` — all `float | int | None`).
   - Justification: Function explicitly constructs a fixed dict at lines 159–173. TypedDict makes the shape discoverable.

3. **`motoquant/llm/runner.py:91–98` — `run_chat_pipeline`**
   - Current: `db: Any` parameter
   - Proposed: `db: MotoQuantDB` (or the actual type the caller passes)
   - Justification: Function only calls `db.get_bike_by_id()`, `db.query_bikes()`, `db.get_venue_by_id()` — all MotoQuantDB methods. Tracking `Any` loses those interface guarantees.

### TypeScript

4. **`desktop/src/types/api.ts:69, 84, 100, 113, 138` — Index signature `[extra: string]: unknown`**
   - Current: `[extra: string]: unknown` on `BikeDetail`, `Venue`, `Tire`, `PartsCategory`, `Part`
   - Proposed: Replace with `[extra: string]: never` (strict mode) or list explicit optional fields if the API does return extras.
   - Justification: `unknown` is too loose; TS strict mode should flag unmapped properties as errors, not silently allow them. If the API legitimately returns extra fields, they should either be enumerated or typed as `never` to catch client-side bugs where the field name is wrong.

5. **`desktop/src/types/api.ts:134–135` — Part fields**
   - Current: `compatible_bikes?: unknown; fitment_rules?: unknown;`
   - Proposed: Study the actual API response schema at `motoquant/api.py` and type these as `CompatibleBikes[] | null` and `FitmentRule[] | null` respectively.
   - Justification: UI code never reads these fields (verified via grep), so the unknown type hides whether they're even being used.

6. **`desktop/src/pages/BuildPage.tsx:80` — Type assertion**
   - Current: `const stockHp = (bike as unknown as { peak_power_hp?: number }).peak_power_hp ?? 100;`
   - Proposed: Use a type guard instead: `function hasPeakPower(b: BikeSummary): b is BikeSummary & { peak_power_hp: number } { return b.peak_power_hp != null; }` then `const stockHp = hasPeakPower(bike) ? bike.peak_power_hp : 100;`
   - Justification: The double-cast `as unknown as {...}` is a red flag that the true type is unknown. BikeSummary already declares `peak_power_hp: number | null`, so the guard pattern is safer.

7. **`desktop/src/pages/SimulatePage.tsx:213` — Type assertion**
   - Current: `splits: result.splits as unknown as Record<string, number>`
   - Proposed: Check `motoquant/api.py` `SimulateResult` schema and type `result.splits` correctly (likely `dict[str, float]` at the API boundary). If the field shape is uncertain, create `SplitsDict: Record<string, number>` and verify the API returns it.
   - Justification: Without knowing the real splits shape, the cast loses information. The shape should come from the schema definition, not from the UI's guess.

## Medium-confidence (worth a closer look)

1. **`motoquant/scraper/importer.py` — All `_build_*_from_spec()` helpers**
   - These return specific dataclass types (EngineParams, ChassisParams, etc.) but internally use loose dict constructions. Worth auditing for internal `dict[str, Any]` usage that could be tightened.
   - Example: `_build_engine_from_spec` constructs a dyno curve dict → should use `DynoCurve` directly instead of a dict passed to the constructor.

2. **`motoquant/llm/runner.py:71–75` — ChatResult fields**
   - Fields like `sim_result: dict[str, Any] | None`, `compare_result: dict[str, Any] | None` etc. should be typed as their actual Pydantic model equivalents (e.g., `SimResult | None`).
   - Justification: These come from the dispatch handlers (`_run_simulate()`, `_run_compare()`, etc.) which return structured dicts that could be Pydantic models for runtime validation.

## Boundary types where weak is correct

- `run_chat_pipeline(db: Any, ...)` — `Any` is intentionally permissive for backwards compat with test mocks that don't inherit from MotoQuantDB. Once test infrastructure is tightened, this can graduate to `MotoQuantDB | MockDB` protocol.
- `[extra: string]: unknown` on API response models — legitimately needed if the backend adds fields dynamically. Recommend documenting in the interface comment if that's intentional.

## Numerical summary

| Category | Count |
|----------|-------|
| Functions audited | 15 |
| Weak function signatures (`Any` params) | 3 |
| Untyped dict returns | 2 |
| TS `any` assertions | 0 |
| TS `unknown` index signatures | 5 |
| TS type assertions (`as X`) | 2 |

**Regressions prevented by fixing #1–3:** DB schema mismatches, lost type information in chat payload dispatch.  
**Regressions prevented by fixing #4–7:** Silent field-name typos in UI, wrong splits shape in PDF export.
# Subagent 6 — Error handling cleanup report
**Scanned:** 2026-06-07
**Files scanned:** 167 Python, 197 JS/TS (grep across motoquant/, desktop/src/, web/)

---

## Critical — silent failures (fix immediately)

- **`motoquant/analysis/build_optimizer.py:90`** — `_check_envelope()` catches `Exception` and returns `(True, [])` (i.e. "in envelope, no violations"). If `surrogate_data.FEATURE_BOUNDS` import fails for any reason, *every config* is declared in-envelope and the surrogate is used unconditionally. In `SurrogatePredictor.__call__` (line 121) `ok=True` suppresses the `allow_fallback` guard, so out-of-distribution configs get surrogate scores silently instead of full-sim fallback. **Fix:** `except ImportError` only (the only expected failure); re-raise or return `(False, ["envelope_check_unavailable"])` on any other exception so the caller falls back to full sim safely.

- **`motoquant/analysis/roi.py:209`** — `_resolve_price()` catches `Exception` and returns `seed_price` (the catalog fallback) without logging. If the DB query fails for a structural reason (schema mismatch, corrupt row), *all parts silently price at their seed value* for every subsequent ROI computation in that session. No log entry is emitted. **Fix:** add `logging.getLogger(__name__).warning(...)` before returning `seed_price` so price-resolution failures are visible.

- **`motoquant/database/seed_recommended_fitments.py:361`** — `except Exception: stats["errors"] += 1` increments a counter but emits no log line (no `logger.warning`, no `print`). A batch of fitment insertions failing silently (e.g. FK violation after a DB wipe + re-seed) will show a non-zero errors count in the returned dict, but the caller in `seed_all()` does not inspect it. **Fix:** add `logger.warning("fitment insert failed: %s", exc)` inside the except block.

---

## Should add logging (warning swallow, not fatal)

- **`motoquant/llm/runner.py:293`** (`resolve_venue`) — `except Exception: return None`. A venue lookup failure silently degrades to default sea-level environment. The caller never learns whether venue resolution failed or the venue legitimately had no data. Add `logger.debug("resolve_venue(%s) failed: %s", parsed.venue_id, exc)`.

- **`motoquant/llm/runner.py:746`** (`_run_recommend`) — `except Exception: parts = []`. If `list_compatible_for_bike` throws (e.g. DB connection lost mid-request), the user receives an empty recommendation with no indication of failure. Add at least a `logger.warning`.

- **`motoquant/llm/runner.py:838`** (tire fitment fetch inside `_run_recommend`) — `except Exception: pass`. Same pattern: DB failure produces an empty tire list silently. Add `logger.warning`.

- **`motoquant/api.py:831`** (bike detail JSON-blob parse) — `except Exception: pass`. Malformed `engine_params`/`aero_params` JSON in the DB degrades the `/api/bikes/{id}` response silently; client sees missing fields. Already mitigated by `_safe_parse` helper at line 777 (which returns `{}` — acceptable), but the outer `except Exception: pass` at 831 hides any non-JSON error (e.g. a programming error in the detail-page enrichment block). Add `logger.warning`.

- **`motoquant/database/weather_repo.py:159`** — `fetch_live` network call swallows all exceptions and returns `None`. The caller in `weather_refresh.py:229` handles `None` by logging an error — **that path is fine**. However no distinction is made between transient network errors and bad API keys; both return `None`. Low severity; acceptable for a best-effort data path.

- **`motoquant/nlp.py:566`** — `except Exception: pass` on budget remaining calculation. Comment says "Silently fail on budget calculation" — the arithmetic is simple (`sum(price_inr for ...)`) and should not raise; if it does that's a programming error worth surfacing. **Fix:** remove the try/except entirely or narrow to `(TypeError, ValueError)`.

---

## Bare except clauses (narrow these)

No bare `except:` (no-type) clauses found in the core motoquant package. All catches name at minimum `Exception`. The TS/JS side uses `catch { }` (no binding) in two places in `web/lib/api.js:42,46`, but these are inside the API error-message parser where degradation to a status-only message is intentional and the outer `throw new Error(msg)` still fires — acceptable.

---

## Defaults masking real problems

- **`motoquant/database/weather_repo.py:163–168`** — OWM response parsed with `data.get("main", {}).get("temp", 25.0)` etc. If the API returns a malformed response (missing `"main"` key entirely), temperature defaults to 25 °C, humidity to 50 %, pressure to 1013.25 hPa — realistic-looking values that will pass downstream physics checks without triggering any alert. A completely bogus API response would produce a valid-seeming weather record. **Mitigation in place:** `resp.raise_for_status()` catches HTTP errors; the silent-default risk is limited to malformed-but-200 responses. Medium severity; add a `if "main" not in data: logger.warning(...)` guard.

- **`motoquant/database/parts_repo.py:77`** — `except (json.JSONDecodeError, TypeError): pass` on `drivetrain_params` parse; `bike_row["chain_pitch"]` is left unset (None). This is the documented fallback for shaft/belt-drive bikes and is correct. Not a real mask.

---

## Acceptable / leave alone (with reason)

- **`motoquant/keepwarm.py`** broad excepts — documented in CLAUDE.md as intentional; keep-alive must never affect availability.
- **`motoquant/api.py` startup keepwarm hook** — same documented design.
- **`motoquant/calibration/calibrator.py:213`** — `except Exception: return 1e6` in the objective function penalises crashed simulations during DE optimisation. This is the correct circuit-breaker pattern for a numerical optimizer; crashes must not propagate.
- **`motoquant/analysis/surrogate_data.py:598`** — training-data generation swallows per-sample sim failures and logs them; the failure rate is reported at the end. Correct for a batch process.
- All `except ImportError` / `except ImportError as exc` optional-dependency patterns throughout analysis modules — correct.
- **`motoquant/database/connection.py:66,118`** — WAL→DELETE fallback on FUSE. Documented design in CLAUDE.md.
- **`motoquant/scraper/bulk_scrape.py:436,444`** — per-bike scrape failures logged and counted; `KeyboardInterrupt` re-raised. Correct.
- **`web/lib/api.js:42,46`** — catch-without-binding inside JSON error-message parser; outer `throw` still fires. Acceptable.
- **`motoquant/auth.py:164`** — fallback JWT decode on `Exception` returns `None` (unauthenticated), which is the safe direction for auth failures.

---

## Numerical summary

```
try_blocks:        ~95 (Python), ~4 (JS/TS)
silent_swallows:   9   (no log + no re-raise)
bare_excepts:      0   (Python); 2 (JS/TS, both acceptable)
default_masks:     1   (OWM response defaults)
critical:          3
medium:            5
acceptable:        11
```
# Subagent 7 — Deprecated code & AI slop report
**Scanned:** 2026-06-07
**Files scanned:** 338 (99 Python, 48 blog page.js, 35 desktop TS/TSX, 156 web JS)

---

## Part 1 — Deprecated / legacy

**1a. `nixpacks.toml` — Railway-specific build config, now superseded by `Dockerfile` + `render.yaml`**
- `nixpacks.toml` header reads *"Railway / Nixpacks build configuration"*. Render uses the Dockerfile exclusively; nixpacks.toml is never read in the current deployment path. Safe to delete or keep as dead documentation, but misleads future sessions into thinking it is live config.
- Confidence: HIGH. `render.yaml` points at `dockerfilePath: ./Dockerfile`; no CI job or render.yaml references nixpacks.toml.

**1b. `Procfile` — Heroku/Railway artifact, not used by Render Docker**
- `Procfile` contains `web: uvicorn motoquant.api:app --host 0.0.0.0 --port $PORT`. Render's Docker runtime uses the `CMD` in `Dockerfile`, not Procfile. Only referenced in `.github/CODEOWNERS` as an ownership record. Safe to delete.
- Confidence: HIGH.

**1c. `Dockerfile` line 15 — stale "Railway injects PORT" comment**
- `# Railway injects PORT at runtime` — production is Render; Render also injects `PORT` but the comment names the wrong platform. One-line cosmetic fix: s/Railway/Render/.
- Confidence: HIGH.

**1d. `web/next.config.js` lines 3–11 — comment block still names Railway as the backend**
- The rewrite destination is correctly `motoquant-api.onrender.com` (line 20), but the surrounding comment block refers to `*.up.railway.app` DNS blocking as the architectural rationale. The rationale is still valid (DNS blocks apply to any non-motoquant.in domain), but the specific domain name is wrong. Should read `*.onrender.com`.
- Confidence: MEDIUM (rationale still holds; only the named domain is stale).

**1e. `web/lib/api.js` lines 5–15 — same Railway comment block**
- Same pattern as next.config.js: the proxy rationale cites `*.up.railway.app` wholesale DNS-blocking. Same medium-confidence fix.
- Confidence: MEDIUM.

**1f. `web/app/bikes/[id]/layout.js` lines 20–23, 57 — Railway-specific timeout comments**
- Comment says *"Give the Railway backend a longer rope for SSR: its free tier can cold-start at 10-30s"* and *"most likely the Railway backend is on a cold start"*. Should reference Render. The timeout logic itself (20 s AbortController) is still correct for Render's free tier.
- Confidence: HIGH (user-facing comment is factually wrong about which platform is running).

**1g. `web/app/privacy/page.js` lines 47, 86 — Railway named as current infrastructure provider**
- Line 47: *"stored on servers in us-west2 (Oregon, USA) via Railway (backend)"* — production is now Singapore/Render. Line 86: *"Railway / Vercel — infrastructure providers"*. Both are live legal/privacy disclosures that are factually incorrect post-migration.
- Confidence: HIGH. Privacy page is a legal document; wrong provider name is a material error.

**1h. `motoquant/observability.py` lines 14, 27 — Railway references in docstring**
- *"Set ONE env var on Railway (or wherever the API is deployed)"* and *"different environments (Railway prod, staging…)"*. Minor docstring inaccuracy; low risk but easy to fix.
- Confidence: LOW (docstrings, not live logic).

---

## Part 2A — AI slop: stubs and placeholders

**2A-1. `motoquant/llm/runner.py:774` — inline `# placeholder rows without real pricing`**
- A comment marking pricing data rows as placeholder. Unlike a stub function this is a data-quality note, but it should either be resolved or converted to a structured TODO with a ticket reference.
- Recommended action: check whether real pricing was subsequently seeded; if yes, delete comment; if no, convert to `# TODO(pricing): resolve after vendor query`.

---

## Part 2B — AI slop: narrative comments

**2B-1. `motoquant/defaults.py` lines 222–223, 264–266 — "# was X" inline changelog**
- `band_hi = 0.12  # was 0.16`, `baseline = 0.20  # was 0.30`, `band_lo = 0.25  # was 0.12 (too peaky)`, `band_hi = 0.15  # was 0.08`, `baseline = 0.25  # was 0.12`. Five consecutive edit-history notes inside `_synthetic_2stroke_torque_curve`. Git history records the prior values; these comments add noise without explaining *why* the current value is correct.
- Recommended action: Delete the `# was X` suffixes; keep or expand the explanatory text that follows on the same line (e.g. "powervalve delivers good off-pipe still" is useful; "was 0.30" is not).

**2B-2. `motoquant/scraper/importer.py` lines 405–412 — "Apr-24 experiment" narrative block**
- Eight-line comment block narrates a failed Apr-24 calibration experiment and its reversion. This is session history, not code documentation. The conclusion ("Reverted; logged as a potential follow-up") is the only load-bearing sentence.
- Recommended action: Compress to one line: `# Wheel-loss factor experiment (Apr-24) made all clusters worse; spec.peak_power_hp treated as wheel power throughout.`

**2B-3. `motoquant/category_profiles.py` lines 165–175 — inline calibration narrative**
- Comment block inside `CategoryProfile` definition reads like a session note: *"was under-representing the real shift dynamics, causing 7 of 8 benchmarked bikes to sim slow (bias +0.21s). At 600 rad/s² cluster mean|Δ| drops…"* This is a session report embedded in production code.
- Recommended action: Keep the final conclusion (`max_engine_decel_rads2=600.0` chosen because clutch slip inertia for 600cc I4 ≈ 0.0065 kg·m²), delete the before/after metric table from the comment.

**2B-4. `web/app/blog/600cc-supersport-launch-physics-engine-deceleration/page.js` lines 51, 278 — K5 baseline mislabelled as R1 value (HIGH PRIORITY)**
- Line 51: *"K5 GSX-R 1000, R1 4C8, and Hayabusa Gen 1 — our three load-bearing reference baselines — were nailed to four decimal places (10.2859s / 10.2859s / 10.4712s)."* The first number should be `10.0334s` (K5), not `10.2859s` (R1). The same error recurs at line 278.
- This is the specific drift documented in CLAUDE.md: *"2 pre-existing unrelated drifts remain in a 600cc blog post (mislabels K5 baseline)"*.
- Recommended action: `s/10.2859s \/ 10.2859s/10.0334s \/ 10.2859s/g` at both lines.

---

## Part 2C — AI slop: over-docs

**2C-1. `motoquant/scraper/importer.py:157` — `_fluid_mass_from_spec()` doc=12L body=3L**
- A 12-line docstring on a 3-line function that clips `fluid_mass_kg` between bounds. The docstring includes calibration rationale that is useful but could be trimmed to 3–4 lines.

**2C-2. `motoquant/scraper/importer.py:176` — `_basket_inertia_from_spec()` doc=14L body=3L**
- Same pattern: 14-line docstring on a 3-line clamp function.

**2C-3. `motoquant/llm/summarize.py:100` — `summarize_result()` doc=11L body=3L**
- 11-line docstring on a dispatcher that calls one of three sub-summarizers.

**2C-4. `motoquant/scraper/bulk_scrape.py:61` — `_utcnow_iso()` doc=6L body=1L**
- 6-line docstring on `return datetime.utcnow().isoformat() + "Z"`. The function name is self-documenting; the docstring is pure noise.
- Recommended action: Delete docstring entirely; it adds nothing over the function name.

---

## Part 2D — Defensive over-wrapping

44 bare `except: pass` handlers found across the codebase. The highest-risk cluster:

**2D-1. `motoquant/api.py:652` — telemetry event logging swallows all exceptions silently**
- `except Exception: pass` wrapping the `/api/event` telemetry write. Acceptable for fire-and-forget telemetry; add `log.debug("telemetry write failed", exc_info=True)` so failures are visible in logs without breaking the endpoint.

**2D-2. `motoquant/api.py:831` — bike detail JSON blob enrichment swallows parse errors**
- `except Exception: pass` on the block that enriches bike config JSON for the detail page. A malformed JSON blob silently returns a partially-enriched response with no indication of failure. Recommend `log.warning(...)` at minimum.

**2D-3. `motoquant/api.py:1051` — stock sim baseline silently drops on any error**
- `except Exception: pass` means a stock sim failure causes the compare route to return delta ET of zero with no warning. The subsequent sim may still succeed, producing a silently wrong delta.

**2D-4. `motoquant/database/retail_adapters/__init__.py` lines 156, 297, 500, 535 — four bare-pass scrapers**
- HTTP scraping failures silently return `None`. Acceptable for scraper resilience, but a counter or warning log would help diagnose systematic failures.

---

## Numerical summary

```
{
  "legacy_blocks": 8,
  "stubs": 1,
  "narrative_comments": 4,
  "over_docs": 4,
  "defensive_wraps": 44,
  "ai_slop_phrase_hits_in_blog": 4
}
```

**Notes:**
- The 4 blog AI-slop phrase hits include 1 true slop word ("transformative" in Dominar post) and 3 uses of "leverage" in technically accurate mechanical context (handlebar leverage, mechanical leverage, thermodynamic leverage) — the 3 mechanical uses are NOT slop and should NOT be changed.
- The 44 bare-pass handlers are dominated by `motoquant/scraper/bikez.py` (7) and `motoquant/database/retail_adapters/__init__.py` (4), which are network-scraping paths where swallowing is defensible. The `motoquant/api.py` cluster (8) is higher risk.
- `nixpacks.toml` and `Procfile` are the cleanest deletes: zero downstream references in active code.
