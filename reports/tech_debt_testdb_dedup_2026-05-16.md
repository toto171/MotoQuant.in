# Tech-debt pass — `_TestDB` deduplication

**Agent:** A9 (technical-debt-pass)
**Date:** 2026-05-16
**Source finding:** `reports/cleanup_subagent_1_dedup.md` §1 (high-confidence)

## Summary

Consolidated two near-identical `_TestDB` class-method-cached singleton
classes from `tests/test_analysis.py` and `tests/test_recommendations.py`
into one shared `SeededTestDB` in a new `tests/_helpers.py` module.

`tests/test_cli.py` was intentionally **not** touched: it defines a
`MotoQuantDB` *subclass* that overrides `.connect()` so a pytest fixture
can drive it — a different pattern that solves a different problem. The
cleanup report's claim of "three identical copies" was inaccurate;
verifying that claim was part of the work and saved a follow-up cleanup.

## Before / after

| Metric | Before | After |
|---|---|---|
| Duplicate seeded-DB singleton classes in `tests/` | 2 identical copies (tests/test_analysis.py + tests/test_recommendations.py) | 1 shared definition (tests/_helpers.py::SeededTestDB) |
| Per-file dependency on `tempfile`, the singleton boilerplate, and the seed import | Inline in 2 files | Centralised |
| `tests/test_analysis.py` | 739 lines | 705 lines (-34) |
| `tests/test_recommendations.py` | 887 lines | 857 lines (-30) |
| `tests/_helpers.py` | did not exist | 67 lines (mostly docstring explaining what it is and why test_cli is excluded) |
| Net source delta | — | +3 LOC (–57 from test files, +60 source in helper) |

## Mechanical change

1. Added `tests/_helpers.py` exporting `SeededTestDB` — the unified
   classmethod-cached singleton with `get_mdb()`, `get_conn()`, and
   `_db_path` mirroring the prior public surface.
2. Replaced the inline class body in both test files with
   ```python
   from tests._helpers import SeededTestDB as _TestDB  # noqa: E402
   ```
   so the existing call sites
   (`_TestDB.get_mdb()`, `_TestDB.get_conn()`, `_TestDB._db_path`)
   continue to work unchanged. No call-site edits needed.
3. Removed the now-unused `import tempfile` from the two test files.

## Why this was safe

* The two original `_TestDB` definitions were byte-for-byte identical
  in their `get_mdb()` body. Verified via diff.
* All existing call sites use only the classmethod surface and the
  `_db_path` class variable — both preserved.
* The singleton is process-scoped, not collection-scoped, so sharing a
  single definition across modules **does not** change isolation
  semantics: each test module that imports it still gets its own
  per-import-process singleton, identical to the prior behaviour.
* Validation gates green: scraper + validation + two_stroke +
  compatibility → 171 passed. test_analysis.py non-Sobol → 46 passed
  (Sobol skipped due to pre-existing SALib-missing in sandbox; verified
  identical behaviour pre/post refactor via `git stash`). test_cli.py →
  51 passed.
* Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s /
  Hayabusa 10.4712s (Δ +0.0000s on all three).

## Tests covering this

The refactor is exercised by the existing `tests/test_analysis.py` and
`tests/test_recommendations.py` modules — both rely on the singleton
returning a seeded `MotoQuantDB`, so if the shared `SeededTestDB`
regressed in any visible way, those test suites would fail. No new test
file is needed; the contract is "these tests pass" and that contract is
upheld.

## What was deliberately not done

* `tests/test_cli.py::_TestDB` was left alone — it is structurally
  different (subclass of `MotoQuantDB` with overridden `.connect()`)
  and serves a pytest fixture, not a classmethod singleton. Merging it
  in would have widened scope and broken the "one concern per session"
  rule.
* The `seed_catalogs/` boilerplate consolidation (finding #2 in the
  dedup report) is a separate refactor with a different blast radius
  and is deferred to a later tech-debt pass.

## Followup ideas (for another agent / day)

* Consider promoting `tests/_helpers.py` to `tests/conftest.py` as a
  pytest fixture if a third test module ever needs the same pattern.
  Right now two consumers don't justify the indirection.
* The `tempfile.NamedTemporaryFile(... delete=False)` pattern leaks
  the temp DB on /tmp for the life of the process. Adding an
  `atexit.register` cleanup would tidy up — but `/tmp` is wiped by the
  OS anyway, so this is purely cosmetic.
