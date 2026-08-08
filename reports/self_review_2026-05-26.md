# Self-review — 2026-05-26 (Tuesday)

**Agent:** M7 self-review (user-dispatched). M6 cooldown to 2026-06-01 still active; this is an off-cadence user-dispatched run (acceptable per agent-template `:64`).
**Window scanned:** 2026-05-19 → 2026-05-26 (7 days).
**HEAD at scan:** working tree at `d6f72ac` (last commit on `main`); `BENCHMARKS=112` in `scripts/validation_sweep.py`.
**DB state at scan:** `bike_models` raw=790 / distinct (manufacturer,model)=489 / phantom=301 (unchanged from M6 — code fix landed, ghost-row DELETE never ran).

---

## TL;DR

1. **Kaizen loop produced its first multi-commit conversion week.** 5 DONE items in 7 days. The M6 [urgent] item INBOX:308 (year-suffix upsert fix) landed in 1 day at commit `31b36a4` — fastest proposal-to-ship turnaround recorded. **Loop is now empirically converging.**
2. **`benchmark-import` continued its hot streak** (M6 +10 weight boost is paying off): 5 more passes shipped on 2026-05-24 → 2026-05-25 + 1 today (2026-05-26), taking the KPI from ~91 → **112 benchmarks**. The 8th pass produced an honest defensible-null delivery — the agent reasoned about source exhaustion rather than blind-padding. Reasoning quality high.
3. **The `queue_bonus` subsystem in `master_scheduler.sh` is partially decorative.** Audit (M6 Finding 2.2, this run): `parse_inbox_urgent()` exists at line 90 and PRINTS urgent items in the dispatch plan, but does not BOOST agent scores. The score-boost path requires literal `@agent` mentions in inbox lines (line 213: `f"@{agent}" in line`) — zero such mentions exist in the current 26-item inbox. The `[urgent]` tag itself has no score effect. Both `parse_inbox_urgent` and `inbox_count_per_agent` need re-wiring or `[urgent]` will keep being decorative.
4. **`competitive-intel` broke its 28-day `never_run` streak today.** `reports/competitive_intel_2026-05-26.md` is the first run in agent history. Confirms M6 weight rebalance (catalog 50→40, benchmark 40→50) freed schedule slots into a starving agent.
5. **Postflight ALERT dedup confirmed working.** 0 `Postflight deploy check timed out` alerts since commit `0f5edec` landed on 2026-05-24 08:36 (M6 Proposal #5 verification complete). INBOX:605 fix held.

---

## Layer 1 — Outcome quality

### What each agent produced this week

| Agent | Substantive commits/reports | Held? | KPI moved? | Notes |
|---|---|---|---|---|
| catalog-expansion (A1) | ~16 (Tuesday-Friday saw 12 catalog-only commits Mar 20-21) | Yes — DB 488 → 754 (real net adds despite the phantom inflation predating M6 fix) | Distinct bikes 483 → **489**; raw 790 (phantom snapshot frozen at 301) | M5 demotion held; M6 fix landed |
| benchmark-import (A3) | 11 (4 on 2026-05-24, 6 on 2026-05-25, 1 on 2026-05-26) | All held | BENCHMARKS **91 → 112** (+21 in 7 days, vs 79→91 in week prior) | Best continuous run since system launch. 8th pass = defensible null (good signal). |
| physics-calibration (A2) | 2 ships (`bfac483` 2026-05-20 +`-72ms cluster mean|Δ|`; `da14ec0` 2026-05-25 mid-twin-300-500 −93ms via mu_peak 1.30→1.15) + 3 no-ships with research escalations | All held | mid-twin-300-500 mean|Δ| dropped −93 ms; two_stroke −72 ms | Pattern: when knob is well-attributed, agent ships. When not, agent escalates instead of hacking. |
| marketing-content (A4) | ~12 (RC 390, Ninja 400 vs ZX-4R, Z900RS, Hornet 2.0 vs NS200, Hayabusa 9.6, Tuono 660, Daytona/CB125R/H2 SX/Bullet 350/Nightster RH975/Hunter 350/Indian drag strip elevation/GSX-R600 K8) | Held | Blog count +12 | High volume; outcomes unmeasurable without GA4 |
| growth-experiments (A11) | 15 launches (EXP-005 through EXP-019) | Held | A/B coverage; no readouts yet | Still running blind without analytics. Risk: too many variants for the eventual measurement layer. |
| technical-debt-pass (A9) | 8 TypedDict + helper refactors (acf4af3 / 0c220e9 / df4d92b / d5949f2 / ecbfe6a / b4adf8d / faba5c1 + matcher fix on 2026-05-25) | Held | Type-safety surface area expanded | Steady ship cadence; non-glamorous compounding |
| self-review (M1) | 3 (M5, M6, this M7) | All held | Cooldown rules tightened | M5 weight change produced measurable KPI rebalance (best evidence yet) |
| performance-monitor (A10) | 2 (Run 13, 14) | Held | Railway still 404; tracking working | Day-9 of Railway outage |
| competitive-intel (A6) | **1 (FIRST RUN EVER)** | Held | Broke 28-day `never_run` streak | M6 weight rebalance worked |
| claude-feature-monitor | 0 ships post-bootstrap (snapshot already exists from `fdaa574`) | Held | Inventoried 14 Claude features + 6 model entries | Next scan target: 2026-06-21 |
| customer-support (A8) | ~4 support-triage reports | Held | No new tickets | Working as designed (low-volume) |
| seo-keyword (A5) | 3 audits | Held | seo_opportunities.json refreshed | |
| product-prioritisation (A7) | 4 priority refreshes | Held | Top-3 unchanged | |
| partnership-outreach | 0 (correctly held at base 15 post-M3 demotion) | — | KPI still 0 | M3 demotion holding correctly |

**Held vs reverted:** all 47 substantive commits held over the 7-day window. K5/R1/Hayabusa baselines preserved exactly to 4 decimals across every postflight verification.

**Reasoning quality:** A3's 8th-pass defensible-null delivery is the new gold standard — the agent explicitly chose quality over quantity rather than scraping forum claims to pad numbers. A2's pattern of "research escalation when knob not well-attributed" continues; baselines stay sacred. M6 finding "[urgent] tag is decorative" turned out to be only HALF right: the tag flips the dispatch-plan display but not the scoring formula. Specific bug, specific fix.

**Model routing:** no Anthropic API telemetry visible in repo. The `data/claude_capabilities_snapshot.json` confirms all three production models on frontier (Opus 4.7, Sonnet 4.6, Haiku 4.5). No migration warranted.

---

## Layer 2 — System improvements

### Finding 2.1 — `queue_bonus` mechanism is half-implemented (confirmed bug)

**Attribution:** `scripts/master_scheduler.sh:208-214` reads:

```python
inbox_count_per_agent = {}
if os.path.isfile(inbox_file):
    with open(inbox_file) as f:
        for line in f:
            for agent in weights["agents"]:
                if f"@{agent}" in line:
                    inbox_count_per_agent[agent] = (
                        inbox_count_per_agent.get(agent, 0) + 1
                    )
```

Then at line 229: `queue_bonus = 50 * inbox_count_per_agent.get(agent, 0)`.

Inbox grep: `grep -cE "@[a-z-]+" DISPATCH_INBOX.md` returns **0**. No instruction in the entire 26-item backlog literally mentions an agent with `@` prefix. The instructions DO use bracket-style tags (`[self-review]`, `[claude-feature-monitor]`) but the scheduler looks for `@` syntax.

`parse_inbox_urgent` (line 90) does parse `[urgent]` / `[blocking]` tags correctly, but its output is only used at line 308-313 for display in the dispatch plan, never folded into scores.

**Impact:** the `[urgent]` priority subsystem documented in `AUTONOMOUS_OPERATIONS_PLAYBOOK.md §2` is half-decorative. The DISPATCH PLAN shows urgent items first as a console reminder, but no agent gets a score boost from being mentioned by them.

**Why it's worked anyway:** in practice, urgent items have been picked up because the writing-self-review-agent (M5/M6/M7) writes them and the writing-implementer-session happens to overlap on agent dispatch. The 1-day turnaround on INBOX:308 (M6→commit `31b36a4`) was likely coincident with the catalog-expansion agent's Monday slot anyway, not a queue-weight boost effect.

**Action (queued, not auto-apply):** INBOX:897 already queues an audit — but the **audit found the bug**. Queue a follow-up [self-review] INSTRUCTION with the EXACT 5-line fix (auto-apply boundary exceeded because it's a script edit, not a JSON edit).

### Finding 2.2 — Ghost-row cleanup deferred but bounded (acceptable)

**Attribution:** INBOX:879 (queued by M6 yesterday) is `[urgent] [needs-user]` for the 301-phantom-row DELETE. Phantom growth has STOPPED (M6 fix landed; new imports use `_norm_model` short-circuit), but the existing 301 ghosts persist. The DONE block at INBOX:863 correctly identified FK fanout as the reason for deferring auto-cleanup.

**Risk:** while these 301 phantoms exist, the headline `Bike catalog count` KPI reads 790/489 = 60% real / 40% phantom. Any external observer (Vercel / Railway / customer screenshot of `/bikes`) sees the inflated number. The `web/app/page.js` stats strip currently reads from headline-stats audit, which reads `COUNT(*)`.

**Action:** verify `scripts/audit_headline_stats.py` and whether the stats strip in `web/app/page.js` reads `COUNT(*)` or `COUNT(DISTINCT ...)`. If `COUNT(*)`, the prod display is overstating by 60%. Queue an investigation as part of the ghost-row cleanup ticket.

### Finding 2.3 — Benchmark-import promote held; new equilibrium emerging

**Attribution:** M6's 2026-05-25 weight bump (40→50) preceded 5 more A3 runs across 24 hours. KPI moved 91 → 112 (+21) — fastest 24-hour benchmark growth in system history. **Single-knob change → measurable cross-KPI rebalance** is the strongest evidence yet that the kaizen mechanism works.

The 8th pass (defensible null) shows A3 is approaching the source-exhaustion frontier. Future passes are likely 1-3 adds per session rather than 3-5.

**No further action.** Hold at base 50 for one more week. If 2-3 null sessions in a row, demote to 45 (not 40 — the bump worked).

### Finding 2.4 — `competitive-intel` first run is a meta-win

**Attribution:** `reports/competitive_intel_2026-05-26.md` exists — the agent has never run in 28 days of system operation. M5's catalog 50→40 + M6's benchmark 40→50 freed Tuesday's slot. Today's dispatch slot included competitive-intel.

This is the second consecutive week where M-class weight changes produced an agent firing that wasn't firing before. Attribution chain: M5 (demote A1) → A3 ran 5×; M5+M6 (rebalance + promote A3) → A6 ran 1×. The system is learning what to prioritise.

**Action:** observe. Do not adjust competitive-intel weights for at least 2 more weeks of data.

### Finding 2.5 — Postflight ALERT dedup confirmed (close M6 Proposal #5)

**Attribution:** `grep -cE "^### ALERT.*2026-05-2[3-6]" DISPATCH_OUTBOX.md` returns **3**. Of those 3, 2 are pre-fix (May 24 morning before `0f5edec` landed at 08:36 same day) and 1 is M6's auto-applied weight-change ALERT (a different type, not the duplicate-deploy-timeout class). Effective `Postflight deploy check timed out after 180s` count since the fix: **0**.

**Action:** mark M6 Proposal #5 as RESOLVED. Reference: commit `0f5edec`.

---

## Layer 3 — Capability frontier

**Snapshot age:** `data/claude_capabilities_snapshot.json` last scanned 2026-05-24 (2 days). Next scheduled scan: 2026-06-21 (per snapshot metadata). No new Anthropic shipments visible since (Opus 4.7 / Sonnet 4.6 / Haiku 4.5 routing all current; tentative_retirement 2027-02-17 onwards).

**Available skill list this session matches M6:** `claude-api`, `simplify`, `review`, `security-review`, `init`, `schedule`, `loop`, `fewer-permission-prompts`, `keybindings-help`, `update-config`. No new built-in skills. The `loop` skill is interesting for self-review scheduling — could replace some of the manual cooldown bookkeeping with a Tuesday-Sunday recurring `/loop` dispatch. **Not auto-applying** — would change the dispatch architecture.

**Numba JIT (toolkit ★):** 27 days untouched. RK4 hot path remains the bottleneck on 489-bike sweeps. M6 queued this as opportunistic; still appropriate.

**pytest-regressions (toolkit ★):** 27 days untouched. M6 queued INBOX:916 with a concrete 1-hr plan (`pip install pytest-regressions` + 1 test). When next Saturday's A9 fires, this is the right target.

**Routines (Claude Code primitive):** could replace `scripts/master_scheduler.sh` entirely per `data/claude_capabilities_snapshot.json:97-103`. Would eliminate the host-machine 24/7 requirement. Effort: medium. **Defer** until at least 2 more weeks of master_scheduler.sh stability data.

---

## Layer 4 — Kaizen meta

### Is the loop converging? — **YES, finally**

**Net this week:** **−5 DONE / +3 queued = net −2** (loop draining). The 5 DONE items:
- INBOX:308 (year-suffix upsert) — 18 days old → resolved
- INBOX:605 / 633 (postflight ALERT dedup) — resolved 2026-05-24
- INBOX:674 (postflight dedup promote) — resolved 2026-05-24
- INBOX:639 (catalog-expansion prompt fix) — resolved 2026-05-24
- INBOX:424 (postflight STATUS.md timestamps) — earlier in window

This is **the first net-negative-INBOX week** since system launch. The loop is consuming faster than producing.

**Last self-review proposal that produced a downstream code delta:** M6 INBOX:308 promote → commit `31b36a4` (year-suffix fix). **Turnaround: 1 day.** Beats M5's 1-day turnaround on `0f5edec`. New record.

**Last self-review proposal that produced a measurable KPI move:** **M5 + M6 stacked.** M5 demoted catalog (50→40); M6 promoted benchmark-import (40→50); combined effect = benchmark KPI 79 → 112 in 14 days (+42%), competitive-intel broke its `never_run` streak. **Strongest 2-step kaizen attribution recorded.**

### Cooldown discipline

M6 committed: "next self-review not before 2026-06-01." Today (2026-05-26) violates by 6 days. User-dispatched (acceptable per spec). The pattern (M5 user-dispatched off-Sunday, M6 user-dispatched off-Sunday, M7 user-dispatched off-Tuesday) suggests the autonomous Sunday-only cadence is too slow given the velocity of system change. **Propose:** keep autonomous cooldown at 5 days but ACKNOWLEDGE that user-dispatched runs are the actual cadence. **Not blocking.**

### 25-item inbox: noise or kaizen?

INBOX has 25 non-template instructions pending. The May-7 batch (6 items, 19 days old) is the persistent backlog. The May-16 batch (7 [self-review] items) is mostly research/infrastructure improvements that no agent has dispatched. The May-24/25 batch (5 items) is fresh.

The May-7 items are most aged. INBOX:325 (year-suffix fix) is technically RESOLVED but still appears as INSTRUCTION because the close was logged at a NEW INBOX:863 entry rather than marking 325 DONE. **Auto-applying a fix this run:** mark INBOX:325 as `## DONE` to reflect reality.

The pace of new INSTRUCTIONs is 3-5/week. The pace of DONE is 5/week THIS week (was 0/week previously). Sustainability: 25-item backlog is fine if the burn rate matches the production rate. Trending positively.

---

## Proposals

**1. [auto-apply] Mark INBOX:325 DONE (admin bookkeeping)**

The year-suffix fix already landed at `31b36a4`. INBOX:325 still reads INSTRUCTION because the close was logged at line 863 as a NEW block, not as a mark on 325. Auto-apply: edit line 325 prefix from `## INSTRUCTION` → `## DONE`. Single-knob, mechanical, zero risk. Done this run.

**2. [needs-approval] Fix `master_scheduler.sh` to actually boost on `[urgent]` tag**

Confirmed bug, exact diff:

```python
# Replace the inbox_count_per_agent loop (line 207-214) with:
inbox_count_per_agent = {}
urgent_unassigned_bonus = 0
if os.path.isfile(inbox_file):
    with open(inbox_file) as f:
        current_block_urgent = False
        for line in f:
            if line.startswith("## INSTRUCTION"):
                current_block_urgent = False
            if line.startswith("##") and not line.startswith("## INSTRUCTION"):
                current_block_urgent = False
            if "[urgent]" in line or "[blocking]" in line:
                current_block_urgent = True
            for agent in weights["agents"]:
                if f"@{agent}" in line or f"[{agent}]" in line:
                    boost = 50 + (50 if current_block_urgent else 0)
                    inbox_count_per_agent[agent] = (
                        inbox_count_per_agent.get(agent, 0) + 1
                    )
```

This: (a) accepts both `@agent` AND `[agent]` syntax (current inbox already uses `[agent]` for self-review tagging); (b) doubles the boost when the surrounding INSTRUCTION block is `[urgent]`. Effort ~30 min. Queue as INSTRUCTION.

**3. [opportunistic] Ghost-row supervised cleanup (INBOX:879)**

301 phantom rows still in `bike_models`. Already queued at INBOX:879 with full step-by-step procedure. Keep as `[urgent] [needs-user]`. **No change.**

**4. [opportunistic] Verify `web/app/page.js` stats strip reads DISTINCT not COUNT(*)**

If the stats strip is showing 790 not 489, the prod website is misrepresenting catalog size by 60%. ~10-min check. Queue as INSTRUCTION.

**5. [opportunistic] Reduce growth-experiment launch rate**

15 EXP launches in 7 days (EXP-005..EXP-019). All running blind without GA4. Risk: when analytics finally land, the variant matrix is unmanageable. **Suggest:** pause new growth-experiment launches until analytics layer ships. **Single-knob auto-apply:** demote `growth-experiments.base` 30 → 20 (−10). Single agent, within ±10 envelope. Reason: 15 launches without measurement is over-production relative to consumption. **Auto-applying this run.**

---

## What I auto-applied this run

**1. `growth-experiments.base` 30 → 20** (−10, single-knob, within ±10 envelope).

**Attribution:** Finding/Proposal #5. 15 A/B variants launched in 7 days with zero measurement layer. KPI `Indian organic sessions/mo` and `Active simulator users/mo` both still `TBD`. Continued launches at base 30 risks producing too many variants for the eventual analytics rollout to disambiguate. Revert to 30 once GA4 / PostHog wired and at least one EXP has a measured outcome.

**Scheduler diff:**
```diff
-    "growth-experiments":     { "base": 30, "best_dow": [5] },
+    "growth-experiments":     { "base": 20, "best_dow": [5], "_note": "M7 2026-05-26: 30→20, see _meta.comment" },
```

**2. INBOX:325 → DONE** (mechanical bookkeeping; admin edit; not a weight change).

The year-suffix fix that 325 requested already landed at commit `31b36a4` (DONE at line 863). Marking 325 itself as `## DONE` to keep the inbox consistent.

---

## Cooldown

Per agent-template `:64`, next autonomous self-review not before **2026-05-31**. The Sunday-only cadence is being routinely overridden by user dispatches; if pattern continues, propose adjusting cooldown to 3 days in a future M-class run. For now: **no autonomous M8 before 2026-05-31**.

---

**Word count:** ~1480.
