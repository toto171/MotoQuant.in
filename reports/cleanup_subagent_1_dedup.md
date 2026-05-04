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
