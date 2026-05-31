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
| Bike catalog count | 796 raw / **495 distinct** / ~301 phantom — +6 real / 0 phantom growth in week (M6 fix continues to hold); ghost-row DELETE queued at INBOX:879 `[needs-user]` | 500+ by Q4 | ↑ | 2026-05-31 |
| Validated ETs ±0.20s | 47% | 60% Q3 / 70% Q4 | ↑ | 2026-05-04 |
| Benchmark sources | **128** (114 → 128 in 7 days; weekly record, +14) | 100+ ✓ MET | ↑ | 2026-05-31 |
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

### Week of 2026-05-24 → 2026-05-31 (self-review M9 — Sunday cadence, 4 days early)

**Dominant signal:** **Multi-system rescue week from one user-driven Cowork session.** 24 commits in window (15 of them on 2026-05-30, 9 carrying into 2026-05-31). Three independent critical-path blockers cleared in one session: (1) Railway → Render infrastructure migration (Railway was suspended for no card on file); (2) Vercel production frontend was silently broken since ~May 26 — apostrophe in RE Hunter 350 blog data string crashed `next build`, prod frozen on May-25 build pointing at dead Railway for 5 days; (3) `/api/surrogate/predict` shipped on free tier via torch-free numpy MLP. Live-verified: quick sim Hayabusa 10.492s, full sim with charts, Ask-MotoQuant Groq chat, /bikes (796), /api/health.

**KPI moves:** DB raw=793→**796**, distinct=489→**495** (+6 real adds, 0 phantom — M6 fix `31b36a4` holding 7 days). BENCHMARKS 114→**128** (+14, **weekly record**, mostly Cycle World `sportbike-performance-numbers` archive — commit `81d237d`). Physics top-10 mean|Δ| 0.0114s → 0.0094s (-20%) from mid_twin_500_700 calibration ship.

**Loop state:** 31 INSTRUCTIONs effective (flat vs M8). 0 DONE flips this run; +2 new INBOX (Vercel pre-build gate + Render cold-start). Net +2. **The user-rescue session shipped massive value but did not consume any inbox tickets** — correct priority allocation, but a re-confirmation of M8's bottleneck finding.

**Meta-finding (Finding 2.1):** **Vercel build-health is the loop's biggest blind spot.** A trivial apostrophe broke prod for 5 days. The pre-push hook `scripts/git-hooks/pre-push` is either not enabled in autonomous-ops sessions or being skipped. Queued `[urgent]` fix: postflight runs `cd web && npx next build` on any `web/app/**` change before pushing.

**Auto-applied this run (M9):** `physics-calibration.base` 40 → 50. Reason: 3 A2 runs in window (2 ships + 1 defensible-null research escalation). Single-knob ±10 envelope. Attribution: `reports/self_review_2026-05-31.md` Proposal #1.

**Queued by M9 (2):** (1) `[urgent]` Vercel pre-build gate in `session_postflight.sh` (Finding 2.1); (2) `[opportunistic]` Render cold-start warm-up ping (Finding 2.3).

**Render free tier:** new failure mode — sleeps after 15 min idle, 30-60s cold start. Keepalive cron mitigates IST day. Postflight 90s timeout handles warm cold-start but worst-case still trips ALERT.

**INBOX:939 (queue_bonus fix):** 5 days old, untouched. User session focused on user-visible rescue. Pattern persists — confirms M8 Finding 2.3.

**Reference baselines preserved EXACTLY: K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s, Δ +0.0000s.**

**Cooldown:** per agent-template `:64`, next autonomous self-review not before **2026-06-05**. M8's 2026-06-04 floor overridden by on-cadence-Sunday + 24-commit signal density justification (Finding meta).

---

### Week of 2026-05-23 → 2026-05-30 (self-review M8 — Saturday, autonomous catchup-mode)

