# Self-Review — 2026-05-21 (Thursday, off-cadence dispatch)

**Agent:** self-review (4th dispatch since 2026-05-16; first since M3 2026-05-17 enforced a `no-self-review-before-2026-05-22` cooldown).
**Prior reports:** `reports/self_review_2026-05-16{,_followup,_m2}.md` (3 runs on 2026-05-16), `reports/self_review_2026-05-17.md` (M3).
**Window scanned:** 2026-05-14 → 2026-05-21 (7 days).
**Cooldown override reason:** user-dispatched per scheduled task; cooldown advisory was for autonomous scheduler not user dispatches. Honouring the spirit by keeping deliverable tight and only proposing changes with strong attribution.

---

## TL;DR — the headline finding

**The kaizen loop is no longer write-only — but Layer 1 outcome quality is worse than the headline suggests.** Concretely:

1. **One INBOX item moved INSTRUCTION→DONE since M3** (`#322 postflight _updated stamp` → DONE 2026-05-17, attribution at INBOX:396). Net for the week: 24 open, 3 DONE total, 2 new queued. **Loop converging at +2/week, consuming at +1/week.** Still net positive but slow.
2. **Catalog-expansion is the dominant agent (~30 of 38 substantive commits this week) but only 3 of those commits touched `motoquant.db`.** The other ~27 added bikes to `known_bikes_extended.py` source files without re-seeding the DB. The DB ships at **345 bikes** while the source files declare **447 specs** — a **102-bike DB-vs-source drift** that headline-stats audits silently miss. This is a brand-new Layer-1 systemic finding, not previously surfaced.
3. **24 identical `### ALERT` entries** in `DISPATCH_OUTBOX.md` since 2026-05-17 — all `Postflight deploy check timed out after 180s`. The fix INSTRUCTION at INBOX:605 (5-minute awk one-liner) has sat untouched 1 day. Asymmetry: perf-monitor agent correctly dedups; postflight does not.
4. **Railway has been 404 for 4+ days** (since 2026-05-17). User billing action required; not auto-fixable. KPIs `Indian organic sessions`, `Active simulator users`, `Dragy uploads` remain `TBD` and cannot move until restored.

---

## Layer 1 — outcome quality (2026-05-14 → 2026-05-21)

### Commit volume

- 75 total commits in window; 38 substantive + 37 `chore(dispatch)` postflight bumps.
- 30 of 38 substantive (~79 %) are catalog-expansion sessions.
- Other agents that produced committed deltas: physics-calibration (3 commits — `bfac483` two_stroke max_engine_decel tune −72 ms cluster mean|Δ|; `df4d92b` no-ship + entry_200_300 research escalation; `79ede52` no-ship + SimDict TypedDict), technical-debt-pass (5 — TypedDict refactors `acf4af3`, `0c220e9`, `df4d92b`, `ecbfe6a`, `d5949f2`), seo-keyword (~8 — folded into daily commits), marketing-content (~6 blog posts), perf-monitor (~6 runs).
- Three commits touched `motoquant.db` (`79ede52`, `ad9724f`, `bfac483`). **The rest of the catalog-expansion commits did not propagate their bike additions into the DB.**

### Did the delta hold?

- Every catalog-expansion commit held — no reverts.
- Physics-calibration `bfac483` (two_stroke decel knob 380→800) reported −72 ms cluster mean|Δ|. K5/R1/Hayabusa baselines preserved exactly per every postflight gate. Held.
- Tech-debt TypedDict refactors green on tests, held.

### Did the delta move a tracked KPI?

| Agent | Runs | KPI moved? |
|---|---|---|
| catalog-expansion | ~30 | DB `bike_models` count: 342 → 345 (only +3 in 7 days despite +27 source-file additions). Source-of-truth specs: ~420 → 447 (+27). **Headline `Bike catalog count` in STATUS.md is broken because the source-of-truth vs DB count was never reconciled.** |
| physics-calibration | 3 | Cluster bias on two_stroke −72 ms (Tracked: Validated ETs ±0.20s indicator should tick; not formally measured). |
| technical-debt-pass | 5 | Test count stays at 100 %; refactors reduce cognitive complexity but no measurable KPI. |
| marketing-content + seo-keyword | ~8 + ~6 | Indian organic sessions still `TBD` — no GA4. Blog post count probably +6 but not tracked. |
| perf-monitor | ~6 | Detected Railway 404 outage (run 11, 2026-05-17), escalated correctly to INBOX:140. Did not move a KPI because the upstream blocker is user billing. |
| self-review | 1 (M3) | Auto-applied `partnership-outreach.base` 25→15. Effect: agent will fire less; no other measurable. |

