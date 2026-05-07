# Product Priorities — 2026-05-07 (Thursday)

**Agent:** product-prioritisation (A7) — first run; no prior `reports/product_priorities_*.md` to diff against. Re-ranking the open Phase 4/5/6 carry-forward items in `CLAUDE.md` against this week's signals.

---

## Signals consumed

| Source | Status | What it told us |
|---|---|---|
| `STATUS.md` KPIs | sparse | Catalog 336 ✓ on track; baselines 0.0000s ✓; **all user-facing KPIs (indexed pages, organic sessions, sim users, B2B convos, Dragy uploads) are TBD/0** — no analytics layer wired yet |
| `data/competitive_landscape.md` | **MISSING** | competitive-intel agent has not produced a landscape file yet (first run pending) |
| `bike_suggestions` table (motoquant.db) | 0 rows | `/api/bikes/suggest` is wired, no submissions in shipped DB |
| `DISPATCH_OUTBOX.md` | 3-day window, 0 ALERT/INCIDENT entries | OUTBOX wired May-4; only setup preamble. Proxy via `reports/support_triage_2026-05-07.md` shows recurring sandbox-only friction, **not** product-facing pain |
| `DISPATCH_INBOX.md` | 3 open `[opportunistic]` instructions | All sandbox-infra (disk-guard, GH-Actions health side-channel, bike_repo year-suffix) — none are product features |
| `motoquant.db` audit | `users` / `sessions` / `subscriptions` / `license_keys` tables **NOT FOUND**; `sim_runs` 0 rows | S5 subscription-auth code merged, but DDL **never ran on the production DB** — silent gap |

The dominant signal this week is **"there are no users yet"** — every user-facing KPI is zero or unknown, no bike suggestions, no Dragy uploads, no sim runs. The second-strongest signal is the silent S5 auth-DDL gap.

---

## Open items, scored

Scale 1–5 each on **Impact** (revenue / KPI move), **Confidence** (we know how to ship it), **Effort** (1=trivial, 5=multi-week). Score = (I × C) / E.

| # | Item (phase) | I | C | E | Score | Note |
|---|---|---|---|---|---|---|
| 1 | **Wire GA4 + PostHog + apply S5 DDL to prod DB** (analytics + auth bootstrap) | 5 | 5 | 1 | **25.0** | Without it, every other KPI stays "TBD". Unblocks B2C path entirely. |
| 2 | **Live `/api/surrogate/predict` route + BuildPage hook** (Phase 4/5) | 4 | 5 | 2 | 10.0 | Pickle ships; route is ~1 day; converts BuildPage from "novelty" to "fast tuner" |
| 3 | **CI sidecar-build matrix → unblock desktop release** (Phase 5) | 4 | 4 | 2 | 8.0 | Only blocker to v1.0 download; user-installable artefact = signup driver |
| 4 | **MCP server wrapping `/api/*`** (Phase 6) | 4 | 4 | 2 | 8.0 | Distribution + marketing demo; OpenAPI already at `/docs` |
| 5 | **Indian retail-adapter live scraping** (Phase 4 carry) | 4 | 3 | 3 | 4.0 | Pricing trust = ROI trust; high cost (per-retailer adapters), medium confidence |
| 6 | **Razorpay live keys + tier gating** (Phase 6) | 5 | 3 | 4 | 3.75 | Required for revenue, but **blocked on**: real users, GST registration, plan IDs |
| 7 | **Pune/Narhe closed beta outreach** (Phase 5) | 5 | 2 | 4 | 2.5 | High value, low confidence in execution from sandbox |
| 8 | **PDF report export** (Phase 5) | 2 | 5 | 1 | 10.0* | High score, but **no users to give reports to** — depromote until #1 produces signups |
| 9 | **3D bike viz / PPO RL / OBD-II** (Phase 5/6 nice-to-haves) | 1 | 2 | 5 | 0.4 | Defer indefinitely — pure roadmap inflation |

\*Item 8 scores high mechanically but fails the gating signal: ship after analytics shows users finishing sims.

---

