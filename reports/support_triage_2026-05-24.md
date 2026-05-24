# Support triage — 2026-05-24

**Agent:** customer-support
**Session workdir:** `/tmp/mq-session-1779647439-649/repo`
**HEAD at start:** `094eef8` (chore(dispatch): postflight outbox entry)

## bike_suggestions triage

**Table state:** present (schema intact: 15 cols) but **0 total rows** — no user submissions to triage.

Per workflow step 3, fell back to outbox-scan over the last 30 days.

## Outbox scan — alerts & incidents

**Window scanned:** `DISPATCH_OUTBOX.md` lines 1–1433 (May 7 → May 24, 2026 — the file's full lifetime; only 17 days, well inside the 30-day window).

**Tallies:**
- `### ALERT` entries: **40**
- `## INCIDENT` entries: **2** (both inline references inside an INSTRUCTION block — not standalone incidents)
- `## SESSION` entries: 0 (the post-flight script uses bare `## YYYY-MM-DDTHH:MM:SS — session N` headers, not `## SESSION`)

**Critical finding:** **All 40 alerts are the same string** — `"Postflight deploy check timed out after 180s"`. Date-range May 17 20:45 → May 24 06:45 (≈7 days), averaging **~5.7 alerts/day**. This is one systemic incident repeating, not 40 distinct events.

## Top-3 systemic fixes proposed

### 1. (Highest priority) Postflight deploy-alert suppression is silently failing while Railway is down
**Root cause chain:**
- Railway trial expired 2026-05-17 (predicted in CLAUDE.md Phase-3 hygiene block; April 23 + 24 days = May 17).
- The blocking inbox ticket `INSTRUCTION — 2026-05-17 — [urgent] Railway API offline` was queued in commit `0128b823` at 20:42 UTC, **3 minutes before** the first alert at 20:45.
- `scripts/session_postflight.sh::_blocking_ticket_open` (lines 284–299) IS designed to suppress duplicate alerts when a matching `[blocking]` + `Railway|deploy` ticket exists.
- Manually running that exact awk against today's inbox returns the matching ticket correctly. So suppression *should* be firing.
- Yet alerts keep appending — most recently 2026-05-24 06:45.
**Suspected real cause:** the awk's per-line state-machine has an ordering subtlety. The `block && tagged && matched` test triggers only AFTER both `tagged=1` and `matched=1` have been set within the same block. For the May-17 ticket, the `## INSTRUCTION` header contains `Railway` (matched=1 set on line 1) but the `[blocking]` tag appears on **line 2** of the block. AWK's per-line evaluation hits the print test at end of line 1 with `tagged=0` (skip), then on line 2 sets `tagged=1` and re-checks (matched still =1 from prior line because `matched=1` was set in the `block && /Railway|deploy/` branch which is sticky across lines, not block-scoped). So it *should* print on line 2. Will need a 5-minute scripted repro on the exact inbox snapshot at each alert timestamp to pin the precise failure mode — could be encoding (CRLF on FUSE checkout?), could be a slim race in `_queue_alert` running before the new inbox commit has actually replaced the working file. **Action:** queue a kaizen instruction (see INBOX append below) to add a regression test + add a "last-alert-fingerprint" file in `/tmp` so the same message can never re-fire within 1 hour.

### 2. Production has been hard-down for 7 days with no escalation cadence
The `[urgent]` Railway ticket has sat in `DISPATCH_INBOX.md` since May 17. No mechanism re-pings the user when a `[blocking]` ticket ages beyond N hours. Customers landing on `motoquant.in` see the static shell load but every interactive feature (simulator, /bikes, /leaderboard) breaks silently. **Proposal:** preflight script should detect `[blocking]` tickets older than 24h and emit an INBOX line "ESCALATION: ticket X open >7 days" plus prepend a banner to the outbox of every subsequent session.

### 3. Outbox is a write-only firehose (only 2 inline incidents in 17 days, but 40 dup alerts)
The outbox conflates three signals: session SUMMARIES (high value), one-off ALERTS (medium value), and repeating ALERTS (noise). At current cadence (~5.7 dup alerts/day) the file grows ~22 KB/day in pure noise, drowning out real session summaries when the user opens it on their phone. **Proposal:** dedup at write-time — if the last `### ALERT` block has identical body, increment a `(repeat #N)` suffix instead of appending a new block. Backstop with a weekly outbox-rotation script that moves alerts older than 14 days to `reports/outbox_archive_YYYY-WW.md`.

## Escalations to the user

1. **Railway API still down on day 7 (was day 1 when first detected).** No autonomous session can fix; needs the user's Railway billing credentials. See `DISPATCH_INBOX.md` line 140.
2. **Postflight deploy-alert suppression bug noted above** — the kaizen system has not yet self-healed this in 7 days despite the design intent. Queued as `## INSTRUCTION` below.

## INBOX queue
- 1 new `[opportunistic]` instruction appended targeting the postflight-script kaizen agent (see step below).
