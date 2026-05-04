# Agent A10: performance-monitor

Read CLAUDE.md.

## Goal

Detect and report drift in: page load time (motoquant.in), API latency (Railway), test wall-clock, sweep wall-clock. Append timeseries to `data/perf_timeseries.json`.

## Workflow

1. WebFetch motoquant.in landing — record TTFB + total payload size.
2. WebFetch /api/health — record latency. Hit it 5x, average.
3. WebFetch /api/bikes?limit=10 — record latency.
4. Run `time pytest tests/test_validation.py tests/test_scraper.py -q --no-header` — record wall-clock.
5. Append all to `data/perf_timeseries.json`.
6. Compare today's values vs the 7-day rolling avg. Anything > +30% drift → report it.

## Deliverable

- `data/perf_timeseries.json` (append today's row)
- `reports/perf_monitor_YYYY-MM-DD.md` with drift table
- If significant drift: queue `[urgent]` for tech-debt-pass

## Don't

- Don't run sweeps that take > 5 minutes (this agent is meant to be fast).
- Don't blame a single bad sample — require 2 consecutive bad runs before raising drift.
- Don't probe rate-limited endpoints aggressively.

Cap ~400 words.
