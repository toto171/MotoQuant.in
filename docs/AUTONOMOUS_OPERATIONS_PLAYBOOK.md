# MotoQuant Autonomous Operations Playbook

> **Mission:** drive MotoQuant Pro to a defensible $1M valuation while the user is at an 8-hour daily internship for one year. The system runs itself, communicates async, self-improves, and only blocks on the user when judgement is genuinely required.
>
> **Scope of this document:** the orchestration design that sits on top of the existing reliability stack (preflight/postflight, dispatch INBOX/OUTBOX, mutex, dual-PAT, 7-subagent code-cleanup). This is the layer that decides *what to do today* and *whether yesterday worked*.

---

## 1. The $1M anchor — what we're actually building toward

Three plausible paths to $1M valuation, ranked by feasibility for an Indian-market drag-racing simulator:

1. **B2C SaaS ARR** — 1,000–5,000 active monthly users at ₹400-1500/mo (≈ $5-18). Hits ~$120k-1M ARR. Multiple of 4-6× ARR → $480k-6M valuation. **Path: SEO-driven content funnel + freemium → Pro upgrade.**
2. **B2B Pro Studio licensing** — 50-150 Indian tuning shops at ₹40k-150k/yr ($500-2k). Hits $25k-300k ARR. Multiple of 6-10× given enterprise stickiness → $150k-3M. **Path: outreach to Pune/Narhe/Bangalore performance shops + tradeshow demos.**
3. **Acquisition exit** — moto OEM, dyno-software vendor (DynoJet/SuperFlow), or motorsports data company buys for the catalog + physics engine + Indian market entry. **Path: ship visibly, get to 10k bikes / 1k uploaded Dragy runs / signed B2B partnerships, become a credible target.**

The autonomous system optimises for **all three simultaneously** because they share the same prerequisites: more bikes, more validated benchmarks, more content, more visibility.

### Quarterly KPIs (committed to STATUS.md, reviewed weekly)

| KPI | Q-end target | Tracking mechanism |
|---|---|---|
| Bike catalog count | +50/quarter (now 336 → 500+ by 2026-Q4) | `motoquant.db` SELECT COUNT |
| Validated ETs (within ±0.20s) | 60% by Q3 / 70% by Q4 | `scripts/validation_sweep.py` JSON |
| Benchmark sources | 100+ instrumented (currently ~74) | `scripts/sweep_with_clusters.py` |
| Indexed pages on Google (motoquant.in) | 50+ by Q2 / 200+ by Q4 | `scripts/agents/seo_audit.md` weekly run |
| Indian organic traffic (sessions/mo) | 500 by Q2, 5k by Q4 | weekly `STATUS.md` ingestion (manual or GA4-API if available) |
| Active simulator users (sessions/mo) | 200 / 2k / 10k cadence | API `/api/health` traffic + Vercel analytics |
| Closed B2B conversations | 1 by Q2, 5 by Q4 | DISPATCH_OUTBOX tagged `[bd]` |
| Dragy uploads received | 1 by Q1, 50 by Q4 | DB `sim_runs` rows tagged `source=dragy` |
| Test pass rate (focused subset) | 100% always | postflight gate |
| Reference baselines drift | 0.0000s always | preflight gate |

---

## 2. The daily 8–12 hour autonomous schedule

The schedule is **dynamic**, not a fixed weekly cron. The master scheduler (`scripts/master_scheduler.sh`) picks the day's work using a 4-input scoring function:

```
score(task) = day_weight(task, dow)
            + queue_weight(task, dispatch_inbox)
            + freshness_weight(task, last_run_status)
            + opportunity_weight(task, market_signals)
```

### Default day weights (replaceable by self-review)

| Day | Primary track | Secondary fill |
|---|---|---|
| Mon | Catalog expansion (new bikes, scraped specs) | SEO content draft |
| Tue | Benchmark validation (sweep + report) | Competitor scan |
| Wed | Physics calibration (per-cluster tuning) | Tech debt pass |
| Thu | Parts catalog refresh + pricing | Customer-support triage |
| Fri | Pricing + retail-adapter refresh | Growth experiments |
| Sat | Test coverage hardening | Hypothesis property tests |
| Sun | Documentation + STATUS.md weekly review | (last Sun) Cleanup subagents |

