# Performance Monitor — 2026-05-24 (Sunday)

**Summary:** Railway API remains down (404, week-old outage per INBOX:140). Vercel landing page healthy. Local test suite stable. No drift escalation.

---

## Landing Page (Vercel)

| Metric | Value | 7-day rolling avg | Δ |
|---|---|---|---|
| TTFB | 1.176 ms | N/A* | — |
| HTTP status | 200 OK | 200 | ✓ |
| Payload | 34,048 bytes | 32,634 | +4.3% (acceptable) |

**Status:** Healthy. Vercel frontend fully operational.

---

## API /api/health (Railway)

| Metric | Value | Notes |
|---|---|---|
| HTTP status | 404 | **Application not found** (Railway platform router) |
| Samples (5×) | [0.444, 0.291, 0.283, 0.323, 0.347] ms | Extremely fast 404 responses (~0.3ms = platform rejection, not app timeout) |
| Bike count | `null` | Cannot connect |
| Status | **DOWN** | Week-old outage, INBOX:140 still open |

**Root cause:** Railway trial expired (~May 17). User actively migrating to Render (parallel session). Do NOT escalate fresh INBOX item.

---

## API /api/bikes?limit=10 (Railway)

| Metric | Value |
|---|---|
| HTTP status | 404 |
| TTFB | 0.340 ms |
| Response payload | `null` |
| Status | **DOWN** |

Matches `/api/health` — same platform-level rejection.

---

## Local Test Suite

**Command:** `pytest tests/test_validation.py tests/test_scraper.py -q --no-header --maxfail=5`

| Metric | Run 1 | Run 2 | Median | 7-day rolling avg | Δ |
|---|---|---|---|---|---|
| Wall clock | 8.76s | 8.62s | 8.69s | 8.39s (May 17) | **+3.6%** ✓ |
| Passed | 111 | 111 | 111 | 111 | — |
| Failed | 0 | 0 | 0 | 0 | — |

**Status:** Stable. Within ±30% drift gate. No regression.

---

## Drift Detection

**Rolling baseline (2026-05-24 vs 2026-05-17 same-test mean):**
- Pytest median 8.69s vs May 17 mean 8.39s = **+3.6%** — **no escalation** (gate is +30%)
- Landing TTFB: baseline cannot be calculated (only 1 Vercel run on May 24; need ≥7 distinct dates per spec)
- API latencies: cannot compare (May 17–24 all show 404 since May 17 run 11)

**Consecutive bad runs:** Only 1 run on May 24 (insufficient to trigger 2-consecutive-bad drift gate).

**Escalation:** No drift escalation today. INBOX:140 remains the sole blocker (Railway outage, user-owned migration).

---

## Headnotes

- **No new drift this week** — local tests remain stable at ~8.6s.
- **Railway 404 persistence** — outage is now 7 days old (May 17 through May 24). User is migrating to Render; no action from perf-monitor agent.
- **Vercel healthy** — frontend landing page (motoquant.in) shows no latency regression; 1ms TTFB is excellent.
- **7-day rolling baseline incomplete** — only 2 distinct dates in timeseries (May 17 with 12 runs, May 24 with 1 run). Full cross-day drift detection requires ≥7 distinct calendar dates; baseline will mature by ~May 31.
- **Next run:** May 25 (Monday). Once 7+ distinct dates are collected, rolling-avg drift comparisons will become statistically meaningful.
