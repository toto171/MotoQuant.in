# Product Priorities — 2026-05-21 (Thursday weekly re-rank)

**Agent:** product-prioritisation (A7).
**Prior report:** `reports/product_priorities_2026-05-07.md` (3-pass, top-1 = analytics bootstrap + S5 DDL).
**Window scanned:** 2026-05-07 → 2026-05-21 (14 days).

---

## TL;DR

**Top-1 changes this week.** New top-1 is **restore Railway service + redeploy** — a `[blocking]` infra dependency, not a product item, but until it is cleared every other Phase 6/7 item is non-actionable. The previous top-1 (analytics + S5 auth DDL) drops to **#2** because applying DDL to a dead service is wasted work, and analytics has nothing to instrument while the simulator is 404.

Phase 6 product re-ranking below assumes Railway comes back online inside the next 7 days. If it does not, the agent will re-dispatch and propose an alternate hosting plan (Fly.io / Hetzner) as a `[blocking]` item.

---

## Signals consumed this week

| Source | Status | Delta vs 2026-05-07 |
|---|---|---|
| `STATUS.md` KPIs | All user-facing rows still `TBD` | Unchanged. Catalog KPI now reads "345 in DB / 447 in source — +102-bike re-seed gap" — new tracked failure mode. |
| `data/competitive_landscape.md` | **STILL ABSENT** | INSTRUCTION queued 2026-05-07 has not been consumed in 14 days. Competitive-intel agent has `_LAST_RUN_JSON.date: null`. |
| `bike_suggestions` table | 0 rows | Unchanged. Cannot use as signal. |
| `DISPATCH_OUTBOX.md` | **27 identical Postflight 180s deploy-check timeout ALERTs** since 2026-05-17 (verified end-of-day 2026-05-21) | Dominant signal — Railway 404 for 4+ days. |
| `DISPATCH_INBOX.md` | INBOX:140 `[urgent] [blocking]` Railway 404 — still open, blocked on user billing | Posted 2026-05-17, unprocessed (user action required). |
| `motoquant.db` S5 tables | All 5 still absent (`users`, `sessions`, `subscriptions`, `license_keys`, `magic_links`) | Unchanged in 14 days. Confirmed via direct sqlite3 read end-of-day 2026-05-21. |
| `motoquant.db` row counts | **488 bikes** / 232 tires / 563 parts / 861 fitments / 20 venues (end-of-day check) | +149 bikes vs morning re-rank (multiple catalog-expansion sessions today closed most of the source-vs-DB gap). |
| Source spec files | `ALL_KNOWN_BIKES` 452 + `EXTENDED_BIKES` 127 = **579 specs declared in source** | Remaining DB-vs-source delta: **91 bikes** (was 102 this morning). Re-seed gap narrowing but not closed. |
| self-review M4 (2026-05-21) | Confirmed loop is converging at +1 DONE/week but Railway is binary-down | New attribution path for the re-seed gap. |

**Dominant signal — different from last week:** infrastructure outage. Last week the dominant signal was "no KPI numbers exist". This week it is "the *service that would generate the numbers* is offline". Different bottleneck, different top-1.

**Secondary signal:** the kaizen loop is no longer purely write-only (+1 DONE since 2026-05-17), but at +1/week consumption rate the existing 14-item backlog will take 14 weeks to clear without intervention.

---

## Re-scoring (impact × confidence / effort)

Scores: Impact 1-10 × Confidence 1-5 / Effort 1-5.

| # | Item | Score | Δ vs 2026-05-07 | Note |
|---|---|---|---|---|
| 1 | **Restore Railway service + redeploy** | 30.0 | NEW | Blocks #2 and #3 entirely. User billing action required. Already `[urgent] [blocking]` in INBOX:140 since 2026-05-17. |
| 2 | Analytics bootstrap + S5 auth-DDL on prod | 20.0 | -5.0 | Was top-1; still essential but cannot be tested until Railway is up. Drop confidence from 5→4 (analytics provider choice still TBD: GA4 vs PostHog vs Plausible). |
| 3 | Catalog re-seed gap fix (DB now 102 bikes behind source) | 18.0 | NEW | Surfaced by self-review M4 Finding 2.1 today. Headline "Bike catalog count" KPI broken because DB-vs-source has never been reconciled. 30-line patch to `scripts/agents/catalog-expansion.md` Validation gates section + one DB re-seed pass. Lower effort than #2 but lower impact ceiling. |
| 4 | Live `/api/surrogate/predict` + BuildPage hook | 10.0 | 0 | Unchanged. Still gated on Railway being up. |
| 5 | CI sidecar-build matrix → v1.0 binaries | 8.0 | 0 | Unchanged. Independent of Railway. Can proceed in parallel. |
| 6 | MCP server wrapping `/api/*` | 8.0 | 0 | Unchanged. Gated on Railway. |
| 7 | Inbox-implementer agent (kaizen consumption) | 6.0 | NEW | Loop is now +1 DONE/week and proposed agent at INBOX:427 is itself unconsumed. Score is capped at 6 because the value-of-information is high but the agent design is non-trivial (anti-slop, scope discipline, prompt eng required). |
| 8 | Indian retail-adapter live scraping | 4.0 | 0 | Unchanged. |
| 9 | Razorpay live keys + tier gating | 3.75 | 0 | Gated on #2 + GST entity + plan IDs. |
| 10 | Pune/Narhe closed beta outreach | 2.5 | 0 | Gated on #5. |

