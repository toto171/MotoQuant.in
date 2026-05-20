# Tech Debt Pass — Seed Catalog Batch Helper
**Date:** 2026-05-20  
**Agent:** A9 technical-debt-pass  
**Source:** cleanup_subagent_1_dedup.md finding #2 (Seed Catalog Boilerplate)

## Refactor Goal

Extract the repeated `for part in parts: try: db.parts.create(...) except: logger.error(...)` boilerplate loop from 4 seed catalog files into a single `_create_parts_batch()` helper in `motoquant/database/seed_catalogs/__init__.py`.

## Files Modified

| File | Change |
|------|--------|
| `motoquant/database/seed_catalogs/__init__.py` | Created — 87 lines, helper + module docstring |
| `motoquant/database/seed_catalogs/adv_cruiser_exhausts.py` | Removed 24-line loop → 1-line call (-23 lines) |
| `motoquant/database/seed_catalogs/drag_specific.py` | Removed 29-line loop → 1-line call (-28 lines) |
| `motoquant/database/seed_catalogs/two_stroke.py` | Removed 29-line loop → 1-line call (-28 lines) |
| `motoquant/database/seed_catalogs/drag_prep_specialty.py` | Removed 28-line loop + stray logger imports → 1-line call (-28 lines) |

**LOC delta:** +87 new / -107 removed = **net -20 lines** (plus 2 identical `import logging` + `logger = getLogger(__name__)` lines removed from each of 4 files). Well within <300 LOC constraint.

## Before / After

**Before (repeated in 4 files, ~25 lines each):**
```python
import logging
logger = logging.getLogger(__name__)
# ... parts list built ...
count = 0
for part in parts:
    try:
        db.parts.create(
            category_name=part["category"],
            brand=part["brand"],
            # ... 12+ kwargs ...
        )
        count += 1
        logger.info(f"✓ Created: {part['brand']} {part['model_name']}")
    except Exception as e:
        logger.error(f"✗ Failed to create {part['brand']} {part['model_name']}: {e}")
logger.info(f"Label: {count} parts seeded")
return count
```

**After (each seeder, 1 line):**
```python
return _create_parts_batch(db, parts, label="ADV/Cruiser Exhausts")
```

## Files NOT touched

- `indian_retailer_depth.py` — different key names (`fitment_notes`, `mrp_inr`, `estimated_delivery_days` are keyed differently vs the other 4 files); risk of silent kwarg mismatch > benefit.
- `premium_universal.py` — no try/except; different `fitment_universal` kwarg; different `availability` default. Left as-is.

## Validation

**Test suite:** `pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py tests/test_submodel_kaizen.py` → **182 passed in 12.70s, 0 failures**

**K5/R1/Hayabusa baselines:**
```
K5:   10.0334 target=10.0334 delta=+0.0000
R1:   10.2859 target=10.2859 delta=+0.0000
Busa: 10.4712 target=10.4712 delta=+0.0000
```

## Kaizen checklist

- [x] No silent failure mode introduced — try/except preserved in helper, errors still logged per-row
- [x] No data/model mismatch — `db.parts.create()` signature unchanged; helper passes all kwargs
- [x] No bypass path — all 4 catalogues now go through the same code path
- [x] Test coverage — 182 tests pass including `test_two_stroke` which exercises the seeded 2T catalog
- [x] Numerical sanity — baselines unchanged at +0.0000s delta
- [x] No dead fields introduced

## Ship or Skip

**SHIP** — clean refactor, tests green, baselines exact, net LOC reduction.
