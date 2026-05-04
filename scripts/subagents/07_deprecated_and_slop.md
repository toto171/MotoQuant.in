# Subagent 7: DEPRECATED CODE AND AI SLOP

You are SUBAGENT 7: DEPRECATED CODE AND AI SLOP for the MotoQuant Pro codebase. Read CLAUDE.md first.

## Your job — find, in two parts

### Part 1: Legacy / deprecated / fallback code

- Code paths marked `# legacy:` or `# deprecated:` or `# old:` in comments
- Functions named `*_v1`, `*_old`, `*_legacy`
- Branches gated on `if False:` or `if 0:` or always-False conditions (forgotten dead branches)
- Compatibility shims for versions/configs that no longer exist
- `# TODO: remove after X` comments where X has happened

### Part 2: AI artifact / slop (this is the meat)

This codebase has been built with heavy LLM assistance. Find:

- Stub functions: `def foo(): pass  # TODO: implement` that have lived for weeks
- Placeholder values that should have been replaced (e.g., `# TODO: actual XXX`, `# placeholder`, magic numbers like 42 or 999 with no explanation)
- Comments that narrate edit history instead of explaining intent: `# Changed from X to Y because Z` (when Y is now obviously the answer)
- Comments that just paraphrase the line below: `# increment counter` above `count += 1`
- Verbose docstrings on trivial helpers (LLM tendency to over-document)
- Excessive try/except wrapping that an LLM added defensively without need
- Code that has been "improved" past readability (over-abstracted)

## Critical context

- CLAUDE.md is THE central project doc and has long historical entries — those are intentional, NOT slop. **DO NOT touch CLAUDE.md.**
- Reports in `reports/` are dated session artifacts — leave them.
- `# Standing tool note` and `# Standing git-auth note` style comments are intentional.
- Recent test files + scripts may look new — those are real work.
- **Do NOT flag inline `# Reference baseline` or `# K5/R1/Hayabusa` notes** — those are load-bearing physics anchors.

## Where to focus first

1. `motoquant/api.py` — old endpoints that may have been replaced
2. `motoquant/llm/runner.py` — multiple refactors, may have stale dispatch branches
3. `motoquant/scraper/*.py` — multi-session work, may have leftover scaffolding
4. `desktop/src/pages/BuildPage.tsx` — recent surrogate wiring, may have dead code paths
5. Top-level scripts — many may be one-shots that ran and shouldn't be re-run

## Deliverable

Write to `reports/cleanup_subagent_7_slop.md`:

```markdown
# Subagent 7 — Deprecated code & AI slop report
**Scanned:** YYYY-MM-DD
**Files scanned:** N

## Part 1 — Deprecated / legacy
- file:line — what & why obsolete & safe to remove?

## Part 2A — AI slop: stubs and placeholders
- file:line — exact pattern, recommended action

## Part 2B — AI slop: narrative comments
- file:line — comment quote, recommended replacement (or just delete)

## Part 2C — AI slop: over-docs
- file:line — function name + LOC of doc vs LOC of body, recommended trim

## Part 2D — Defensive over-wrapping
- file:line — try/except that catches nothing real

## Numerical summary
- {legacy_blocks: N, stubs: N, narrative_comments: N, over_docs: N, defensive_wraps: N}
```

Cap 700 words. Read-only. Return a 2-3 sentence summary.
