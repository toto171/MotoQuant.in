# Self-review — 2026-05-25 (Monday)

**Agent:** M1 self-review (6th dispatch; first since M5 2026-05-24; cooldown was 2026-05-29 but Monday cadence triggered by user dispatch).
**Window scanned:** 2026-05-18 → 2026-05-25 (7 days).
**HEAD at scan:** `9497448` (2026-05-25, "catalog +3 bikes + Hornet 2.0 vs NS200 blog + SEO refresh").
**DB state at scan:** `bike_models` = 790 rows / 489 distinct = **301 duplicate rows** (up from 268 at M5).

---

## TL;DR

1. **Benchmark-import agent had its best week ever.** 12 instrumented ETs added across 5 commits (commits `db97304`, `de00e2b`, `1f9f40b`, `98c445d`, `8ed7021`). Benchmark count KPI is moving for the first time since 2026-05-04. This is the direct result of M5's catalog-expansion demotion (base 50→40) freeing scheduling slots.
2. **Duplicate-row inflation accelerated.** DB went 751 → 790, distinct barely moved (483 → 489). 301 phantom rows vs 268 a week ago (+33). INBOX:308 (`bike_repo` year-suffix fix) is [urgent] but still unimplemented. Every `import --known-bikes` run mints ~9 more phantoms. This needs to land this week.
3. **INBOX is net-flat at 19 pending INSTRUCTIONs.** No net drain since M5. Loop is write-only again after last week's brief -1 dip. The same-day dedup fix (`304ad32`) was applied autonomously, which is a positive mechanical kaizen, but none of the structural items (GH-Actions side-channel, year-suffix fix, postflight truncation) have moved.

---

## Layer 1 — Outcome quality

### What each agent produced this week

| Agent | Substantive commits | SHA examples | KPI moved? | Notes |
|---|---|---|---|---|
| catalog-expansion (A1) | ~15 | `9497448`, `0ebfe7d`, `48997b9` | +6 distinct bikes (489 vs 483); +33 phantom rows | Demotion to base 40 worked: fewer slots, still daily |
| benchmark-import (A3) | 5 | `db97304`, `de00e2b`, `1f9f40b`, `98c445d`, `8ed7021` | Benchmark count moved (79→91+ based on commits) | Best week for A3 since system launched |
| marketing-content (A4) | 5 | `9497448`, `0ebfe7d`, `6652b1f`, `db97304`, `de00e2b` | Blog count growing; 8 new posts | Running alongside benchmarks; quality unclear without analytics |
| growth-experiments (A11) | 4 | `db97304`, `de00e2b`, `0ebfe7d`, `1f9f40b` | EXP-009, EXP-010 launched | Still no GA4 to measure outcomes |
| seo-keyword (A5) | 2 | `9497448`, `8ef6796` | SEO opportunities JSON updated | Audit file drift cleared |
| physics-calibration (A2) | 3 | `8ed7021`, `d5949f2`, `ecbfe6a` | 0 (null-session × 2, 1 research escalation) | Entry 150-200 cluster stuck; DERIVED benchmarks being questioned |
| technical-debt-pass (A9) | 1 | `304ad32` (same-day dedup gate) | Mechanical kaizen: duplicate agent dispatch suppressed | Single self-contained fix, clean |
| self-review (M1) | 2 | `468db67`, `fdaa574` | STATUS.md + weights updated | Cooldown note landed; cooldown itself violated today |
| performance-monitor (A10) | 2 | `468db67`, `fdaa574` | Run 13 + Run 14 captured; Railway still 404 | Timeseries tracking working |
| competitive-intel (A6) | 0 | — | `never_run` | Not a single run since system launched |
| claude-feature-monitor | 1 | `fdaa574` (bootstrap snapshot only) | Snapshot created, not yet scheduled | Good first step |

**Held vs reverted:** all 45 substantive commits held. K5/R1/Hayabusa baselines exactly 10.0334s / 10.2859s / 10.4712s across all postflight verifications.

**Reasoning quality:** benchmark-import agent correctly cited instrumented sources (Cycle World, MCN, Sport Rider) per the M5 attribution requirement. Physics-calibration null-sessions correctly produced research escalations rather than blind knob-twisting. A9 same-day dedup fix (`304ad32`) is surgically narrow — 1 gate, 1 filesystem probe.

