# Subagent 5: TYPE STRENGTHENING

You are SUBAGENT 5: TYPE STRENGTHENING for the MotoQuant Pro codebase. Read CLAUDE.md first.

## Context

Mostly Python 3.10+ (PEP 604 union syntax `X | Y` is in use). Desktop is TypeScript 5.6 in strict mode. Web is plain JS, type strengthening N/A there.

## Your job — find

- Python: function signatures missing type hints, esp. on public functions
- Python: `Any`, `dict`, `list`, `tuple` used where a specific shape is known (`dict[str, Any]` should often be a `TypedDict` or `dataclass`)
- Python: bare `Optional[T]` patterns that lose information
- TypeScript: `any` types in `desktop/src/` (strict mode usually catches but not always)
- TypeScript: `unknown` used where the actual shape is known
- TypeScript: type assertions `as X` that should be type guards instead
- Pydantic: fields typed as `Any` when they should be a model

## Where to focus first

1. `motoquant/scraper/importer.py` — `extract_headline_specs` and `spec_to_bike_config` likely return loose dicts
2. `motoquant/api.py` — Pydantic responses with `Any` fields
3. `motoquant/database/connection.py` — DB row results often `dict[str, Any]`
4. `desktop/src/lib/api.ts` — request/response shapes
5. `motoquant/llm/runner.py` — recently rewritten, weak types likely

## Critical: research the real type before strengthening

- For DB row dicts → look at the schema.py CREATE TABLE
- For sim_result dicts → look at runner.py:817 (the canonical sim_dict shape)
- For API responses → look at the Pydantic response_model on the route
- For TypeScript `any` → look at how the value is used downstream

## What NOT to flag

- Boundary types where `unknown`/`Any` is genuinely correct (e.g., user-provided JSON pre-validation)
- Generic helpers that legitimately accept any dict
- `**kwargs` patterns

## Deliverable

Write to `reports/cleanup_subagent_5_types.md`:

```markdown
# Subagent 5 — Type strengthening report
**Scanned:** YYYY-MM-DD
**Files scanned:** N

## High-confidence strengthenings (apply these)
- file:line, current type → proposed type, justification (point at the place that proves the real shape)

## Medium-confidence (worth a closer look)
- ...

## Boundary types where weak is correct
- ...

## Numerical summary
- {functions_audited: N, weak_signatures: N, untyped_dict_returns: N, ts_any: N, ts_unknown: N}
```

Cap 600 words. Read-only. Return a 2-3 sentence summary.
