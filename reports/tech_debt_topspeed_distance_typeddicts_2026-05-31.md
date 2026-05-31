# Tech-Debt Pass — `TopSpeedResultDict` + `DistanceResultDict` TypedDicts
**Date:** 2026-05-31 (Sunday)
**Agent:** A9 (technical-debt-pass)
**Scope:** `motoquant/api.py` (single file)
**Source finding:** Carry-forward from
`reports/tech_debt_quicksim_result_typeddict_2026-05-31.md` "Out of scope"
list (other endpoint return types: `TopSpeedResponse`, `DistanceResponse`).

## Refactor goal (one sentence)

Make the `/api/simulate/top-speed` and `/api/simulate/distance` response
shapes explicit via `TopSpeedResultDict`, `DistanceResultDict`, plus the
supporting `LsrSplitDict` and `TopSpeedTimeseriesDict`, matching the
pattern this morning's `QuickSimResultDict` pass established so the LSR
endpoint contracts are statically type-checkable.

## Why this one

- Today's earlier session typed `/api/simulate/quick` with
  `QuickSimResultDict` and explicitly listed the LSR endpoints as the
  natural follow-up.
- Same mechanical, additive, single-file pattern — no physics, no catalog,
  no test relaxation.
- No TypeScript counterpart exists in `desktop/src/types/api.ts` for these
  two routes (web simulator consumes them as untyped JS in
  `web/app/simulator/page.js:482`), so this is a pure backend type-safety
  win with zero TS drift risk.

## Success criteria

- [x] `LsrSplitDict` declared next to the existing TypedDict block.
- [x] `TopSpeedTimeseriesDict` declared (single-source for the seven
      channels emitted when `include_timeseries=True`).
- [x] `TopSpeedResultDict(total=False)` declared — `total=False` because
      `timeseries` is the only optional key.
- [x] `DistanceResultDict` declared (all keys always populated).
- [x] `simulate_top_speed` return-type annotation set to
      `TopSpeedResultDict`; inline `response` literal annotated.
- [x] `simulate_distance` return-type annotation set to
      `DistanceResultDict`; inline `result` literal annotated.
- [x] Inline `splits_fmt` dict annotated `dict[str, LsrSplitDict]` so a
      future per-split key typo fails the type checker rather than
      silently shipping.
- [x] Single file touched.
- [x] LOC delta ≤ 300 (actual: +85 / -6 = **net +79**).
- [x] Focused tests green.
- [x] K5 / R1 / Hayabusa baselines preserved to 4 decimals.

## Field-shape derivation

Shapes derived from the actual inline literals at the existing call sites:

- `TopSpeedResultDict`: read directly off
  `motoquant/api.py:simulate_top_speed` (lines 1063-1080 in HEAD, the only
  construction site).
- `LsrSplitDict`: read off the `splits_fmt[k] = {...}` literal in the same
  function (lines 1056-1061 in HEAD).
- `TopSpeedTimeseriesDict`: read off the
  `response["timeseries"] = {...}` literal (lines 1086-1094 in HEAD).
- `DistanceResultDict`: read off `simulate_distance` (lines 1166-1176 in
  HEAD).

No web/TS counterpart to cross-check — the web simulator
(`web/app/simulator/page.js`) parses these responses as untyped JSON. If a
desktop TS interface is ever added, this TypedDict is the canonical
source-of-truth to mirror.

## Before / after

### Before

```python
@app.post("/api/simulate/top-speed")
def simulate_top_speed(req: TopSpeedRequest):
    ...
    splits_fmt = {}
    for k, v in ts.lsr_splits.items():
        splits_fmt[k] = {"time_s": ..., "speed_ms": ..., ...}

    response = {
        "terminal_velocity_ms": ...,
        # 17 more fields, untyped
    }
    if req.include_timeseries:
        response["timeseries"] = {...}
    return response


@app.post("/api/simulate/distance")
def simulate_distance(req: DistanceRunRequest):
    ...
    return {
        "distance_m": ...,
        # 8 more fields, untyped
    }
```

### After

