# Performance Monitor — 2026-05-17

Two perf-monitor probes have now landed on 2026-05-17. The first run (earlier today) was the inaugural seed of `data/perf_timeseries.json`; this second run confirms the signals are stable across the day and documents the result delta.

## Run 1 (inaugural, earlier today) — measurements

| Probe                          | Result                                       | Notes                                                                 |
| ------------------------------ | -------------------------------------------- | --------------------------------------------------------------------- |
| Railway `/api/health`          | 200 OK, `bike_count: 342`                    | DB connected. Egress worked despite prior "blocked" note in CLAUDE.md |
| Vercel `www.motoquant.in`      | Reachable, title renders                     | Page-title string matches expected SEO copy                            |
| `tests/test_validation.py + test_scraper.py` | 111 passed in 9.231 s wall-clock | Matches the ~10 s focused-subset budget documented in CLAUDE.md      |
| Baseline sim (K5 + R1 + Hayabusa) | 0.7682 s for 3 bikes (~0.256 s each)      | All three ETs match locked references exactly to 4 dp                  |
| Surrogate pickle               | Absent                                       | Neither `surrogate_dnn.pkl` nor `surrogate.pkl` present in this clone  |

## Run 2 (this session) — measurements

| Probe | Status | Detail |
|---|---|---|
| `https://www.motoquant.in/` | ok | Page rendered; title = `MotoQuant Pro — Motorcycle Quarter-Mile Drag Racing Simulator | ET Predictor & Build Optimizer` |
| `https://web-production-de6eb.up.railway.app/api/health` | ok | `{"status":"ok","database":"connected","bike_count":342}` — first attempt |
| `https://web-production-de6eb.up.railway.app/api/bikes?limit=10` | ok | 10 rows; first row = `Aprilia RS 457 (2024-2026)` |
| `pytest tests/test_validation.py tests/test_scraper.py` | ok | `111 passed in 7.90s` (also captured via `/usr/bin/time`: 8.38s first invocation including warmup) |

## Drift table

| Metric | Run 1 | Run 2 | Delta | Verdict |
|---|---|---|---|---|
| `api_health.bike_count` | 342 | 342 | 0 | unchanged |
| `tests_passed` | 111 | 111 | 0 | unchanged |
| `tests_wall_s` | 9.231 | 7.90 | -14.4% | within noise (drift gate +30%) |
| `web_landing.title` | matches | matches | 0 | unchanged |

Only two datapoints exist on the timeseries so the 7-entry rolling comparison the spec calls for is not yet possible. No drift flag raised. Two consecutive measurements is the escalation gate per spec — both runs today are within noise, so no INBOX item queued.

## NETWORK_ACCESS

- motoquant.in: **ok** — first-attempt success, title renders
- railway api: **ok** — `/api/health` and `/api/bikes?limit=10` both succeeded on first attempt; no retries required

Two consecutive perf-monitor sessions on 2026-05-17 (run 1 + run 2) hit Railway and Vercel cleanly from the sandbox. The CLAUDE.md "cowork-egress-blocked" note (May 2/3/4 daily reports) does not currently apply in this sandbox tier — at least intermittently reachable. The GH-Actions side-channel design remains queued in `DISPATCH_INBOX.md` (`[urgent]` with full design notes from the 2026-05-16 self-review follow-up) as a reliability hedge — no duplicate INBOX entry created from this run.

## Notable observations (carry-forward from run 1, still true)

1. **Production `bike_count` is 342**, while CLAUDE.md headline-stats are pinned at 336 (May 4 daily session). Production is 6 ahead — consistent with autonomous catalog additions since May 4 that haven't been mirrored back into CLAUDE.md's last-updated header.
2. **Surrogate pickles still missing locally** in this clone. Phase 4 status says they ship in repo root (`surrogate_dnn.pkl` 10.8 MB); they're either gitignored or pruned. Inference-latency timing skipped again this run.
3. **TTFB still cannot be measured via WebFetch.** The tool returns content + status only, no network timing. The GH-Actions side-channel (queued INBOX item) can use `curl -w "%{time_starttransfer}"` to close this gap naturally — recommend that be the canonical TTFB source once it ships.

## No INBOX entries queued this run

Measurements within envelope; egress functional; no drift; no missing-deploy signal. The two pre-existing related `[urgent]` INBOX items (GH-Actions side-channel build + design notes) already cover the observability gap that would have motivated a new queue entry.
