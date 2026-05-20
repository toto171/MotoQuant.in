# Tech Debt: Seed Catalog Inline Loop Consolidation
**Date:** 2026-05-20  
**Agent:** technical-debt-pass  
**Outcome:** ship

## Finding

The dedup subagent report (2026-05-05) identified that all seed catalog files should use
`_create_parts_batch()` from `seed_catalogs/__init__.py`. Five of six files had already
been migrated. `indian_retailer_depth.py` still contained the original 28-line inline
loop, for two reasons:

1. It was written before `_create_parts_batch()` existed.
2. It used `"estimated_delivery_days"` as the dict key, while the helper only
   recognised `"delivery_days"`. A naïve swap would have silently dropped delivery-day
   data for all ~90 Indian-market parts.

## Change

**`motoquant/database/seed_catalogs/__init__.py`** (+5 LOC):
- `_create_parts_batch()` now resolves `estimated_delivery_days` as a fallback alias:
  `part.get("delivery_days") or part.get("estimated_delivery_days")`.
  The `"delivery_days"` key retains precedence (backwards compat with all other catalogs).
- Module docstring updated to document both accepted keys.

**`motoquant/database/seed_catalogs/indian_retailer_depth.py`** (-30 LOC):
- Removed inline `import logging` / `logger = getLogger(...)` from function body.
- Removed 28-line try/except insertion loop.
- Replaced with single `return _create_parts_batch(db, parts, label="Indian Retailer Depth Parts")`.

## Before / After

| Metric | Before | After |
|--------|--------|-------|
| Inline loop files | 1 of 6 | 0 of 6 |
| LOC in `indian_retailer_depth.py` | 2764 | 2734 |
| `__init__.py` | 102 | 107 |
| Net LOC delta | — | −25 |

## Behavioral changes

None. The only functional difference is that `estimated_delivery_days` values (14–42 days
on Indian import parts) now correctly pass through `_create_parts_batch()` instead of
being silently lost. This was a latent bug in the original — the old loop was correct but
the helper was not. Both are now consistent.

## Tests

- `tests/test_compatibility.py` + `tests/test_scraper.py` + `tests/test_two_stroke.py`:
  **140 passed** in 4.94s, 0 failures.
- Physics baselines: K5=10.0334s / R1=10.2859s / Hayabusa=10.4712s — exact match.
