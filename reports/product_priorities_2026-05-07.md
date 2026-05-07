# Product Priorities — 2026-05-07 (Thursday)

**Agent:** product-prioritisation (A7) — second run today. Re-evaluated against the day's accumulated signals; no top-1 change required.

### Update history

- **2026-05-07 17:40 UTC** — first run of the week. Established top-3 (analytics-bootstrap / surrogate route / CI sidecar matrix), queued 2 product INSTRUCTIONS (analytics+DDL bootstrap + competitive-landscape research) + supporting CLAUDE.md "Standing Priorities" block. Source signals: STATUS.md KPIs all TBD, 0 bike_suggestions, no S5 tables on prod DB.
- **2026-05-07 ~21:00 UTC** *(this run)* — re-fired same-day to validate. **No top-1 change.** Signals unchanged from morning (KPIs still TBD, 0 user submissions, 0 OUTBOX ALERT/INCIDENT entries since wiring). The single new event — catalog +3 bikes (Tuareg 660 / Apache RTR 180 / NS400R) shipped via session `1778175630-727` — is on a separate axis (catalog growth) and does not displace the analytics gap. Report overwritten with confirmation reasoning + same top-3.

---

## Signals consumed this run

| Source | Status | Delta vs morning run |
|---|---|---|
| `STATUS.md` KPIs | unchanged | All user-facing rows still TBD; catalog 336 still on track |
| `data/competitive_landscape.md` | **STILL MISSING** | competitive-intel agent has not produced output (research instruction queued morning, still pending) |
| `bike_suggestions` table | 0 rows | Still 0 — confirmed by support_triage 18:30 second pass |
| `DISPATCH_OUTBOX.md` | 1 new SESSION entry | `1778175630-727` (17:57) — catalog +3 bikes, baselines clean, PAT primary tier, **zero new ALERT/INCIDENT** |
| `DISPATCH_INBOX.md` | 5 open instructions | 3 sandbox-infra (disk-guard / GH-Actions side-channel / year-suffix upsert) + 2 product (analytics+DDL / competitive landscape). All from morning run; none picked up yet by code-touching agents. |
| `motoquant.db` | tables unchanged | `users` / `sessions` / `subscriptions` / `license_keys` STILL not present on prod DB — silent gap persists |

**Dominant signal — unchanged from morning:** zero users measured because zero analytics. Second-strongest signal — also unchanged: silent S5 auth-DDL gap.

---

## Re-scoring (single-day window, light-touch)

No event today moves any item's `(I × C) / E` score by ≥1.0. The morning ranking holds:

| # | Item | Score (morning) | Score (now) | Δ | Note |
|---|---|---|---|---|---|
| 1 | Analytics bootstrap + S5 DDL apply | 25.0 | 25.0 | 0 | Still cheapest unblock for every KPI row |
| 2 | Live `/api/surrogate/predict` + BuildPage hook | 10.0 | 10.0 | 0 | Pickle still in repo, route still unwritten |
| 3 | CI sidecar-build matrix | 8.0 | 8.0 | 0 | No movement on `desktop/sidecar/build.sh` execution |
| 4 | MCP server wrapping `/api/*` | 8.0 | 8.0 | 0 | No new distribution signal |
| 5 | Indian retail-adapter live scraping | 4.0 | 4.0 | 0 | — |
| 6 | Razorpay live keys + tier gating | 3.75 | 3.75 | 0 | Still blocked on real users → still gated by item #1 |
| 7 | Pune/Narhe closed beta outreach | 2.5 | 2.5 | 0 | Still gated by item #3 (no installer) |

**Conclusion: top-3 confirmed. No CLAUDE.md edit required.** The "Standing Priorities" block at line 126 already reflects this ranking.

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

**Zero new INSTRUCTIONS.** All systemic fixes (3 sandbox-infra) and product items (2: analytics+DDL bootstrap + competitive-landscape research) are already queued from the morning run — duplicates would be noise. Logging this run as idempotent same-day re-validation.