## Top-3 — recommended order this week

### 1. **Bootstrap analytics + apply auth-DDL on prod** — *new top-1*

**What:** (a) Add Google Analytics 4 to `web/app/layout.js`; (b) wire PostHog free-tier to FastAPI `/api/*` middleware; (c) ship a `scripts/apply_s5_ddl.py` migration that runs `ensure_tables()` on the production `motoquant.db` so `users` / `sessions` / `subscriptions` / `license_keys` tables exist. Verify on Railway via the new GH-Actions health side-channel (already queued in INBOX) before declaring done.

**Success metric:** Within 14 days of ship, **STATUS.md "Indexed pages" + "Indian organic sessions/mo" + "Active simulator users/mo" rows show real numbers** (any non-TBD value), and `users` table query returns ≥0 rows on prod (i.e., schema exists). 30-day target: 200 active sim users / month.

**Why now:** every other Phase 6 commercial item (Razorpay, B2B outreach, freemium signup flow) depends on knowing whether anyone is actually visiting. Currently we are flying blind. Cheapest, fastest, highest-leverage move.

### 2. **Live `/api/surrogate/predict` + BuildPage live preview**

**What:** FastAPI startup loads `surrogate_dnn.pkl` (10.8 MB, already in repo); `POST /api/surrogate/predict` scores one feature vector in ~1 ms; new `useSurrogate()` React Query hook in desktop + web `SimulatorWidget`; toggle keeps "real" sim available.

**Success metric:** BuildPage slider tick latency drops from ~50 ms (full sim) to ≤5 ms p95 (surrogate). User-perceived "drag the slider, watch ET move" — measurably interactive, not click-and-wait.

**Why:** the surrogate is the highest-prepared, lowest-effort capability we are sitting on. Apr 22 BuildPage write explicitly TODO'd this; pickle has been in the repo for 3+ weeks. Direct conversion-driver for the desktop v1.0 download.

### 3. **CI sidecar-build matrix → first downloadable v1.0 binaries**

**What:** Add `desktop-build` job to `.github/workflows/ci.yml` matrix `{ubuntu-latest, windows-latest, macos-latest}` running `desktop/sidecar/build.sh|ps1` + `tauri build`, uploading platform binaries as workflow artifacts on every `v*` tag push.

**Success metric:** Tagging `v1.0.0-beta.1` produces 3 downloadable artifacts in GitHub Releases within 30 minutes, each passing the local smoke-test (sidecar boots, `/api/health` returns 200).

**Why:** unblocks the "Pune/Narhe closed beta" Phase 5 outreach item. We have a 2433-module bundle compiling cleanly and a packaging scaffold complete since Apr 23, but no actual installable binary anywhere. Without this, item #7 (closed beta) is impossible.

---

## Conflicts / escalations

- **Conflict:** Item #1 (analytics bootstrap) is not on any current Phase list — it's *implicit* in the KPI tracking but uncodified. Recommend adding a "Phase 5.5: Instrumentation" half-step to CLAUDE.md.
- **Budget gate (Item #6, future):** Razorpay needs GST-registered Indian entity + real bank account + plan IDs created in dashboard. Already known from S5 carry-forward — defer until Item #1 produces signup volume justifying the paperwork. **Not queued as `[blocking]` this week** — too early.
- **Missing data:** `data/competitive_landscape.md` does not exist. Recommend a `[research]` INSTRUCTION to bootstrap the competitive-intel agent's first scan. Without it, opportunity-weight in the master scheduler is dead-input.

---

## CLAUDE.md edit recommended

CLAUDE.md has no "Standing priorities" section. Recommend adding one immediately under the standing-notes block at the top, as a numbered top-3 that the daily scheduler can read. (Edit applied alongside this report.)

## Inbox actions queued

1. `[opportunistic]` — bootstrap analytics + apply S5 DDL on prod DB (Top-1 owner: next code-touching agent).
2. `[research]` — populate `data/competitive_landscape.md` with an initial scan of Bikes.app, Drag-y app, MotoCalc, Tuneboss (2-page brief, no action yet).
