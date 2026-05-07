# DISPATCH INBOX — User → Claude

> **Asynchronous instruction queue.** Drop instructions for the next autonomous Claude session here. Claude's preflight script reads this at session start and processes any block under a `## INSTRUCTION` heading, then marks it `## DONE`, `## DEFERRED`, or `## RESPONDED` once handled.
>
> **Format:** Use the templates below. One instruction per `## INSTRUCTION` block. Anything outside an INSTRUCTION block is ignored.
>
> **Where to write from:** Phone (via GitHub mobile app or git web edit), real terminal, IDE — any tool that can edit a markdown file. The file is committed to git so changes sync across devices.

---

## How to use this

1. Add a new `## INSTRUCTION — <date> — <one-line summary>` block at the top.
2. Inside, give Claude the context. Be specific. Use the templates below.
3. Commit + push (or just save in workspace folder if you have a sync running).
4. Next autonomous session picks it up automatically.
5. After handling, Claude renames the heading to `## DONE — <date> — <summary>` and adds a `### Result` section underneath. Status becomes part of the git history.

## Severity tags (optional, in INSTRUCTION title)

- `[urgent]` — handle in the very next session, even if it's the daily catalog session
- `[blocking]` — don't start any other work until this is done
- `[opportunistic]` — fold in when convenient, no rush
- `[research]` — Claude should investigate + report back, not act

---

## Templates

### Add a bike to the catalog

```
## INSTRUCTION — YYYY-MM-DD — add bike: <make> <model> <year>
[opportunistic]

Spec source: <URL or "service manual" or "magazine test">
Key numbers: <hp / torque / mass / displacement>
Drivetrain: <chain pitch + sprocket if non-default>
Notes: <anything weird like 2T, shaft drive, etc>
```

### Investigate a bug

```
## INSTRUCTION — YYYY-MM-DD — investigate: <one-line problem statement>
[research]

Context: <where you noticed it>
Reproduction: <CLI / API call / test name>
Expected: <what should happen>
Actual: <what does happen>
Don't act yet — write findings to outbox and ask before fixing.
```

### Run a sweep / report

```
## INSTRUCTION — YYYY-MM-DD — sweep: <what kind>
[opportunistic]

Filter: <subset of bikes if any>
Output: reports/<filename>.md
Compare against: <prior report or benchmark>
```

### Direct task

```
## INSTRUCTION — YYYY-MM-DD — <verb>: <object>
[urgent | blocking | opportunistic]

<full description of what to do>
<any constraints>
<expected deliverable>
```

---



## Mobile shorthand DSL

For one-tap dispatch from your phone, drop a `## MOBILE — YYYY-MM-DD — HH:MM` block anywhere in this file. The preflight handler expands it into proper INSTRUCTION blocks. Available verbs:

```
ship                                # process inbox + commit + push
pause                               # halt all autonomous sessions
unpause                             # resume autonomous sessions
rerun yesterday                     # re-execute yesterday's primary task
rerun <agent>                       # run a specific agent immediately
add bike <make> <model> <year>      # queue [urgent] catalog request
investigate <topic>                 # queue [research] investigation
+1 <agent>                          # bump weight +10 for this agent
-1 <agent>                          # cut weight -10
status                              # post current STATUS.md to OUTBOX
incident <text>                     # raise an incident manually
```

Once processed, the block is renamed `## MOBILE-PROCESSED — ...` so it isn't re-fired.

Example:

```
### MOBILE EXAMPLE — 2026-05-15 — 10:30
add bike Aprilia Tuono V4 1100 Factory 2024
+1 marketing-content
investigate why ZX-25R sim trap is 5 km/h slow
```

## INSTRUCTION — 2026-05-07 — sync all headline numbers + regen OG social card + wire postflight auto-patch gate
[urgent]

Problem: WhatsApp/Twitter/Slack link previews for motoquant.in show severely stale numbers in the OG card image — **287 BIKES / 465 PARTS / 12 VENUES / 739 TESTS / ±0.07s accuracy** vs current reality **~341 / ~562 / 20 / [collect via pytest] / ±0.032s top-10 mean**. The OG image is the worst offender; it's a static PNG that hasn't been regenerated since circa April-mid. Even the meta description text ("334+ bikes") is stale. Screenshot evidence: user dispatch 2026-05-07 chat.

