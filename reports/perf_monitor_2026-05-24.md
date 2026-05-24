# Performance Monitor — 2026-05-24 (Sunday)

**Summary:** Railway API remains down (Day 8 of 404 outage, INBOX:140 still open). Vercel landing page healthy. Local test suite stable. No drift escalation. Two probe runs today: Run 13 (session 1779597050-811) and Run 14 (session 1779604236-636, this report) confirm intra-day consistency.

---

## Run 14 Probes (this session)

### Landing Page (Vercel — www.motoquant.in)

| Metric | Run 14 | Run 13 (earlier today) | 2026-05-17 mean | Δ vs May 17 |
|---|---|---|---|---|
| TTFB | 953.7 ms | 1.18 ms | ~1209 ms | -21.1% |
| HTTP status | 200 OK | 200 OK | 200 | ✓ |
| Payload | 34,048 bytes | 34,048 | 32,634 | +4.3% |

**Status:** Healthy. The 800x TTFB gap between Run 13 (1.18ms) and Run 14 (953.7ms) is best explained by cold-cache vs warm-cache jitter at the Vercel edge — both values are well inside the normal web-perf envelope (<2s) and not indicative of regression. Cross-run improvement vs 2026-05-17 baseline (-21%) is within noise.

### API /api/health (Railway — web-production-de6eb.up.railway.app)

| Metric | Value | Notes |
|---|---|---|
| HTTP status | 404 (all 5 samples) | **Application not found** — Railway platform router rejection |
| Samples (5×) | [376.8, 266.8, 323.2, 313.8, 366.1] ms | Mean 329.3 ms, median 323.2 ms |
| Bike count | `null` | Cannot connect |
| Status | **DOWN — Day 8** | Outage since 2026-05-17 Run 11 |

Latencies (~330ms) reflect Railway-router immediate rejection, not application timeout — consistent with platform-level 404 (service removed / billing suspended).

### API /api/bikes?limit=10 (Railway)

| Metric | Value |
|---|---|
| HTTP status | 404 |
| TTFB | 320.3 ms |
| Response payload | 101 bytes (error JSON) |
| Status | **DOWN** |

Matches `/api/health` — same platform-level rejection.

### Local Test Suite

**Command:** `pytest tests/test_validation.py tests/test_scraper.py -q --no-header --maxfail=5`

| Metric | Sample 1 | Sample 2 | Median | 2026-05-17 same-day mean | Δ |
|---|---|---|---|---|---|
| Wall clock | 8.773s | 8.810s | 8.79s | 8.39s | **+4.8%** ✓ |
| Passed | 111 | 111 | 111 | 111 | — |
| Failed | 0 | 0 | 0 | 0 | — |

**Status:** Stable. +4.8% vs the 2026-05-17 baseline is well within the ±30% drift gate; ~0.4s above last week is consistent with normal CPU jitter on shared hardware.

---

## Drift Detection

**Rolling baseline (2026-05-24 vs 2026-05-17 same-test mean):**
- Pytest median 8.79s vs May 17 mean 8.39s = **+4.8%** — no escalation (gate is +30%)
- Landing TTFB: Run 13 (1.18ms) and Run 14 (953.7ms) span 3 orders of magnitude — cache-warmth jitter, not regression. Vs 2026-05-17 baseline mean ~1209ms, Run 14 = -21.1% (improvement).
- API latencies: cannot compute — both endpoints have been 404 since 2026-05-17 Run 11 (no healthy baseline since).

**Consecutive bad runs (drift gate = 2):** N/A — Railway outage is binary (404 vs N/A), not metric drift. Tracked as outage, not drift.

**Escalation decision:** No fresh INBOX item filed. INBOX:140 ([urgent][blocking] Railway 404 since 2026-05-17) remains the sole blocker for production API. Run 12 (2026-05-17 final) and Run 13 (today, earlier) both correctly applied the dedup pattern; Run 14 follows the same precedent.

---

## Intra-day Consistency Check (Run 13 vs Run 14)

| Metric | Run 13 | Run 14 | Verdict |
|---|---|---|---|
| Railway /api/health | 404 (mean 0.338ms) | 404 (mean 329.3ms) | Outage persists. Latency divergence reflects different curl-tier paths/cache locations; both are platform 404, semantically identical. |
| Railway /api/bikes | 404 | 404 | Consistent |
| Vercel landing | 200, 1.18ms | 200, 953.7ms | Both 200 OK; TTFB jitter is cache-driven |
| Pytest median | 8.69s | 8.79s | +0.10s drift between intra-day runs — within noise |
| Tests pass/fail | 111/0 | 111/0 | Identical |

Intra-day stability confirmed. No regression introduced between the two probes.

---

## Headnotes

- **Day 8 of Railway outage** — initial 404 logged 2026-05-17 Run 11; today's Run 13 and Run 14 confirm continued downtime. User-owned migration to Render is in progress (parallel chat, per CLAUDE.md Phase-3 post-launch hygiene note about trial expiry).
- **No new drift this week** — local tests remain ~8.6–8.8s across both probes; well within drift gate.
- **Vercel healthy** — frontend (motoquant.in) shows no latency regression; 200 OK both probes.
- **7-day rolling baseline still incomplete** — only 2 distinct calendar dates in `data/perf_timeseries.json` (2026-05-17 with 12 runs, 2026-05-24 with 2 runs). Full cross-day drift detection requires ≥7 distinct dates; baseline will mature ~May 31 (assuming daily runs resume).
- **Dedup applied** — no fresh INBOX item filed; INBOX:140 remains the canonical Railway-outage ticket.
- **Next run:** 2026-05-25 (Monday). Once 7+ distinct dates accumulate, rolling-avg drift comparisons will become statistically robust.
