# Subagent 6 — Error handling cleanup report
**Scanned:** 2026-06-07
**Files scanned:** 167 Python, 197 JS/TS (grep across motoquant/, desktop/src/, web/)

---

## Critical — silent failures (fix immediately)

- **`motoquant/analysis/build_optimizer.py:90`** — `_check_envelope()` catches `Exception` and returns `(True, [])` (i.e. "in envelope, no violations"). If `surrogate_data.FEATURE_BOUNDS` import fails for any reason, *every config* is declared in-envelope and the surrogate is used unconditionally. In `SurrogatePredictor.__call__` (line 121) `ok=True` suppresses the `allow_fallback` guard, so out-of-distribution configs get surrogate scores silently instead of full-sim fallback. **Fix:** `except ImportError` only (the only expected failure); re-raise or return `(False, ["envelope_check_unavailable"])` on any other exception so the caller falls back to full sim safely.

- **`motoquant/analysis/roi.py:209`** — `_resolve_price()` catches `Exception` and returns `seed_price` (the catalog fallback) without logging. If the DB query fails for a structural reason (schema mismatch, corrupt row), *all parts silently price at their seed value* for every subsequent ROI computation in that session. No log entry is emitted. **Fix:** add `logging.getLogger(__name__).warning(...)` before returning `seed_price` so price-resolution failures are visible.

- **`motoquant/database/seed_recommended_fitments.py:361`** — `except Exception: stats["errors"] += 1` increments a counter but emits no log line (no `logger.warning`, no `print`). A batch of fitment insertions failing silently (e.g. FK violation after a DB wipe + re-seed) will show a non-zero errors count in the returned dict, but the caller in `seed_all()` does not inspect it. **Fix:** add `logger.warning("fitment insert failed: %s", exc)` inside the except block.

---

## Should add logging (warning swallow, not fatal)

- **`motoquant/llm/runner.py:293`** (`resolve_venue`) — `except Exception: return None`. A venue lookup failure silently degrades to default sea-level environment. The caller never learns whether venue resolution failed or the venue legitimately had no data. Add `logger.debug("resolve_venue(%s) failed: %s", parsed.venue_id, exc)`.

- **`motoquant/llm/runner.py:746`** (`_run_recommend`) — `except Exception: parts = []`. If `list_compatible_for_bike` throws (e.g. DB connection lost mid-request), the user receives an empty recommendation with no indication of failure. Add at least a `logger.warning`.

- **`motoquant/llm/runner.py:838`** (tire fitment fetch inside `_run_recommend`) — `except Exception: pass`. Same pattern: DB failure produces an empty tire list silently. Add `logger.warning`.

- **`motoquant/api.py:831`** (bike detail JSON-blob parse) — `except Exception: pass`. Malformed `engine_params`/`aero_params` JSON in the DB degrades the `/api/bikes/{id}` response silently; client sees missing fields. Already mitigated by `_safe_parse` helper at line 777 (which returns `{}` — acceptable), but the outer `except Exception: pass` at 831 hides any non-JSON error (e.g. a programming error in the detail-page enrichment block). Add `logger.warning`.

- **`motoquant/database/weather_repo.py:159`** — `fetch_live` network call swallows all exceptions and returns `None`. The caller in `weather_refresh.py:229` handles `None` by logging an error — **that path is fine**. However no distinction is made between transient network errors and bad API keys; both return `None`. Low severity; acceptable for a best-effort data path.

- **`motoquant/nlp.py:566`** — `except Exception: pass` on budget remaining calculation. Comment says "Silently fail on budget calculation" — the arithmetic is simple (`sum(price_inr for ...)`) and should not raise; if it does that's a programming error worth surfacing. **Fix:** remove the try/except entirely or narrow to `(TypeError, ValueError)`.

---

## Bare except clauses (narrow these)

No bare `except:` (no-type) clauses found in the core motoquant package. All catches name at minimum `Exception`. The TS/JS side uses `catch { }` (no binding) in two places in `web/lib/api.js:42,46`, but these are inside the API error-message parser where degradation to a status-only message is intentional and the outer `throw new Error(msg)` still fires — acceptable.

---

## Defaults masking real problems

- **`motoquant/database/weather_repo.py:163–168`** — OWM response parsed with `data.get("main", {}).get("temp", 25.0)` etc. If the API returns a malformed response (missing `"main"` key entirely), temperature defaults to 25 °C, humidity to 50 %, pressure to 1013.25 hPa — realistic-looking values that will pass downstream physics checks without triggering any alert. A completely bogus API response would produce a valid-seeming weather record. **Mitigation in place:** `resp.raise_for_status()` catches HTTP errors; the silent-default risk is limited to malformed-but-200 responses. Medium severity; add a `if "main" not in data: logger.warning(...)` guard.

- **`motoquant/database/parts_repo.py:77`** — `except (json.JSONDecodeError, TypeError): pass` on `drivetrain_params` parse; `bike_row["chain_pitch"]` is left unset (None). This is the documented fallback for shaft/belt-drive bikes and is correct. Not a real mask.

---

## Acceptable / leave alone (with reason)

- **`motoquant/keepwarm.py`** broad excepts — documented in CLAUDE.md as intentional; keep-alive must never affect availability.
- **`motoquant/api.py` startup keepwarm hook** — same documented design.
- **`motoquant/calibration/calibrator.py:213`** — `except Exception: return 1e6` in the objective function penalises crashed simulations during DE optimisation. This is the correct circuit-breaker pattern for a numerical optimizer; crashes must not propagate.
- **`motoquant/analysis/surrogate_data.py:598`** — training-data generation swallows per-sample sim failures and logs them; the failure rate is reported at the end. Correct for a batch process.
- All `except ImportError` / `except ImportError as exc` optional-dependency patterns throughout analysis modules — correct.
- **`motoquant/database/connection.py:66,118`** — WAL→DELETE fallback on FUSE. Documented design in CLAUDE.md.
- **`motoquant/scraper/bulk_scrape.py:436,444`** — per-bike scrape failures logged and counted; `KeyboardInterrupt` re-raised. Correct.
- **`web/lib/api.js:42,46`** — catch-without-binding inside JSON error-message parser; outer `throw` still fires. Acceptable.
- **`motoquant/auth.py:164`** — fallback JWT decode on `Exception` returns `None` (unauthenticated), which is the safe direction for auth failures.

---

## Numerical summary

```
try_blocks:        ~95 (Python), ~4 (JS/TS)
silent_swallows:   9   (no log + no re-raise)
bare_excepts:      0   (Python); 2 (JS/TS, both acceptable)
default_masks:     1   (OWM response defaults)
critical:          3
medium:            5
acceptable:        11
```