CLAUDE.md "Sync the headline numbers across the codebase" hygiene already flags this class of bug and references `scripts/audit_headline_stats.py`. The audit script needs extending and a postflight auto-patch gate needs wiring so this never drifts again.

Source-of-truth values for THIS session (derive at runtime, do NOT hard-code anywhere):

- bike_models row count: `python3 -c "import sqlite3; print(sqlite3.connect('motoquant.db').execute('SELECT COUNT(*) FROM bike_models').fetchone()[0])"`
- parts / tire_models / bike_tire_fitments / venues row counts (same pattern)
- BENCHMARKS list length (grep `motoquant/scraper/` or wherever it lives)
- Total fast pytest count: `python3 -m pytest --collect-only -q tests/ 2>&1 | tail -3`
- Top-10 mean |Δ| from the latest `reports/sweep_et_*.json` — extract programmatically
- K5/R1/Hayabusa reference baselines: 10.0334s / 10.2859s / 10.4712s (preserved exactly — DO NOT touch)

Tasks (all in one session, single commit):

1. **Audit drift.** Run `python3 scripts/audit_headline_stats.py` — capture report.

2. **Patch every drift on every visible surface** (numbers derived at runtime, no constants):
   - `web/app/page.js` — landing stats strip + schema.org product schema
   - `web/app/bikes/page.js` — metadata title + body
   - `web/app/features/page.js` — feature subtitles
   - `web/app/blog/*/page.js` — every post that quotes counts
   - `web/app/docs/*/page.js`
   - `web/app/layout.js` — meta description + OG / Twitter card meta tags
   - `web/components/StructuredData.js` (if hard-coded)
   - `README.md`

3. **Regenerate the OG social-card image.** Locate the canonical path (likely `web/public/og-image.png` or `web/public/og.png`, or a Next.js dynamic route at `web/app/opengraph-image.{js,tsx}`). Match the existing card layout from the screenshot exactly:
   - Top pill row: "Free · Open Source · India" (orange dot)
   - Hero: large "MotoQuant" wordmark, "The Physics of Faster" subtitle, "Quarter-mile simulation · ±[current top-10 mean]s accuracy" small line
   - 4-stat grid in orange: BIKES / PARTS / VENUES / TESTS with current counts
   - Right panel: GSX-R 1000 K5 v(t) curve hero with "10.03s · 239 km/h" badge — keep this exactly (baseline preserved)
   - Bottom-right: "motoquant.in" pill
   - Dimensions: **1200×630** (Twitter/Facebook standard) — verify before commit
   - Save with the same filename so existing meta tags resolve unchanged
   - Implementation choice: prefer Pillow/Cairo from Python (deterministic, no headless browser dep) OR Next.js dynamic `opengraph-image` route reading from a build-time JSON. If you go dynamic, also commit a static fallback PNG so deploys without the build step still serve current numbers.

4. **Extend `scripts/audit_headline_stats.py`** to:
   - Check OG image mtime vs `motoquant.db` mtime — flag if image is older
   - Parse OG meta description "X+ bikes" string
   - Parse Twitter card meta tags
   - Parse Schema.org structured-data numeric fields
   - Add a `--fix` flag that auto-patches all listed surfaces (used by postflight below)

5. **Wire postflight auto-patch gate.** Edit `scripts/session_postflight.sh` to run `python3 scripts/audit_headline_stats.py --fix` AFTER agents finish their work but BEFORE the explicit-list `git add`. Behaviour:
   - Auto-patches stale numbers in all listed surfaces in-place
   - Regenerates OG image if any checked surface shifted
   - Lists files modified by `--fix`; postflight adds them to the same commit as the agents' work (no separate `chore(headline-sync)` commits — drift fix rides whatever commit caused the drift)
   - If `--fix` fails for unrecoverable reasons (e.g. cannot regenerate image), abort the push and write `### ALERT` to outbox with diagnostic details

6. **Optional new agent (only if postflight gate exceeds ~50 LOC inline).** Factor out as `scripts/agents/headline-sync.md` with low scheduler base weight (5) for on-demand / weekly Sunday firing. The postflight gate stays — it runs every session unconditionally.