---

## Top-3 — confirmed for week of 2026-05-21

### 1. Restore Railway service + redeploy *(NEW top-1)*

**Status:** `[urgent] [blocking]` in `DISPATCH_INBOX.md:140` since 2026-05-17. Open. Pure user action — sandbox cannot perform billing operations.

**Why top-1 this week:** until `https://web-production-de6eb.up.railway.app/api/health` returns `{status:ok}`, the next two items (#2 + #4) cannot be smoke-tested or shipped. Every additional day of downtime degrades motoquant.in trust (landing page renders but every transactional click 404s).

**Success metric:** `/api/health` returns `bike_count >= 345` within 7 days; ALERT entries in OUTBOX stop accumulating.

**Escalation:** if not restored by 2026-05-28, queue `[blocking]` INSTRUCTION to evaluate Fly.io / Hetzner / Render migration as alternate hosting plan. The DB is already in git, so portability is high.

### 2. Bootstrap analytics + apply S5 auth-DDL on prod *(was #1, now #2)*

**Status:** INSTRUCTION queued in DISPATCH_INBOX since 2026-05-07 (`[opportunistic]`). Has not been consumed in 14 days. **No demotion despite delayed execution** — this is exactly the type of high-impact item the prompt requires we not depromote when it has a customer-facing INSTRUCTION queue already.

**Why #2:** depends on #1. Applying DDL via the API is impossible while Railway is 404. Once Railway is restored, this becomes top-1 again automatically.

**Success metric:** STATUS.md user-facing KPI rows show real (non-TBD) numbers within 14 days of Railway restoration; `users` table query returns ≥0 rows on prod.

### 3. Catalog DB-vs-source re-seed gap fix *(NEW — partial closure in progress)*

**Status:** Multiple INSTRUCTIONs queued by self-review M4 (2026-05-21) including `[urgent]` prompt edit for catalog-expansion agent + the actual re-seed pass. **End-of-day update:** today's catalog-expansion sessions imported 143 of the missing bikes (DB grew 345 → 488). Remaining delta: **91 bikes** (579 source vs 488 DB).

**Why still ranked here:** self-review M4 surfaced today that the DB has been silently drifting behind source files (originally 102-bike, 4-week-old drift). Headlines silently understate growth. Today's progress shows the prompt edit is working, but the gap is not closed yet and the success criterion (DB ≥ source) is not met. The fix is a continuing-pass discipline plus one final `python3 -m motoquant.run import --known-bikes` reconciliation. Lower impact ceiling than #2 (does not unlock revenue) but **the highest-confidence + lowest-effort item on the board** by score.

**Success metric:** `SELECT COUNT(*) FROM bike_models >= 579` within 7 days; subsequent catalog-expansion sessions show DB delta == source delta in the same commit (verified by next self-review run). Demote to "closed" once DB ≥ source for 2 consecutive sessions.

---

## Open conflicts / escalations

- **Competitive landscape data still missing.** INSTRUCTION queued 2026-05-07; competitive-intel agent has never fired. No data to diff against. Re-queue with `[opportunistic]` next week if still absent.
- **Razorpay gating:** still deferred — needs real users + GST entity + plan IDs. Re-evaluate when #2 produces non-TBD signup numbers.
- **Inbox-implementer agent:** ranked #7 not in top-3 because the design discipline required is high and current backlog (24 items, 6 unique) can be cleared by hand if user assigns 30 min/week. Promote to top-3 only if backlog grows past 30 unique items.

---

## Inbox actions this run

**Zero new product INSTRUCTIONS queued.** The Railway 404 ticket (INBOX:140) and the re-seed prompt-edit ticket (queued by self-review M4) already cover top-1 and top-3 respectively. Top-2 already has an open ticket from 2026-05-07. No new queueing avoids duplicate-noise.

CLAUDE.md "Standing Priorities" block needs a small surgical edit because the top-1 changed (Railway-restore is now #1, the previous top-1 drops to #2, and the re-seed gap item is new at #3).

---

## Summary for orchestrator

1. **Files touched:** `reports/product_priorities_2026-05-21.md` (updated end-of-day with refreshed DB counts + remaining 91-bike re-seed gap), `CLAUDE.md` (surgical Edit on item #3 success-metric line to reflect end-of-day state).
2. **Commit summary:** `docs(priorities): refresh 2026-05-21 re-rank with end-of-day DB counts; remaining catalog gap 91 bikes`.
3. **Top-1 changed (vs last weekly run, 2026-05-07):** YES — was "Bootstrap analytics + apply S5 auth-DDL"; now "Restore Railway service + redeploy". Driven by 27 identical 180s deploy-check ALERTs since 2026-05-17 in OUTBOX. Re-confirmed end-of-day 2026-05-21.
4. **CLAUDE.md edited:** YES (today) — Standing Priorities block top-3 already swapped per the morning re-rank; the end-of-day pass refines item #3's threshold (447 → 579) and notes 91-bike remaining gap.
