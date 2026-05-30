# Tech-Debt Pass — `datetime.utcnow()` Deprecation Removal
**Date:** 2026-05-30 (Saturday)
**Agent:** A9 (technical-debt-pass)
**Scope:** `motoquant/scraper/spec.py` + `motoquant/scraper/bulk_scrape.py` (two files, same package)
**Source finding:** Observed during baseline pytest run — 596 `DeprecationWarning: datetime.datetime.utcnow() is deprecated` warnings on the focused-test subset, all originating from `motoquant/scraper/spec.py:101` (BikeSpec auto-stamping) called 596 times across the 78-bike `ALL_KNOWN_BIKES` import path. Python 3.12+ deprecates this function; Python 3.13 keeps it as warning, future versions may remove it.

## Refactor goal (one sentence)

Replace all 5 call sites of the deprecated `datetime.utcnow().isoformat()` with a timezone-aware UTC equivalent that produces byte-identical naive ISO output, eliminating 596 deprecation warnings per focused-test run and pre-emptively closing a future Python compatibility risk.

## Success criteria

- [x] All `datetime.utcnow()` calls in `motoquant/` source removed
- [x] Output string format preserved byte-for-byte (`2026-05-30T18:34:42.702753`, no `+00:00` suffix) so any downstream parsers or audit log readers are unaffected
- [x] LOC delta ≤ 300 (actual: +14 / -5 = +9 net)
- [x] Single concern (deprecation removal), two adjacent files in same package
- [x] Focused test subset green: 221/221 passed
- [x] 596 deprecation warnings on baseline run → 0 warnings after refactor
- [x] K5/R1/Hayabusa baselines preserved EXACTLY (Δ +0.0000s on all three)

## Before / after

### Before (5 sites)

```python
# motoquant/scraper/spec.py
from datetime import datetime
...
def __post_init__(self):
    if self.scraped_at is None:
        self.scraped_at = datetime.utcnow().isoformat()   # ❌ DeprecationWarning


# motoquant/scraper/bulk_scrape.py
from datetime import datetime
...
started_at=datetime.utcnow().isoformat(),     # ❌ DeprecationWarning x2
prog.finished_at = datetime.utcnow().isoformat()  # ❌ DeprecationWarning
result.finished_at = datetime.utcnow().isoformat()  # ❌ DeprecationWarning
```

### After

```python
# motoquant/scraper/spec.py
from datetime import datetime, timezone
...
def __post_init__(self):
    if self.scraped_at is None:
        self.scraped_at = (
            datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        )


# motoquant/scraper/bulk_scrape.py
from datetime import datetime, timezone

def _utcnow_iso() -> str:
    """Naive UTC ISO timestamp (Python 3.12+ safe replacement)."""
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

...
started_at=_utcnow_iso(),
prog.finished_at = _utcnow_iso()
result.finished_at = _utcnow_iso()
```

## Why preserve naive ISO output?

The existing strings (`2026-05-30T18:34:42.702753`) are timezone-naive. Switching to the canonical Python 3.12+ form `datetime.now(timezone.utc).isoformat()` would produce `2026-05-30T18:34:42.702753+00:00` — semantically equivalent and parser-compatible, **but** the `+00:00` suffix could surprise any external consumer (e.g. a log-shipper, audit pipeline, or future SQL `DATETIME` column) that assumed the prior naive format.

`.replace(tzinfo=None)` strips the timezone marker after we've used it to compute the correct UTC value, giving byte-for-byte identical output to `datetime.utcnow().isoformat()`.

Verified at the REPL:

```
old:        2026-05-30T18:34:42.702753
new_aware:  2026-05-30T18:34:42.702769+00:00   ← what we did NOT pick
new_naive:  2026-05-30T18:34:42.702773         ← what we chose (identical shape to `old`)
```

## Style choice: helper vs inline

- `spec.py` has **one** call site — inlined the 1-line expression (3 logical lines with the explanatory comment).
- `bulk_scrape.py` has **four** call sites — extracted a 3-line `_utcnow_iso()` private helper so the four call sites stay 1-liners and the deprecation context is documented once.

Both files import `timezone` from `datetime`; no new third-party deps.

## Files touched

| File | Change | Net delta |
|---|---|---|
| `motoquant/scraper/spec.py` | Import `timezone`; replace 1 `utcnow()` call with the naive-ISO equivalent + 3-line explanatory comment | +6 / -1 = **+5** |
| `motoquant/scraper/bulk_scrape.py` | Import `timezone`; add `_utcnow_iso()` helper; replace 4 `utcnow()` call sites with helper calls | +8 / -4 = **+4** |
| **TOTAL** | | **+14 / -5 = +9** |

## Validation

| Check | Before | After |
|---|---|---|
| `pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py tests/test_compatibility.py tests/test_submodel_kaizen.py tests/test_power_boost_regression.py` | 221 passed, **596 warnings** in 15.60s | 221 passed, **0 warnings** in 15.54s |
| K5 baseline | 10.0334s | 10.0334s (Δ +0.0000s) PASS |
| R1 baseline | 10.2859s | 10.2859s (Δ +0.0000s) PASS |
| Hayabusa baseline | 10.4712s | 10.4712s (Δ +0.0000s) PASS |
| `grep -rn 'datetime\.utcnow' motoquant/` | 5 call sites | 0 call sites (only 2 docstring/comment mentions remain) |

## Kaizen checklist

- [x] **No silent failure** — `datetime.now(timezone.utc).replace(tzinfo=None).isoformat()` is a deterministic 1-line expression; if it ever raised (`TypeError`, etc.), the `__post_init__` / orchestrator caller would propagate the exception identically to the prior code path.
- [x] **No data/model mismatch** — `scraped_at`/`started_at`/`finished_at` are `str` fields; the output string format is preserved byte-for-byte.
- [x] **No bypass path** — all 5 call sites converted; `grep` confirms zero `datetime.utcnow` calls remain in production source.
- [x] **Test coverage** — `test_scraper.py::test_scraped_at_auto_set` already asserts `spec.scraped_at is not None`; runs green post-refactor.
- [x] **Numerical sanity** — physics untouched; baselines preserved exactly.
- [x] **No dead fields introduced** — `_utcnow_iso` is a 1-statement helper.
- [x] **Backwards compat** — output string format identical to pre-refactor; no external parser surprise.

## Files NOT touched

- All other `datetime` usage in the codebase (e.g. `weather_refresh.py`, `auth.py`) uses `datetime.fromisoformat()` (read-only parsing) or non-deprecated constructors — already 3.12-safe.
- `scripts/master_scheduler.sh` uses `datetime.date.today()` which is not deprecated.
- Test files do not call `datetime.utcnow()` directly.

## Out of scope (deferred)

- The `app.py` Streamlit UI was not audited (it's not in the focused-test path; can be checked in a separate session if it lights up new warnings).
- The deprecation warnings from `pkg_resources`, `pydantic` validators, etc. are upstream-library issues out of project scope.

## One-line summary

Five `datetime.utcnow().isoformat()` call sites across two scraper modules are now `datetime.now(timezone.utc).replace(tzinfo=None).isoformat()` (via a tiny `_utcnow_iso` helper in the multi-site file); 596 deprecation warnings per focused-test run dropped to 0; baselines preserved Δ +0.0000s on K5/R1/Hayabusa; output string format byte-for-byte identical to pre-refactor.
