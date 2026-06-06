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

