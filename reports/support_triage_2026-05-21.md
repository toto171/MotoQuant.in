# Customer-Support Triage — 2026-05-21 (Thursday)

Agent: `customer-support` per `scripts/agents/customer-support.md`.
Session: 1779323436-681 autonomous run.

## 1. `bike_suggestions` table — empty

Inspected `motoquant.db.bike_suggestions` (schema confirmed; columns: `id, make, model, year, displacement_cc, peak_power_hp, dry_mass_kg, category, notes, submitter_email, source_url, flagged_out_of_bounds, status, created_at, reviewed_at`).

```
SELECT COUNT(*) FROM bike_suggestions;
-> 0
SELECT status, COUNT(*) FROM bike_suggestions GROUP BY status;
-> (empty)
```

No pending, needs_info, rejected, or duplicate rows. Status: **empty**. This is expected — the `/api/bikes/suggest` endpoint has shipped (per CLAUDE.md April 20 entry) but the user-facing form is at `/bikes` (`SuggestBikeForm` component) and the production API has been down since 2026-05-17 (see §2), so no real user submissions could have landed during this window. Once the Railway API is restored, this table is the canonical inbound channel.

Pivoting per template to outbox-pattern analysis.

## 2. Recent ALERT / INCIDENT patterns (2026-04-21 → 2026-05-21)

`DISPATCH_OUTBOX.md` lines 430–923 contain **22 `### ALERT` entries**, all dated 2026-05-17 through 2026-05-20.

**Categorical breakdown:**

| Category | Count | First seen | Last seen |
|---|---:|---|---|
| `Postflight deploy check timed out after 180s` | **22** | 2026-05-17T20:45:51Z (line 430) | 2026-05-20T23:02:46Z (line 902) |
| All other ALERT categories | 0 | — | — |

**All 22 ALERTs share one root cause.** They are not 22 independent failures — they are 22 sessions where `scripts/session_postflight.sh::verify_deploy()` (lines 252-273) polled `https://web-production-de6eb.up.railway.app/api/health` for 180 s, received HTTP 404 `Application not found` every poll, and emitted the same alert template via `_queue_alert` (line 270).

**Live verification (2026-05-21, this session):**

```
$ curl -s --max-time 10 https://web-production-de6eb.up.railway.app/api/health
{"status":"error","code":404,"message":"Application not found","request_id":"q1ODF6P2Qli5jl8XoB_USg"}
$ curl -s -o /dev/null -w "%{http_code}" https://www.motoquant.in/
200
```

**Outage is ongoing — 4+ days since first detection.** Vercel landing page still 200 OK; backend dead.

## 3. Top systemic findings

### Finding A — Single platform-attributable outage masquerading as 22 distinct alerts

Original incident detection: perf-monitor run 11, `reports/perf_monitor_2026-05-17.md` lines 322-381 (clean diagnostic — confirmed Railway *platform* router 404, not FastAPI route 404). Root-cause hypothesis: Railway trial expiry (CLAUDE.md Phase-3 hygiene flagged this on April 23: *"$4.86 / 24 days left as of Apr 23"*; April 23 + 24 = May 17, the exact day of the outage). Hypothesis remains the most likely cause; no Railway dashboard access from sandbox to confirm.

**Already-queued INSTRUCTION:** `DISPATCH_INBOX.md` lines 140-182 (`[urgent] [blocking] Railway API offline`). User action required (billing / redeploy). No duplicate filed by this session.

### Finding B — Postflight alert noise during a known outage

The postflight script unconditionally re-fires the same alert every session while the API is down. Across 4 days that is 22 identical entries. This is signal-dilution: future genuine deploy-check timeouts (different commit, different cause) will be lost in the noise. The `[urgent]` INBOX ticket at line 140 is already authoritative; subsequent postflights should suppress duplicates of the same symptom while that ticket is open.

Specific log: `DISPATCH_OUTBOX.md` lines 430, 452, 474, 496, 518, 540, 562, 584, 606, 628, 650, 672, 695, 718, 741, 764, 787, 810, 833, 856, 879, 902 — same one-line body verbatim.

### Finding C — Perf-monitor agent is correctly silent on this; postflight is the noise source

`reports/perf_monitor_2026-05-17.md` runs 11-12 escalated exactly once and stopped (line 394: "the corresponding INBOX ticket already exists, so no duplicate is filed"). Postflight lacks the equivalent deduplication logic. Asymmetry across two agents observing the same signal is a real systemic gap.

## 4. INSTRUCTION proposals queued

**One new INSTRUCTION queued** to `DISPATCH_INBOX.md` (appended, not overwritten):

- `[opportunistic]` — *"Postflight alert deduplication during open INBOX outage tickets"* — proposes the postflight script check for an existing matching `## INSTRUCTION` with `[blocking]` tag before queueing a fresh ALERT for the same symptom. Cites Finding B + outbox line ranges.

**Not queued (already exists):** Railway outage [urgent] — DISPATCH_INBOX.md:140.

**Not queued (out-of-scope for support agent):** the actual Railway billing / redeploy fix — needs user credentials.

## 5. Pending suggestion count: 0

Once production API is restored, this triage should be re-run weekly to drain `bike_suggestions`. Suggest adding a `[research]` INSTRUCTION on day-of-restoration to confirm the `/api/bikes/suggest` endpoint accepts real submissions end-to-end.

---

## Addendum — session 1779330632-637 (re-run, same day)

This report was first authored by an earlier session (1779323436-681) on 2026-05-21. A second
customer-support dispatch fired the same day; this addendum reconciles the new state without
overwriting prior findings.

**Delta since prior triage:**
- ALERT count in DISPATCH_OUTBOX.md is now **23** (was 22). One new ALERT landed at
  line 925 (`2026-05-21T00:50:14+00:00`) — same `Postflight deploy check timed out after 180s`
  body, same Railway 404 root cause. The dedup INSTRUCTION at `DISPATCH_INBOX.md:605` already
  filed by the prior session predicts this — each subsequent session continues to dilute
  signal until the fix lands.
- `bike_suggestions` table still empty. No new triage actions.
- No new INSTRUCTION queued by this session (correctly avoided duplicate of `:605`).

**Confirmation of prior session's work:**
- `DISPATCH_INBOX.md:140` (urgent Railway 404): still open, still blocking, still requires user
  billing action.
- `DISPATCH_INBOX.md:605` (opportunistic dedup): still open, awaiting implementer. Proposed
  `awk` one-liner in line 617 is a 5-minute fix for the next implementer agent.

No DB rows touched. Report finalised by session 1779330632-637.
