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

