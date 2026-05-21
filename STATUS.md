# MotoQuant Status — Live Ledger

> **What this is:** the canonical state of the autonomous-ops system. Updated by every postflight run. Read by every preflight + master scheduler. Reviewed weekly by the self-review agent.
>
> **What this is NOT:** a roadmap doc. See `docs/AUTONOMOUS_OPERATIONS_PLAYBOOK.md` for that.

last_updated: <!-- AUTO-UPDATED -->

---

## North Star — current trajectory

**Target:** $1M valuation by 2026-12-31 (Phase 1) → $10M by 2027-12-31 (Phase 2)

**Current monthly burn:** ~$5/mo (Vercel free tier + Railway Hobby pending) — plenty of runway

**Path mix (rebalance weekly):**
- B2C SaaS ARR — _track Indian organic traffic + signup conversions_
- B2B Pro Studio — _track outreach conversations + closed conversations_
- Acquisition optionality — _track catalog size + benchmarks + B2B pipeline as proof points_

---

## KPIs (refreshed weekly by self-review)

| KPI | Now | Q-end target | Direction | Last-updated |
|---|---|---|---|---|
| Bike catalog count | 349 (commit msg); 342 in DB — mismatch flagged | 500+ by Q4 | ↑ | 2026-05-17 |
| Validated ETs ±0.20s | 47% | 60% Q3 / 70% Q4 | ↑ | 2026-05-04 |
| Benchmark sources | 79 | 100+ | ↑ | 2026-05-04 |
| Indexed pages (motoquant.in) | (TBD) | 50+ Q2 / 200+ Q4 | ↑ | (need GA4) |
| Indian organic sessions/mo | (TBD) | 500 Q2, 5k Q4 | ↑ | (need GA4) |
| Active simulator users/mo | (TBD) | 200 / 2k / 10k cadence | ↑ | (need analytics) |
| Closed B2B conversations | 0 | 1 Q2, 5 Q4 | ↑ | (start outreach) |
| Dragy uploads received | 0 | 1 Q1, 50 Q4 | ↑ | (need users first) |
| Test pass rate (focused) | 100% | 100% always | flat | 2026-05-04 |
| Reference-baseline drift | 0.0000s | 0.0000s always | flat | 2026-05-04 |

---

## Last 7 days — session-level digest

<!-- self-review weekly summary lives here. Updated every Sunday. -->

### Week of 2026-05-10 → 2026-05-17 (self-review M3 — Sunday cadence)

**Dominant signal:** INBOX backlog at 14 unprocessed INSTRUCTIONs (6 from 2026-05-07 aged 10 days, 8 from 2026-05-16 aged 1 day). **Zero items consumed since 2026-05-07.** The proposed remedy — `inbox-implementer` agent at INBOX:427 — is itself queued, not built. Loop is empirically write-only: +15 items queued / 0 consumed since system shipped 2026-05-04. See `reports/self_review_2026-05-17.md` for full Layer 4 attribution.

**Commits 2026-05-10 → 2026-05-17 (7-day window):** 6 commits, all on 2026-05-16. May 10-15 empty (carry-over from the M1-identified dark window). Today's 2026-05-17 has 1.77 hours elapsed since M2 (no other commits yet — this M3 will be the first).

**Catalog:** 343 pushed → 346 (M1 morning, +3) → 349 (M2 evening, +3 Honda). DB ships at 342 — mismatch with declared 349 in commit message. **Flagged for `scripts/audit_headline_stats.py` next session.**

**Tech debt:** A9 ran twice (morning `_TestDB` lift to `tests/_helpers.py`, evening bridge.py TypedDict refactor). Both held; 100% test pass.

**Self-review activity (anomalous):** 3 dispatches in 24h (M1 morning + followup + M2), now M3 on natural Sunday cadence. All produced reports; M1 morning + M2 made the only code changes (`scripts/scheduler_weights.json` weight bumps × 4 single-knob edits across both runs).

**Reference baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — held (Δ +0.0000s).

**Auto-applied this run (M3):** `partnership-outreach.base` 25 → 15. Reason: 20 drafts in `outreach/` since May 8, no SMTP send infra, KPI `Closed B2B conversations` = 0. Demote until either send-pipeline lands or drafts get consumed.

**Inbox queued by M3 (1):** single meta-INSTRUCTION about the 14-deep backlog, with three remediation paths and dependency-ordering for items 322 → 376 → 300 → 341. Avoids adding individual items per the brief's "if dominant signal is M1/M2 queued items still unprocessed, write ONE meta-INSTRUCTION instead".

**Cooldown:** per agent-template `:64` ("Don't run more than one self-review per 5 days"), M3 commits to no further self-review before 2026-05-22.

---

### Week of 2026-05-09 → 2026-05-16 (self-review M1 — inaugural run)

**Dominant signal:** ~7.5-day dark window between last commit `c6670d3` (2026-05-08 23:00 IST) and today's in-flight session. Zero commits May 9 → May 15. Root cause likely a wrapper/cron regression after the three May 7 fixes (CRLF, stdin-redirect, MINGW path translation); no smoke-test caught it because no agent observed the silence — no health-check side-channel exists yet. See `reports/self_review_2026-05-16.md` for full attribution.

