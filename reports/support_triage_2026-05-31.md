# Support triage — 2026-05-31

**Agent:** customer-support
**Session workdir:** `/tmp/mq-session-1780216247-642/repo`
**HEAD at start:** `b87a251` (fix(catalog): de-dupe bikes 796->495 + idempotent imports)

## bike_suggestions triage

**Table state:** present (schema intact: 15 cols), **0 total rows**. The table has been empty on every triage run to date (May-7, May-21, May-24, May-25, and now May-31). Six weeks live, zero user submissions.

Per workflow step 3, fell back to outbox-scan.

---

## Outbox scan, alert analysis

**Window scanned:** full `DISPATCH_OUTBOX.md` (1995 lines), May 17 through May 31 2026.

**Alert counts by category (last 30 days):**

| Category | Count | Date range |
|---|---|---|
| `Postflight deploy check timed out after 180s` | 40 | May-17 to May-24 |
| `self-review M6 auto-applied weight change` | 1 | May-25 |
| **Total** | **41** | |

**Key changes since May-25 triage:**

1. **The 40-alert Railway-timeout cluster is now fully resolved.** The 2026-05-31 Cowork-chat session (outbox line 1839) migrated production off Railway (suspended, no card) onto Render free tier at `motoquant-api.onrender.com` (Singapore, Docker). The blocking ticket from `DISPATCH_INBOX.md:140` (open 14 days) is closed by infrastructure substitution rather than Railway billing. Quick-sim, full-sim, chat, /bikes, /api/health all verified live; baselines exact (K5 10.0334 / R1 10.2859 / Hayabusa 10.4712).

2. **Second build-freeze root cause discovered and fixed during the same migration session.** Every Vercel production deploy had silently failed since ~May 26 because of an unescaped apostrophe in a single-quoted data string in the RE Hunter 350 blog post. Production had been frozen on the May-25 build the entire time, pointing at the dead Railway URL. The grep confirmed it was the only such bug in `web/app`. Patched, deployed, verified live.

3. **No new alert categories since May-25.** The self-review weight-change alert has not fired again. The postflight `_blocking_ticket_open()` dedup helper (commit `0f5edec`, May-24 08:39) plus the Render migration together close the alert-noise loop.

---

## Top-3 systemic fixes proposed

### 1. (High priority) Wire the /api/bikes/suggest endpoint into a postflight smoke test

The May-25 triage proposed this and it remains the highest-value open item. Now that Render is live and Vercel is unfrozen, the conditions for it are met. Without a smoke test, the table will keep showing zero rows on every future triage run and we cannot distinguish "no users" from "form is broken". Estimated work: about 30 minutes. Add a POST then 200 then DELETE cycle to `scripts/session_postflight.sh` gated on `/api/health` returning ok.

**Queue as `[opportunistic]` INSTRUCTION,** see queued block below.

### 2. (Medium priority) Add a visible "Request a bike" CTA on /bikes and /simulator

Six weeks of zero submissions through `POST /api/bikes/suggest` is a discoverability finding, not a backend finding. The `SuggestBikeForm` component exists in `web/components/` but the only path that surfaces it is the empty-state on a filtered `/bikes` search that returns zero results, a rare event with a 796-bike catalog. A header-strip CTA on `/bikes` plus an inline "Don't see your bike?" prompt below the simulator's BikePicker would likely produce the first submissions.

**Queue as `[opportunistic]` INSTRUCTION for the landing-marketing or content agent.**

### 3. (Low priority) Schedule a one-time `bike_suggestions` table verification after Render warm-up

Because Render free tier sleeps after inactivity, the first POST to `/api/bikes/suggest` after a long idle period may 502 while the container spins up. The keepalive workflow (`.github/workflows/keepalive.yml`, mentioned in the migration session log) should mitigate this but has not been verified end-to-end against the suggestion submit path specifically. One scripted submission per week from a GitHub action would both keep the table populated with at least one synthetic test row and confirm the path is alive.

**Defer for now,** gather one week of live keepalive metrics first before adding more scheduled traffic.

---

## Escalations to the user

1. **Render keepalive verification.** The Render migration session noted `keepalive.yml` was committed but did not explicitly confirm it has run yet against the new endpoint. After 24h, check the GitHub Actions log for `keepalive` workflow runs and confirm 200s. If any 502 or timeout shows up, the free-tier cold-start is biting.
2. **The bike_suggestions table has now been empty for six weeks across five triage runs.** With Vercel and Render both healthy, the next two weeks will be the cleanest natural experiment yet on whether the suggest endpoint gets any organic traffic at all. If it stays empty through June 14, fix #2 above (visible CTA) becomes the only remaining option.

## INBOX queue

One `[opportunistic]` INSTRUCTION queued, see `DISPATCH_INBOX.md` head for "Wire bike-suggest smoke test into postflight".

## Baseline verification

K5 10.0334 / R1 10.2859 / Hayabusa 10.4712, preserved exactly. No physics or catalog files touched in this triage.
