# Tech-debt pass — `_TestDB` subclass dedup

**Date:** 2026-05-16
**Agent:** A9 (technical-debt-pass)
**Source finding:** `reports/cleanup_subagent_1_dedup.md` finding #1

## Refactor goal

Move the WAL-disabling `MotoQuantDB` subclass out of `tests/test_cli.py` and
into the shared `tests/_helpers.py` module so the test-DB lifecycle layer has
one canonical place to live.

## Why this one

The subagent dedup report flagged `_TestDB` triplication across `test_cli.py`,
`test_analysis.py`, `test_recommendations.py`. Two of the three already share
`tests/_helpers.SeededTestDB` (process-scoped singleton). The third
(`test_cli.py`) uses a different lifecycle (per-module fixture with cleanup
+ path passed via `--db` CLI arg), so the singleton helper doesn't fit it,
but the underlying *WAL-disabling subclass* is mechanically identical and
the right unit to share.

The pre-existing `_helpers.py` docstring claimed `test_cli.py` was
"intentionally untouched" — that read flagged the subclass piece as
shareable on closer inspection, and the rest of the lifecycle stays in the
test module where it belongs.

## Changes

| File | Before | After | Δ LOC |
|---|---|---|---|
| `tests/_helpers.py` | 67 | 87 | +20 |
| `tests/test_cli.py` | 937 | 922 | -15 |
| **Total** | **1004** | **1009** | **+5** |

- Added `WalDisabledDB(MotoQuantDB)` to `_helpers.py` (mirrors
  `MotoQuantDB.connect()` byte-for-byte except `PRAGMA journal_mode=DELETE`).
- Removed the inline `_TestDB` class definition from `test_cli.py` (15 lines,
  including the `import sqlite3` it had inside the method body).
- `test_cli.py` now does `from tests._helpers import WalDisabledDB as _TestDB`
  so every existing call site (`_TestDB(TEST_DB)` in the fixture, etc.) keeps
  its name.
- Dropped the unused `from motoquant.database import MotoQuantDB` import
  from `test_cli.py` (the subclass was its only consumer).
- Updated `_helpers.py` docstring to reflect that the `test_cli.py` subclass
  pattern lives here now.

## Net effect

Net LOC went up +5 because the moved subclass picked up a real docstring
during the move, but **the duplicated class definition is gone**. Any future
edit to the WAL-fallback connect logic (e.g. raising the `foreign_keys`
pragma or swapping isolation modes) lands in one place instead of two.

## Test evidence

Pre-refactor baseline:
```
$ python3 -m pytest tests/test_cli.py --no-header
51 passed in 10.76s
```

Post-refactor:
```
$ python3 -m pytest tests/test_cli.py --no-header
51 passed in 10.61s

$ python3 -m pytest tests/test_cli.py tests/test_recommendations.py --no-header
89 passed, 27 skipped in 10.50s   # 27 skips are SLOW_TESTS-gated, pre-existing
```

Reference baselines (load-bearing per CLAUDE.md):
```
K5:   10.0334s   (target 10.0334)  Δ +0.0000
R1:   10.2859s   (target 10.2859)  Δ +0.0000
Busa: 10.4712s   (target 10.4712)  Δ +0.0000
```

The pre-existing `test_analysis.py` SALib-related errors
(`TestComputeSobolIndices::*` ERRORs) were verified to exist on `HEAD`
before the refactor via `git stash` round-trip — they are unrelated to this
change.

## Out of scope (intentionally not touched)

- The `SeededTestDB` singleton lifecycle pattern stays as-is. It serves a
  different need (process-wide cache for slow-to-seed catalog data) from
  the per-module fixture pattern in `test_cli.py`.
- Seed-catalog boilerplate (subagent dedup finding #2, ~150 LOC) deferred —
  touches `seed_catalogs/` which is the catalog agent's domain.
- The aero / engine-inertia architectural smells (findings #3, #4) deferred —
  they need a design discussion, not a mechanical refactor.

## Risk assessment

Low. The moved subclass is byte-equivalent (verified by reading both
side-by-side). Behavioural change is zero: the only caller is the
`test_cli.py` module-scope `db` fixture, which still constructs the
subclass the same way with the same path.