**Catalog:** 341 → 343 (May 8) → 346 (May 16, in-flight). +1.46% w/w. On track for Q4 target 500 if cadence holds.

**Content:** 4 blog posts shipped May 8 (KTM 1390, Hero Xtreme 200S 4V, Hayabusa vs ZX-14R, 2T expansion chamber). No new blogs May 9-16.

**Growth experiments:** EXP-001..004 launched as A/B tests but running blind — no GA4/PostHog wired yet. Top-1 standing priority `bootstrap analytics + apply S5 auth-DDL` is still pending after 9 days (tagged `[opportunistic]` in INBOX — severity mismatch with stated priority; flagged in self-review Finding 2.4).

**Partnership outreach:** 20 outreach drafts produced (Pune, Bangalore/Hyderabad, dyno vendors, moto press) but no send infrastructure (no SMTP). Files-only, not conversations.

**Tech debt:** Today's A9 run consolidated `_TestDB` duplicates into `tests/_helpers.py`. Saved a follow-up by verifying that `test_cli.py`'s pattern is intentionally different.

**Reference baselines:** K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s — held perfectly (Δ +0.0000s).

**Auto-applied scheduler changes:** self-review base 50→60, best_dow [7]→[6,7]; added missing claude-feature-monitor entry (base 15, [7]). See changelog field in `scripts/scheduler_weights.json`.

**Inbox queued by M1 (5):** GH-Actions health-check (urgent), standing-priorities → queue_weight rule, outbox truncation fix, motoquant.skill bootstrap, wrapper smoke-test in preflight.

**Follow-up run (evening 2026-05-16, same day):** M1 re-dispatched to audit the URGENT GH-Actions side-channel proposal before any session implements it. Six design tightenings logged in `reports/self_review_2026-05-16_followup.md` Section A (cron cadence 30-min → 6h, curl timeout 10s → 20s, JSON schema additions, side-branch isolation, PAT scope spec, INCIDENT-push race fix). Two new INSTRUCTIONs queued: companion `[urgent]` design-notes block + `[opportunistic]` postflight `_updated`-timestamp fix (current `null` would break the side-channel's staleness check on first cron tick). Total INBOX backlog now 8 self-review items + 6 carry-over from May 7.

---

## Open blockers (resolve before next major sprint)

- (none currently — initial setup of autonomous-ops system in progress)

---

## Currently-paused agents

<!-- self-review auto-pauses agents that fail 3+ runs. They live here until restart. -->

(none)

---

## Capability frontier (tracked by claude-feature-monitor)

- **Models in use:** Sonnet 4.6 (routine), Opus 4.6 (deep), Haiku 4.5 (fast lookups), Gemini 2.5-flash (Railway prod /api/chat)
- **MCP servers connected:** Chrome (browser ops), Workspace bash, Cowork artifact tools
- **Last claude-feature scan:** (never — runs on first Sun)

---

## Auto-applied scheduler weight changes (last 28d)

<!-- self-review logs every weight change here. Reverted within 28 days if it caused regression. -->

- **2026-05-16 M1:** `self-review.base` 50 → 60; `self-review.best_dow` [7] → [6, 7]. Reason: agent never fired on Sun May 10 (the only available Sun in the window since system shipped). Doubling the day-of-week surface area to Sat+Sun gives the loop a second chance against day-weight competition.
- **2026-05-16 M1:** Added `claude-feature-monitor` entry (base 15, best_dow [7]). Reason: missing from the JSON file entirely; agent prompt template exists but scheduler couldn't pick it.
- **2026-05-17 M3:** `partnership-outreach.base` 25 → 15. Reason: 20 outreach drafts produced May 8 but 0 sent, no SMTP wiring exists, KPI `Closed B2B conversations` = 0 after 9 days. Demote until either send infra lands or a downstream agent consumes the drafts. Single-knob change, within ±10 envelope per agent-template policy. Attribution: `reports/self_review_2026-05-17.md` Finding 3.2.

---

## Machine-readable last-run state (DO NOT EDIT BY HAND)

<!-- LAST_RUN_JSON
{
  "_schema": 1,
  "_updated": "2026-05-21T00:47:04Z",
  "catalog-expansion":      { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "physics-calibration":    { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "benchmark-import":       { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "marketing-content":      { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "seo-keyword":            { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "competitive-intel":      { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "product-prioritisation": { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "customer-support":       { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "technical-debt-pass":    { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "performance-monitor":    { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "growth-experiments":     { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "partnership-outreach":   { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "claude-feature-monitor": { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "self-review":            { "date": "2026-05-17", "outcome": "success", "consecutive_fails": 0 },
  "incident-postmortem":    { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "source-verifier":        { "date": null, "outcome": "never_run", "consecutive_fails": 0 }
}
-->

last_run: 2026-05-21T00:47:04Z  <!-- AUTO-UPDATED — used by catchup_detect to decide if we need recovery mode -->
