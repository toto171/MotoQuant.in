# Tech-debt pass — Tighten `db: Any` to `db: MotoQuantDB` in `motoquant/llm/`

**Date:** 2026-05-20
**Agent:** A9 (technical-debt-pass)
**Source finding:** `reports/cleanup_subagent_5_types.md` finding #3
("`motoquant/llm/runner.py:91–98` — `run_chat_pipeline` — Current: `db: Any` parameter, only calls `db.get_bike_by_id()` / `db.query_bikes()` / `db.get_venue_by_id()` — all `MotoQuantDB` methods. Tracking `Any` loses those interface guarantees.")

## Refactor goal

Replace the 13 weak `db: Any` function-parameter annotations across the
LLM module with `db: MotoQuantDB`, imported under `TYPE_CHECKING` so the
runtime cost is zero and test mocks (MagicMock-based) still work.

## Why this one

Subagent 2 (Type Consolidation) and Subagent 5 (Type Strengthening) both
flagged the LLM module as the largest cluster of weak `db: Any`
annotations in the codebase. Two prior tech-debt passes already shipped
type-strengthening for `_bike_row_to_summary` (TypedDict) and
`extract_headline_specs` (TypedDict). This pass closes the same finding
class for the chat pipeline.

Verified via `grep -hn "db\.\w\+" motoquant/llm/*.py | sort -u` that the
LLM module only touches `db._conn`, `db.bikes`, `db.parts`, `db.tires`,
`db.venues` — all attributes that live on `MotoQuantDB`. No
non-`MotoQuantDB` callers were found (only `motoquant.run.cmd_chat`,
`motoquant.api`, and `scripts/validate_chat_corpus.py`, all of which pass
a real `MotoQuantDB` instance).

The `TYPE_CHECKING`-guarded import pattern was already used by
`motoquant/database/seed_catalogs/__init__.py` (added during the May-20
seed-catalog-batch-helper refactor), so we re-use the same idiom for
project consistency.

## Changes

| File | Before | After | Δ LOC |
|---|---|---|---|
| `motoquant/llm/runner.py` | 1472 | 1475 | +3 |
| `motoquant/llm/parse_query.py` | 562 | 565 | +3 |
| `motoquant/llm/resolver.py` | 372 | 375 | +3 |
| **Total** | **2406** | **2415** | **+9** |

The net LOC went **up by 9** (not down) because each file picked up a
3-line `if TYPE_CHECKING: from ..database.connection import MotoQuantDB`
block. The 13 actual annotation swaps (`db: Any` → `db: MotoQuantDB`)
are byte-neutral on each line.

Sites touched:

| File | Function | Line (post-edit) |
|---|---|---|
| `runner.py` | `run_chat_pipeline` | 96 |
| `runner.py` | `_run_simulate` | 164 |
| `runner.py` | `_run_smalltalk` | 205 |
| `runner.py` | `_run_recommend` (helper) | 287 |
| `runner.py` | `_run_compare` | 518 |
| `runner.py` | `_run_explain` | 713 |
| `runner.py` | `_load_config_for_bike` | 779 |
| `runner.py` | `_bike_suggestions` | 875 |
| `runner.py` | `_apply_archetype` | 1104 |
| `parse_query.py` | `parse_query` | 343 |
| `parse_query.py` | `_resolve_against_db` | 403 |
| `resolver.py` | `resolve_bike` | 146 |
| `resolver.py` | `resolve_venue` | 232 |
| `resolver.py` | `resolve_archetype` | 305 |

Out of scope (intentionally left):
- `config: Any` annotations (BikeConfig from various paths — opaque by design here).
- `dict[str, Any]` payload annotations (response bodies — Any is correct).
- `motoquant/llm/summarize.py` — already uses concrete types; nothing to tighten.

## Why `TYPE_CHECKING` (not direct import)

Direct `from ..database.connection import MotoQuantDB` would create a
circular import risk: `motoquant.database.connection` could plausibly
import from `motoquant.llm` in the future (e.g., for query logging). The
`TYPE_CHECKING` guard means the import only happens during static
type-check passes (mypy, IDEs) — at runtime the annotation is the string
`"MotoQuantDB"` thanks to `from __future__ import annotations`.

This is also what allows MagicMock-based tests to keep working: the test
passes `MagicMock()` for `db`, Python doesn't validate it at runtime,
and a structural type-checker would either be configured to allow it
(via `# type: ignore`) or be skipped on test files entirely.

## Net effect

- **Static type-checkers** (mypy, pyright, IDE intellisense) now know
  the real DB shape across 14 LLM call sites. Misspelled method names
  (`db.serach` instead of `db.search`) would now be caught at lint time.
- **Runtime behaviour:** zero change. `TYPE_CHECKING` is False at
  runtime, so the import never fires.
- **Test compatibility:** zero change. `MagicMock()` still satisfies
  every `db.*` call site duck-typed-ly.

## Test evidence

Pre-refactor baseline:
```
$ pytest tests/test_scraper.py tests/test_validation.py tests/test_compatibility.py tests/test_submodel_kaizen.py tests/test_llm.py tests/test_llm_runner.py --no-header
181 passed, 528 warnings, 6 errors in 10.33s
```
(The 6 errors are pre-existing `ModuleNotFoundError: No module named 'fastapi'`
in `TestChatEndpoint` — unrelated; fastapi is not installed in this sandbox.)

Post-refactor:
```
$ pytest tests/test_scraper.py tests/test_validation.py tests/test_compatibility.py tests/test_submodel_kaizen.py tests/test_llm.py tests/test_llm_runner.py --no-header
181 passed, 528 warnings, 6 errors in 10.76s
```

Additional power-boost + chat-resolver suites:
```
$ pytest tests/test_power_boost_regression.py tests/test_chat_resolver.py tests/test_chat_advanced.py --no-header
62 passed in 3.07s
```

Reference baselines (load-bearing per CLAUDE.md):
```
K5:   10.0334s   (target 10.0334)  Δ +0.0000
R1:   10.2859s   (target 10.2859)  Δ +0.0000
Busa: 10.4712s   (target 10.4712)  Δ +0.0000
```

## Risk assessment

**Very low.** This is a pure type-annotation change behind
`TYPE_CHECKING` — runtime semantics are byte-identical. Verified by:

1. `python3 -c "import motoquant.llm.runner"` passes (no runtime
   ImportError from the TYPE_CHECKING block).
2. Baselines unchanged at the 4th decimal.
3. The two test suites that actually exercise the LLM module
   (`test_llm.py`, `test_llm_runner.py`) pass exactly as before; the 6
   pre-existing `fastapi`-missing errors are unrelated and reproduce on
   a clean `HEAD`.
4. MagicMock-based error-path tests (`test_llm_not_configured_returns_typed_error`,
   `test_parse_failed_returns_typed_error`) pass — confirming the
   structural-typing escape hatch is intact.

## Out of scope (deferred)

- **TS index signatures `[extra: string]: unknown`** (finding #4 in
  subagent 5) — belongs to a TS-side pass; not Python tech-debt.
- **BuildPage type assertions `as unknown as {...}`** (finding #6) —
  desktop frontend, separate agent's domain.
- **Subagent 2 finding #5 (`QuickSimResponse` field verification)** —
  pending grep audit of `motoquant/api.py` `/api/simulate/quick`
  response builder; logged for the next types pass.
