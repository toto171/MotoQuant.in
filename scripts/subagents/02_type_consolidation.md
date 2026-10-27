# Subagent 2: TYPE CONSOLIDATION

You are SUBAGENT 2: TYPE CONSOLIDATION for the MotoQuant codebase. Read CLAUDE.md first.

## Context

Mixed-language project. Python physics core uses `dataclass`, `pydantic.BaseModel`, plus plain `dict`. The web frontend (`web/lib/api.js`, `web/components/`) consumes the FastAPI JSON shapes with ad-hoc types. The optional Rust core (`rust/motoquant-core/src/config.rs`) has a serde schema that must mirror `motoquant/native.py`'s resolved config.

## Your job — scan for

- Type definitions duplicated across files (e.g., `BikeConfig` Python dataclass vs `BikeDetail` TS interface vs `BikeSummary` JSON shape)
- Pydantic models that have been quietly diverged from the dataclass they shadow
- Web client code that reads fields the API response no longer has (drift)
- Pydantic models in `motoquant/api.py` that should reuse `motoquant/models.py` types

## Where to focus first

1. `motoquant/models.py` (dataclasses) vs `motoquant/api.py` (Pydantic for HTTP) — these often go out of sync
2. `motoquant/native.py` resolved-config keys vs `rust/motoquant-core/src/config.rs`
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
