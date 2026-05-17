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

## Run 4 — measurements (curl-based, full latency primitives)

First run today to use `curl -w` end-to-end so TTFB / payload-bytes / per-sample latencies are captured numerically.

| Probe | Value | Status |
|---|---|---|
| motoquant.in TTFB (`time_total`) | 1330.65 ms | 200 OK |
| motoquant.in payload | 32,634 bytes | — |
| Railway `/api/health` × 5 (ms) | 850.12 / 677.04 / 664.67 / 669.37 / 672.48 | 200 OK |
| `/api/health` mean / median | 706.74 / 672.48 ms | — |
| Railway `/api/bikes?limit=10` | 703.99 ms, 10 bikes, first = Aprilia RS 457 | 200 OK |
| pytest wall (`/usr/bin/time`) | 10.40 s | 111 passed, 460 warnings |
| pytest internal summary | 8.13 s | — |
| `bike_count` | 342 | unchanged across all 4 runs |

### Run 4 drift table

| Metric | Today | Same-day prior | Δ vs mean | Verdict |
|---|---|---|---|---|
| pytest_wall_s | 10.40 | [9.231, 7.90, 8.154] mean 8.43 | +23.4% | within +30% gate — NOT escalated |
| api_health_mean_ms | 706.74 | n/a (first curl-measured) | — | baseline-building |
| web_ttfb_ms | 1330.65 | n/a (first curl-measured) | — | baseline-building |
| api_bikes_ms | 703.99 | n/a (first curl-measured) | — | baseline-building |
| bike_count | 342 | 342 (× 3 prior) | 0 | stable |

### Run 4 notes

- First sample of `/api/health` was 850 ms vs subsequent 4 at ~670 ms — cold-cache / cold-process signature. Flag if the gap widens across future runs.
- pytest wall 10.40 s vs internal 8.13 s — 2.3 s collection/import overhead; `/usr/bin/time` value tracks what CI sees.
- Drift escalation gate (≥3 prior **rows** + 2 **consecutive** > +30% deltas) still not met. No DISPATCH_INBOX action.
- Baselines (K5 / R1 / Hayabusa) not re-verified this run — relying on prior same-day runs' confirmation.

## Run 5 — measurements (WebFetch-based)

Fifth perf-monitor probe on 2026-05-17. WebFetch used (no curl this run) so TTFB / payload primitives left null per tool limitation.

| Probe | Status | Detail |
|---|---|---|
| `https://www.motoquant.in/` | ok | title matches expected SEO copy |
| `https://web-production-de6eb.up.railway.app/api/health` × 5 | ok | `{"status":"ok","database":"connected","bike_count":342}` on every sample |
| `https://web-production-de6eb.up.railway.app/api/bikes?limit=10` | ok | 10 rows; first = `Aprilia RS 457 (2024-2026)` |
| `pytest tests/test_validation.py tests/test_scraper.py` | ok | **111 passed in 7.775 s** (`real 0m7.775s` per `time`) |

### Run 5 drift table

| Metric | Today | Same-day prior | Δ vs mean | Verdict |
|---|---|---|---|---|
| pytest_wall_s | 7.775 | [9.231, 7.90, 8.154, 10.40] mean 8.921 | **-12.8%** | within noise (gate +30%) |
| api_health bike_count | 342 | 342 (× 4 prior) | 0 | stable |
| api_bikes count | 10 | 10 (× prior) | 0 | unchanged |
| web title | matches | matches | 0 | unchanged |
| network egress | functional | functional | 0 | unchanged |

5 same-day datapoints now exist; rolling-baseline still not formed across distinct dates. No drift flag raised. No `DISPATCH_INBOX.md` escalation queued — all metrics inside envelope.

### Run 5 notes

- Pytest 7.775 s sits at the low end of today's spread [7.78–10.40 s] — confirms run-4's 10.40 s `/usr/bin/time` reading was overhead-tainted, not a real regression.
- All 5 today's `bike_count` reads stable at 342 — no DB rollback / re-seed event.
- WebFetch tool still lacks TTFB / payload-bytes primitives. Run 4 captured those via curl; no escalation signal this run warranted a re-shell.
- Surrogate pickles still not re-checked this run (out of fast-probe scope).

## Run 6 (perf-monitor agent A11) — full curl primitives

Probed via curl this run for TTFB + payload bytes. All probes returned HTTP 200 first attempt.

| Metric                    | Today (run 6) | Prior (run 4 — full curl) | Δ vs run 4 | Same-day pytest mean | Δ vs mean | Gate (>+30%) |
|---------------------------|---------------|----------------------------|------------|----------------------|-----------|--------------|
| Landing TTFB (ms)         | 1378.51       | 1330.65                    | +3.6%      | —                    | —         | ok           |
| Landing payload (bytes)   | 32,634        | 32,634                     | 0.0%       | —                    | —         | ok           |
| /api/health avg (n=5, ms) | 708.29        | 706.74                     | +0.2%      | —                    | —         | ok           |
| /api/health median (ms)   | 687.44        | 672.48                     | +2.2%      | —                    | —         | ok           |
| /api/bikes latency (ms)   | 478.23        | 703.99                     | -32.1%     | —                    | —         | improvement  |
| Pytest wall-clock (s)     | 7.898         | 10.40                      | -24.1%     | 8.692                | -9.1%     | ok           |
| Pytest pass / fail        | 111 / 0       | 111 / 0                    | flat       | —                    | —         | ok           |
| api_health bike_count     | 342           | 342                        | flat       | —                    | —         | ok           |

Raw 5-sample /api/health latency (ms): `[821.71, 656.88, 703.23, 687.44, 672.21]`. First sample +21% above the trailing 4 — cold-cache pattern consistent with run 4.

Same-day pytest history vector: `[9.231, 7.900, 8.154, 10.400, 7.775, 7.898]` → mean 8.560 s.

**Verdict:** No drift. `/api/bikes` improved -32% vs run 4 (negative drift = faster, not escalated per agent spec). All other metrics within ±5% of run 4 capture. Pytest wall-clock comfortably below same-day rolling mean. No `[urgent]` queued to DISPATCH_INBOX.md.

**Baseline status:** 6 same-date entries; cross-day rolling baseline still not formed. First cross-day comparison possible from 2026-05-18 onward.

