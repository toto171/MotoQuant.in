# Tech-Debt Pass — `BikeRowSummary` TypedDict
**Agent:** A9 technical-debt-pass
**Date:** 2026-05-20 (Wednesday)
**Source finding:** `reports/cleanup_subagent_5_types.md` finding #1 (high-confidence type strengthening)

## Goal (one sentence)

Replace the loose `_bike_row_to_summary(row: dict) -> dict` signature in `motoquant/api.py` with a concrete `BikeRowSummary` TypedDict so the 9-field contract between this helper and the `BikeSummary` TypeScript interface in `desktop/src/types/api.ts` is explicit, discoverable, and type-checkable.

## Success criteria

- `_bike_row_to_summary` returns a typed `BikeRowSummary` (9 fields, all nullable to mirror `row.get(...)` semantics + the TS contract).
- Both call sites continue to work unchanged at runtime (TypedDict is erased — `dict` subtype).
- Focused tests + `test_database.py` still pass.
- K5/R1/Hayabusa baselines preserved exactly to 4 decimals.
- LOC delta ≤ 50.

## Files modified

| File | Change |
|---|---|
| `motoquant/api.py` | +29 / -2 = **net +27 lines** |

That is the only file touched. No call-site edits were needed — both existing call sites (`/api/bikes` list at line 482, `/api/bikes/{id}` detail at line 510) continue to work because TypedDict is erased at runtime and `**dict` semantics are unchanged.

## Before / after

**Before:**
```python
def _bike_row_to_summary(row: dict) -> dict:
    return {
        "id": row.get("id"),
        ...
    }
```

**After:**
```python
class BikeRowSummary(TypedDict):
    """Shape of the dict returned by _bike_row_to_summary.
    Mirrors BikeSummary in desktop/src/types/api.ts ..."""
    id: int | None
    manufacturer: str | None
    model: str | None
    year: int | None
    category: str | None
    displacement_cc: float | None
    peak_power_hp: float | None
    dry_mass_kg: float | None
    data_quality: str | None


def _bike_row_to_summary(row: dict[str, Any]) -> BikeRowSummary:
    return {
        "id": row.get("id"),
        ...
    }
```

## Why each field is `| None`

The function uses `row.get(...)` which returns `None` for any missing key. Even though the DB schema declares `bike_models.id` and `manufacturers.name` (the JOIN alias source) as `NOT NULL`, the parameter is a generic `dict[str, Any]` and a hypothetical caller could pass a row missing those keys (e.g. test fixtures, error responses). Marking every field nullable matches the existing `BikeSummary` TS contract:

```ts
export interface BikeSummary {
  id: number;                         // strictly required on TS side; Python is wider on purpose
  manufacturer: string | null;
  ...
  data_quality: string | null;
}
```

The Python TypedDict being slightly wider (`int | None` vs TS `number`) is the safe direction — the server can never produce a value the client can't handle, and the existing schema invariant guarantees `id` is in fact an int in practice.

## Tests run

```
python3 -m pytest tests/test_scraper.py tests/test_validation.py \
                  tests/test_two_stroke.py tests/test_compatibility.py \
                  tests/test_submodel_kaizen.py tests/test_power_boost_regression.py
# → 192 passed in 15.36s

python3 -m pytest tests/test_database.py
# → 65 passed in 2.32s
```

Total: **257 tests passed, 0 failed.**

`tests/test_api.py` is not run locally because the sandbox lacks `fastapi`; CI installs it and runs the full suite on every push, so the type-only change will be exercised end-to-end on the next push.

## Baseline verification

| Bike | Baseline | This run | Δ |
|---|---|---|---|
| GSX-R 1000 K5 | 10.0334s | 10.0334s | +0.0000s |
| YZF-R1 4C8 | 10.2859s | 10.2859s | +0.0000s |
| Hayabusa Gen 1 | 10.4712s | 10.4712s | +0.0000s |

All three reference baselines preserved exactly to 4 decimals.

## Metrics

| Metric | Before | After |
|---|---|---|
| `_bike_row_to_summary` return type | `dict` (opaque) | `BikeRowSummary` (9 named fields) |
| `row` parameter type | `dict` | `dict[str, Any]` |
| `api.py` LOC | 2838 | 2865 |
| Net LOC delta | — | +29 / -2 = **+27** |
| Tests run | 257 | 257 |
| Tests passed | 257 | 257 |
| K5 / R1 / Hayabusa drift | n/a | 0.0000s on all three |

## Kaizen checklist

- [x] No silent failure introduced — runtime behaviour unchanged; TypedDict is erased.
- [x] No data/model mismatch — TypedDict mirrors `desktop/src/types/api.ts::BikeSummary` field-for-field.
- [x] No bypass path — both call sites unchanged; second call site (`d[extra] = full[extra]` mutation in `/api/bikes/{id}`) keeps working because `dict` subtype assignment still accepts arbitrary keys at runtime.
- [x] Test coverage — existing tests exercise both call sites via the catalog-loaded DB; no new test fixture needed because the contract is "these keys are present with these types" which is structural.
- [x] Numerical sanity — physics baselines unchanged.
- [x] Backwards compatibility — `BikeRowSummary` is `dict` at runtime; all `**`-unpacking, `.get(...)`, and JSON serialisation paths work identically.

## Rationale

Flagged by `reports/cleanup_subagent_5_types.md` finding #1 as a high-confidence type-strengthening target. The previous tech-debt pass (`tech_debt_headline_specs_typeddict_2026-05-16.md`) did the same surgery on `extract_headline_specs` in `motoquant/database/bridge.py`. This pass extends the same pattern to the API-layer twin — a function that constructs a fixed-shape dict that feeds straight into a documented JSON response. Before this change, a future contributor could add a key to the Python side or to the TS interface without the other side noticing; now any drift is visible at the TypedDict definition.

The change is purely additive — the previous report explicitly listed `_bike_row_to_summary` as the next "out-of-scope deferred" item, and this pass closes that follow-up.

## Out of scope (deferred to future passes)

From `cleanup_subagent_5_types.md`, still open:

- **#3** `run_chat_pipeline(db: Any, ...)` in `motoquant/llm/runner.py` — needs a `MotoQuantDB | MockDB` protocol decision first.
- **#4** TypeScript `[extra: string]: unknown` index signatures on `BikeDetail`, `Venue`, `Tire`, `PartsCategory`, `Part`. Each needs an independent audit of which extras are legitimately consumed by the UI.
- **#5** `compatible_bikes?: unknown; fitment_rules?: unknown` on `Part` in `desktop/src/types/api.ts`.
- **#6, #7** TypeScript double-cast patterns (`as unknown as { ... }`) in `BuildPage.tsx` and `SimulatePage.tsx`.

These are separate refactors with their own blast radii.

## Ship or skip

**SHIP** — clean type strengthening, runtime behaviour unchanged, 257 tests green, baselines exact, +27 LOC. No risk.