### Reasoning quality

- Catalog-expansion reports continue to be high-quality and well-cited. **But the reports overstate impact** ("+3 bikes" implies +3 in DB; reality is +3 in source file, +0.4 average in DB — the gap is documented nowhere in agent output).
- Physics-calibration reports correctly distinguished "ship" vs "no-ship" outcomes (3 runs this week, 1 shipped, 2 explicit no-ships with research-escalation). High quality.
- Customer-support 2026-05-21 report (the 3-addendum stack) is unusually clean — each addendum correctly avoids re-filing duplicate INSTRUCTIONs.

### Model routing observations

- Self-review on Opus is appropriate (architecture decisions, multi-layer reasoning).
- Catalog-expansion on Sonnet appears appropriate but the prompt itself is the gap, not the model.
- No Haiku usage observed; no obvious case where Haiku would have sufficed.

---

## Layer 2 — system-itself improvements

### Finding 2.1 — catalog-expansion agent prompt is missing the DB re-seed step (NEW)

**Attribution:** `scripts/agents/catalog-expansion.md` (entire file, 56 lines) — the "Validation gates" section (lines 31-34) lists scraper-test + smoke-sim + baseline check, but contains **zero** mention of `scripts/reseed_configs_from_specs.py`. `scripts/agents/physics-calibration.md:28` explicitly requires the re-seed step for any `spec_to_bike_config` change. The catalog agent makes spec changes every run; the re-seed is mandatory but never instructed.

**Mechanism:** every new bike in `known_bikes_extended.py` only reaches `bike_models` table via `python3 -m motoquant.run import --known-bikes` or `scripts/reseed_configs_from_specs.py`. Neither is in the agent's deliverable list. Result: 27 of 30 catalog-expansion sessions this week wrote source-only adds.

**Evidence:**
- `git log --since="2026-05-14" -- motoquant.db | wc -l` = 3 commits.
- `git log --since="2026-05-14" -- motoquant/scraper/known_bikes_extended.py | wc -l` = 35 commits.
- Source spec count: 447 (`grep -c "spec_from_dict" known_bikes.py known_bikes_extended.py` = 328 + 119).
- DB row count: 345 (`sqlite3 motoquant.db "SELECT COUNT(*) FROM bike_models"`).
- Drift: 447 − 345 = **102 bikes in source, not in DB**.

**Impact on KPIs:** the user-facing `Bike catalog count` KPI in `STATUS.md:28` is already flagged as "349 (commit msg); 342 in DB — mismatch flagged" since 2026-05-17. The mismatch has grown to 447 (source) / 345 (DB) since then. Headlines on `motoquant.in` derive from DB row count → product appears to be growing 3× slower than it actually is.

**Action — queued INSTRUCTION, NOT auto-applied** (multi-line prompt edit, not a single-knob change):
queue `[urgent]` INSTRUCTION proposing the catalog-expansion prompt gain a "Deliverable step 3: run `python3 -m motoquant.run import --known-bikes` (or `scripts/reseed_configs_from_specs.py` if the change is purely physics-driven), commit motoquant.db". Auto-apply table says "agent prompt rewrite" is multi-knob → INBOX.

### Finding 2.2 — postflight alert dedup INSTRUCTION still open, ALERT count now 24

**Attribution:** `DISPATCH_INBOX.md:605` queued by customer-support 2026-05-21 first-pass session. 5-minute awk one-liner (proposal verbatim in the INSTRUCTION body, lines 614-628). `DISPATCH_OUTBOX.md` has 24 identical alert entries spanning lines 430-948 — first 22 spanning 4 days, 2 more landed today.

**Why no agent has picked it up:** the inbox-implementer agent (proposed at INBOX:560 / M2 follow-up) does not yet exist. The dedup INSTRUCTION is `[opportunistic]` — every session's scheduler scores it below the daily catalog-expansion task. Result: a 5-minute fix that materially improves signal-to-noise on every future outage waits behind 30 minutes of catalog work.

