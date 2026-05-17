# Performance Monitor — 2026-05-17

Three perf-monitor probes have now landed on 2026-05-17 (runs 1, 2, 3). All three confirm stable production + green focused-test subset; no drift escalation.

## Run 1 (inaugural) — measurements

| Probe                          | Result                                       | Notes                                                                 |
| ------------------------------ | -------------------------------------------- | --------------------------------------------------------------------- |
| Railway `/api/health`          | 200 OK, `bike_count: 342`                    | DB connected. Egress worked despite prior "blocked" note in CLAUDE.md |
| Vercel `www.motoquant.in`      | Reachable, title renders                     | Page-title string matches expected SEO copy                            |
| `tests/test_validation.py + test_scraper.py` | 111 passed in 9.231 s wall-clock | Matches the ~10 s focused-subset budget documented in CLAUDE.md      |
| Baseline sim (K5 + R1 + Hayabusa) | 0.7682 s for 3 bikes (~0.256 s each)      | All three ETs match locked references exactly to 4 dp                  |
| Surrogate pickle               | Absent                                       | Neither `surrogate_dnn.pkl` nor `surrogate.pkl` present in this clone  |

## Run 2 — measurements

| Probe | Status | Detail |
|---|---|---|
| `https://www.motoquant.in/` | ok | title rendered |
| `https://web-production-de6eb.up.railway.app/api/health` | ok | `{"status":"ok","database":"connected","bike_count":342}` |
| `https://web-production-de6eb.up.railway.app/api/bikes?limit=10` | ok | 10 rows; first row = `Aprilia RS 457 (2024-2026)` |
| `pytest tests/test_validation.py tests/test_scraper.py` | ok | `111 passed in 7.90s` |

## Run 3 (this session, agent A10) — measurements

| Probe | Status | Detail |
|---|---|---|
| `https://www.motoquant.in/` | ok | title unchanged |
| `https://web-production-de6eb.up.railway.app/api/health` | ok | `bike_count: 342` |
| `https://web-production-de6eb.up.railway.app/api/bikes?limit=10` | ok | 10 rows; first = `Aprilia RS 457 (2024-2026)` |
| `pytest tests/test_validation.py tests/test_scraper.py` | ok | `111 passed in 8.154s` (`real 0m8.154s` per /usr/bin/time) |

## Drift table

| Metric | Run 1 | Run 2 | Run 3 | vs same-day mean (8.428 s of runs 1+2) | Verdict |
|---|---|---|---|---|---|
| `api_health.bike_count` | 342 | 342 | 342 | 0 | unchanged |
| `tests_passed` | 111 | 111 | 111 | 0 | unchanged |
| `tests_wall_s` | 9.231 | 7.90 | **8.154** | **-3.2 %** | within noise (drift gate +30 %) |
| `web_landing.title` | matches | matches | matches | 0 | unchanged |

Three same-day datapoints exist; 7-entry rolling window the spec calls for still not populated. No drift flag raised — pytest run 3 is well within ±30 % of same-day mean and within ±15 % of either prior run. No `DISPATCH_INBOX.md` escalation queued.

## NETWORK_ACCESS

- motoquant.in: **ok** — first-attempt success, title renders
- railway api: **ok** — `/api/health` and `/api/bikes?limit=10` both succeeded on first attempt; no retries required

Three consecutive perf-monitor sessions on 2026-05-17 have hit Railway and Vercel cleanly from the sandbox. The CLAUDE.md "cowork-egress-blocked" note (May 2/3/4 daily reports) does not currently apply — recommend retiring it on the next CLAUDE.md hygiene pass.

## Carry-forward observations (still true)

1. **Production `bike_count` is 342**, while CLAUDE.md headline-stats are pinned at 336 (May 4 daily session). Production is 6 ahead — consistent with autonomous catalog additions since May 4 that haven't been mirrored back into CLAUDE.md's last-updated header.
2. **Surrogate pickles still missing locally** in this clone. Phase 4 status says they ship in repo root (`surrogate_dnn.pkl` 10.8 MB); inference-latency timing skipped again this run.
3. **TTFB cannot be measured via WebFetch.** The tool returns content + status only, no network timing primitives. A lower-level probe (`urllib` + `time.perf_counter()` or `curl -w '%{time_starttransfer}'`) is needed to close this gap; queued GH-Actions side-channel INBOX item already covers it.

## No INBOX entries queued this run

Measurements within envelope; egress functional; no drift; no missing-deploy signal.
