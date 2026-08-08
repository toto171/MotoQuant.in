# Tech-Debt Pass — `_resolve_venue_env` helper extracts triplicated venue-lookup boilerplate
**Date:** 2026-05-30 (Saturday — second tech-debt pass this dispatch)
**Agent:** A9 (technical-debt-pass)
**Scope:** `motoquant/llm/runner.py` (single file)
**Source finding:** Pattern discovery during cleanup-subagent triage — all three high-confidence findings in `reports/cleanup_subagent_1_dedup.md` + all top findings in `reports/cleanup_subagent_5_types.md` were already resolved by prior tech-debt sessions (test fixture dedup landed 2026-05-16; seed catalog helper landed 2026-05-20; TypedDicts for ChatResult/HeadlineSpecs/BikeRowSummary all done; `as unknown as` casts removed; `run_chat_pipeline(db: Any)` already typed `MotoQuantDB`). A grep-style pass for residual duplication surfaced **three identical 7-9 line `env = None / if parsed.venue_id ... / try: db.venues.to_environment(...) / except: env = None` blocks** at runner.py:556, 979, and 1526 — one per dispatch path that needs a seasonal venue environment for a sim call.

## Refactor goal (one sentence)

Extract three identical 7-9 line "build EnvironmentParams from `parsed.venue_id`" blocks across three dispatch handlers in `motoquant/llm/runner.py` into a single private `_resolve_venue_env(db, parsed)` helper, so future seasonal-lookup behaviour changes (e.g. switching to UTC-month, threading rider weather overrides, plumbing live-weather records) only need to land in one place.

## Success criteria

- [x] All three duplicated blocks reduced to a single 1-line helper call
- [x] LOC delta ≤ 50 (actual: +24 / -22 = **+2 net**, but ~10 lines of logic deduplicated to one site)
- [x] Single file, single concern (venue-env lookup boilerplate)
- [x] Focused test subset green: 222/222 passed
- [x] Pre-existing LLM-test failures (7 failed / 6 errors due to missing `fastapi` optional dep + 3 chat-resolver bike-name carryforwards) **unchanged in count after refactor** — i.e. no regression introduced
- [x] K5/R1/Hayabusa baselines preserved EXACTLY (Δ +0.0000s on all three)
- [x] Behaviour byte-identical: same `try/except Exception` swallow-and-return-None pattern preserved across all three call sites

## Before / after

### Before (3 sites, ~7-9 lines each)

```python
# motoquant/llm/runner.py:556  (_run_rank, candidate-sim block)
env = None
if parsed.venue_id is not None:
    try:
        env = db.venues.to_environment(parsed.venue_id, month=datetime.now().month)
    except Exception:
        env = None

# motoquant/llm/runner.py:979  (_run_one_sim)
env = None
if parsed.venue_id is not None:
    try:
        env = db.venues.to_environment(parsed.venue_id, month=datetime.now().month)
    except Exception:
        env = None

# motoquant/llm/runner.py:1526 (_run_choose_bike, candidate-sim block)
env = None
if parsed.venue_id is not None:
    try:
        env = db.venues.to_environment(parsed.venue_id, month=datetime.now().month)
    except Exception:
        env = None
```

### After (1 helper + 3 one-line call sites)

```python
def _resolve_venue_env(db: MotoQuantDB, parsed: ParsedSimRequest) -> Any:
    """Build an EnvironmentParams for `parsed.venue_id` if set, else None.

    Used by three dispatch paths (_run_one_sim, _run_choose_bike,
    rank_pool sim block) that all need the same seasonal environment
    lookup keyed on the current calendar month. Returns None on any
    failure so callers degrade gracefully to bike-spec defaults.
    """
    if parsed.venue_id is None:
        return None
    try:
        return db.venues.to_environment(parsed.venue_id, month=datetime.now().month)
    except Exception:
        return None


# Call sites now uniform:
env = _resolve_venue_env(db, parsed)
```

## Files touched

| File | Change | Net delta |
|---|---|---|
| `motoquant/llm/runner.py` | Added 21-line `_resolve_venue_env` helper (mostly docstring); replaced 3 triplicated 7-9 line blocks with 1-line calls | +24 / -22 = **+2** |

## Validation

| Check | Result |
|---|---|
| `python3 -m pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py tests/test_category_dispatch.py -q` | **222 passed in 13.31s** |
| K5 baseline | 10.0334s (Δ +0.0000s) PASS |
| R1 baseline | 10.2859s (Δ +0.0000s) PASS |
| Hayabusa baseline | 10.4712s (Δ +0.0000s) PASS |
| `grep -cn 'venues\.to_environment' motoquant/llm/runner.py` | 3 sites → **1 site** (the helper) |
| `grep -cn 'datetime\.now()\.month' motoquant/llm/runner.py` | 3 sites → **1 site** (inside the helper) |
| LLM-runner regression check (stash + re-run pre-edit) | 7 failed / 6 errors / 74 passed **before AND after** — zero new failures |

## Why this matters

The three blocks were drift-prone. If a future change wanted to:

- Switch from naive `datetime.now()` to UTC-aware `datetime.now(timezone.utc)` (M6 deprecation cleanup style)
- Plumb a user-supplied weather override (e.g. "simulate at 38°C with 65% humidity")
- Add structured logging on `to_environment` failures (currently silently swallowed)

...the change would need to land in three independent sites with no enforcement that they stayed in sync. Centralising in `_resolve_venue_env` makes the next change a 1-line edit and prevents the "fixed in 2 of 3 sites" class of bug.

## Kaizen checklist

- [x] **No silent failure** — preserved the existing `try/except Exception: return None` swallow-and-degrade pattern verbatim (callers already handle env=None correctly downstream).
- [x] **No data/model mismatch** — helper returns the same `EnvironmentParams | None` shape that `db.venues.to_environment()` returns directly.
- [x] **No bypass path** — all three call sites converted; grep confirms zero remaining inlined patterns.
- [x] **Test coverage** — the helper has no dedicated unit test, but it's exercised end-to-end by all `_run_one_sim` / `_run_rank` / `_run_choose_bike` call sites in the LLM dispatch tests (74 passing tests in `test_llm.py` + `test_chat_advanced.py`).
- [x] **Numerical sanity** — physics untouched; baselines preserved exactly.
- [x] **No dead fields introduced** — helper is single-purpose and called by 3 sites.
- [x] **Backwards compat** — behaviour byte-identical; same return shape, same swallow-and-return-None pattern.

## Out of scope (deferred)

- The `Any` return annotation is intentional rather than `EnvironmentParams | None`. Importing `EnvironmentParams` would require either a runtime import (cost) or extending the `TYPE_CHECKING` block (cosmetic). Left as `Any` because the wider runner.py already uses `Any` liberally for parsed/config/db payloads.
- Other 4-occurrence `datetime.now().month` calls (3 inside this helper now, 1 in `motoquant/run.py::cmd_venues`) are NOT duplications — they live in entirely different intent contexts and don't share the surrounding env-lookup logic. No further extraction warranted.

## One-line summary

Three identical 7-9 line `env = None / if parsed.venue_id / try: db.venues.to_environment / except` blocks across `_run_rank`, `_run_one_sim`, and `_run_choose_bike` in `motoquant/llm/runner.py` are now single 1-line `env = _resolve_venue_env(db, parsed)` calls behind a new 21-line private helper (mostly docstring); 222/222 focused tests green, baselines preserved Δ +0.0000s on K5/R1/Hayabusa, zero new LLM-test failures over pre-edit count.