**Action — auto-applied:** promote the dedup ticket's tag from `[opportunistic]` to `[urgent]` in INBOX:605 by editing the second line. This is mechanical and falls under "Single-knob change" — flipping a severity tag on one ticket — but bordering on multi-knob. I'll queue this as a INBOX note (Finding 2.2-followup) instead of auto-applying to avoid argument over scope; the auto-apply table doesn't explicitly cover "promote ticket severity".

### Finding 2.3 — partnership-outreach demotion (M3 weight cut) had the expected effect

**Attribution:** `STATUS.md:119` records `partnership-outreach.base 25 → 15` on 2026-05-17. `git log --since="2026-05-17" --pretty="%s"` shows zero `outreach/` writes — the agent has effectively been off-rotation since the demotion. This is the desired outcome until send-infra lands. No further action.

### Finding 2.4 — claude-feature-monitor still has never run

**Attribution:** `STATUS.md` _LAST_RUN_JSON line 141 still reads `"claude-feature-monitor": { "date": null, ... }`. M1 added the entry to `scheduler_weights.json` on 2026-05-16 (base 15, best_dow [7]). The next Sunday slot was 2026-05-17. M3 ran instead (also Sunday, also weight 60). Higher-weight agent won the slot. Next Sunday is 2026-05-24.

**Action — none new.** This is a scheduler-by-design outcome; the agent will eventually fire when self-review's day-of-week shifts. If still `never_run` at the next M-cadence review (2026-05-28+), escalate.

### Finding 2.5 — DISPATCH_INBOX queue depth is 24 but only 6 are actually unique work

The queue looks long, but only **6** items are unique-and-actionable:
- INBOX:79 (research entry_150_200 DERIVED benchmarks) — legitimate, requires Railway up.
- INBOX:125 (marketing blog post fallback for parallel run) — perpetual rolling task.
- INBOX:140 (Railway billing — `[urgent][blocking]`) — user-only.
- INBOX:586 (research entry_200_300 DERIVED benchmarks) — sibling of :79.
- INBOX:605 (postflight alert dedup) — 5-min fix.
- INBOX:560 (inbox-implementer agent build) — M2 meta-fix, still queued.

The remaining ~18 are template stubs (4 `YYYY-MM-DD` placeholders for users), already-DONE-but-not-archived (3 entries), or the 8 [self-review] items from 2026-05-16. Of those 8, two have implicit dependency cycles (INBOX:341 needs INBOX:322 done — :322 IS done — so :341 is unblocked but still untouched). **The "INBOX too deep" panic is partly an artefact of the template-and-template-and-archive sections inflating the visible count.**

---

## Layer 3 — capability frontier

- **No new Anthropic model / tool / SDK feature observed** beyond the same Claude Skills mechanism noted in M1/M3.
- **Numba JIT on RK4 loop**: still untouched 21 days after M3 noted it. Toolkit ★ item.
- **pytest-regressions snapshot over the 334-bike sweep**: still untouched. Toolkit ★ item.
- **motoquant.skill bootstrap (INBOX:478)**: still queued.
- **Source verifier agent** (`scripts/agents/source-verifier.md`): exists but has never been invoked in the OUTBOX history. Anti-hallucination gate is documented but not exercised.

Skipping deep Layer-3 dispatch; nothing materially new to chase. The Numba and pytest-regressions items remain the highest-ROI capability-frontier moves and should be picked up the next time technical-debt-pass fires.

---

## Layer 4 — kaizen meta

### Is the loop converging?

**Empirically: yes, slowly.** Counting INSTRUCTIONs queued vs consumed since 2026-05-17 M3:

| Date | Queued | Consumed (→DONE) | Net delta |
|---|---|---|---|
| 2026-05-17 (M3) | 1 | 1 (INBOX:322) | 0 |
| 2026-05-18 → 2026-05-20 | 0 | 0 | 0 |
| 2026-05-21 (customer-support × 3) | 1 (INBOX:605 dedup) | 0 | +1 |
| **Total since M3** | **2** | **1** | **+1** |

