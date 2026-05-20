# Tech-Debt Pass — `CompareDict` TypedDict for `_run_compare` result shape
**Agent:** A9 technical-debt-pass
**Date:** 2026-05-20
**Source finding:** `reports/cleanup_subagent_5_types.md` medium-confidence — `ChatResult.compare_result: dict[str, Any] | None` is opaque; the constructor builds a fixed 5-top-level-field dict with two nested `_CompareBikeEntry` dicts whose contract is invisible to type checkers.

## Goal (one sentence)

Introduce `CompareDict` (and a private `_CompareBikeEntry`) TypedDict in `motoquant/llm/runner.py` to name the fixed-shape dict returned by `_run_compare` and consumed by `_summarize_compare`, so the compare-result contract is discoverable, type-checkable, and pinned against future field-name drift — mirroring the `SimDict` pattern landed earlier today.

## Success criteria

- `_run_compare` constructs a typed `compare_payload: CompareDict` local before assigning to `result.compare_result`.
- `ChatResult.compare_result` typed `CompareDict | None` instead of `dict[str, Any] | None`.
- `_summarize_compare`'s `comp` parameter tightened to `CompareDict`.
- Nested `a` / `b` entries typed via `_CompareBikeEntry` (which reuses the existing `SimDict` for `sim`).
- Focused tests (192) and `test_llm_runner.py` unit tests (7) still pass.
- K5/R1/Hayabusa baselines preserved exactly to 4 decimals.
- Single file touched, <60 LOC delta.

## Files modified

| File | Change |
|---|---|
| `motoquant/llm/runner.py` | +37 / -3 = **net +34 lines** |

Single file touched.

## Before / after

**Before:**
```python
class ChatResult:
    compare_result: dict[str, Any] | None = None  # compare

def _run_compare(...):
    ...
    result.compare_result = {
        "a": {"bike_id": ..., "bike_name": ..., "sim": sim_a},
        "b": {"bike_id": ..., "bike_name": ..., "sim": sim_b},
        "delta_et_s": round(delta_et, 4),
        "delta_trap_kmh": round(delta_trap, 1),
        "faster": faster,
    }

def _summarize_compare(
    parsed: ParsedSimRequest, comp: dict[str, Any], client: LLMClient | None
) -> str:
```

**After:**
```python
class _CompareBikeEntry(TypedDict):
    bike_id: int | None
    bike_name: str | None
    sim: SimDict

class CompareDict(TypedDict):
    a: _CompareBikeEntry
    b: _CompareBikeEntry
    delta_et_s: float
    delta_trap_kmh: float
    faster: str  # "A" | "B" | "tie"

class ChatResult:
    compare_result: CompareDict | None = None  # compare

def _run_compare(...):
    ...
    compare_payload: CompareDict = {
        "a": {"bike_id": parsed.bike_id, "bike_name": parsed.bike_name, "sim": sim_a},
        "b": {"bike_id": parsed.bike_b_id, "bike_name": parsed.bike_b_name, "sim": sim_b},
        "delta_et_s": round(delta_et, 4),
        "delta_trap_kmh": round(delta_trap, 1),
        "faster": faster,
    }
    result.compare_result = compare_payload

def _summarize_compare(
    parsed: ParsedSimRequest, comp: CompareDict, client: LLMClient | None
) -> str:
```

## Design choices

### `_CompareBikeEntry` private + reused `SimDict`
The nested `a` / `b` dicts share the same shape and contain a `SimDict`-typed `sim` payload. Naming this `_CompareBikeEntry` (leading underscore = module-private) keeps the public surface tight — only `CompareDict` is exported via the type system.

### `faster: str` (not `Literal["A", "B", "tie"]`)
The constructor builds `faster` from a 3-branch if/elif/else that pinpoints `"A"` / `"B"` / `"tie"`, so a `Literal` annotation would be more precise. However, `_summarize_compare` interpolates `comp['faster']` into an f-string with no narrowing — Literal vs str makes no semantic difference at the use site, and a future maintainer wanting to add e.g. `"close"` should not have to chase Literal type errors across two callers. Kept `str` with a comment documenting the actual value space.

