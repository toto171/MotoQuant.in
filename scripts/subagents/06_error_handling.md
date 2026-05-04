# Subagent 6: ERROR HANDLING CLEANUP

You are SUBAGENT 6: ERROR HANDLING CLEANUP for the MotoQuant Pro codebase. Read CLAUDE.md first — note the Kaizen Principle's #1 rule: **"silent failure modes — does any code swallow errors without logging or raising?"** This is the most important pass for this codebase.

## Your job — find

- `try/except` blocks that catch and silently pass (`except: pass`, `except Exception: pass`)
- `try/except` that catch and return `None`/empty without logging
- Bare `except:` clauses (catches `BaseException` including `KeyboardInterrupt`)
- `except Exception` where a narrower type would be safer
- Defaults-as-fallback patterns that mask real problems (`x = obj.get("k", 0)` where 0 is a real value, masking missing key)
- TS `try/catch` that swallow errors (`catch (e) {}`)
- `dict.get(k, default)` patterns where the default conflicts with valid data
- Async error swallowing (Promise without `.catch`, FastAPI handlers without 500 paths)

## Critical context — KEEP these patterns (they're load-bearing)

- Optional-import patterns: `try: import torch; except ImportError: torch = None` (this is fine)
- Best-effort cleanup: `try: cleanup(); except Exception: pass` in a finally-block context
- Circuit-breaker style: rate limiter that swallows after N retries with logged failure
- Anywhere CLAUDE.md notes a documented limitation (e.g., FUSE permission tier blocks)

## The smoking-gun bug from CLAUDE.md (Apr 24 AM session)

`_synthetic_torque_curve` returned silently for tiered branches and the `power_boost_pct` knob was completely dead. That's the kind of bug you're hunting for in OTHER places — silent fallthrough that makes a knob look live but isn't.

## Where to focus first

1. `motoquant/physics.py` — RK4 loop, NaN guard added in Apr 15 hardening, but other paths?
2. `motoquant/submodels/*.py` — `bridge.py` warns on bad paths but does the warn fire?
3. `motoquant/database/bridge.py` — `apply_part_to_config` was a known offender
4. `motoquant/api.py` — exception handlers that return generic 500
5. `motoquant/calibration/*.py` — overlay/calibrator may swallow during fit
6. `motoquant/llm/runner.py` — recently rewritten, may have new silent paths
7. `desktop/src/hooks/useApi.ts` — Mutation `onError` might be missing

## Deliverable

Write to `reports/cleanup_subagent_6_errors.md`:

```markdown
# Subagent 6 — Error handling cleanup report
**Scanned:** YYYY-MM-DD
**Files scanned:** N

## Critical — silent failures (fix immediately)
- file:line — describes what's swallowed, why it's a real bug, fix proposal

## Should add logging (warning swallow, not fatal)
- ...

## Bare except clauses (narrow these)
- ...

## Defaults masking real problems
- ...

## Acceptable / leave alone (with reason)
- ...

## Numerical summary
- {try_blocks: N, silent_swallows: N, bare_excepts: N, default_masks: N, critical: N}
```

Cap 700 words. Read-only. Return a 2-3 sentence summary.
