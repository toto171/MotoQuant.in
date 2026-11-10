# Subagent 3: DEAD CODE REMOVAL

You are SUBAGENT 3: DEAD CODE REMOVAL for the MotoQuant codebase. Read CLAUDE.md first — note the Kaizen Principle ("dead fields - do any DB columns, dataclass fields, or config keys exist that nothing reads?") which is exactly what you're hunting for.

## Your job — find

- Unused exports from Python modules (`from motoquant.x import y` where y is never imported)
- Unreferenced functions, classes, methods (defined but never called)
- Orphaned files (modules nobody imports)
- Dead dataclass fields (defined but never read)
- Dead DB columns (in `schema.py` but no SELECT/INSERT writes them)
- Dead config keys (CLAUDE.md noted `power_boost_pct` was a dead knob — find similar)
- Dead CLI subcommands or args that were superseded

## Critical: VERIFY MANUALLY before flagging

Static analysis misses:

- Dynamic imports (`importlib`, `__import__`)
- String references (`getattr(obj, name)`, dict keys built at runtime)
- Framework conventions (FastAPI route handlers, pytest fixtures auto-discovered)
- Code generation (e.g., scripts that templatize output)
- Reference baselines / locked-in physics constants (K5/R1/Hayabusa hand-tuned values look unused but are load-bearing — DO NOT touch `defaults.py` reference bikes)

## Where to focus first

1. `scripts/` — many one-shot patches that may have been applied and are now dead
2. `motoquant/calibration/` — calibrator-v2 work may have left v1 leftovers
3. `motoquant/llm/` — provider-agnostic refactor might have left old client code
4. `web/components/` — UI components may have been replaced
5. Old `seed_catalogs/` files

## What NOT to flag

- Anything in `tests/` (test discovery is dynamic)
- FastAPI route handlers in `motoquant/api.py` (registered via decorators)
- Pydantic model classes (used as type hints + serialization)
- Anything documented as "open carry-forward" in CLAUDE.md

## Deliverable

Write to `reports/cleanup_subagent_3_dead.md`:

```markdown
# Subagent 3 — Dead code removal report
**Scanned:** YYYY-MM-DD
**Files scanned:** N

## High-confidence dead (safe to delete)
- file:line — {function_name | class | dataclass field | DB column}: never referenced anywhere

## Medium-confidence (verify before deleting)
- file:line — same format, plus a note about why I'm not 100% sure

## Looks dead but ISN'T (false positives I caught)
- file:line — looks unused but is referenced via {dynamic_mechanism}

## Numerical summary
- {functions_audited: N, dead: N, dead_LOC: N, files_orphaned: N}
```

Cap 700 words. Use `grep -r` extensively. Return a 2-3 sentence summary.
