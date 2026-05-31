# Bike Catalog De-duplication + Idempotency Fix — 2026-06-01

## Result
**799 → 498 bikes** (301 phantom duplicate rows purged) and the import path is now
**fully idempotent**, so the autonomous cron can no longer re-inflate the catalog.

## Why it recurred after the 2026-05-31 pass
The previous fix was committed locally but **never pushed to origin** (no PAT that
session). The daily cron clones origin, so it kept running the *old* buggy
`create_model` and re-bloated the catalog (→799). This pass pushes the fix to origin.

## Root cause
`UNIQUE(manufacturer_id, model_name, model_code, year_from)` cannot dedupe rows whose
`model_code` is NULL — SQLite treats NULLs as distinct in UNIQUE constraints — so
`INSERT OR IGNORE` minted a new row on every re-import (Norden 901 Expedition ×10).
An earlier partial fix matched on the normalized name **alone**, which (a) missed
single-year suffixes like `(2025)` and (b) risked collapsing distinct generations.

## Fix (motoquant/database/bike_repo.py)
- `_YEAR_SUFFIX_RE` now strips single `(YYYY)` as well as `(YYYY-YYYY)`/`(YYYY-YY)`.
- `create_model` matches on a code-independent identity — manufacturer + year-stripped
  name **+ full year range** — so re-imports reuse the row while distinct generations
  (GSX-R 1000 2001-02 vs 2003-04 …) stay separate.
- `create_config` reuses any existing version with byte-identical params (and marks it
  current), so re-imports add no new version/dyno rows — even when the source list
  carries two conflicting specs for one bike (Versys 650, Yezdi Adventure, etc.).
- Verified idempotent: importing all known bikes 3× holds at 495 models / 499 configs / 0 dup groups.

## DB purge (motoquant.db)
- bike_models 799 → **498** (dropped 301 exact/normalized duplicates; generations kept).
- bike_configs 1311 → **498** (dropped 309 loser configs + 504 churned non-current versions).
- dyno_curves and 578 duplicate fitments cascaded; 0 sim_runs lost; archetypes re-pointed.
- `integrity_check`=ok, `foreign_key_check`=clean, 0 orphans, 1 config/bike, Norden=1.
- Baselines unchanged: K5 10.0334 / R1 10.2859 / Hayabusa 10.4712.
- Catalog intact: 30 manufacturers, 563 parts, 232 tires, 20 venues.

## Headline sync
`audit_headline_stats.py --fix` set 28 sites (web/* + README + OG card) to 498.
2 pre-existing drifts remain in a 600cc blog post (mislabels K5 baseline as 10.2859) —
unrelated to this work, left for a content pass.

## Tests
`tests/test_import_idempotency.py` drives the real repo path (10× Norden → 1 row;
generations preserved; suffix/NULL-code/conflicting-code collapse; config no-op on
re-import; new version only on real spec change).
