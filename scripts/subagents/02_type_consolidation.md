# Subagent 2: TYPE CONSOLIDATION

You are SUBAGENT 2: TYPE CONSOLIDATION for the MotoQuant Pro codebase. Read CLAUDE.md first.

## Context

Mixed-language project. Python physics core uses `dataclass`, `pydantic.BaseModel`, plus plain `dict`. Desktop frontend (`desktop/src/types/api.ts`) mirrors Pydantic models for the FastAPI endpoints. Web frontend (`web/components/`) has its own ad-hoc types.

## Your job — scan for

- Type definitions duplicated across files (e.g., `BikeConfig` Python dataclass vs `BikeDetail` TS interface vs `BikeSummary` JSON shape)
- Pydantic models that have been quietly diverged from the dataclass they shadow
- TypeScript interfaces in desktop that don't match the actual API response shape (drift)
- Pydantic models in `motoquant/api.py` that should reuse `motoquant/models.py` types

## Where to focus first

1. `motoquant/models.py` (dataclasses) vs `motoquant/api.py` (Pydantic for HTTP) — these often go out of sync
2. `desktop/src/types/api.ts` vs Python Pydantic models
3. `web/components/*.js` typeof shapes vs the API client
4. `motoquant/scraper/spec.py` (BikeSpec) vs `motoquant/models.py` (BikeConfig) — they overlap

## What NOT to do

- Don't propose merging types that intentionally differ (e.g., wire format vs internal representation)
- Don't suggest converting dataclasses to Pydantic just for consistency — performance matters here
- Boundary types where divergence is intentional (HTTP request/response vs internal config) should stay separate

## Deliverable

Write to `reports/cleanup_subagent_2_types.md`:

```markdown
# Subagent 2 — Type consolidation report
**Scanned:** YYYY-MM-DD
**Files scanned:** N

## Drifted types (definitions out of sync)
- [type X]: defined in A.py with fields {a,b,c}, also in B.ts with {a,b,d}. Drift: missing 'c' in TS.

## Duplicates that should be merged
- ...

## Intentional divergences (leave alone)
- ...

## Numerical summary
- {types_audited: N, drift_pairs: N, merge_candidates: N}
```

Cap 600 words. Read-only. Return a 2-3 sentence summary.
