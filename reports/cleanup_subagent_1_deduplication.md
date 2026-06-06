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
