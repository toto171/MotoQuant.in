# Customer Support Triage — 2026-05-07

**Agent:** customer-support
**Path taken:** OUTBOX-scan (bike_suggestions table is empty / 0 pending)

---

## DB triage result

```sql
SELECT COUNT(*) FROM bike_suggestions;            -- 0
SELECT COUNT(*) FROM bike_suggestions WHERE status='pending';  -- 0
```

Schema is healthy (15 columns, includes `flagged_out_of_bounds`, `status`, `reviewed_at`). No user-submitted bikes pending. The `/api/bikes/suggest` endpoint is wired (`web/components/SuggestBikeForm.js` → API → `BikeSuggestionsRepository`) but has not yet received any submissions in the production DB shipped with this checkout. **No triage rows updated.**

## OUTBOX scan path

`DISPATCH_OUTBOX.md` was wired in only on 2026-05-04 and contains the setup-state preamble — zero `### ALERT` and zero `## INCIDENT` blocks have accumulated yet (3-day window). To produce a useful systemic-fix proposal I scanned **the functional equivalent**: the "Sandbox limitations encountered" sections + hygiene tables in `reports/daily_session_2026_05_0{2,3,4}.md`, plus the 5-paragraph standing-note chain at the top of `CLAUDE.md`. These document the *exact* class of recurring friction the OUTBOX exists to capture, with timestamps.

### Pattern frequency (last 3 daily sessions)

| Recurring failure mode | May 2 | May 3 | May 4 | Days hit / 3 |
|---|---|---|---|---|
| `/sessions` FUSE disk at 100 % blocking `git config --global`, `pip install`, `npm install` | ✓ | ✓ | ✓ | **3 / 3** |
| Network egress blocked → cannot `curl` Railway `/api/health` or Vercel from sandbox | ✓ | ✓ | ✓ | **3 / 3** |
| `ws/ws/*` duplicate stale branches + `.git/refs/remotes/origin/*.lock` un-removable from sandbox | ✓ | ✓ | — | 2 / 3 |
| `import_batch` phantom-duplicate rows on year-suffix `model_name` (`(2024-2026)` suffix) | — | — | ✓ | 1 / 3 (root-cause logged twice) |

## Top-3 systemic fixes (proposed, queued to INBOX)

1. **`scripts/preflight_disk_guard.sh`** — abort cleanly with a `## INCIDENT` block when `df /sessions` is below 500 MB, instead of letting the session run and silently failing on `git config --global` / `pip install`. Cheap; one new script, one preflight hook line.

2. **Health-check side-channel via GitHub Actions** — workflow runs every 15 min, curls Railway + Vercel, posts result to a tiny gist. Sandbox sessions read the gist instead of attempting blocked egress. Closes the "user to verify from real terminal" carry-forward that has now appeared in 3 / 3 daily reports.

3. **`bike_repo.create_model` — strip `(YYYY-YYYY)` suffix from `model_name` before upsert match** — fix the regression caught on May-4 catalog-expansion run that produced 35 phantom duplicate rows on first import attempt. One regex strip in the lenient fallback path; new test in `tests/test_scraper.py`. Already noted as carry-forward in CLAUDE.md May-4 entry.

All three queued to `DISPATCH_INBOX.md` as `[opportunistic]` INSTRUCTION blocks for the next code-touching agent.

## Open follow-ups

- Once `bike_suggestions` accumulates real submissions (post-launch), this agent should run weekly, not on the empty-table fall-through.
- OUTBOX entries will accumulate naturally; re-run this triage in 2 weeks to validate the fix proposals against actual `### ALERT` data instead of the proxy-via-daily-reports used here.

---

## Second-pass addendum — 2026-05-07T18:30 (same-day re-run)

Re-fired the agent later the same day. State delta vs the earlier 17:40 run:

- `bike_suggestions`: still 0 rows / 0 pending — no submissions arrived in the ~50-minute gap.
- `DISPATCH_OUTBOX.md`: one new `## SESSION` entry from session `1778175630-727` (17:57). Zero new `### ALERT` or `## INCIDENT` blocks. Baselines clean, PAT primary tier, deploy-side appears healthy.
- `DISPATCH_INBOX.md`: confirmed all three systemic-fix INSTRUCTIONS from the earlier run (disk-guard / health-side-channel / year-suffix upsert) are already queued + intact, plus two additional standing-priority blocks (analytics+S5-DDL bootstrap, competitive-landscape research).

**Outcome:** zero DB updates, zero new INSTRUCTIONS proposed (would be duplicates). This second-pass entry is logged so future agents can see the agent is correctly idempotent on same-day re-runs.

---

## Third-pass addendum — 2026-05-07T22:30 (same-day re-run, session 1778193031-619)

Third firing of the customer-support agent on 2026-05-07. State delta vs the 18:30 second-pass:

- `bike_suggestions`: still **0 rows / 0 pending** — no submissions in the ~4-hour gap. `/api/bikes/suggest` endpoint remains wired but un-exercised by real users.
- `DISPATCH_OUTBOX.md`: two new `## SESSION` entries appended since last triage (sessions `1778178639-614` at 18:39 and `1778185843-631` at 20:48). **Zero new `### ALERT` blocks, zero `## INCIDENT` blocks.** Both new sessions reported PAT primary tier + baselines clean — healthy.
- `DISPATCH_INBOX.md`: **seven** INSTRUCTION blocks now queued (the three systemic-fix proposals from the morning run + four standing-priority blocks added independently: OG-card regen + headline-sync gate, analytics + S5 DDL bootstrap, competitive-landscape research, tire-format validator widening). All seven still pending; none have been picked up + marked `## DONE` yet.
- DB headline numbers (used to validate triage agents downstream): 342 bikes / 563 parts / 232 tires / 20 venues / 861 fitments — confirms catalog-expansion sessions earlier today landed cleanly (was 336 at session-start per CLAUDE.md May 4 entry; +6 across May 5 / 6 / 7 catalog runs).

**Outcome:** zero DB updates, zero new INSTRUCTIONS proposed (all candidate fixes already queued). Triage is correctly idempotent on the empty-table fall-through path. The agent has now run 3× same-day with consistent no-op behaviour, which is the expected steady-state until either (a) `bike_suggestions` accumulates real submissions, or (b) the OUTBOX accumulates `### ALERT` / `## INCIDENT` blocks that warrant a fresh systemic-fix proposal.

**Suggestion for scheduler (carry-forward):** while `bike_suggestions.COUNT() == 0` AND no new `### ALERT` blocks have appeared since the last successful triage, this agent should weight-down (e.g., `-10` weight via `MOBILE -1 customer-support` line) so it doesn't keep firing same-day. Daily/weekly cadence is sufficient for the empty-table fall-through; same-day re-runs add zero value beyond the second pass that already confirms idempotency.