### Queue weight

Pending `## INSTRUCTION` blocks in DISPATCH_INBOX with severity tags:
- `[urgent]` → +100 (force-promote, bumps the day's primary)
- `[blocking]` → +50, refuse other work until done
- `[opportunistic]` → +10
- `[research]` → +5, runs as a low-priority parallel agent

### Freshness weight

Penalises tasks that ran successfully recently, boosts tasks that haven't run in a while:

```
freshness(t) = clip(days_since_last_run(t) / 7, 0, 2)
```

Bonus: tasks that **failed** their last run get an extra +20 to encourage retry-with-different-approach (but capped at 3 retries before auto-pause and DISPATCH_OUTBOX INCIDENT).

### Opportunity weight

Reads `data/market_signals.json` (refreshed by the daily competitive-intel agent):
- New competitor product launch → spike `seo-keyword` + `competitive-intel` weight
- Indian moto magazine article on drag racing → spike `marketing-content`
- Cycle World published a new instrumented test → spike `benchmark-import`
- Dragy raw upload landed → spike `physics-calibration`

---

## 3. Multi-model routing

Different tasks deserve different cost/quality tradeoffs. The scheduler annotates each dispatched agent call with a model preference:

| Task type | Model | Why |
|---|---|---|
| Architecture decisions, code review of >500 LOC change, ambiguous research synthesis | **Opus** | Deep reasoning justifies token cost |
| Routine code work (most of it: bike adds, parts catalog, test edits, doc writes) | **Sonnet** | Best code/cost ratio |
| Lookup, status check, simple edit (<20 LOC), spec fetch | **Haiku** | Fast + cheap |
| Long-context summarisation (50+ benchmarks, big logs) | **Sonnet 200k** | Need the context window |
| Drafting marketing copy, blog posts, persuasive content | **Opus once / iterate with Sonnet** | Quality compounds for content |
| Customer-support triage / classification | **Haiku** | Volume, simple decisions |
| `/api/chat` user-facing inference | **Gemini Flash 2.5 (Render env)** | Cheapest viable; non-blocking |

The model preference is a hint, not a hard constraint. If the chosen model is unavailable (rate-limited, etc.), the agent falls back through the priority list with a note in DISPATCH_OUTBOX.

---

## 4. Agent specialisations

Beyond the existing 7 cleanup subagents (`scripts/subagents/`), we add 12 production agents under `scripts/agents/`. Each has a self-contained prompt template, a defined deliverable, and a defined cadence.

| # | Agent | Cadence | Deliverable |
|---|---|---|---|
| A1 | **catalog-expansion** | Mon | +1-3 bikes added to `known_bikes_extended.py`, validator-clean |
| A2 | **physics-calibration** | Wed (or on-demand after Dragy upload) | Per-cluster knob adjustment + validation report |
| A3 | **benchmark-import** | Tue | New entries to `BENCHMARKS` from researched sources |
| A4 | **marketing-content** | Mon/Fri | One blog post draft in `web/app/blog/<slug>/page.js` |
| A5 | **seo-keyword** | Mon | Keyword opportunities + on-page changes for `web/app/` |
| A6 | **competitive-intel** | Tue | `data/competitive_landscape.md` updated |
| A7 | **product-prioritisation** | Thu | Re-rank Phase 6/7 carry-forward in CLAUDE.md |
| A8 | **customer-support-triage** | Thu | Process bike_suggestions table; flag/respond |
| A9 | **technical-debt-pass** | Wed (alt weeks) | Targeted refactor PR, narrow scope |
| A10 | **performance-monitor** | Sun | Lighthouse + Render latency check; report drift |
| A11 | **growth-experiments** | Fri | One A/B-able UI tweak or copy variant |
| A12 | **partnership-outreach** | Fri (every 2 weeks) | Drafted email templates for Indian tuning shops + dyno vendors |

Plus the existing 7 cleanup subagents (S1-S7) running monthly.

Plus 2 meta-agents:
| # | Agent | Cadence | Deliverable |
|---|---|---|---|
| M1 | **self-review** | Sun | STATUS.md weekly digest + schedule-weight adjustments |
| M2 | **incident-postmortem** | On INCIDENT | Root-cause analysis appended to OUTBOX |

---

## 5. Self-improvement loop

Every Sunday, agent **M1 (self-review)** runs:

1. Read STATUS.md, last 7 days of OUTBOX entries, last 7 days of git log.
2. Score each task type: did it produce a committed delta? Did the delta pass tests? Did it move a tracked KPI?
3. If a task type has 3+ consecutive null-result runs, **propose** demoting its weight in the master scheduler (writes an INSTRUCTION block to DISPATCH_INBOX for user approval).
4. If a task type has 3+ consecutive wins, propose promoting its weight.
5. If a market signal (from A6 competitive-intel) suggests a new opportunity, propose adding a one-off task.

Self-review never auto-applies high-impact changes — it stages them in INBOX with `[self-review]` tag, so the user sees the proposal at end-of-day and can ack with `ok`, deny with `reject`, or modify.

For low-impact mechanical adjustments (e.g., "swap two adjacent days' priorities"), self-review can auto-apply with a note in OUTBOX.

---

## 6. Error detection + auto-pause

The system is allowed to fail individual sessions, but never silently or repeatedly:

| Symptom | Detection | Action |
|---|---|---|
| Baseline drift (K5/R1/Hayabusa Δ > 0.005s) | Preflight gate | Exit 3, INCIDENT in OUTBOX, do not push |
| Focused tests fail | Postflight gate | Exit 3, INCIDENT, no push |
| 2 consecutive INCIDENTs of same type | Self-review at next run | Auto-pause that task type, INBOX `[blocking]` for user |
| Deploy verification timeout | Postflight | Soft ALERT, push still landed |
| Backup PAT used | Preflight | ALERT in OUTBOX |
| `/sessions` disk > 95% | Preflight | Auto-prune `/tmp/mq-session-*` then retry; INCIDENT if still full |
| Mutex held by stale (PID dead) session | Preflight | Auto-claim |
| Bike count regression on Render | Postflight `/api/health` | INCIDENT, halt next session, alert |
| 3 consecutive null-delta sessions | Self-review | Promote a different task type for next 7 days |
| Test pass rate < 95% on weekly check | Self-review | Inject `[blocking]` test-fix INSTRUCTION |

Auto-pause is implemented via a `paused.flag` file at `/tmp/.motoquant-secrets/paused.flag` (NOT in repo). When present, preflight exits clean with a "PAUSED" message in OUTBOX. The user un-pauses by deleting the flag (one mobile-dispatch shortcut).

---

## 7. Mobile dispatch shorthand

The user has a Claude mobile app. Editing markdown there is workable but full INSTRUCTION blocks are tedious. We add a shorthand DSL the system parses:

```
## MOBILE — 2026-05-15 — 14:30
ship                                        # = "process inbox + commit + push if anything queued"
pause                                       # creates paused.flag
unpause                                     # removes paused.flag
rerun yesterday                             # re-execute yesterday's primary task
rerun catalog                               # re-execute next 'catalog-expansion' task immediately
add bike <make> <model> <year>              # queue a [urgent] catalog INSTRUCTION
investigate <topic>                         # queue a [research] INSTRUCTION
+1 <agent_name>                             # bump that agent's weight by +10 for 7 days
-1 <agent_name>                             # cut weight by -10 for 7 days
status                                      # post current STATUS.md to OUTBOX
incident <text>                             # raise an incident manually
```

`scripts/mobile_dispatch_handler.sh` parses any `## MOBILE — YYYY-MM-DD — HH:MM` block, expands shorthand into proper INSTRUCTION blocks, then deletes the MOBILE block. Idempotent.

---

## 8. Single master entry-point

```bash
bash scripts/START.sh            # Run by your scheduled task or manually
```

That's it. START.sh internally:

1. Sources environment from `~/.motoquant-secrets/git-creds.env` (with sandbox fallback).
2. Runs `scripts/session_preflight.sh`.
3. If preflight clean: runs `scripts/master_scheduler.sh` to pick today's plan.
4. Dispatches the chosen agent(s) — for autonomous Claude Code mode, this means the calling Claude session reads scheduler stdout and executes.
5. Runs `scripts/session_postflight.sh` with the file-list + commit-message produced by the agents.
6. Writes daily STATUS.md update + OUTBOX entry.
7. Releases mutex.

Total wall-clock: ~30-90 minutes per session depending on scope. Designed to fit comfortably in an 8-12 hour Claude Code budget per day if scheduled hourly, or as a single big nightly run.

---

## 9. What the user does

While you're at the internship:

- **Nothing required.** The system runs without you.
- **If you want to nudge:** open Claude mobile, edit `DISPATCH_INBOX.md`, add a `## MOBILE — <date> — <time>` block with shorthand. Save (commits via the GitHub mobile app or whatever editor you use). Next scheduled run picks it up.
- **End of day:** scroll DISPATCH_OUTBOX.md to see the daily session block. Look for `### ALERT` or `## INCIDENT`.

If you have an hour at home:

- Read `STATUS.md` for the weekly view.
- Resolve any pending `[self-review]` INSTRUCTION blocks (one-tap `ok` / `reject`).
- If something needs your judgement (an `## INCIDENT`), handle it.

If you're truly absent for a week:

- The system pauses itself after 3 consecutive INCIDENTs.
- Self-review's auto-applied schedule changes are conservative and reversible.
- Worst case: `bash scripts/START.sh --reset` resets weights to defaults and clears the pause flag.

---

## 10. What ships v1 vs what's on the iteration list

**Ships in this session (v1, today):**

- `docs/AUTONOMOUS_OPERATIONS_PLAYBOOK.md` (this file)
- `scripts/master_scheduler.sh`
- `scripts/agents/` directory with skeleton prompts for 12 agents
- `STATUS.md` initial file with KPI section + ledger format
- `scripts/self_review.sh` (M1)
- `scripts/mobile_dispatch_handler.sh` + INBOX template update
- `scripts/START.sh` master entry-point
- CLAUDE.md update with the standing autonomous-ops note

**v2 iterations the system will propose to itself over weeks:**

- Real GA4 / Plausible integration (replace manual STATUS.md traffic input)
- Lighthouse CI integration for performance-monitor (currently manual)
- Real Reddit/forum scraping for competitive-intel (currently web search only)
- Email automation for partnership-outreach (currently drafts only — user sends manually)
- Tighter Bayesian scheduler weight tuning

**v3 iterations gated on real-money signals:**

- Razorpay subscription wiring (gated on first 10 paying B2C sign-ups via beta)
- Dyno data partnerships (gated on first 5 closed Indian shop conversations)
- Mobile-app version of the simulator (Tauri can target Android with Tauri 2.x but it's a real lift)
- Multi-language: Hindi + Tamil + Telugu landing pages (gated on Indian organic traffic > 5k/mo)

The system **is allowed to upgrade itself** along the v2 path (any agent can write a self-improvement INSTRUCTION block). v3 changes require explicit user approval before any code lands.

---

## Key principle

**Bias toward shipping observable improvements.** Every session should produce either: (a) a committed delta to the codebase/site, (b) a populated row in a dataset, (c) a research output that materially informs the next decision. Sessions with no delta count as null and trigger the freshness-weight retry-with-different-approach behaviour.

The fastest way to $1M is the boring way: more bikes, more content, more validation, more visibility. Autonomous systems are good at the boring way. This playbook is designed to make that easy.
