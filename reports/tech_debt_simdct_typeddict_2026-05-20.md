# Tech-Debt Pass — `SimDict` TypedDict for `_run_one_sim` return shape
**Agent:** A9 technical-debt-pass
**Date:** 2026-05-20 (Tuesday)
**Source finding:** `reports/cleanup_subagent_5_types.md` medium-confidence finding — `ChatResult.sim_result: dict[str, Any] | None` is opaque; `_run_one_sim` builds a fixed 6-required + 3-optional field dict whose contract is invisible to type checkers.

## Goal (one sentence)

Introduce a `SimDict` TypedDict in `motoquant/llm/runner.py` that names the fixed-shape dict returned by `_run_one_sim` and consumed by `ChatResult.sim_result`, so the sim-result contract is discoverable, type-checkable, and pinned against future field-name drift.

## Success criteria

- `_run_one_sim` returns `SimDict | str` instead of `dict[str, Any] | str`.
- `ChatResult.sim_result` is typed `SimDict | None` instead of `dict[str, Any] | None`.
- `SimDict` splits 6 required fields (always produced) from 3 optional split-time fields (added only when `SimResult` carries the attribute), matching exactly what `_run_one_sim` constructs.
- `_summarize_explain`'s `sim_context` parameter tightened to `SimDict | None`.
- Local variable `sim_for_context` in `_run_explain` tightened to `SimDict | None`.
- Focused tests + `test_llm_runner.py` unit tests still pass.
- K5/R1/Hayabusa baselines preserved exactly to 4 decimals.
- Single file touched, ≤60 LOC delta.

## Files modified

| File | Change |
|---|---|
| `motoquant/llm/runner.py` | +40 / -10 = **net +30 lines** |

That is the only file touched.

## Before / after

**Before:**
```python
from typing import TYPE_CHECKING, Any
# ...
class ChatResult:
    sim_result: dict[str, Any] | None = None  # simulate

def _run_one_sim(bike_id, parsed, db) -> dict[str, Any] | str:
    out: dict[str, Any] = { "et_quarter_s": ..., ... }
    return out

def _run_explain(...):
    sim_for_context: dict[str, Any] | None = None

def _summarize_explain(parsed, sim_context: dict[str, Any] | None, client) -> str:
```

**After:**
```python
from typing import TYPE_CHECKING, Any, TypedDict

class _SimDictBase(TypedDict):
    """Required fields — always present in a successful _run_one_sim result."""
    et_quarter_s: float
    trap_speed_kmh: float
    trap_speed_mph: float
    et_60ft_s: float
    peak_accel_g: float
    bike_name: str

class SimDict(_SimDictBase, total=False):
    """Full sim result including optional split-time fields."""
    et_330ft_s: float
    et_eighth_s: float
    et_1000ft_s: float

class ChatResult:
    sim_result: SimDict | None = None  # simulate

def _run_one_sim(bike_id, parsed, db) -> SimDict | str:
    out: SimDict = { "et_quarter_s": ..., ... }
    return out

def _run_explain(...):
    sim_for_context: SimDict | None = None

def _summarize_explain(parsed, sim_context: SimDict | None, client) -> str:
```

## Design choices

### Two-class inheritance pattern (`_SimDictBase` + `SimDict`)
`TypedDict` does not support mixing required and optional fields in a single class.
The idiomatic Python approach (documented in PEP 655 / mypy docs) is to separate
required and optional fields into two classes and inherit: `_SimDictBase(TypedDict)`
carries the 6 always-present fields with `total=True` (default); `SimDict(_SimDictBase, total=False)`
adds the 3 optional split-time fields.

Verified: `SimDict.__required_keys__` = `{et_quarter_s, trap_speed_kmh, trap_speed_mph, et_60ft_s, peak_accel_g, bike_name}` and `SimDict.__optional_keys__` = `{et_330ft_s, et_eighth_s, et_1000ft_s}` — exactly matching what `_run_one_sim` constructs.

### `total=False` optional keys match the conditional-add pattern
The three split fields are added via `out[key] = round(float(val), 4)` inside a loop that only fires when `getattr(sim, attr, None)` is non-None. TypedDict optional keys document this correctly without lying about what's always there.

