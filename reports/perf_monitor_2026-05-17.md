# Performance Monitor — 2026-05-17 (inaugural run)

First run of agent A10 (`performance-monitor`). No rolling-average baseline exists
yet; today's row establishes the seed. Future runs will diff against the trailing
7-day mean and flag > +30% drift.

## Measurements

| Probe                          | Result                                       | Notes                                                                 |
| ------------------------------ | -------------------------------------------- | --------------------------------------------------------------------- |
| Railway `/api/health`          | 200 OK, `bike_count: 342`                    | DB connected. Egress worked despite prior "blocked" note in CLAUDE.md |
| Vercel `www.motoquant.in`      | Reachable, title renders                     | Page-title string matches expected SEO copy                            |
| `tests/test_validation.py + test_scraper.py` | 111 passed in 9.231 s wall-clock | Matches the ~10 s focused-subset budget documented in CLAUDE.md      |
| Baseline sim (K5 + R1 + Hayabusa) | 0.7682 s for 3 bikes (~0.256 s each)      | All three ETs match locked references exactly to 4 dp                  |
| Baseline ET — K5               | 10.0334 s                                    | Locked reference; Δ +0.0000                                            |
| Baseline ET — R1               | 10.2859 s                                    | Locked reference; Δ +0.0000                                            |
| Baseline ET — Hayabusa         | 10.4712 s                                    | Locked reference; Δ +0.0000                                            |
| Surrogate pickle               | Absent                                       | Neither `surrogate_dnn.pkl` nor `surrogate.pkl` present in this clone  |

## Drift check

First run — no prior data to diff. The threshold rule (> +30% over 7-day rolling
mean, two consecutive bad samples) cannot fire yet. Earliest meaningful drift
report: 2026-05-24 with N=7 prior rows.

## Notable observations

1. **Egress to Railway + Vercel succeeded** from this sandbox. CLAUDE.md and the
   May-3 daily-aborted report both list these domains as blocked. Either the
   allowlist was widened recently, or the prior cache went stale. Worth flagging
   so future runs don't pre-emptively skip the WebFetch step.
2. **Production `bike_count` is 342**, while local clone CLAUDE.md headline-stats
   are pinned at 336 (May 4 daily session). Production is 6 ahead — consistent
   with additional autonomous catalog additions between May 4 and today that
   haven't yet been mirrored back into CLAUDE.md.
3. **Surrogate pickles missing locally.** Per Phase 4 status in CLAUDE.md they
   ship in repo root (`surrogate_dnn.pkl` 10.8 MB). They're gitignored or got
   pruned in this session's clone. Inference-latency timing skipped this run;
   capture it next time if the file is present.
4. **TTFB cannot be measured via WebFetch.** The tool returns content but not
   network timing. If TTFB tracking matters, swap to a `curl -w "%{time_starttransfer}"`
   probe in a follow-up. Recorded `ttfb_ms: null` to keep the schema honest.

## No INBOX entries queued

Measurements are within expected envelopes. Tests at 9.2 s and 3-bike baseline
at 0.77 s are nominal. No urgent action required.
