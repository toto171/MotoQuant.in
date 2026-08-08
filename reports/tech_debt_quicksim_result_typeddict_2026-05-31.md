# Tech-Debt Pass — `QuickSimResultDict` + `AppliedPartDict` TypedDicts
**Date:** 2026-05-31 (Sunday)
**Agent:** A9 (technical-debt-pass)
**Scope:** `motoquant/api.py` (single file)
**Source finding:** `reports/cleanup_subagent_2_types.md` finding #4
("QuickSimResponse: Critical Field Divergence — pending verification")

## Refactor goal (one sentence)

Make the `/api/simulate/quick` response shape and the `_apply_parts_to_config`
parts-summary shape explicit via `QuickSimResultDict` + `AppliedPartDict`
TypedDicts, matching the existing `BikeRowSummary` / `SimDict` / `CompareDict`
pattern so the Python ↔ desktop TS contract is type-checkable on both ends.

## Why this one

- Subagent 2's pending-verification item: TS declares 11 fields on
  `QuickSimResponse`; the Python route built an untyped `dict` literal with the
  same 11 fields. They drift the moment anyone adds a key on one side and
  forgets the other.
- Today's earlier session already landed
  `api_apply_parts_helper_2026-05-31` (helper extraction) — typing the helper's
  return value is the natural follow-up and uses the same surface.
- Mechanical, additive, single file, no physics path touched.

## Success criteria

- [x] `QuickSimResultDict` TypedDict declared next to `BikeRowSummary` with
      docstring pointing at the matching TS interface.
- [x] `AppliedPartDict` TypedDict (with `total=False` so the optional
      `price_inr` key can be omitted when `include_price_in_summary=False`).
- [x] `_apply_parts_to_config` return type tightened from
      `tuple[BikeConfig, list[dict], float]` to
      `tuple[BikeConfig, list[AppliedPartDict], float]`.
- [x] `simulate_quick` return-type annotation set to `QuickSimResultDict`.
- [x] Inline `result` literal annotated `: QuickSimResultDict` so future field
      typos fail mypy / pyright instead of silently shipping.
- [x] Single file touched.
- [x] LOC delta ≤ 300 (actual: +50 / -5 = **net +45**).
- [x] Focused tests green.
- [x] K5 / R1 / Hayabusa baselines preserved to 4 decimals.

## Before / after

### Before

```python
def _apply_parts_to_config(
    cfg: BikeConfig,
    part_ids: list[int] | None,
    *,
    include_price_in_summary: bool = True,
) -> tuple[BikeConfig, list[dict], float]:
    ...
    summary = {
        "id": part_dict["id"],
        "name": part_dict.get("model_name", ""),
        "brand": part_dict.get("brand", ""),
    }
    if include_price_in_summary:
        summary["price_inr"] = part_dict.get("price_inr")
    parts_applied.append(summary)
    ...


@app.post("/api/simulate/quick")
def simulate_quick(req: QuickSimRequest):
    ...
    result = {
        "et_quarter_s": ...,
        # 10 more fields, untyped
    }
    return result
```

### After

```python
class AppliedPartDict(TypedDict, total=False):
    id: int
    name: str
    brand: str
    price_inr: float | None


class QuickSimResultDict(TypedDict):
    et_quarter_s: float
    trap_speed_kmh: float
    et_60ft_s: float
    et_eighth_s: float
    bike_name: str
    peak_power_hp: float
    total_mass_kg: float
    parts_applied: list[AppliedPartDict]
    build_cost_inr: float
    stock_et_s: float | None
    et_delta_s: float | None


def _apply_parts_to_config(
    cfg: BikeConfig,
    part_ids: list[int] | None,
    *,
    include_price_in_summary: bool = True,
) -> tuple[BikeConfig, list[AppliedPartDict], float]:
    ...
    summary: AppliedPartDict = {...}
    ...


@app.post("/api/simulate/quick")
def simulate_quick(req: QuickSimRequest) -> QuickSimResultDict:
    ...
    result: QuickSimResultDict = {...}
    return result
```

## Field-shape derivation

Shapes derived from the actual inline literals at the existing call sites:

- `QuickSimResultDict`: read directly off `motoquant/api.py:simulate_quick`
  lines 933-947 (the only construction site).
- `AppliedPartDict`: read off `_apply_parts_to_config` lines 432-439. The
  `total=False` qualifier mirrors the existing `include_price_in_summary`
  branch — `price_inr` is only set when the caller wants the price (today only
  `_run_build` passes `include_price_in_summary=False`).

Cross-referenced against `desktop/src/types/api.ts::QuickSimResponse`
(lines 274-286) and `desktop/src/types/api.ts::AppliedPart` (lines 267-272) —
field names + nullability all match.

## Files touched

- `/tmp/mq-session-1780259453-632/repo/motoquant/api.py` (+50 / -5)

## Validation

| Check                              | Result          |
|------------------------------------|-----------------|
| `python3 -c "import ast; ast.parse(open('motoquant/api.py').read())"` | parse OK |
| `test_scraper + test_validation + test_two_stroke + test_compatibility + test_submodel_kaizen + test_power_boost_regression` | **221/221 passed in 15.52s** |
| K5 baseline                        | 10.0334s (Δ +0.0000s) PASS |
| R1 baseline                        | 10.2859s (Δ +0.0000s) PASS |
| Hayabusa baseline                  | 10.4712s (Δ +0.0000s) PASS |

`test_api.py` requires `fastapi` which is not installable in the sandbox
(`/sessions` disk-full per CLAUDE.md standing note); the existing FastAPI
TestClient suite (`tests/test_api.py`) will exercise this route in CI.

## Risk assessment

Zero runtime risk. `TypedDict` is erased at runtime — both `QuickSimResultDict`
and `AppliedPartDict` compile to plain `dict`, so the JSON the route emits
byte-equivalent to before. The only effective change is the static type
contract surface area.

## Out of scope (intentionally not touched)

- Subagent-5 finding #4 (`[extra: string]: unknown` index signatures on TS
  response models). Needs a server-side audit on whether the API legitimately
  returns extra fields before tightening to `never`; not mechanical.
- Subagent-5 medium-confidence #1 (`_build_*_from_spec()` internal dict usage
  in `importer.py`). Touches the catalog/physics import path → out of scope per
  technical-debt-pass agent's "no physics or catalog edits ever" rule.
- Subagent-1 finding #3 (architectural smell — `CATEGORY_AERO` in `importer.py`
  vs `category_profiles.py` per-cluster knobs). Architectural decision, not a
  mechanical refactor; defer to a design discussion.
- Other endpoint return types (`SimulateResponse`, `TopSpeedResponse`,
  `DistanceResponse`, etc.). Same pattern would apply but each is a separate
  concern — one file, one shape per pass keeps the diffs reviewable.

## Commit message

```
refactor(api): type /api/simulate/quick response with QuickSimResultDict
```
