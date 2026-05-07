# Product Priorities — 2026-05-07 (Thursday)

**Agent:** product-prioritisation (A7) — third run today. Re-evaluated against end-of-day accumulated signals; no top-1 change required.

### Update history

- **2026-05-07 17:40 UTC** — first run of the week. Established top-3 (analytics-bootstrap / surrogate route / CI sidecar matrix), queued 2 product INSTRUCTIONS (analytics+DDL bootstrap + competitive-landscape research) + supporting CLAUDE.md "Standing Priorities" block. Source signals: STATUS.md KPIs all TBD, 0 bike_suggestions, no S5 tables on prod DB.
- **2026-05-07 ~21:00 UTC** — second run, same-day validation. No top-1 change. Signals unchanged from morning. Single new event: catalog +3 bikes (session `1778175630-727`) — separate catalog-growth axis, no priority displacement.
- **2026-05-07 ~22:30 UTC** *(this run, session `1778185835-631`)* — third validation pass, end-of-day. **No top-1 change.** New signals vs second run: catalog now 339 bikes (delta +1 from session `1778178639-614`'s PM batch). S5 auth tables still absent on prod DB. `[urgent]` OG-card + headline-sync instruction still unprocessed (opened this morning, queue weight +100 per scheduler model) — this is a content/ops task, not a Phase 6/7 capability item; it does not displace product ranking but flags that the next engineering session should execute it. Zero new ALERT/INCIDENT in OUTBOX.

---

## Signals consumed this run (third pass — end-of-day)

| Source | Status | Delta vs second run (18:39 UTC) |
|---|---|---|
| `STATUS.md` KPIs | unchanged | All user-facing rows still TBD; catalog now 339 bikes (+3 vs second pass) |
| `data/competitive_landscape.md` | **STILL MISSING** | competitive-intel agent has not yet run; INSTRUCTION queued (DISPATCH_INBOX line 258) |
| `bike_suggestions` table | 0 rows | No new submissions; confirmed via `SELECT COUNT(*) FROM bike_suggestions` |
| `DISPATCH_OUTBOX.md` | 1 new SESSION entry since second run | `1778178639-614` (18:39 UTC) — catalog +2 bikes (Hero Mavrick 440 / Yamaha Tenere 700), baselines clean, zero new ALERT/INCIDENT |
| `DISPATCH_INBOX.md` | 6 open instructions | Added `[research]` tire-format validator instruction (line 277). The `[urgent]` OG-card instruction (line 110) still unprocessed — highest queue-weight item but ops/content scope, not Phase 6/7 product capability. |
| `motoquant.db` S5 tables | ALL MISSING | `users`, `sessions`, `subscriptions`, `license_keys`, `magic_links` — confirmed absent this pass. DDL exists in codebase (`motoquant/auth.py` + `subscriptions_repo.py`) but has never been applied to prod. |
| `motoquant.db` row counts | 339 bikes / 232 tires / 563 parts / 861 fitments / 20 venues | Delta from morning: +3 bikes, +1 part, fitments unchanged |

**Dominant signal — unchanged from morning:** zero user-facing KPIs measurable because analytics is absent. Second-strongest: S5 auth tables absent, so subscriptions/signups cannot be tracked even if users arrive. Third signal added this pass: `[urgent]` OG-card instruction sitting in queue since morning — not a Phase 6 item but the highest-priority unprocessed engineering task by scheduler weight.

---

## Re-scoring (end-of-day, third pass)

No event this day moves any item's `(I × C) / E` score by ≥1.0. Scores derived as: Impact 1-10 × Confidence 1-5 / Effort 1-5. Morning ranking confirmed unchanged.

| # | Item | Score (I×C/E) | Delta vs morning | Note |
|---|---|---|---|---|
| 1 | Analytics bootstrap + S5 auth-DDL on prod | 25.0 | 0 | Blocks all user-facing KPIs; 5 S5 tables confirmed absent (verified this session); INSTRUCTION queued `[opportunistic]` |
| 2 | Live `/api/surrogate/predict` + BuildPage hook | 10.0 | 0 | `surrogate_dnn.pkl` (10.8 MB) in repo root; route not yet written; gated on #1 producing usable engagement signal |
| 3 | CI sidecar-build matrix → v1.0 binaries | 8.0 | 0 | `desktop/sidecar/build.sh` written but never executed; unblocks Pune/Narhe outreach |
| 4 | MCP server wrapping `/api/*` | 8.0 | 0 | OpenAPI spec exists (`/docs`); no new distribution signal today |
| 5 | Indian retail-adapter live scraping | 4.0 | 0 | `pricing_refresh.py` URL templates exist; no scraping layer |
| 6 | Razorpay live keys + tier gating | 3.75 | 0 | Gated on #1 (need real users) + user's GST-registered entity + plan IDs |
| 7 | Pune/Narhe closed beta outreach | 2.5 | 0 | Gated on #3 (no installer artifact yet) |

**Conclusion: top-3 confirmed unchanged for full day 2026-05-07. No CLAUDE.md edit required.** The "Standing Priorities" block at CLAUDE.md line 126 already reflects this ranking and was set on first run of the day.

---

## Top-3 — confirmed for week of 2026-05-07

### 1. Bootstrap analytics + apply auth-DDL on prod *(top-1, unchanged)*

**Status:** INSTRUCTION queued in DISPATCH_INBOX (line 167), `[opportunistic]`. Awaiting next code-touching agent.

**Success metric:** STATUS.md user-facing KPI rows show real (non-TBD) numbers within 14 days; `users` table query returns ≥0 rows on prod.

### 2. Live `/api/surrogate/predict` + BuildPage live preview *(unchanged)*

**Status:** Not yet queued as an INSTRUCTION (intentional — top-1 should ship first; once analytics is producing numbers, queue this as the next product feature).

**Success metric:** BuildPage slider tick latency p95 ≤ 5 ms.

### 3. CI sidecar-build matrix → first downloadable v1.0 binaries *(unchanged)*

**Status:** Not queued. Same staging logic — once #1 is in flight, queue this so the Pune/Narhe outreach gate clears.

**Success metric:** `v1.0.0-beta.1` tag → 3 platform artifacts in GitHub Releases within 30 min.

---

## Open conflicts / escalations *(carried over)*

- **Missing data:** `data/competitive_landscape.md` still absent. INSTRUCTION already queued (line 182, `[research]`). Future weekly competitive-intel runs will diff against the eventual baseline.
- **Razorpay gating:** still deferred — needs real users + GST-registered entity + plan IDs. Re-evaluate in 4 weeks.

## Inbox actions this run

**Zero new product INSTRUCTIONS queued.** The new `[research]` tire-format validator instruction (line 277, queued by PM catalog session) is an engineering-hygiene item, not a Phase 6/7 product item — no ranking impact.

The `[urgent]` OG-card + headline-sync instruction (line 110) has the highest scheduler queue weight (+100) of any open item but is a content/ops task, not a product capability. The product-prioritisation agent does not depromote or displace it — it should be the next engineering session's primary task per the scheduler scoring model. Logging this observation so the master scheduler reads it correctly.

**Summary:** third same-day run confirms the morning top-3. All 6 open INBOX instructions are accounted for (3 sandbox-infra + 1 urgent OG-card ops + 1 product analytics + 1 product competitive-landscape + 1 research tire-format). No duplicates queued.
