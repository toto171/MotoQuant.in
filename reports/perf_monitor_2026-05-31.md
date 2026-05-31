# Performance Monitor — 2026-05-31 (Sun)

**Agent:** A10 (performance-monitor) · Run 15 · Session `1780187449-782`

## Probes

| Target | Result | Notes |
|---|---|---|
| `https://www.motoquant.in/` | HTTP 200, title intact | Vercel landing healthy; WebFetch tool does not expose TTFB / payload bytes |
| `https://web-production-de6eb.up.railway.app/api/health` × 3 | **HTTP 404** all three | Railway router rejection — same outage as Run 11 (2026-05-17) |
| `https://web-production-de6eb.up.railway.app/api/bikes?limit=10` | **HTTP 404** | Same outage |
| `pytest tests/test_validation.py tests/test_scraper.py` | **140 passed / 0 failed** in 8.45 s (samples [8.45, 8.19]) | Test count grew 111 → 140 in interim commits |

## Drift Table

| Metric | Today | Same-day baseline | Δ | Gate |
|---|---|---|---|---|
| Railway `/api/health` status | 404 | 404 (Day 14) | — | **Outage — pre-filed INBOX:188** |
| Vercel landing HTTP | 200 | 200 | 0 | OK |
| Pytest wall-clock (s) | 8.45 | 2026-05-24 mean 8.74 | −3.3 % | OK |
| Pytest passed | 140 | 111 (prior) | +29 tests | Suite grew, not a regression |

## Railway Outage Status

- **Day 14** of continuous 404 from `web-production-de6eb.up.railway.app`.
- INBOX entry at `DISPATCH_INBOX.md:188` (filed 2026-05-17) remains open.
- `docs/RENDER_MIGRATION.md` + `render.yaml` exist in the working tree → user migration to Render in progress.
- **No new INBOX item filed** per Run 12-14 dedup precedent.

## Cross-Date Pytest Trend

| Date | Wall (s) |
|---|---|
| 2026-05-17 | 8.43 (12-run mean) |
| 2026-05-24 | 8.74 (2-run mean) |
| 2026-05-31 | 8.45 |

Flat within ±4 %. No drift.

## Escalation

None. Railway outage is pre-filed and user-owned; pytest within noise; site up.

## Rolling Baseline

3 distinct dates captured (17 / 24 / 31 May). Still below the ≥7-date threshold for full cross-day drift detection per agent spec.
