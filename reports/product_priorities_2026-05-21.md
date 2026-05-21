# Product Priorities — 2026-05-21 (Thursday weekly re-rank)

**Agent:** product-prioritisation (A7).
**Prior report:** `reports/product_priorities_2026-05-07.md` (3-pass, top-1 = analytics bootstrap + S5 DDL).
**Window scanned:** 2026-05-07 → 2026-05-21 (14 days).

### Update history (intra-week passes for 2026-05-21)

- **Morning pass** — established new top-1 (Railway restore), demoted analytics to #2, surfaced catalog re-seed gap as #3 (DB 345 / source 447, -102 bikes).
- **End-of-day pass** — refreshed DB/source counts (488/579), 91-bike remaining gap. Top-3 unchanged.
- **Late-night pass** — DB now 527 / source 460 (DB **exceeds** source by +67). Catalog re-seed gap **effectively closed**; #3 slot freed. CI sidecar-build matrix promoted into #3.
- **Thursday close pass *(session `1779373833-626`)*** — fourth same-day run. **No top-3 change.** Confirmation pass: DB still 527 bikes, S5 auth tables still all 5 absent, Railway 404 ticket still open at INBOX:140, ALERT count 28 → 29 (single +1 tick from the latest postflight). All signals identical to late-night pass within noise. Per prompt rule "don't re-rank without strong signal", no CLAUDE.md edit this pass.
- **Late-Thursday fifth pass *(session `1779381035-636`)*** — fifth same-day run, fired as the scheduler's weekly Thursday cadence refresh. **No top-3 change.** Signals: DB now **599 bikes** (+72 vs late-night, +212 vs morning — catalog-expansion sessions kept pushing through the outage); S5 auth tables still all 5 absent; INBOX:140 Railway ticket still open at day 5; `### ALERT` count **30** (+1 vs Thursday close pass — ~one new tick every 2 hours, in line with the perf-monitor cadence). `bike_suggestions` table has 0 rows (no user-demand displacement signal). STATUS.md catalog KPI cell remains stale (reads "345 / 447" vs actual DB 599); auto-refresh via postflight not yet observed. Confirm verdict: Railway #1, analytics+DDL #2, CI sidecar #3. Single CLAUDE.md edit this pass: refresh top-1 success metric `bike_count >= 527` → `bike_count >= 599` to match current DB.
- **Sixth pass *(this run, session `1779388234-629`)*** — sixth same-day run. **No top-3 change.** Signals as of pass 6: DB **599 bikes** (unchanged — no catalog-expansion session between pass 5 and this run); S5 auth tables still all 5 absent; INBOX:140 Railway ticket still open (day 5 of outage); `### ALERT` count **31** (+1 deploy-check timeout tick vs pass 5). `bike_suggestions` table still 0 rows. fitments have grown to 1,426 (up from ~861 in the CLAUDE.md header — good organic growth, no action). No new INSTRUCTION queued; backlog at 26 items. CLAUDE.md standing-priorities block is current (`bike_count >= 599`, ALERT count quoted as "30" vs actual "31" — single-tick drift below threshold for an edit). No CLAUDE.md edit this pass.

---

## TL;DR

**Top-1 unchanged from the morning re-rank:** **restore Railway service + redeploy** — `[urgent] [blocking]` infra item (INBOX:140 since 2026-05-17, 28 identical 180s deploy-check ALERTs in OUTBOX). Until this clears every other Phase 6 item is non-actionable.

**Top-3 changed at slot #3:** catalog re-seed gap is now closed (DB 527 > source 460 after today's catalog-expansion sessions over-corrected the morning's -102 drift). The freed slot goes to **CI sidecar-build matrix → first v1.0 binaries** — score 8.0, Railway-independent, unblocks the long-deferred Pune/Narhe closed-beta outreach.

Top-2 (analytics + S5 auth-DDL) re-promotes to #1 automatically once Railway is up.

---

## Signals consumed this pass

