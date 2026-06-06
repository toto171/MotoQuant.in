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