### `bike_name: str` in required keys despite being filled by caller
`_run_one_sim` always initialises `"bike_name": ""` (empty string) before returning. Callers patch it in after. The field is therefore always structurally present on the returned dict; it just may be `""`. Marking it required in `_SimDictBase` is accurate — it is never absent.

### Runtime cost: zero
`TypedDict` is completely erased at runtime (`SimDict` is just a `dict` subclass marker). The `isinstance(sim, dict)` guards throughout the file continue to work identically. The `asdict(self)` call in `ChatResult.to_dict()` continues to serialise `sim_result` as a plain dict to JSON.

## Tests run

```
python3 -m pytest tests/test_scraper.py tests/test_validation.py \
    tests/test_two_stroke.py tests/test_compatibility.py \
    tests/test_submodel_kaizen.py tests/test_power_boost_regression.py
# → 192 passed, 533 warnings in 15.76s

python3 -m pytest tests/test_llm_runner.py -k "not TestChatEndpoint"
# → 7 passed in 1.09s
# (TestChatEndpoint skipped: fastapi not installed in sandbox — pre-existing)
```

Total: **199 tests passed, 0 failed.**

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
| `_run_one_sim` return type | `dict[str, Any] \| str` | `SimDict \| str` |
| `ChatResult.sim_result` type | `dict[str, Any] \| None` | `SimDict \| None` |
| `_summarize_explain` param type | `dict[str, Any] \| None` | `SimDict \| None` |
| `sim_for_context` local type | `dict[str, Any] \| None` | `SimDict \| None` |
| Named sim-result fields | 0 (opaque) | 9 (6 required + 3 optional) |
| `runner.py` LOC | 1475 | 1505 |
| Net LOC delta | — | +40 / -10 = **+30** |
| Tests run | 199 | 199 |
| Tests passed | 199 | 199 |
| K5 / R1 / Hayabusa drift | n/a | 0.0000s on all three |

## Kaizen checklist

- [x] **No silent failure** — TypedDict is erased at runtime; all dict access, `isinstance(sim, dict)` guards, and `asdict()` calls work identically. No behavioural change.
- [x] **No data/model mismatch** — `SimDict` was constructed by reading `_run_one_sim` line-by-line: the 6 always-initialised keys become required; the 3 conditionally-added split keys become optional. The split between required and optional keys is verified by `SimDict.__required_keys__` / `__optional_keys__` at runtime.
- [x] **No bypass path** — `_run_one_sim` is the only constructor for this dict shape; all callers (`_run_simulate`, `_run_compare`, `_run_explain`, `_run_choose_bike`) assign via `result.sim_result = sim` or `sim_for_context = sim`. All annotated now.
- [x] **Test coverage** — `test_llm_runner.py` tests verify `result.sim_result["et_quarter_s"]` is present and in range (7 unit tests pass); future code that tries to read a misspelled key (`sim_result["et_quater_s"]`) will get a type error.
- [x] **Numerical sanity** — physics untouched; all three baselines Δ +0.0000s.
- [x] **No dead fields introduced** — each field maps exactly to a key produced by `_run_one_sim`.
- [x] **Backwards compatibility** — `dict` subtype; all JSON serialisation, dict access, and `isinstance` checks continue to work.

## Rationale

The three prior tech-debt passes in this sprint applied TypedDict strengthening to
`extract_headline_specs` (bridge.py, 2026-05-16) and `_bike_row_to_summary` (api.py, 2026-05-20).
This pass closes the same pattern for the LLM chat pipeline — `_run_one_sim` is the
innermost physics dispatch function in the chat loop and its return shape is the most
frequently consumed fixed-shape dict in that module. Without `SimDict`, any future
field rename or addition on either the Python or frontend side is invisible to the type
checker; with `SimDict`, the mismatch surfaces at the definition site.

The subagent report flagged this as medium-confidence because the `dict[str, Any]` was
"intentionally permissive for test mocks". In practice, the only two mock callers in
the test suite (`TestRunChatPipeline`) pass a real DB and hit the real `_run_one_sim`
path — no mock ever returns a hand-crafted `sim_result`. TypedDict is safe here.

## Ship or skip

**SHIP** — clean type strengthening, runtime behaviour unchanged, 199 tests green, baselines exact, +30 LOC. Zero risk.