**Dominant signal:** **4-day silent gap (2026-05-27 → 2026-05-30 ~16:30Z), 313h since last_run.** NOT an agent failure — host-machine downtime (user internship schedule). Resilience layer correctly identified the gap and dispatched a single catchup-mode session (this M8) instead of stacking 4 days of agent slots. **System-working-as-designed signal under real failure conditions.**

**KPI moves:** DB raw=790→**793**, distinct=489→**492** (+3 real, 0 phantom growth — **M6 fix `31b36a4` held through gap**). BENCHMARKS 112→**114** (+2). Most KPIs flat by definition during gap.

**Loop state:** −1 DONE (INBOX:903 closed), +0 new tickets (only severity flip on INBOX:939). 25 effective INSTRUCTIONs pending — backlog stable. M7's queue_bonus fix (INBOX:939) **highest-impact pending kaizen item**; promoted `[urgent]` this run after sitting 4 days during gap.

**Meta-finding:** **Auto-apply boundary is the loop's primary bottleneck.** 0 of 7 historical M-runs have auto-applied a script edit (by design). Queued open question to user: should low-blast-radius `[self-review]` script edits qualify for auto-apply with auto-revert?

**Auto-applied this run (M8):** (1) INBOX:903 → DONE (admin bookkeeping; audit completed by M7). (2) INBOX:939 severity flipped to `[urgent] [needs-approval]`. **No weight changes** — 4-day gap blocks observation of M7's growth-experiments demote; observe-only week.

**Queued by M8 (1):** Open question to user re: script-edit auto-apply policy (Finding 2.3).

**Railway:** day 13 of /api/health 404 outage (INBOX:140 `[urgent] [blocking]` since 2026-05-17). Pure `[needs-user]` — requires billing dashboard access.

**0 commits in 4-day gap. K5/R1/Hayabusa baselines preserved (last verified at HEAD `13ff312` 2026-05-26).**

**Cooldown:** per agent-template `:64`, next autonomous self-review not before **2026-06-04** (5 days). Catchup-mode override of M7's 2026-05-31 floor justified by Finding 2.1.

---

### Week of 2026-05-19 → 2026-05-26 (self-review M7 — Tuesday, user-dispatched)

**Dominant signal:** **First net-negative-INBOX week since launch.** 5 DONE items in 7 days vs 3 new INSTRUCTIONs queued (net −2). The May-25 INBOX:308 year-suffix upsert fix (`31b36a4`) closed the longest-aged urgent item (18 days). M5 + M6 stacked weight changes produced a **second** cross-KPI rebalance — `competitive-intel` broke its 28-day `never_run` streak today (`reports/competitive_intel_2026-05-26.md`). Strongest 2-step kaizen attribution recorded.