### Runtime cost: zero
`TypedDict` is erased at runtime; `CompareDict` is just a `dict` subclass marker. Verified at the REPL:
```
CompareDict.__required_keys__ = {'a', 'b', 'delta_et_s', 'delta_trap_kmh', 'faster'}
CompareDict.__optional_keys__ = frozenset()  # all required, no None defaults
```
The `result.summary = _summarize_compare(parsed, result.compare_result, client)` call site continues to pass the dict through with no boxing/serialisation changes. `asdict(self)` on the parent dataclass still serialises `compare_result` as plain dict.

## Tests run

```
python3 -m pytest tests/test_scraper.py tests/test_validation.py \
    tests/test_two_stroke.py tests/test_compatibility.py \
    tests/test_submodel_kaizen.py tests/test_power_boost_regression.py
# → 192 passed, 536 warnings in 16.26s

python3 -m pytest tests/test_llm_runner.py -k "not TestChatEndpoint"
# → 7 passed, 6 deselected in 1.08s
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
| `ChatResult.compare_result` type | `dict[str, Any] \| None` | `CompareDict \| None` |
| `_summarize_compare` param type | `dict[str, Any]` | `CompareDict` |
| `_run_compare` local construction | untyped `dict` literal | typed `CompareDict` local |
| Named compare-result fields | 0 (opaque) | 5 top-level + 3 per-side |
| `runner.py` LOC | 1505 | 1539 |
| Net LOC delta | — | +37 / -3 = **+34** |
| Tests run | 199 | 199 |
| Tests passed | 199 | 199 |
| K5 / R1 / Hayabusa drift | n/a | 0.0000s on all three |

## Kaizen checklist

- [x] **No silent failure** — TypedDict is erased at runtime; all dict access, `asdict()`, and JSON serialisation work identically. No behavioural change.
- [x] **No data/model mismatch** — `CompareDict` was constructed by reading the 5-line dict literal in `_run_compare` (lines 288–302) and the 5 field-reads in `_summarize_compare` (`comp["a"]`, `comp["b"]`, `comp["delta_et_s"]`, `comp["delta_trap_kmh"]`, `comp["faster"]`). 1:1 match.
- [x] **No bypass path** — `_run_compare` is the only constructor for this dict shape; `_summarize_compare` is the only typed consumer; `asdict(self)` and JSON serialisation transit it as a plain dict. All annotated now.
- [x] **Test coverage** — existing `test_llm_runner.py` exercises the `_run_compare` → `_summarize_compare` path; future code that tries to read `comp["delta_et"]` (missing the `_s` suffix) will get a type error.
- [x] **Numerical sanity** — physics untouched; all three baselines Δ +0.0000s.
- [x] **No dead fields introduced** — each field maps exactly to a key produced by `_run_compare`.
- [x] **Backwards compatibility** — `dict` subtype; all JSON serialisation, dict access, and `isinstance` checks continue to work.

## Rationale

This pass extends the TypedDict strengthening already applied to `extract_headline_specs` (bridge.py, 2026-05-16), `_bike_row_to_summary` (api.py, 2026-05-20), and `_run_one_sim` → `SimDict` (runner.py, earlier 2026-05-20). The `compare_result` payload was the next-most-frequently-consumed fixed-shape dict in `runner.py`, and its 5-field shape with a nested SimDict made it a natural fit for the same pattern. Both `rank_result` and `recommend_result` remain opaque `dict[str, Any]`; those are larger payloads (~10–14 fields each with nested arrays) and warrant their own dedicated passes.

## Out of scope (intentionally not touched)

- `ChatResult.rank_result` and `ChatResult.recommend_result` — bigger payloads with nested arrays of heterogeneous dicts, each deserves its own pass.
- `ChatResult.explain_result` — explainer payload, structure varies by sub-intent.
- The `faster` Literal narrowing — judged not worth the maintenance cost (see Design Choices).

## Ship or skip

**SHIP** — clean type strengthening, runtime behaviour unchanged, 199 tests green, baselines exact, +34 LOC, single file. Zero physics risk.
