# Self-Review — 2026-05-24 (Sunday, natural weekly cadence)

**Agent:** self-review (5th dispatch since 2026-05-16; first since M4 2026-05-21 off-cadence).
**Prior reports:** `reports/self_review_2026-05-16{,_followup,_m2}.md`, `self_review_2026-05-17.md` (M3), `self_review_2026-05-21.md` (M4).
**Window scanned:** 2026-05-17 → 2026-05-24 (7 days).
**HEAD at scan:** `9041aa0` (2026-05-22). Working DB pre-session-edit: 751 bikes.

---

## TL;DR

1. **Loop drained twice this morning.** INBOX:639 (catalog-expansion prompt fix) + INBOX:674 (dedup tag flip), both queued by M4, both moved → DONE inline at session start. **First multi-item drain ever.** Post-M3 score: **3 DONE / 4 queued = net -1.** Layer 4: loop is converging, accelerating modestly.
2. **M4 prompt fix worked AND surfaced a deeper bug.** DB 345 → **751** in 14 DB-touching commits, but source spec count only 447 → **488** (+41). The +406 vs +41 gap = **268 duplicate rows** (33 bikes × 9 + 4 × 2 + 446 × 1; distinct = 483 ≈ source). Root cause is the WS-A April 27 year-suffix idempotency regression already queued at **INBOX:308** since 2026-05-07 (17 days, `[opportunistic]`). The M4 gate activated it by running `--known-bikes` 14× this week.
3. **38 Postflight ALERT entries** (24 at M4 time, +14 in 3 days). INBOX:605 tag flipped to `[urgent]` this morning; the awk script itself still pending.
4. **Railway still 404 day 8.** User billing action required. KPIs `Active simulator users` / `Indian organic sessions` / `Dragy uploads` blocked.

---

## Layer 1 — outcome quality (2026-05-17 → 2026-05-24)