Deliverables (single commit):

- "feat(web): regen OG card + sync all headline numbers + wire postflight auto-patch gate"
- Updated `scripts/audit_headline_stats.py` (with `--fix` + OG/twitter-card checks)
- Regenerated OG PNG at the canonical path
- Updated `scripts/session_postflight.sh` with the auto-patch gate
- Every web/blog/docs surface showing current numbers
- Outbox `## SESSION` block lists drift-fix delta + path to the regenerated PNG (and ideally the image dimensions verified)

Quality gates (do not skip):

- Reference baselines K5/R1/Hayabusa MUST stay at +0.0000s — patches to web copy must NOT touch physics
- Pre-push smoke: `python3 -c "import motoquant; e = motoquant.MotoQuantEngine(motoquant.gsxr1000_k5()); print(f'{e.run().time_quarter:.4f}s')"` should print exactly `10.0334s`
- Focused tests still pass (scraper / validation / two_stroke / compatibility / submodel_kaizen / power_boost_regression)
- ZERO hard-coded count constants added anywhere — every number derived at runtime from DB / pytest / sweep JSON
- New OG image visually matches the screenshot layout; dimensions verified 1200×630

Source: user dispatch 2026-05-07 with WhatsApp screenshot showing 287 BIKES / 465 PARTS / 12 VENUES / 739 TESTS card. Standing rule going forward (per user): "every time numbers / features / lists change in any commit, the next consecutive push (or same push) must update all visible surfaces — the postflight gate makes this automatic."

---

## INSTRUCTION — 2026-05-07 — preflight: /sessions disk-guard
[opportunistic]

Add `scripts/preflight_disk_guard.sh` invoked from `scripts/session_preflight.sh`.
Behaviour: `df --output=avail /sessions | tail -1` — if < 500 MB, write a
`## INCIDENT` block to `DISPATCH_OUTBOX.md` with the disk-usage snapshot and
exit non-zero. Rationale: `/sessions` at 100% silently broke `git config --global`,
`pip install`, and `npm install` in 3/3 of the last daily sessions
(May 2 / 3 / 4). Source: `reports/support_triage_2026-05-07.md`.

Expected deliverable: one new script + one line in preflight + a test that
mocks `df` output below threshold and asserts non-zero exit.

---

## INSTRUCTION — 2026-05-07 — investigate: health-check side-channel via GH Actions
[research]

Context: 3/3 of the last daily sessions logged "Production health NOT VERIFIED —
sandbox network egress blocked Railway domain (cowork-egress-blocked)". Even
the `/api/health` smoke-test the postflight script wants to do as a deploy-gate
cannot run from the sandbox.

Investigate: a GitHub Actions workflow on a 15-min cron that curls
`https://web-production-de6eb.up.railway.app/api/health` and
`https://www.motoquant.in`, writes JSON to a gist (or a `health/` branch
in the repo). Sandbox sessions read the file via `git fetch` (which IS
permitted) instead of attempting the blocked egress.

Don't act yet — write findings to outbox with a one-page proposal (cron freq,
auth model for the gist, JSON schema, fallback if the workflow itself fails)
and ask before implementing.

Source: `reports/support_triage_2026-05-07.md`.

---

## INSTRUCTION — 2026-05-07 — fix: bike_repo year-suffix matching for upsert
[opportunistic]

Root cause already documented in CLAUDE.md May-4 entry: `bike_repo.create_model`
upsert fallback doesn't strip `(YYYY-YYYY)` model-name suffixes before matching
against existing rows, so re-running `python3 -m motoquant.run import --known-bikes`
inserts phantom duplicates whose `model_name` carries the suffix. May-4 hit
this with 35 phantom rows on first attempt; the workaround was
`git checkout HEAD -- motoquant.db` then a manual 2-bike `import_batch` call.

Fix: in `motoquant/database/bike_repo.py::create_model`, normalise
`model_name` by stripping a trailing ` \(\d{4}-\d{4}\)` regex group before
the lenient `(manufacturer_id, model_name) ORDER BY year proximity` fallback
match. Add a regression test in `tests/test_scraper.py` that imports the same
bike list twice and asserts row count doesn't grow.

