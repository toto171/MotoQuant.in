# Subagent 4: CIRCULAR DEPENDENCIES

You are SUBAGENT 4: CIRCULAR DEPENDENCIES for the MotoQuant codebase. Read CLAUDE.md first.

## Your job — find

- Circular imports between Python modules in `motoquant/` (A imports B, B imports A directly or transitively)
- Imports that are deferred to function bodies to dodge cycles (these are fingerprints of unresolved cycles)
- Layer violations: high-level modules importing implementation details of low-level ones (e.g., `motoquant.api` importing private helpers from `motoquant.scraper.bikez`)
- Test fixtures that import production code which then imports test fixtures (rare but happens)
- Web: same for `web/app/` and `web/components/`

## Tools available

- `python3 -c "import ast" + Glob + Read` — write a small AST-based import-graph builder
- `grep -rn "^from motoquant" motoquant/ tests/ scripts/`
- For web/JS: grep imports from `@/` and relative paths

## Where to focus first

1. `motoquant/scraper/importer.py` ↔ `motoquant/database/seed.py` ↔ `motoquant/scraper/known_bikes.py`
2. `motoquant/llm/` modules: client.py, runner.py, parse_query.py, resolver.py, summarize.py
3. `motoquant/parts/compatibility.py` ↔ `motoquant/database/parts_repo.py`
4. `motoquant/calibration/` — calibrator + dragy + dyno + ecu + overlay + connection?

## What NOT to do

- Don't propose breaking cycles by introducing a new abstraction layer just to do so. CLAUDE.md explicitly warns: "Do not introduce new abstractions just to break a cycle."
- Don't flag deferred imports inside `if TYPE_CHECKING:` — that's the standard pattern.
- Don't flag deferred imports that exist for genuine lazy-loading reasons (heavy deps).

## Deliverable

Write to `reports/cleanup_subagent_4_cycles.md`:

```markdown
# Subagent 4 — Circular dependencies report
**Scanned:** YYYY-MM-DD
**Module count:** N

## True cycles (import-time loops)
- A.py → B.py → C.py → A.py (length 3)
  - Description of what each module legitimately needs from the others
  - Untangling proposal: extract shared X into D.py (neutral module)

## Deferred-import cycles (dodged via function-body import)
- Same format. These are softer because they don't fail at import time, but they signal architectural drift.

## Layer violations (no cycle, but bad direction)
- {high-level} imports {low-level private helper}; should call public API instead.

## Acceptable / leave alone
- ...

## Numerical summary
- {modules: N, true_cycles: N, deferred_cycles: N, layer_violations: N}
```

Cap 600 words. Read-only. Return a 2-3 sentence summary.
