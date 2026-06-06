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
