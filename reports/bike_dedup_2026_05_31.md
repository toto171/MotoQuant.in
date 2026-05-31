# Bike Catalog De-duplication — 2026-05-31

## Result
**796 → 495 bike_models** (301 phantom duplicate rows purged). All distinct generations preserved; only exact-identity duplicates removed.

## What was wrong
- The `/bikes` page showed the same bike (e.g. *Norden 901 Expedition (2025)* ×10) repeated. Cause: repeated autonomous daily `import --known-bikes` runs re-inserted bikes that already existed, because the year-suffixed `model_name` (`Norden 901 Expedition (2025)`) didn't match the existing row in the lenient upsert fallback (the documented `bike_repo.create_model` year-suffix bug). One extra copy accumulated per run (created_at timestamps 2026-04-27 → 05-25).
- The live catalog had grown to **796** rows, of which **301** were exact duplicates across **37** groups (10×, etc.).
- The working-tree `motoquant.db` on the mount was also **truncated/corrupted** (6.6 MB, unreadable) from a prior bad write. The committed git blob was a stale **342**-bike copy — neither was the real catalog. The true 796-bike DB was recovered from a prior-session `/tmp` clone (integrity OK).

## Duplicate key
Exact identity = `(manufacturer_id, model_name, year_from, year_to)`. This collapses re-import copies while keeping legitimate generation splits (e.g. GSX-R 1000 2001-02 / 2003-04 / 2007-08 … and the reference rows GSX-R 1000 K5/K6, YZF-R1 4C8, Hayabusa GSX1300R Gen1 all retained). Keeper per group = highest data_completeness → has model_code → longest code → lowest id.

## Cascade (orphans cleaned)
- bike_models: −301 (→ 495)
- bike_configs: −301 (→ 511)
- dyno_curves: −301 (→ 511)
- bike_tire_fitments: −540 (→ 1229)
- sim_runs: 0 lost · spec_corrections: 0 · bike_archetypes: 0 (none referenced a duplicate)

## Verification (post-purge, read back from the mount)
- `PRAGMA integrity_check` = **ok**; `PRAGMA foreign_key_check` = **clean**
- bike_models = **495**; remaining exact-dup groups = **0**; orphans = **0**; bikes with 0 configs = **0**
- Reference baselines (defaults.py, DB-independent): **K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — Δ +0.0000s**
- Untouched: 30 manufacturers · 563 parts · 232 tires · 20 venues

## Follow-ups (not done here)
1. **Root cause** — patch `bike_repo.create_model` to strip the `(YYYY-YYYY)` suffix before matching, or duplicates will re-accumulate on the next daily import.
2. **Commit** — committed HEAD `motoquant.db` is the stale 342-row truncated copy; the fixed 495-row DB is in the working tree and should be committed/pushed via the normal workflow.
3. `motoquant.db.corrupt-20260531` (backup of the corrupt original) and the stale 0-byte `motoquant.db-wal` can be deleted from a real terminal.
4. Headline-stats sync: any "N bikes" strings in `web/`, `README.md`, blog/docs should be re-pointed to 495.