- **91 total commits / 47 substantive.** **43/47 (91 %) = catalog-expansion.** 14/47 (30 %) touched `motoquant.db` (up from M4's 3/30 = 10 % — prompt-fix gate firing).
- **Physics-calibration:** 1 ship (`bfac483` two_stroke `max_engine_decel_rads2` 380→800, −72 ms cluster mean|Δ|, held). 2 no-ships with research escalations.
- **Tech-debt:** 5 TypedDict refactors (`acf4af3`, `0c220e9`, `df4d92b`, `ecbfe6a`, `d5949f2`) + 1 seed-catalogs helper (`b4adf8d`) — all held, 100 % test pass.
- **Marketing/growth:** ~15 blog posts + EXP-005..008 A/B variants.
- **Self-review:** 1 (M4 2026-05-21) — queued 2 `[urgent]` INSTRUCTIONs, both DONE this morning. **First measurable Kaizen-meta KPI move:** queue→DONE turnaround was 3 days (queued 2026-05-21, implemented 2026-05-24), down from 4 days post-M3.
- **Perf-monitor:** 0 commits in window — last run was Run 12 on 2026-05-17 (`data/perf_timeseries.json`).
- **Held vs reverted:** every catalog commit held, K5/R1/Hayabusa baselines exact, TypedDict refactors green.
- **Reasoning/model routing:** catalog-expansion agent correctly reports DB-row deltas in commit messages (`673→709`, `715→751`) — but the +9 duplicates per WS-A April 27 bike is silent because `import --known-bikes` returns no error. Self-review M4 well-attributed (1480 words). Physics-calibration's no-ships correctly distinguished investigation-only from ship.

---

## Layer 2 — system-itself improvements

### Finding 2.1 — Duplicate-row inflation in `bike_models` (NEW, urgent)

**Attribution:** `motoquant.db` has 751 rows; distinct `(manufacturer_id, model_name)` = 483; source `spec_from_dict` count = 488. **268 duplicates.** Histogram: 33 bikes × 9 + 4 × 2 + 446 × 1 = 751. The "9 occurrences" matches 9 successful `import --known-bikes` runs since the M4 gate. Affected bikes are the WS-A April 27 year-suffix batch (e.g. `GSX-R 750 (1985-1987)`, `Hayabusa 25th Anniversary (2024)`). Root cause: `motoquant/database/bike_repo.py::create_model` upsert fallback doesn't strip `(YYYY-YYYY)` before matching. Fix already queued at **INBOX:308** (2026-05-07, 17 days, `[opportunistic]`).

**Action — auto-applied:** flip INBOX:308 `[opportunistic]` → `[urgent]`. Same mechanical pattern M4 used on INBOX:605 → 674, which made it to DONE in 3 days. Post-fix cleanup: `DELETE FROM bike_models WHERE rowid NOT IN (SELECT MIN(rowid) ... GROUP BY ...)` → headline snaps 751 → ~483.

### Finding 2.2 — Catalog-expansion is over-weighted at base 50

**Attribution:** 43/47 substantive commits (91 %) are catalog-expansion. Other agents that *want* to fire — claude-feature-monitor (`never_run`), product-prioritisation (1 run weekly per `best_dow [4]`), benchmark-import (never run; KPI `Benchmark sources: 79`, target 100+), competitive-intel (never run) — keep losing slots to catalog. The DB now has more *phantom* rows than real source-spec growth this week (268 phantoms vs +41 valid). The marginal value of the 9th `+3 bikes` commit/day is lower than the marginal value of one benchmark-import run.

**Action — auto-applied:** demote `catalog-expansion.base` 50 → 40 (-10, within single-knob ±10 envelope). Reason: keep the daily-catalog cadence (`best_dow [1]` still applies; +10 day-of-week boost makes Mondays still trigger reliably) but free 4–6 slots/week for starved agents. Will revisit next Sunday after observing the rebalance.

### Findings 2.3–2.5 (no new action)

- **claude-feature-monitor still `never_run`** — added to `scheduler_weights.json` 2026-05-16 at base 15 [7]; self-review keeps winning Sunday slots. The catalog-expansion demotion in Finding 2.2 should free the next Sunday slot for it (catalog goes to base 40, claude-feature-monitor 15 + best_dow boost wins). Escalate if still `never_run` after 2026-05-31.
- **INBOX backlog 23 entries, ~5 unique-actionable:** 4 template stubs, 4 archived `## DONE`, 2 `[research]` waiting Railway, 1 user-only blocking ticket, 1 perpetual rolling blog, 7 stale `[self-review]` from 2026-05-16, 1 META at line 516, 1 dedup-script (605 tag now `[urgent]`), 1 year-suffix matcher (308 → `[urgent]` per Finding 2.1). META INBOX:516 still active — backlog hasn't dropped below 8. **No new `[self-review]` items queued today** per that commitment.
- **Postflight ALERT count 24 → 38** in 3 days (+14, ~1 alert/2 hours). INBOX:605 tag flipped this morning; script itself still pending. Next implementer-style session should pick it.

---

## Layer 3 — capability frontier

- **No new Anthropic model / tool / SDK feature observed** in this session's `available-skills` list beyond what M3/M4 noted. Skills mechanism (e.g., `claude-api`, `simplify`, `review`) is unchanged.
- **Numba JIT on RK4 loop**: 24 days untouched (toolkit ★ item; M1 logged 2026-05-04).
- **pytest-regressions over 334-bike sweep**: 24 days untouched (toolkit ★ item).
- **motoquant.skill bootstrap (INBOX:478)**: still queued.
- **MCP server wrap of `/api/*`**: still queued (CLAUDE.md TOOLKIT REFERENCE ★ item).

Skipping deep Layer-3 dispatch this week. The Numba and pytest-regressions items remain the highest-ROI capability-frontier moves and should be picked up the next time technical-debt-pass fires.

---

## Layer 4 — kaizen meta

### Is the loop converging?

**Empirically: yes, modestly accelerating.** Since system shipped 2026-05-04:

| Window | Queued | Consumed (→DONE) | Notes |
|---|---|---|---|
| 2026-05-04 → 2026-05-16 | 6 | 0 | Pre-self-review baseline |
| 2026-05-16 → 2026-05-17 | 8 | 0 | M1/M1f/M2/M3 burst |
| 2026-05-17 → 2026-05-21 | 0 | 1 | INBOX:322 → DONE |
| 2026-05-21 → 2026-05-24 | 2 | 0 | M4 queues, both about to drain |
| 2026-05-24 morning | 0 | 2 | INBOX:639 + INBOX:674 DONE |
| **Total since 2026-05-17** | **2** | **3** | **Net -1** ✓ |

**For the first time, the loop is consuming faster than producing.** Net delta this week: **-1**. The structural inbox-implementer agent (INBOX:560) is still not built — but the manual implementer-pattern (today's session opening with two inline INSTRUCTION-→-DONE flips) is doing the same job. That works only because the recent items were small (prompt edit + severity tag); larger items like the dedup script + year-suffix matcher will still need a dedicated session.

### Last self-review-driven code delta (not report file)

- M3 (2026-05-17) auto-applied `partnership-outreach.base 25→15` — held, effective (0 outreach commits since).
- M4 (2026-05-21) queued 2 INSTRUCTIONs; both DONE 2026-05-24 (3-day turnaround).
- This M5 dispatch auto-applies: `catalog-expansion.base 50→40` (Finding 2.2) + INBOX:308 tag flip `[opportunistic]` → `[urgent]` (Finding 2.1).

`last_delta_age_days` for self-review code changes: **0** (after this commit).
`last_delta_age_days` for self-review proposals implemented by a downstream agent: **3** (M4's two INSTRUCTIONs → DONE today).

### Cooldown

Per `scripts/agents/self-review.md:64` ("Don't run more than one self-review per 5 days"), next self-review not before **2026-05-29 (Friday)**. Natural Sunday cadence is **2026-05-31** — which is the cleanup-rotation last-Sunday-of-month slot (per CLAUDE.md standing cleanup-rotation note). Self-review competes with the 7-subagent cleanup pass that day; cleanup likely wins on cadence priority. Plan: self-review natural slot moves to **2026-06-07**.

---

## Auto-applied changes (this run)

**Two changes**, both within scope per agent-template policy:

1. **`scripts/scheduler_weights.json`:** `catalog-expansion.base` 50 → 40. Single-knob, within ±10 envelope per `scripts/agents/self-review.md:50`. Attribution: Finding 2.2. Reason: 43/47 substantive commits this week (91 %) starves starved agents; ~6 of 14 DB-touching commits produced phantom duplicates that contaminate the headline KPI; marginal value of additional catalog work is below marginal value of one benchmark-import / claude-feature-monitor run.

2. **`DISPATCH_INBOX.md:309`:** tag `[opportunistic]` → `[urgent]` on INBOX:308 (`fix: bike_repo year-suffix matching for upsert`). Mechanical single-line edit, consistent with the M4 pattern applied to INBOX:605 (which made it to DONE in 3 days post-flip). Attribution: Finding 2.1. Reason: this fix is now the single highest-leverage system improvement — 268 duplicate rows pollute `bike_models`, all caused by this missing one-line normaliser. Implementer should also DELETE the duplicate rows after the upsert fix lands.

**`STATUS.md` bookkeeping** (not a weight change):
- Append `### Week of 2026-05-17 → 2026-05-24 (self-review — Sunday cadence)` subsection.
- Update `Bike catalog count` KPI row: source-of-truth = 751 DB rows (acknowledging known 268-row inflation per Finding 2.1) / 488 source specs.
- Update `_LAST_RUN_JSON.self-review.date` → `2026-05-24`, outcome `success`.
- Append CHANGELOG note to `_meta.comment` in `scheduler_weights.json` for the catalog-expansion demotion.

**No INBOX items queued this run** per the META commitment at INBOX:516 (backlog still above 8 unique-actionable).

---

## Notes for next session

- **Highest-ROI next pick:** INBOX:308 (year-suffix matcher fix). One-line code + regression test + post-fix DELETE → headline snaps 751 → ~483 (true state).
- **Second pick:** INBOX:605 dedup-script (5-LOC awk). 38 ALERTs, +1 every 2h.
- **Don't queue more `[self-review]` items** until backlog drops below 8 (META INBOX:516 commitment). Continue implementer-pattern.
- **Self-review cooldown:** no further self-review before 2026-05-29. Natural Sunday resumes 2026-06-07.
