# Support triage — 2026-05-25

**Agent:** customer-support
**Session workdir:** `/tmp/mq-session-1779683449-749/repo`
**HEAD at start:** `094eef8` (chore(dispatch): postflight outbox entry)

## bike_suggestions triage

**Table state:** present (schema intact: 15 cols), **0 total rows** — no user submissions have ever landed (table has been empty on every triage run to date: May-7, May-21, May-24, May-25).

Per workflow step 3, fell back to outbox-scan.

---

## Outbox scan — alert analysis

**Window scanned:** full `DISPATCH_OUTBOX.md` (1536 lines), May 7 → May 25 2026.

**Alert counts by category:**

| Category | Count | Date range |
|---|---|---|
| `Postflight deploy check timed out after 180s` | 40 | May-17 → May-24 |
| `self-review M6 auto-applied weight change` | 1 | May-25 |
| **Total** | **41** |  |

**Key inflection since May-24 triage:**

1. **ALERT dedup fix is working.** The May-24 08:39 session (commit `0f5edec`) implemented `_blocking_ticket_open()` in `session_postflight.sh`. The last two Railway-timeout alerts fired at 05:13 and 06:45 UTC on May-24 — both BEFORE the fix landed at 08:39. No further Railway-timeout alerts have appeared in the outbox since then (8+ sessions have run across May-24–25 without a fresh duplicate). The suppression is functioning exactly as designed.

2. **New alert category appeared: self-review weight-change.** `### ALERT — 2026-05-25T09:00:00Z — self-review M6 auto-applied weight change` — the self-review agent auto-bumped `benchmark-import.base` 40 → 50. This is expected and benign (per its own attribution and playbook §5 "3+ consecutive wins → bump single knob"). However it is the first time this category of self-modification alert has appeared; worth monitoring whether the format stays clean or generates noise at scale.

3. **Railway blocking ticket still open.** `DISPATCH_INBOX.md` line 140, `## INSTRUCTION — 2026-05-17 — [urgent] Railway API offline`, remains un-archived (status: open, above the `## DONE / DEFERRED ARCHIVE` divider). The alert suppression works around it but the underlying production outage is now 8 days old.

---

## Top-3 systemic fixes proposed

(Note: Fixes 1 and 2 below were also proposed by the May-24 triage. They remain unimplemented by autonomous sessions because they require the user's Railway billing credentials. Fix 3 is new, surfaced by the May-25 self-review alert.)

### 1. (Highest priority, user-action required) Restore Railway production service

The blocking ticket (`DISPATCH_INBOX.md:140`) has been open 8 days. Every interactive feature on `motoquant.in` — simulator, `/bikes`, `/api/health`, leaderboard — returns HTTP 404 to real users. The postflight alert-suppression fix is working but is a logging patch, not a service fix. Revenue and credibility impact compound daily.

**Action for user:** Log into `railway.com/dashboard` → project `proactive-adventure` → service `web`. Upgrade trial to Hobby/Pro. Redeploy. Once `/api/health` returns `{status:ok}`, archive `DISPATCH_INBOX.md:140` by adding it to the `## DONE / DEFERRED ARCHIVE` section — the suppression helper will then stop suppressing and future genuine deploy-check timeouts will surface again as alerts.

### 2. (Medium priority) bike_suggestions table still has zero rows after 18 days live

The `bike_suggestions` table was wired up to `POST /api/bikes/suggest` in the April-20 web-launch session. Since then — across 4 support-triage runs — zero users have submitted a suggestion. Three possible causes: (a) the Railway outage means the submit endpoint 404s so user submissions are silently failing; (b) the suggest form on `/bikes` is not prominent enough to drive submissions; (c) organic traffic is too low to generate submissions yet.

**Proposed fix:** once Railway is restored, add a quick end-to-end test that POST-submits a test suggestion, confirms the row is created, then deletes it — ensures the endpoint is alive every session. Queue as `[opportunistic]` INSTRUCTION for the catalog-expansion or benchmarks agent.

### 3. (Low priority) Self-review auto-weight alert format needs clarity spec

The May-25 alert `### ALERT — 2026-05-25T09:00:00Z — self-review M6 auto-applied weight change` carries a structured inline message (attribution, reason, revert condition). This is genuinely useful signal — but the timestamp format `09:00:00Z` (hardcoded or rounded?) differs from all other alerts (`+00:00` suffix). If the self-review agent fires multiple weight changes in future, a burst of these could visually blend with the Railway-type alerts unless the body is parsed.

**Proposed fix:** self-review agent should prefix its auto-applied-weight ALERTs with a distinguishing tag, e.g. `### ALERT [scheduler-weight]` vs the generic `### ALERT`, so the user can visually distinguish categories when scrolling. Alternatively, route auto-weight changes to a dedicated outbox section `## SCHEDULER TUNING LOG` rather than ALERT. Queue as `[opportunistic]` for the self-review agent template.

---

## Escalations to the user

1. **Railway API still down, now day 8.** INBOX:140 still open. The alert-suppression fix is masking the noise but the production service is dead for real users. Needs Railway billing credentials — cannot be fixed by autonomous session.
2. **Consider: a 5-minute end-to-end POST to `/api/bikes/suggest` smoke-test** as a standing postflight gate (runs only when Railway is healthy, so zero cost while the outage persists). Would catch silent form-submission regressions that currently have no detection.

## INBOX queue

No new INSTRUCTION blocks queued — both actionable items require user credentials (Railway) or are low-priority suggestions that do not justify an immediate instruction. The self-review weight-format suggestion is captured above for the user's awareness.

## Baseline verification

K5 10.0334s confirmed. No physics files touched.