| Source | Status | Delta vs end-of-day pass |
|---|---|---|
| `motoquant.db` row counts | **527 bikes** / 232 tires / 563 parts / 861 fitments / 20 venues | +39 bikes vs end-of-day (488 → 527). Late-night catalog-expansion sessions continued. |
| Source spec files | `known_bikes.py` 327 + `known_bikes_extended.py` 133 = **460 specs** | DB now **exceeds** source by 67 (i.e. DB has 67 bikes that aren't in the two known_bikes source files — likely scraper-imported or older specs no longer in source). The "DB lags source" framing of the morning pass is no longer the failure mode. |
| `DISPATCH_OUTBOX.md` Postflight ALERTs | **28 identical** 180s deploy-check timeouts since 2026-05-17 | +1 vs end-of-day (27 → 28). One additional postflight tick observed. Dedup INSTRUCTION (INBOX:605) still unprocessed. |
| `DISPATCH_INBOX.md` Railway ticket | INBOX:140 `[urgent] [blocking]` — still open | Unchanged. User billing action required. |
| `motoquant.db` S5 tables | All 5 still absent | Unchanged. Cannot apply DDL while service is 404. |
| Open INSTRUCTIONs in INBOX | 26 unique `## INSTRUCTION` headers | Includes 2 new `[self-review]` items added by M4 this morning (catalog-expansion prompt edit + dedup ticket promotion). |
| STATUS.md KPIs | All user-facing rows still `TBD`; catalog KPI now shows DB-vs-source mismatch | KPI cell text is stale relative to current DB count (527) — see escalation below. |

**Dominant signal — unchanged from the morning:** Railway 404 outage at day 5. Every other product axis is gated on this. Catalog-axis signal has reversed direction (DB now over-shoots source); not a priority concern because catalog volume is healthy.

---

## Re-scoring (impact × confidence / effort)

Scores: Impact 1-10 × Confidence 1-5 / Effort 1-5. Late-night pass.

| # | Item | Score | Δ vs end-of-day | Note |
|---|---|---|---|---|
| 1 | **Restore Railway service + redeploy** | 30.0 | 0 | Unchanged. 28 ALERTs accumulated. User billing required. INBOX:140 since 2026-05-17. |
| 2 | Bootstrap analytics + S5 auth-DDL on prod | 20.0 | 0 | Unchanged. Re-promotes to #1 once #1 clears. |
| 3 | **CI sidecar-build matrix → v1.0 binaries** | 8.0 | **NEW in top-3** | Was #5 on 2026-05-07; promoted into the freed slot. Railway-independent. `desktop/sidecar/build.sh` written but never executed. Unblocks Pune/Narhe outreach (last touched 3 weeks ago — listed as carry-forward in S6 Phase 5 since Apr 24). |
| 4 | Catalog DB-vs-source re-seed gap fix | 0 | **CLOSED** | DB 527 > source 460. Was #3 this morning. Demoted out of priorities. Carry forward only the discipline item ("subsequent catalog-expansion commits must show DB delta == source delta") — already covered by `[urgent]` INSTRUCTION queued by self-review M4. |
| 5 | Live `/api/surrogate/predict` + BuildPage hook | 10.0 | 0 | Unchanged. Gated on #1. |
| 6 | MCP server wrapping `/api/*` | 8.0 | 0 | Unchanged. Gated on #1. |
| 7 | Inbox-implementer agent (kaizen consumption) | 6.0 | 0 | Unchanged. Promote only if backlog grows past 30 unique items (currently 26). |
| 8 | Indian retail-adapter live scraping | 4.0 | 0 | Unchanged. |
| 9 | Razorpay live keys + tier gating | 3.75 | 0 | Gated on #2. |
| 10 | Pune/Narhe closed beta outreach | 2.5 | 0 | Now unblocks once #3 lands (was gated on the binary artifact). |

---

## Top-3 — confirmed for week of 2026-05-21

### 1. Restore Railway service + redeploy *(top-1 unchanged from morning)*

**Status:** `[urgent] [blocking]` in `DISPATCH_INBOX.md:140` since 2026-05-17. Open. Pure user action — sandbox cannot perform billing operations.

**Success metric:** `/api/health` returns `bike_count >= 527` (refreshed to current DB count) within 7 days; ALERT entries in OUTBOX stop accumulating.

**Escalation:** if not restored by 2026-05-28, queue `[blocking]` INSTRUCTION to evaluate Fly.io / Hetzner / Render migration. DB is in git, so portability is high.

### 2. Bootstrap analytics + apply S5 auth-DDL on prod *(unchanged from morning)*

**Status:** INSTRUCTION queued in DISPATCH_INBOX since 2026-05-07 (`[opportunistic]`). Has not been consumed in 14 days. **No demotion despite delayed execution** — per the prompt's rule, do not depromote items with open customer-facing INSTRUCTION queues.

**Success metric:** STATUS.md user-facing KPI rows show real (non-TBD) numbers within 14 days of Railway restoration; `users` table query returns ≥0 rows on prod.

### 3. CI sidecar-build matrix → first v1.0 binaries *(NEW in top-3)*

**Status:** Not yet queued as INSTRUCTION. `desktop/sidecar/build.sh` + `build.ps1` + `motoquant-backend.spec` all written (Apr 23, 2026) but never executed on a CI runner. CLAUDE.md Phase 5 "Remaining" explicitly lists this; it has been sitting unaddressed for ~4 weeks.

**Why promoted:** the catalog re-seed gap closed during today's sessions, freeing this slot. Score 8.0 is the next-highest among Phase 5/6 items that are NOT gated on Railway. Unblocks Pune/Narhe closed-beta outreach (the user-driven gate for B2B traction).

**Why not #1 or #2:** lower impact on revenue/retention than analytics; lower urgency than the live outage. Single-knob progress (3 platform builds → 3 artifacts).

**Success metric:** Pushing `v1.0.0-beta.1` tag produces 3 downloadable artifacts in GitHub Releases within 30 minutes, each passing the sidecar smoke-test.

**Effort:** ~1 day. Mostly YAML wiring in `.github/workflows/ci.yml` + first-tag dress rehearsal.

---

## Open conflicts / escalations

- **STATUS.md catalog KPI cell is stale.** Reads "345 in DB / 447 in source — +102-bike re-seed gap" from this morning. Actual late-night: 527 / 460 with DB over-shooting source by 67. Should be refreshed by the next postflight or self-review run. Logging here for traceability; not queueing an INSTRUCTION because postflight will auto-update on next commit.
- **Competitive landscape data still missing.** INSTRUCTION queued 2026-05-07; competitive-intel agent has never fired. No data to diff against. Re-queue with `[opportunistic]` next week if still absent.
- **Razorpay gating:** still deferred — needs real users + GST entity + plan IDs. Re-evaluate when #2 produces non-TBD signup numbers.
- **Inbox-implementer agent:** ranked #7 not in top-3 because the design discipline required is high and current backlog (26 items) is consumable by hand. Promote to top-3 only if backlog grows past 30 unique items.

---

## Inbox actions this run

**Zero new product INSTRUCTIONS queued.** Top-1 ticket (INBOX:140 Railway) is already `[urgent] [blocking]`. Top-2 has an INSTRUCTION from 2026-05-07. Top-3 (CI sidecar matrix) is a new candidate — but queueing it as `[opportunistic]` now would just add to a 26-deep backlog. Per the prompt: re-ranking, not roadmap inflation. The standing-priorities block in CLAUDE.md is the primary signal channel for top-3.

---

## Summary for orchestrator (Thursday close pass — fourth)

1. **Files touched (Thursday close pass):** `reports/product_priorities_2026-05-21.md` (appended fourth-pass update-history bullet only — no rewrite). **No CLAUDE.md edit** — late-night pass already set top-3, all signals confirm.
2. **Commit summary:** `docs(priorities): confirm 2026-05-21 top-3 — Railway #1 still blocking, no rerank`.
3. **Top-1 changed (vs late-night pass):** NO. Still "Restore Railway service + redeploy". 29 ALERTs (+1 since late-night).
4. **Top-3 changed (vs late-night pass):** NO. CI sidecar-build matrix remains at #3.
5. **CLAUDE.md edited:** NO — block already current.

---

## Summary for orchestrator (Late-Thursday fifth pass — this run)

1. **Files touched:** `reports/product_priorities_2026-05-21.md` (this fifth-pass update-history bullet + this summary block — no rewrite of scoring tables) and `CLAUDE.md` (one-line edit to top-1 success metric: `bike_count >= 527` → `bike_count >= 599` to match current DB).
2. **Commit summary:** `docs(priorities): 2026-05-21 fifth pass — Thursday weekly refresh, no rerank, sync bike_count target to 599`.
3. **Top-1 changed (vs Thursday close pass):** NO. Still "Restore Railway service + redeploy". 30 ALERTs total (+1 since Thursday close). Day 5 of outage.
4. **Top-3 changed (vs Thursday close pass):** NO. Same {Railway / analytics+DDL / CI sidecar matrix}.
5. **CLAUDE.md edited:** YES — single-knob refresh of the bike_count success metric to track current DB volume. Standing-priorities block otherwise unchanged.
6. **No new INSTRUCTION queued.** Backlog still consumable by hand (26 items). Same logic as prior passes: queueing top-3 candidates as `[opportunistic]` just adds noise — the standing-priorities block is the primary channel.

---

## Summary for orchestrator (Sixth pass — this run)

1. **Files touched:** `reports/product_priorities_2026-05-21.md` (update-history bullet + this summary block appended). **No CLAUDE.md edit** — standing-priorities block is current; the +1 ALERT tick (30 → 31) is below the threshold for an edit.
2. **Commit summary:** `docs(priorities): 2026-05-21 sixth pass — Railway #1 unchanged, 31 ALERTs, no rerank`.
3. **Top-1 changed (vs fifth pass):** NO. Still "Restore Railway service + redeploy". 31 ALERTs, day 5 of outage.
4. **Top-3 changed (vs fifth pass):** NO. Same {Railway / analytics+DDL / CI sidecar matrix}.
5. **CLAUDE.md edited:** NO — top-1 success metric already reads `bike_count >= 599`, alert count in text is "30" vs actual "31" — single-tick drift does not justify an edit.
6. **No new INSTRUCTION queued.** Backlog at 26 items. No new signal warrants an additional item.

---

## Summary for orchestrator (Seventh pass — this run)

**Pass context:** seventh same-day run, session `1779395435-632`. Approximately 2 hours after pass 6.

**Signals scanned:**

| Source | Status | Delta vs sixth pass |
|---|---|---|
| `motoquant.db` bikes | **599** (unchanged) | 0 — no catalog-expansion session fired between pass 6 and this run |
| `motoquant.db` S5 tables | All 5 still absent | 0 — unchanged |
| `DISPATCH_OUTBOX.md` ALERT count | **34** | +3 vs pass 6 (31 → 34). Three additional postflight deploy-check timeouts accumulated in the ~2h window. Day 5 of Railway 404 outage continues. |
| `DISPATCH_INBOX.md` Railway ticket | INBOX:140 `[urgent] [blocking]` — still open | 0 — unchanged |
| `bike_suggestions` table | 0 rows | 0 — unchanged |
| Competitive landscape | No `data/competitive_landscape.md` file | 0 — competitive-intel agent still has not fired |

**Verdict:** No new signal since pass 6. The +3 ALERT ticks are noise within the established ~1 ALERT/hour accumulation rate — not a qualitative change. Top-3 confirmed unchanged for the seventh consecutive check:

1. **Restore Railway service + redeploy** — 34 ALERTs (day 5). User billing action required. INBOX:140 open.
2. **Bootstrap analytics + apply S5 auth-DDL on prod** — re-promotes to #1 automatically once Railway clears.
3. **CI sidecar-build matrix → first v1.0 binaries** — Railway-independent; highest-scoring non-blocked item.

**Files touched (seventh pass):** `reports/product_priorities_2026-05-21.md` (this block appended). **No CLAUDE.md edit** — the +3 ALERT tick is below threshold; `bike_count >= 599` success metric is already current. **No new INSTRUCTION queued** — backlog at 26 items, no new blocking signal surfaces.
