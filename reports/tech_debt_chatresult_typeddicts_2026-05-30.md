# Tech-Debt Pass — ChatResult TypedDicts
**Date:** 2026-05-30 (Saturday)
**Agent:** A9 (technical-debt-pass)
**Scope:** `motoquant/llm/runner.py` (single file)
**Source finding:** subagent-5 medium-confidence item #2 (`reports/cleanup_subagent_5_types.md`)

## Refactor goal (one sentence)

Replace the remaining three `dict[str, Any]` payload fields on `ChatResult`
(`rank_result`, `recommend_result`, `explain_result`) with `TypedDict` shapes
so the chat dispatch surface is fully typed end-to-end.

## Success criteria

- [x] Three new `TypedDict` classes: `RankResult`, `RecommendResult`, `ExplainResult`
- [x] `ChatResult` field annotations updated from `dict[str, Any] | None` to the new TypedDicts
- [x] `_summarize_rank` and `_summarize_recommend` parameter signatures tightened
- [x] LOC delta ≤300 (actual: +125 / -5 = 130 net)
- [x] Single file touched (`motoquant/llm/runner.py`)
- [x] All focused tests green (221/221 in `test_scraper + test_validation + test_two_stroke + test_compatibility + test_submodel_kaizen + test_power_boost_regression`)
- [x] All chat-pipeline tests green (30/30 in `test_chat_advanced + test_llm_runner` excl. fastapi-gated tests)
- [x] K5/R1/Hayabusa baselines preserved exactly (Δ +0.0000s)

## Before / after

### Before

```python
@dataclass
class ChatResult:
    ...
    sim_result: SimDict | None = None            # typed
    compare_result: CompareDict | None = None    # typed
    rank_result: dict[str, Any] | None = None    # ❌ untyped
    recommend_result: dict[str, Any] | None = None  # ❌ untyped
    explain_result: dict[str, Any] | None = None    # ❌ untyped

def _summarize_rank(parsed, rk: dict[str, Any], client): ...
def _summarize_recommend(parsed, rec: dict[str, Any], client): ...
```

Typed-vs-untyped payload fields: **2 typed / 5 total = 40%**

### After

```python
class _RankEntry(TypedDict):    # 12 fields
class RankResult(TypedDict):    # 4 fields, .top: list[_RankEntry]

class _RecommendPart(TypedDict):  # 8 fields
class _RecommendTire(TypedDict):  # 9 fields
class RecommendResult(TypedDict): # 8 fields, .parts/.tires lists of the above

class ExplainResult(TypedDict):   # 2 fields

@dataclass
class ChatResult:
    ...
    sim_result: SimDict | None = None
    compare_result: CompareDict | None = None
    rank_result: RankResult | None = None         # ✅ typed
    recommend_result: RecommendResult | None = None  # ✅ typed
    explain_result: ExplainResult | None = None      # ✅ typed

def _summarize_rank(parsed, rk: RankResult, client): ...
def _summarize_recommend(parsed, rec: RecommendResult, client): ...
```

Typed-vs-untyped payload fields: **5 typed / 5 total = 100%**

## Field-shape derivation

Shapes were derived by reading the assignment sites (`result.rank_result = {...}`
at line 493, `result.recommend_result = {...}` at line 719, `result.explain_result
= {...}` at line 813) and cross-referencing the consumer sites:

- `_summarize_rank` reads `rk.get("top")`, `.get("filter")`, `.get("matches")`,
  `.get("candidates_simulated")` — confirmed all four are in the TypedDict.
- `_summarize_recommend` reads `rec.get("parts")`, `.get("tires")`,
  `.get("bike_name")`, `.get("budget_inr")`, `.get("total_inr")` — confirmed.
- `scripts/validate_chat_corpus.py` reads `r.recommend_result.get("build_tier")`,
  `.get("parts")`, `r.rank_result.get("top")` — confirmed.
- `ExplainResult` has no consumer reader (the LLM-generated text lives in
  `ChatResult.summary`; `explain_result` only carries metadata). Documented this
  in the docstring so the next maintainer doesn't expect a summarizer to exist.

## Files touched

- `/tmp/mq-session-1780158642-983/repo/motoquant/llm/runner.py` (+125 / -5)

## Validation

| Check                              | Result          |
|------------------------------------|-----------------|
| `test_chat_advanced.py`            | 23/23 passed    |
| `test_llm_runner.py` (non-fastapi) | 7/7 passed      |
| `test_scraper.py + test_validation.py + test_two_stroke.py + test_compatibility.py + test_submodel_kaizen.py + test_power_boost_regression.py` | 221/221 passed |
| K5 baseline                        | 10.0334s (Δ +0.0000s) PASS |
| R1 baseline                        | 10.2859s (Δ +0.0000s) PASS |
| Hayabusa baseline                  | 10.4712s (Δ +0.0000s) PASS |

## Out of scope (deferred)

- Subagent-5 finding #6: `BuildPage.tsx` `as unknown as {peak_power_hp?}` cast.
  TypeScript-only change in `desktop/`; separate concern.
- Subagent-5 finding #7: `SimulatePage.tsx` `splits as unknown as Record` cast.
  Same — defer to a desktop-focused refactor.
- Subagent-5 finding #4: TS index signatures `[extra: string]: unknown`.
  Architectural decision that needs product input on whether the API legitimately
  returns extras (see Phase 6 schema-evolution policy); not mechanical.
- Subagent-5 medium-confidence #1: `_build_*_from_spec()` internal dict usage in
  `importer.py`. Touches the catalog/physics import path → out of scope for
  technical-debt-pass agent per playbook ("No physics or catalog edits ever").

## One-line summary

Three remaining untyped payload fields on `ChatResult` (`rank_result`,
`recommend_result`, `explain_result`) are now backed by `TypedDict` classes,
matching the existing `SimDict`/`CompareDict` pattern, with zero physics impact
and the full chat-pipeline test suite green.
