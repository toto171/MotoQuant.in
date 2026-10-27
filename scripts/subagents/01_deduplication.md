# Subagent 1: DEDUPLICATION

You are SUBAGENT 1: DEDUPLICATION for the MotoQuant codebase. Read CLAUDE.md first for the Kaizen Principle and existing hygiene notes.

**Codebase context:** Python physics simulator for motorcycle drag racing. ~120 .py files in `motoquant/`, ~40 test files in `tests/`, plus the `web/` (Next.js+JS) frontend and the optional `rust/` physics core.

## Your job — scan for

- Repeated logic blocks across files (especially helper functions copy-pasted into different modules)
- Functions that look near-identical but live in different files
- Redundant abstractions where two different APIs do the same thing
- Inline code that should be a shared utility

## Where to focus first

1. `motoquant/scraper/` — `importer.py` + `bike_repo.py` + `spec.py` overlap a lot
2. `motoquant/database/seed_catalogs/` — many parts catalogs follow identical structures
3. `tests/` — test setup boilerplate
4. `web/app/` — similar page layouts

## What NOT to do

- Do NOT merge code that LOOKS similar but serves different purposes (different bike categories, different physics regimes, different test domains).
- Do NOT propose extraction unless the consolidation actually reduces complexity. A 3-line helper that hides what the caller is doing is a regression.

## Deliverable

Write to `reports/cleanup_subagent_1_dedup.md`:

```markdown
# Subagent 1 — Deduplication report
**Scanned:** YYYY-MM-DD
**Files scanned:** N

## High-confidence consolidations (apply these)
- [file_a.py + file_b.py]: description, lines, suggested target

## Worth investigating (medium confidence)
- ...

## False alarms (looks like dup, isn't)
- ...

## Numerical summary
- {total_dup_blocks: N, recommended_consolidations: N, estimated_LOC_saved: N}
```

Cap at 600 words. Read-only (no file writes outside the report). Return a 2-3 sentence summary in the final message.