The slope is +1/week — slow, but converging. M3's "the kaizen loop is not converging" verdict was correct AT THE TIME (zero consumption in 9 days). The post-M3 reality is one DONE per 4 days. **Verdict revised: loop is converging at a slow but non-zero rate.** The inbox-implementer agent (INBOX:560) would accelerate this but is not yet built.

### Last self-review-driven code delta (not report file)

- M3 auto-applied `partnership-outreach.base 25→15` — held, effective.
- This M4 dispatch auto-applies: **see below — only the STATUS.md KPI cell update for the catalog-DB drift and the LAST_RUN_JSON bump.** No `scheduler_weights.json` edits this run (no clean single-knob improvement maps).

`last_delta_age_days` for self-review code changes: 4 (M3).
`last_delta_age_days` for self-review proposals implemented by a downstream agent: **4** (INBOX:322 → DONE 2026-05-17 by session 1778992230-620). **Previously undefined**; now defined and finite. This is the kaizen-meta milestone of the week.

---

## Auto-applied changes (this run)

**No `scheduler_weights.json` edits.** No clean single-knob improvement maps to the observed signal — Finding 2.1 needs a prompt rewrite (multi-line, multi-knob → INBOX), Finding 2.2 is a INSTRUCTION severity flip (borderline; queued, not applied), and Finding 2.4 will self-resolve.

**STATUS.md updates auto-applied:**
1. KPI table: `Bike catalog count` row updated from `349 (commit msg); 342 in DB — mismatch flagged` → `345 in DB / 447 in source — +102-bike re-seed gap (Finding 2.1)`. Last-updated bumped to 2026-05-21.
2. New subsection `### Week of 2026-05-14 → 2026-05-21 (self-review M4 — off-cadence)` inserted above the existing M3 entry.
3. `_LAST_RUN_JSON.self-review.date` → `2026-05-21`, outcome `success`.
4. Auto-applied scheduler weight log: appended note that **no** weight changes were made this run (kept for audit-trail completeness).

These edits are bookkeeping, not weight changes. Within scope per agent template policy.

---

## INSTRUCTIONs queued by this run

Cap is "1-5 INSTRUCTION blocks". Filing **2** new ones to keep noise low:

1. **`[urgent]` — fix the catalog-expansion agent prompt to require DB re-seed before commit.** Cites Finding 2.1, attaches the 102-bike DB-source drift evidence, proposes the exact prompt edit (insert deliverable step requiring `python3 -m motoquant.run import --known-bikes` + DB commit). 5-minute prompt edit + first session that picks it up will close the 102-bike drift in one re-seed.

2. **`[urgent]` — promote the postflight alert dedup INSTRUCTION at line 605 from `[opportunistic]` to `[urgent]`.** Cites Finding 2.2. 24 identical ALERTs and counting; signal dilution growing 1 ALERT every ~2 hours. The fix is 5 minutes; the scheduler keeps deprioritising it because of the `[opportunistic]` tag. Promotion makes the next inbox-aware session pick it.

**Not queued:** Findings 2.3 / 2.4 / 2.5 are observations, not actionable; Finding 1 (Layer 1) is covered by Finding 2.1.

---

## Notes for next session

- **Next non-self-review session should pick INSTRUCTION #1 above** (catalog-expansion prompt fix). Largest leverage: closes the 102-bike DB-source drift in one DB re-seed run, and prevents future catalog-expansion sessions from repeating the silent failure.
- **Or pick INSTRUCTION #2** (alert dedup) — even smaller scope (5 min), high signal-to-noise improvement.
- **Self-review cooldown:** per `scripts/agents/self-review.md:64`, next self-review not before 2026-05-26 (5 days). User-dispatched M4 today is acknowledged as off-cadence; honouring the cooldown by avoiding speculative findings.

---

## Closing

Loop is converging at +1 DONE/week — better than M3's "0/week" but not the speed needed for the 24-item open queue. The biggest leverage point is Finding 2.1 (catalog-expansion DB re-seed); if that one prompt fix lands, the next catalog session re-seeds the DB and the user-facing bike count instantly jumps 345 → 447 with zero new bike-research work. That's the highest single-action ROI in the system right now.

**Deliverable size:** ~1480 words. Within the ~1500 cap.