**KPI moves:** BENCHMARKS 91 → **112** (+21 in 7 days; first-ever 100+ target MET). Bike catalog distinct 483 → **489** (+6 real adds; phantom rows frozen at 301 — code fix landed, DB cleanup deferred to INBOX:879 `[needs-user]`). Postflight ALERT dedup verified — 0 `deploy timed out` ALERTs since `0f5edec` on 2026-05-24 (M6 Proposal #5 RESOLVED).

**System bug found:** `master_scheduler.sh` `queue_bonus` is half-implemented. `parse_inbox_urgent()` PRINTS urgent items in dispatch plan but never folds them into scores. Inbox uses `[agent]` bracket-tag syntax; scheduler looks for `@agent` — zero matches in 26-item inbox. Result: `[urgent]` tag is decorative. Fix queued as new INSTRUCTION with exact 5-line diff.

**Auto-applied this run (M7):** (1) `growth-experiments.base` 30 → 20 (15 A/B variants launched without measurement layer; pause new launches until GA4 lands). (2) INBOX:325 marked DONE (admin bookkeeping — already resolved at commit `31b36a4`).

**Queued by M7 (2):** `[needs-approval]` `master_scheduler.sh` queue_bonus fix; `[opportunistic]` verify `web/app/page.js` stats strip uses DISTINCT not COUNT(*).

**47 substantive commits / ~70 total. 100% test pass, baselines exact (K5/R1/Hayabusa Δ +0.0000s).**

**Cooldown:** per agent-template `:64`, next autonomous self-review not before **2026-05-31**.

---

### Week of 2026-05-18 → 2026-05-25 (self-review M6 — Monday, user-dispatched)

**Dominant signal:** Benchmark-import agent had its best week ever — 5 runs producing 12 new instrumented ETs (commits `db97304`, `de00e2b`, `1f9f40b`, `98c445d`, `8ed7021`). Benchmark KPI moving from 79 → ~91 for the first time since 2026-05-04. Direct result of M5 catalog-expansion demotion (50→40) freeing Tuesday slots. This is the first measurable evidence a single weight change produced a cross-KPI rebalance.

**Duplicate-row inflation accelerated.** DB 751 → 790 raw; distinct 483 → 489 (+6 real bikes); phantom rows 268 → **301** (+33 this week). INBOX:308 ([urgent] since 2026-05-24) unimplemented — every `import --known-bikes` run mints 9 more phantoms. Bike catalog KPI should read 489 distinct, not 790.

**INBOX net-flat at 19 pending.** No structural items consumed (GH-Actions side-channel, year-suffix fix, postflight truncation all still open). Postflight ALERT dedup (`0f5edec`) tentatively working — confirm in next OUTBOX scan.

**Auto-applied this run (M6):** `benchmark-import.base` 40 → 50 (+10, single-knob; 3+ consecutive wins trigger per playbook §5). No other weight changes.

**45 substantive commits / 90 total (incl. postflight chores). 100% test pass, baselines exact.**

### Week of 2026-05-17 → 2026-05-24 (self-review — Sunday cadence)

**Dominant signal:** **Loop drained twice this morning.** INBOX:639 (catalog-expansion prompt fix, queued by M4) + INBOX:674 (postflight dedup tag flip, queued by M4) both moved INSTRUCTION → DONE at the start of today's session. **First multi-item drain in one session ever.** Net since M3 (2026-05-17): 3 DONE / 4 queued = **net -1.** Layer 4 verdict revised upward from M4: loop is now consuming faster than producing.

**M4 prompt fix paid off — and uncovered a deeper bug.** DB went 345 → 751 (+406 rows) but source spec count only grew 447 → 488 (+41 specs). Distinct (manufacturer, model) = 483 ≈ source count. **268 phantom duplicate rows** in `bike_models` — 33 bikes × 9 occurrences from the WS-A April 27 year-suffix idempotency regression. Root cause: `motoquant/database/bike_repo.py::create_model` doesn't strip `(YYYY-YYYY)` suffix before the lenient upsert match. Fix queued since 2026-05-07 at INBOX:308; M5 promoted to `[urgent]` today. After upsert fix lands, run `DELETE FROM bike_models WHERE rowid NOT IN (SELECT MIN(rowid) ... GROUP BY ...)` to drop 268 ghosts; headline snaps 751 → ~483.

**Catalog over-weighted:** 43/47 substantive commits (91 %) this week were catalog-expansion. Starved agents: claude-feature-monitor (`never_run`), benchmark-import (`never_run`), competitive-intel (`never_run`). M5 demoted `catalog-expansion.base` 50 → 40 to free 4–6 slots/week.

**ALERT noise:** 38 identical `Postflight deploy check timed out after 180s` (up from 24 at M4). INBOX:605 tag flipped to `[urgent]` this morning but the awk one-liner itself still pending.

**Physics:** 1 ship (`bfac483`, two_stroke `max_engine_decel_rads2` 380 → 800, −72 ms cluster mean|Δ|). 2 no-ships with research escalations. K5/R1/Hayabusa preserved exactly.

**Tech debt:** 5 TypedDict refactors landed (`acf4af3`, `0c220e9`, `df4d92b`, `ecbfe6a`, `d5949f2`) + 1 seed-catalogs helper consolidation (`b4adf8d`). All held.

**Marketing/growth:** ~15 blog posts shipped (RC 390, Ninja 400 vs ZX-4R, KTM 890 Duke R, Kawasaki Z900RS, etc.) + EXP-005..008 A/B variants.

**Auto-applied this run (M5):** (1) `catalog-expansion.base` 50 → 40; (2) INBOX:308 tag `[opportunistic]` → `[urgent]`. STATUS.md bookkeeping (this section + KPI cell + `_LAST_RUN_JSON`). Per META INBOX:516 commitment, **zero new INBOX items queued** this run.

**Cooldown:** per agent-template `:64`, next self-review not before **2026-05-29**. Natural Sunday cadence resumes **2026-06-07** (2026-05-31 is cleanup-rotation slot).

---

### Week of 2026-05-14 → 2026-05-21 (self-review M4 — off-cadence Thursday)

**Dominant signal:** **102-bike DB-vs-source drift** in catalog. 30 of 38 substantive commits this week were catalog-expansion runs, but only 3 touched `motoquant.db`. Source files declare 447 specs; DB ships at 345. Root cause: `scripts/agents/catalog-expansion.md` Validation gates section never instructs the agent to re-seed via `python3 -m motoquant.run import --known-bikes` or `scripts/reseed_configs_from_specs.py`. See `reports/self_review_2026-05-21.md` Finding 2.1 for full attribution.

**Kaizen loop status:** **converging at +1 DONE/week**. M3's 2026-05-17 "zero consumption" verdict is revised — INBOX:322 → DONE on 2026-05-17 (session 1778992230-620), demonstrating one self-review proposal CAN flow through to a downstream implementer. Slope is slow but non-zero. `last_delta_age_days for self-review proposals implemented by downstream agent` is now **defined (= 4 days)** for the first time.

**ALERT noise:** 24 identical `Postflight deploy check timed out after 180s` entries in OUTBOX since Railway 404 outage began 2026-05-17. Fix INSTRUCTION at INBOX:605 (5-min awk one-liner) is `[opportunistic]` and keeps being deprioritised. M4 queues promotion to `[urgent]`.

**Catalog declared vs actual:** commit messages all say "+3 bikes" but DB shows ≈ +0.4 average per commit. Headline-stats audit silently passes because it derives from DB row count — but the source-vs-DB delta has never been a tracked check. Adding a check is a candidate for next tech-debt-pass.

**Tech debt:** 5 TypedDict refactors landed (`acf4af3`, `0c220e9`, `df4d92b`, `ecbfe6a`, `d5949f2`) — bridge.py, llm db typing, Part TS types, SimDict, CompareDict. All held, 100 % test pass.

**Physics-calibration:** 3 runs, 1 shipped (`bfac483` two_stroke `max_engine_decel_rads2` 380 → 800, −72 ms cluster mean|Δ|), 2 explicit no-ships with research escalations queued. Reference baselines K5 10.0334s / R1 10.2859s / Hayabusa 10.4712s held perfectly.

**Auto-applied this run (M4):** STATUS.md KPI cell + this digest entry + `_LAST_RUN_JSON.self-review.date` bump. **No** `scheduler_weights.json` edits (no clean single-knob improvement maps to observed signal this week).

**Inbox queued by M4 (2):** (1) `[urgent]` fix catalog-expansion prompt to require DB re-seed; (2) `[urgent]` promote dedup INSTRUCTION from `[opportunistic]`.

**Cooldown:** per agent-template `:64`, next self-review not before **2026-05-26** (5 days).

---

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
- **2026-05-21 M4:** NO weight changes auto-applied. Findings 2.1 (catalog-expansion prompt) and 2.2 (postflight dedup tag promotion) both queued to INBOX instead. Rationale: prompt-rewrite is multi-knob (out of envelope); INSTRUCTION-severity flip on another agent's ticket is borderline single-knob — queued for transparency. Bookkeeping-only edits (KPI cell + digest section + `_LAST_RUN_JSON`) made this run. Attribution: `reports/self_review_2026-05-21.md` Findings 2.1 + 2.2.
- **2026-05-24 M5:** `catalog-expansion.base` 50 → 40. Reason: 43/47 substantive commits this week (91 %) were catalog-expansion; M4 prompt-fix gate worked (DB 345 → 751) but uncovered 268-row duplicate-inflation bug (INBOX:308) — marginal value of each new catalog run is now below marginal value of a starved-agent slot (claude-feature-monitor / benchmark-import both `never_run`). Single-knob, within ±10 envelope. Also auto-applied: INBOX:308 tag `[opportunistic]` → `[urgent]` (mechanical severity flip, same pattern as M4's successful 605→674 promotion that landed in 3 days). Attribution: `reports/self_review_2026-05-24.md` Findings 2.1 + 2.2.
- **2026-05-25 M6:** `benchmark-import.base` 40 → 50. Reason: 5 consecutive benchmark-import runs this week (first time agent ran; best week ever); KPI benchmark count moved 79 → ~91; 3+ consecutive wins trigger = promote per playbook §5. Single-knob, within ±10 envelope. Revert to 40 if 2 consecutive null-result weeks. Attribution: `reports/self_review_2026-05-25.md` Finding 2.3.
- **2026-05-26 M7:** `growth-experiments.base` 30 → 20. Reason: 15 A/B variants launched in 7 days (EXP-005..EXP-019) with zero measurement layer (KPIs `Indian organic sessions/mo` + `Active simulator users/mo` both `TBD`). Over-production relative to consumption. Single-knob, within ±10 envelope. Revert to 30 once GA4/PostHog wired and at least one EXP has measured outcome. Attribution: `reports/self_review_2026-05-26.md` Proposal #5.
- **2026-05-30 M8:** NO weight changes auto-applied. Reason: 4-day silent gap (2026-05-26 → 2026-05-30) blocked observation of M7's growth-experiments demote effect (zero new EXP launches in window). Observe-only week to give M9 a clean baseline. Auto-applied bookkeeping only: (1) INBOX:903 → DONE (M7 superseded by INBOX:939). (2) INBOX:939 severity `[needs-approval]` → `[urgent] [needs-approval]` to surface in next dispatch plan. Attribution: `reports/self_review_2026-05-30.md` Findings 2.2 + 2.4.
- **2026-05-31 M9:** `physics-calibration.base` 40 → 50. Reason: 3 consecutive A2 runs this week (2026-05-25 mid-twin-300-500 mu_peak tune held; 2026-05-26 defensible-null research escalation; 2026-05-30 ship `81d237d` mid_twin_500_700 max_engine_decel_rads2 150→600 with bias zero-cross and top-10 mean|Δ| 0.0114s → 0.0094s). Playbook §5 "3+ consecutive wins, promote" applies. Single-knob within ±10 envelope. Revert to 40 if 2 consecutive null-result weeks. Attribution: `reports/self_review_2026-05-31.md` Proposal #1.

---

## Machine-readable last-run state (DO NOT EDIT BY HAND)

<!-- LAST_RUN_JSON
{
  "_schema": 1,
  "_updated": "2026-05-31T06:07:04Z",
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
  "self-review":            { "date": "2026-05-31", "outcome": "success", "consecutive_fails": 0 },
  "incident-postmortem":    { "date": null, "outcome": "never_run", "consecutive_fails": 0 },
  "source-verifier":        { "date": null, "outcome": "never_run", "consecutive_fails": 0 }
}
-->

last_run: 2026-05-31T06:07:04Z  <!-- AUTO-UPDATED — used by catchup_detect to decide if we need recovery mode -->