Source: `reports/support_triage_2026-05-07.md`.

---

## INSTRUCTION — 2026-05-07 — bootstrap: analytics + apply S5 auth-DDL on prod DB
[opportunistic]

This is the new top-1 standing priority (see CLAUDE.md "STANDING PRIORITIES" + `reports/product_priorities_2026-05-07.md`). Three sub-tasks, ship together:

1. **GA4** — add `<Script>` tag to `web/app/layout.js` with `NEXT_PUBLIC_GA_MEASUREMENT_ID` env var (placeholder OK for first ship; user supplies the real ID separately).
2. **PostHog free-tier** — wire to FastAPI `/api/*` middleware in `motoquant/api.py`. Capture endpoint + bike_id + user-agent + response time. PostHog Python SDK + env-gated init so dev tests don't dispatch.
3. **Apply S5 DDL on prod DB** — write `scripts/apply_s5_ddl.py` that calls `subscriptions_repo.ensure_tables()` + `users_repo.ensure_tables()` against `motoquant.db` (idempotent — uses `CREATE TABLE IF NOT EXISTS`). Run once locally, commit the migrated DB. Verify tables exist post-deploy via the GH-Actions health side-channel (instruction above).

Success metric: STATUS.md user-facing KPI rows show real (non-TBD) numbers within 14 days of ship; `users` table query returns ≥0 rows on prod (i.e., schema exists).

Source: `reports/product_priorities_2026-05-07.md` (top-1).

---

## INSTRUCTION — 2026-05-07 — research: bootstrap data/competitive_landscape.md
[research]

Context: the `competitive-intel` agent's output file `data/competitive_landscape.md` does not exist yet (verified 2026-05-07). This makes `opportunity_weight` in the master scheduler dead-input and product-prioritisation cannot factor competitor moves into ranking.

Bootstrap a one-time scan covering the 4 nearest products:

- **Bikes.app** (community ride-tracking + leaderboards) — pricing, free-tier limits, last visible feature ship
- **Dragy app** (GPS timeslip, the user-data layer we want to ingest) — recent updates, integration APIs (any open?), Indian-market presence
- **MotoCalc** (gear-ratio + power calculators, desktop) — feature set, last release, price
- **Tuneboss / Race-y / similar** — any Indian-market drag prediction tool? capture or note absence

Output: `data/competitive_landscape.md`, ~2 pages markdown, sections per competitor with `last_scanned: 2026-05-07`. Don't act on findings yet; future weekly competitive-intel runs will diff against this baseline.

Source: `reports/product_priorities_2026-05-07.md` (escalation: missing data).

---

## INSTRUCTION — 2026-05-07 — research: widen scraper tire-format validator for Indian bias-ply notation
[research]

Three consecutive autonomous catalog runs (May 4 Hero Xtreme 200S 4V, May 7 AM TVS Apache RTR 180, May 7 PM Hero Mavrick 440) hit cosmetic warnings from the scraper validator's tire-size regex. The current regex is hardcoded for ZR/R radial notation (`120/70ZR17`); Indian-market and small-cc commuter bikes commonly carry bias-ply notation like `100/80-17`, `90/90-17`, `110/70-17`, `150/60-17`. Each run produces 1-2 cosmetic warnings that drop the spec confidence score from ~0.85 to ~0.82 even though the spec itself is valid.

Proposal: extend the tire-size regex in `motoquant/scraper/validator.py` to accept `WWW/HH-RR` and `WWW/HH RR` (no Z, no R prefix), with NO confidence penalty for bias-ply hits — the format is legitimate for the affected segment, not a low-confidence flag. Test against the three bikes above to confirm the warnings clear.

Effort: ~30 min — single regex edit, one new test class. Low-risk.

Source: `reports/catalog_expansion_2026-05-07_pm.md` + carry-forward from May 4.

---

## INSTRUCTIONS QUEUE

> _Add new `## INSTRUCTION` blocks above this divider. Claude marks them `## DONE` once handled._

(none yet)

---

## DONE / DEFERRED ARCHIVE

> _Claude moves processed instructions here. Trim periodically — git keeps the full history._

(none yet)