```python
class LsrSplitDict(TypedDict):
    time_s: float
    speed_ms: float
    speed_kmh: float
    speed_mph: float


class TopSpeedTimeseriesDict(TypedDict):
    t: list[float]
    v_ms: list[float]
    v_kmh: list[float]
    rpm: list[float]
    gear: list[int]
    power_kw: list[float]
    x_m: list[float]


class TopSpeedResultDict(TypedDict, total=False):
    terminal_velocity_ms: float
    terminal_velocity_kmh: float
    terminal_velocity_mph: float
    time_to_terminal_s: float
    distance_to_terminal_m: float
    terminal_power_kw: float
    terminal_power_hp: float
    terminal_gear: int
    terminal_rpm: float
    reached_plateau: bool
    lsr_splits: dict[str, LsrSplitDict]
    bike_name: str
    peak_power_hp: float
    total_mass_kg: float
    parts_applied: list[AppliedPartDict]
    build_cost_inr: float
    timeseries: TopSpeedTimeseriesDict


class DistanceResultDict(TypedDict):
    distance_m: float
    time_s: float
    trap_speed_ms: float
    trap_speed_kmh: float
    trap_speed_mph: float
    peak_velocity_kmh: float
    bike_name: str
    peak_power_hp: float
    total_mass_kg: float


@app.post("/api/simulate/top-speed")
def simulate_top_speed(req: TopSpeedRequest) -> TopSpeedResultDict:
    ...
    splits_fmt: dict[str, LsrSplitDict] = {}
    ...
    response: TopSpeedResultDict = {...}
    if req.include_timeseries:
        timeseries: TopSpeedTimeseriesDict = {...}
        response["timeseries"] = timeseries
    return response


@app.post("/api/simulate/distance")
def simulate_distance(req: DistanceRunRequest) -> DistanceResultDict:
    ...
    result: DistanceResultDict = {...}
    return result
```

## Files touched

- `motoquant/api.py` (+85 / -6)

## Validation

| Check                              | Result          |
|------------------------------------|-----------------|
| `python3 -c "import ast; ast.parse(open('motoquant/api.py').read())"` | parse OK |
| `test_scraper + test_validation + test_two_stroke + test_compatibility + test_submodel_kaizen` | **211/211 passed in 12.73s** |
| K5 baseline                        | 10.0334s (Δ +0.0000s) PASS |
| R1 baseline                        | 10.2859s (Δ +0.0000s) PASS |
| Hayabusa baseline                  | 10.4712s (Δ +0.0000s) PASS |

`test_api.py` requires `fastapi` which is not installable in the sandbox
(`/sessions` disk-full per CLAUDE.md standing note); the existing FastAPI
TestClient suite (`tests/test_api.py`) will exercise these two routes in
CI as it does for `/api/simulate/quick`.

## Risk assessment

Zero runtime risk. `TypedDict` is erased at runtime — every new TypedDict
compiles to plain `dict`, so the JSON the two routes emit is
byte-equivalent to before. The only effective change is the static type
contract surface area, identical pattern to today's
`QuickSimResultDict` pass.

The one micro-rearrangement is in `simulate_top_speed`: the optional
`timeseries` payload is now built into a local `timeseries` variable
before assignment to `response["timeseries"]`. Same field values, same
emission, just a typeable two-step. Verified against the focused test
suite + baselines.

## Out of scope (intentionally not touched)

- Other endpoint return types still emitting untyped dicts
  (`/api/simulate` full sim, `/api/calibrate/dragy`,
  `/api/calibrate/dyno`, `/api/bikes/{id}`, `/api/leaderboard`,
  `/api/parts`, `/api/venues`, `/api/specs/correct`, `/api/venues/resolve`,
  the pricing endpoints). Same pattern applies but each is a separate
  concern — one file, one shape per pass keeps diffs reviewable.
- The `SaveRunRequest` / `simulate_compare` endpoints already use the
  `CompareDict` / `SimDict` TypedDicts (per 2026-05-20 pass).
- The Pricing endpoints already use Pydantic `BaseModel` response models
  (`PartPricingOut`, `BikePricingSummaryOut`, `PricingRefreshOut`) which
  is a different — and equally valid — typing strategy.
- Adding a corresponding TypeScript interface in
  `desktop/src/types/api.ts` for the LSR endpoints. The desktop app
  doesn't consume these yet; deferring until a desktop LSR feature lands.

## Commit message

```
refactor(api): type LSR endpoints with TopSpeedResultDict + DistanceResultDict
```