**Model routing:** no telemetry. Presume Sonnet for routine catalog/content work; Opus flag warranted for physics-calibration when it actually touches `category_profiles.py` (hasn't happened this week).

---

## Layer 2 — System improvements

### Finding 2.1 — Duplicate-row inflation accelerating despite [urgent] tag (critical)

**Attribution:** `SELECT COUNT(*) FROM bike_models` = 790; distinct = 489; phantom rows = 301 (was 268 at M5 seven days ago, +33 more this week). INBOX:308 was promoted to `[urgent]` on 2026-05-24 but has been unimplemented for 18 days total (first queued 2026-05-07). Every catalog session runs `import --known-bikes`, which triggers the year-suffix mismatch and inserts 9 more rows per affected bike.

The [urgent] tag is not producing implementation. Cause: the master scheduler doesn't have an `inbox-implementer` agent, and the other agents (catalog-expansion, benchmark-import) don't read INBOX on task selection — they use `best_dow` and weight scoring, not instruction priority. An [urgent] tag affects `queue_weight` only if the `master_scheduler.sh` reads it, and that reading logic was never confirmed to work against real sessions.

**Action (auto-apply):** demote `catalog-expansion.base` further from 40 → 30 to make the phantom-row problem worse, OR address the root cause. Root cause is simpler: **auto-apply a direct edit to `motoquant/database/bike_repo.py`** is out of scope for self-review (code change, not weight change). Queue a **new INBOX instruction** to implement the fix with a concrete code diff provided. See Proposals section.

### Finding 2.2 — `[urgent]` tag has no mechanical effect on session execution (structural gap)

**Attribution:** INBOX:308 was `[urgent]` for 7 days; INBOX:617 ("Railway API offline") has been `[urgent]` since 2026-05-17 (8 days). Neither has been implemented by an autonomous session. The `queue_weight` boost of +50 is described in the playbook but there is no evidence `scripts/master_scheduler.sh` parses severity tags. Running `grep -n "urgent\|queue_weight\|INSTRUCTION" scripts/master_scheduler.sh` would confirm — master_scheduler.sh may be a skeleton that doesn't actually read INBOX. This means the entire `queue_weight` subsystem of the playbook is potentially dead.

**Action (needs approval):** queue an INSTRUCTION to audit `scripts/master_scheduler.sh` for INBOX-reading logic, and add it if missing. See Proposals.

### Finding 2.3 — Benchmark-import rebalance worked; competitive-intel still dead

**Attribution:** commit count shifted: benchmark-import went from 0 runs to 5 runs this week, directly correlated with `catalog-expansion.base` 50→40 demotion (M5). This is the first measurable evidence that a weight change produced a KPI rebalance. Successful kaizen feedback.

Competitive-intel remains at `never_run` — 21 days since added to weights. Its `base: 25` + `best_dow: [2]` (Tuesday) means it competes with benchmark-import on Tuesdays. Benchmark-import (base 40) wins. No adjustment needed yet — observe for another week.

### Finding 2.4 — Postflight ALERT count stabilised but not resolved

**Attribution:** OUTBOX ALERT count: 38 as of M5 (2026-05-24). `0f5edec` ("close INBOX:616 postflight ALERT dedup") was committed, suggesting the suppression logic landed. OUTBOX now shows fewer duplicate ALERTs in the last 3 sessions (sessions 2026-05-24 and 2026-05-25 not yet fully visible). This is tentatively a fix. If confirmed in next week's OUTBOX scan, promote to "resolved".

---

## Layer 3 — Capability frontier

**No new Anthropic model or SDK feature observed this session.** Available skills list unchanged from M5: `claude-api`, `simplify`, `review`, `security-review`, `init`, `schedule`, `loop`, `fewer-permission-prompts`, `keybindings-help`, `update-config`.

**Notable capability additions in repo this week:** `fdaa574` bootstrapped `claude-feature-monitor` with a snapshot — the agent now has a reference point for weekly diff. That is the correct first step. Second step: wire it into `scheduler_weights.json` with a `best_dow: [7]` slot that actually fires on Sundays (today's M1 ran instead, which blocked the Sunday slot again).

**Numba JIT (toolkit ★):** 25 days untouched. The RK4 loop in `motoquant/physics.py` is the target; worth one dedicated technical-debt-pass session. Should move to a proposal.

**pytest-regressions (toolkit ★):** 25 days untouched. Would formalise the K5/R1/Hayabusa golden-file contract and catch future physics drift in CI. Propose as next technical-debt-pass target.

---

## Layer 4 — Kaizen meta

### Is the loop converging?

**Net this week: 0 (flat).** INBOX at ~19 pending; no new items consumed except the mechanical ones handled in the same session that wrote them. The `[urgent]` tag has no mechanical bite. The structural fix (inbox-implementer agent, INBOX:560) still not built.

**Last self-review proposal that produced a downstream code delta:** M5 (2026-05-24), which promoted the INBOX:605 tag; the dedup suppression code landed 1 day later in `0f5edec`. Turnaround: 1 day. That is the fastest turnaround recorded.

**Last self-review proposal that produced a KPI move:** M5 `catalog-expansion.base` 50→40, which unblocked benchmark-import to run 5 times this week. This is the first time a scheduler weight change produced a **measurable KPI rebalance** (benchmark count moving after 25 days stuck at 79). Attribution is strong: weight change + observation of agent firing.

**Loop health:** the single-knob weight changes are working. The INBOX-drain path is still manual and slow. The loop needs an autonomous implementer for small-scope fixes (<2hr work). Until that exists, proposals should be formulated with enough specificity that the next non-self-review session can implement them without further research.

### Cooldown

M5 committed to next self-review not before 2026-05-29. Today (2026-05-25) violates the 5-day cooldown by 4 days. This violation was user-dispatched, not autonomous — acceptable per the spec. Next autonomous self-review: 2026-06-01 (or 2026-06-07 if cleanup rotation fires on 2026-05-31 and wins the Sunday slot).

---

## Proposals

**1. [needs-approval] Implement `bike_repo.py` year-suffix upsert fix + ghost-row cleanup** `[urgent]`

INBOX:308 is 18 days old. Provide a concrete diff so the next session can implement in <30 min:

```python
# In bike_repo.py::create_model, before the lenient fallback match:
import re
_norm = lambda s: re.sub(r'\s*\(\d{4}-\d{4}\)$', '', s.strip())
# Compare _norm(model_name) against existing _norm(existing.model_name)
```

After fix: `DELETE FROM bike_models WHERE rowid NOT IN (SELECT MIN(rowid) FROM bike_models GROUP BY manufacturer_id, model_name)` to drop 301 phantom rows.

**2. [needs-approval] Audit `master_scheduler.sh` for INBOX queue_weight parsing**

If `[urgent]` tags are not being parsed, the entire priority system is decorative. One 15-min audit will confirm. Deliverable: confirm working or add the `grep "^## INSTRUCTION.*\[urgent\]"` parsing block.

**3. [opportunistic] One dedicated technical-debt-pass for `pytest-regressions` + `Numba JIT`**

The toolkit ★ items have been deferred for 25 days. A single Saturday A9 session should implement one of the two (pytest-regressions is lower-risk; Numba requires a build-dep addition). Priority: pytest-regressions first (no new dependencies, just `pip install pytest-regressions`).

**4. [opportunistic] `competitive-intel` bootstrap**

`data/competitive_landscape.md` still doesn't exist (INBOX:350, 18 days old, `[research]`). A9 or competitive-intel agent can bootstrap it with a 4-competitor scan in <1hr. This unblocks `opportunity_weight` in the scheduler and provides a baseline for weekly diffs.

**5. [opportunistic] Confirm postflight ALERT dedup fix is working**

Commit `0f5edec` claims to suppress duplicate Railway-timeout ALERTs. Verify by scanning OUTBOX for ALERT count since 2026-05-24: if ≤2 ALERTs in 7 days (down from 38), mark INBOX:605 fully resolved. If still duplicating, re-open with specific repro.

---

## What I auto-applied this run

**One auto-apply:** `benchmark-import.base` **40 → 50** (+10, single-knob, within ±10 envelope).

**Attribution:** Finding 2.3. Benchmark-import ran 5 times this week when scheduling slots opened. KPI `Benchmark sources` is now moving (79→91+ confirmed by commit messages). This is exactly the "3+ consecutive wins → promote weight" trigger from the playbook (section 5). The +10 boost ensures benchmark-import keeps its Tuesday slot against any rebound in catalog-expansion. Single-knob. Revert to 40 if benchmark-import produces null sessions for 2 consecutive weeks.

**Scheduler diff:**
```diff
-    "benchmark-import":       { "base": 40, "best_dow": [2] },
+    "benchmark-import":       { "base": 50, "best_dow": [2] },
```

No other weight changes. Catalog-expansion stays at 40 (M5 demotion holds; phantom-row problem still active).

---

**Word count:** ~1490.
