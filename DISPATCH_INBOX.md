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

## DONE — 2026-05-07 — sync all headline numbers + regen OG social card + wire postflight auto-patch gate
[urgent] · resolved 2026-05-08 by autonomous session 1778200249-734

Resolution summary — the implementation landed earlier (audit script `--fix`/`--regen-og` flags + postflight `headline_sync_gate` step 2.5 were already in `scripts/audit_headline_stats.py` and `scripts/session_postflight.sh` as of the 2026-05-04 catalog session). Today's session (2026-05-08) verified the wiring against fresh drift:

- 2026-05-08 audit run reported 5 drift sites (`web/app/page.js` × 3, `web/app/blog/how-the-motoquant-physics-engine-works/page.js` × 1, `README.md` × 1) all declaring `339` while DB-truth is `341` (DB has 339 rows but `all_known_bikes` user-facing tier resolves to 341 via the source-of-truth derivation rule — see audit script comments).
- This commit's postflight run will (a) auto-patch the 5 drift sites in place, (b) regenerate `web/public/og-image.png` because its mtime is older than `motoquant.db`, (c) append the fixed files to COMMIT_FILES so the drift fix rides this same commit (no separate `chore(headline-sync)` commit).
- Reference baselines K5 / R1 / Hayabusa preserved at +0.0000s (preflight gate verified, postflight will re-verify before push).

If a future session shows fresh drift, the same gate handles it automatically — no human intervention required.

[original instruction preserved below for the historical record]
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

## INSTRUCTION — 2026-05-16 — [self-review] design notes for GH-Actions side-channel (read before implementing)
[urgent]

**Attribution:** self-review M1 2026-05-16 follow-up Section A. Companion to the existing `[urgent]` INSTRUCTION below ("build GH-Actions health-check side-channel"). Read `reports/self_review_2026-05-16_followup.md` Section A in full before writing any YAML.

Six design tightenings the morning's minimum-viable-build under-specified:

1. **Cron cadence:** drop from `*/30 * * * *` to `0 */6 * * *` (4 runs/day). The May 9-15 failure mode is a 7.5-day silence; catching it on a 6h vs 30-min schedule produces the same outcome and is 12× cheaper on Actions minutes budget (matters if the repo flips private). Pair with the alert threshold at 36h — gives 6 polling windows before fire-true-alert, correct flap protection.
2. **Curl timeouts:** bump `-m 10` → `-m 20`. Railway Hobby cold-starts run 8-12s; 10s creates false-positive `fail` JSON. Specify `-X GET` for `/api/health` and `-I` (HEAD) for `motoquant.in/`.
3. **JSON schema additions:** include `api_latency_ms`, `web_latency_ms`, `workflow_sha`, `commit_sha_at_check` in `latest.json`. Without latency fields the signal is binary and degradation can't be graphed.
4. **Side branch + rolling history:** pin `git checkout -B health && git push -f origin health` (never merged to main). Keep `health/latest.json` plus `health/history.jsonl` capped to 7-day rolling window. Sandbox reads via `git fetch origin health && git show origin/health:latest.json`.
5. **PAT scope and rotation:** dedicated fine-grained PAT, scope Contents:R+W only, repo-scoped not org-scoped, stored as `HEARTBEAT_PAT` GH Actions Secret. Add a workflow startup step `gh api user` to verify token alive; on 401 mark workflow failed (the red X in the Actions tab is the user's only OOB signal). Default expiry 90 days — needs calendar reminder for rotation.
6. **Race on the INCIDENT push to main:** the workflow's `git push origin main` for the INCIDENT block will race with autonomous-session postflight pushes. Pin `git pull --rebase` with retries. Spec the INCIDENT block format as `## INCIDENT — YYYY-MM-DDTHH:MM:SSZ — heartbeat — <reason>` to match the existing `## SESSION` parser pattern.

Also fix this BEFORE the side-channel ships: per follow-up Section B.2 + B.3, `STATUS.md _LAST_RUN_JSON._updated` and the top-level `last_run:` placeholder are both `null` because the postflight script does not write them. The side-channel's staleness check evaluates `null → unparseable → false-positive alert on first run`. See separate INSTRUCTION below for the postflight fix.

Done when: the original implementation (INSTRUCTION below) lands incorporating all six tightenings.

Source: `reports/self_review_2026-05-16_followup.md` Section A.

---

## DONE — 2026-05-17 — [self-review] postflight updates STATUS.md timestamps
[opportunistic — resolved]

**Resolution:** session 1778992230-620 (2026-05-17, Path C of the META INSTRUCTION at line 427).

- New script `scripts/stamp_status_timestamps.py` — stamps both `_LAST_RUN_JSON._updated` and the top-level `last_run:` placeholder with the current UTC ISO timestamp. Idempotent. Exits non-zero on missing/malformed STATUS.md.
- Wired into `scripts/session_postflight.sh::main()` as `stamp_status_timestamps()` between `headline_sync_gate` and `stage_files`. Auto-appends `STATUS.md` to `COMMIT_FILES` (de-duplicated) so the bump rides the same commit — no separate chore commit.
- Regression suite: `tests/test_status_timestamp_stamp.py` — 7 tests covering null→stamp, prior-timestamp overwrite, idempotency with same `--now`, missing-file error, malformed-STATUS error, the public `stamp()` function's change-flag return, and a smoke test against the live STATUS.md so format drift is caught immediately. All 7 green.
- Unblocks INBOX:341 (GH-Actions heartbeat side-channel) Section A.4 — the staleness check now has a non-null timestamp to read.

Source: `reports/self_review_2026-05-16_followup.md` Section B.2 + B.3.

---

## Original instruction (preserved for traceability)

[opportunistic]

**Attribution:** self-review M1 2026-05-16 follow-up Section B.2 + B.3. The `_LAST_RUN_JSON._updated` field at STATUS.md line 103 and the top-level `last_run:` placeholder at line 123 are both `null` even after the morning M1 session successfully pushed. The postflight script writes per-agent `date` and `outcome` fields under `_LAST_RUN_JSON.<agent_name>` but does NOT write the top-level `_updated` field nor the `last_run:` line.

**Why it matters:** the GH-Actions heartbeat side-channel (urgent INSTRUCTION above) reads `_updated` to decide if the system has gone dark. If `_updated` stays `null`, the staleness check will misfire on the first cron tick — either as a permanent false-positive (`null > 36h ago`) or it skips the check entirely. Either way the alert is broken before it ships.

**Proposed fix:** in `scripts/session_postflight.sh`, after the per-agent state update, also stamp:
- `_LAST_RUN_JSON._updated` ← `$(date -u +%Y-%m-%dT%H:%M:%SZ)`
- The `last_run:` placeholder at STATUS.md (search for the `<!-- AUTO-UPDATED — used by catchup_detect` comment marker and rewrite the line) ← same ISO timestamp.

Both writes are single-line sed substitutions; the changes ride the same commit as the agent's work (no separate commit). Add a regression case: postflight on a no-op session should still bump `_updated`.

**Effort:** ~30 min. Low-risk. Unblocks Section A.4 of the GH-Actions design above.

Source: `reports/self_review_2026-05-16_followup.md` Section B.2 + B.3.

---

## INSTRUCTION — 2026-05-16 — [self-review] build GH-Actions health-check side-channel
[urgent]

**Attribution:** self-review M1 2026-05-16 Finding 2.1 + the May 9-15 dark-window incident (zero commits for 7.5 days, no `## INCIDENT` block written because no observer existed).

A `[research]` instruction queued 2026-05-07 already proposed investigating this — promoting to `[urgent]` with direct attribution. Without it, future cron/wrapper regressions will silently extend dark windows for days.

**Minimum viable build:**
1. `.github/workflows/heartbeat.yml` — cron `*/30 * * * *` (every 30 min)
2. Job: `curl -s -m 10 https://web-production-de6eb.up.railway.app/api/health` and `https://www.motoquant.in` (HEAD only, just status)
3. Write `health/latest.json` (or a side branch) with `{ "checked_at": "...", "api": "ok|fail", "web": "ok|fail", "bike_count": N }`
4. Additionally: read `STATUS.md _LAST_RUN_JSON._updated`; if >36h stale, write `## INCIDENT — heartbeat — no autonomous activity >36h` to `DISPATCH_OUTBOX.md` via the workflow's own `git push` (use a GH-Actions-scoped PAT, not the user's primary)
5. Sandbox sessions read `health/latest.json` via `git fetch && git show origin/health:latest.json` instead of attempting blocked egress.

**Done when:** the workflow runs for 7 days, catches one synthetic outage (test by manually pausing the cron), and the OUTBOX gets an INCIDENT block from CI.

**Expected impact:** dark windows ≤2 days instead of ~8 days. Resolves the single biggest root cause this week.

---

## INSTRUCTION — 2026-05-16 — [self-review] promote standing-priorities → queue_weight boost
[opportunistic]

**Attribution:** self-review M1 2026-05-16 Finding 2.4. The top-1 standing priority "bootstrap analytics + apply S5 auth-DDL" sits in INBOX tagged `[opportunistic]` (queue_weight = +10) for 9 days while being CLAUDE.md's #1 priority. Severity tag and CLAUDE.md priority disagree.

**Proposal:** Extend `scripts/master_scheduler.sh::queue_weight` to also scan the `## STANDING PRIORITIES — top-3` section of CLAUDE.md and apply a +25 boost to any agent whose name appears as a keyword in those priorities. Cap: only the top-3 priorities count; no compounding stacking.

**Why this is approval-needed:** scoring-formula change → policy table says INBOX.

**Effort:** ~1 hr — single bash function + a unit-style test of the parser. Low-risk; weights and priorities are both static files.

**Done when:** for the current state of CLAUDE.md, dispatching the scheduler in `--dry-run` shows an agent matching "analytics" / "surrogate" / "release pipeline" gets +25 in its detailed scoring breakdown.

---

## INSTRUCTION — 2026-05-16 — [self-review] fix postflight outbox truncation bug
[opportunistic]

**Attribution:** self-review M1 2026-05-16 Finding 2.5. Multiple `## SESSION` blocks in DISPATCH_OUTBOX.md show `> ## Work performed` as the final line of the embedded session-log heredoc — content after the header is being eaten by the postflight script's quoting / heredoc handling.

**Repro:** scroll through DISPATCH_OUTBOX.md; sessions `1778175630-727` / `1778178639-614` / `1778185843-631` / `1778193038-619` / `1778200249-734` / `1778214642-622` / `1778221840-619` all show this truncation. Session `1778207448-655` and the May-4 setup entry have correct full content, so the bug isn't 100% — it's intermittent or depends on session-log content.

**Investigation needed before fix:** which postflight code path writes the embedded `## Work performed` block. Probably a here-doc with an unescaped sentinel, or a `cat $SESSION_LOG` that hits a `## ` line that's interpreted as a new section by the outer parser.

**Effort:** ~1 hr investigation + ~30 min fix. Cosmetic only — data is not lost (the actual commit + session log file are fine), only the outbox embed is truncated.

---

## INSTRUCTION — 2026-05-16 — [self-review] bootstrap motoquant.skill for Claude
[opportunistic]

**Attribution:** self-review M1 2026-05-16 Layer 3 + CLAUDE.md TOOLKIT REFERENCE "Adopt this quarter ★".

**Proposal:** Use the `skill-creator` skill to write `skills/motoquant.skill/` that teaches Claude:
- The bike spec schema (`BikeSpec`, `BikeConfig`, `EngineParams`, `DrivetrainParams`)
- The 8-cluster category taxonomy (litre_sport_195p / litre_sport_600_1000 / mid_twin_*_700 / entry_*_300 / two_stroke / cruiser_1300p)
- Drag glossary (60-foot, ET, trap, two-step, anti-squat, slipper, expansion chamber)
- The K5/R1/Hayabusa reference baselines (10.0334 / 10.2859 / 10.4712 — never touch)
- The standing dispatch protocol (INBOX/OUTBOX)
- The standing hygiene rules (CLAUDE.md hygiene section)

**Done when:** a fresh session can answer "what cluster does the Z H2 SE fall in?" without first reading 9 files.

**Effort:** ~2 hr — mostly extracting and condensing from CLAUDE.md.

---

## INSTRUCTION — 2026-05-16 — [self-review] add wrapper smoke-test in preflight
[opportunistic]

**Attribution:** self-review M1 2026-05-16 Finding 2.1 root-cause prevention. After May 7 saw THREE wrapper regressions in one day (CRLF, stdin-redirect, MINGW path), the system shipped to production without a smoke-test for the wrapper itself. May 9-15 silence suggests at least one more wrapper-class regression occurred and went unnoticed.

**Proposal:** Add `scripts/preflight_wrapper_smoke.sh` that:
1. Runs `claude --version` with `< /dev/null` and `-p ''` to verify it doesn't hang
2. Verifies `scripts/run_autonomous_session.sh` syntax with `bash -n`
3. Verifies all shebang lines + line endings on `scripts/*.sh` (LF only)
4. Writes a one-line PASS/FAIL to `preflight.env`

Invoked from `scripts/session_preflight.sh` before mutex acquisition.

**Done when:** intentionally introducing a CRLF into one of the wrapper scripts fails the next preflight with a clear error message.

**Effort:** ~1 hr.

---

## INSTRUCTION — 2026-05-17 — [self-review] META: 14 INSTRUCTIONs unprocessed — pick a remediation path
[urgent]

**Attribution:** self-review M3 2026-05-17 (`reports/self_review_2026-05-17.md` Layer 4 + Finding 3.1). Replaces issuing more individual INBOX items per the brief's "if dominant signal is M1/M2 queued items still unprocessed, write ONE meta-INSTRUCTION instead".

**The fact:** 14 INSTRUCTIONs are queued in this file, none have moved to `## DONE` since 2026-05-07. 6 are 10 days old (lines 197, 212, 234, 254, 269, 287); 8 are 1 day old (lines 300, 322, 341, 361, 376, 389, 408, 427). Counted backlog growth since system shipped 2026-05-04: **+15 queued / 0 consumed.** The kaizen loop is structurally write-only.

**Three remediation paths — pick one (or combine):**

**Path A — Approve building `inbox-implementer` (INBOX:427) as the immediate next priority.** This is the structural fix M2 identified. Once an agent exists whose scope is "consume the oldest urgent INBOX item per session", every future self-review run becomes net-zero or net-negative rather than net-positive. Effort: ~2 hours per INBOX:427's Done-when block. **Recommended.**

**Path B — Manually triage the 6 items from 2026-05-07.** Some may be stale (e.g., INBOX:234 `bike_repo year-suffix matching` may have been done implicitly by a catalog-expansion session — quick `git log --all -S "year_suffix" -- motoquant/database/bike_repo.py` would tell). Mark stale items `## DEFERRED` with reason. Shrinks the surface area before any implementer agent picks them up. Effort: ~30 minutes user-side.

**Path C — Dispatch the next session manually with line-number priority list.** E.g., "implement INBOX:322 (postflight `_updated` stamp) + INBOX:376 (outbox truncation) in that order; mark DONE on completion." Bypasses the agent infrastructure for one cycle. Effort: per-item; INBOX:322 is ~1 hour, INBOX:376 is ~1 hour (both shell-script edits to `scripts/session_postflight.sh`).

**Dependency order if Path A or C picks the GH-Actions side-channel chain (per Finding 3.5):**

```
INBOX:322 (postflight writes _updated)        — prerequisite for staleness check to function
 └─> INBOX:376 (fix OUTBOX heredoc truncation) — prerequisite for cron to parse OUTBOX
      └─> INBOX:300 (read side-channel design notes)
           └─> INBOX:341 (build the side-channel itself)
```

Implementing INBOX:341 before INBOX:322 + INBOX:376 produces false-positive alerts on first cron tick (per M1 followup Section A.4 + B.2/B.3 + M3 Finding 3.5).

**Done when:** any one of Paths A/B/C is chosen and at least 1 of the 14 listed INSTRUCTIONs moves to `## DONE` with a citing commit SHA. M3 commits to NOT queueing any more `[self-review]`-tagged items until backlog drops below 8.

**Cooldown note:** per `scripts/agents/self-review.md:64`, no further self-review runs before **2026-05-22**.

### RESPONDED — 2026-05-17 — session 1778992230-620 — Path C chosen

The scheduler picked `self-review` for today's dispatch despite the 5-day cooldown rule + this META's own cooldown lockout. Session honoured the cooldown and skipped `self-review`. Instead:

- **Path C selected** (line-number priority list, single-cycle bypass of agent infrastructure).
- **INBOX:322 implemented and moved to ## DONE** above (postflight `_updated` stamp + 7-test regression suite + idempotency + smoke against live STATUS.md).
- **INBOX:376 deferred** to the next session that has time for the investigation: the root-cause is a heredoc-quoting interaction in `append_outbox()` that needs reproduction first, not a simple sed swap. Out of session budget today after running 2 agents + 1 manual fix.
- **No new `[self-review]`-tagged items queued** this session, per M3's stated commitment.
- Catalog-expansion + performance-monitor both ran successfully alongside this fix — net session output: +3 bikes, +1 perf data row, +1 INBOX item closed.

Backlog now: 13 pending (was 14). One down. Path A (build `inbox-implementer`) remains the better structural fix — defer to next non-cooldown self-review-eligible window.

---

## INSTRUCTION — 2026-05-16 — [self-review] add `inbox-implementer` agent (meta-fix for stalled kaizen queue)
[urgent]

**Attribution:** self-review M2 2026-05-16 (`reports/self_review_2026-05-16_m2.md` Layer 4 + capability-frontier sections). Last 14 days produced 7 `[self-review]`-tagged INSTRUCTIONS (INBOX:300, 322, 341, 361, 376, 389, 408) plus 6 carry-over from 2026-05-07 — none implemented. Root cause: the 14 agents in `scripts/scheduler_weights.json::agents` all *generate* work, none *consume* INBOX backlog. Toolkit star-list (CLAUDE.md TOOLKIT REFERENCE) has 6 of 8 items untouched 17 days after listing — same shape.

**Proposed agent:**

- Name: `inbox-implementer`
- Scope: each session, pick the oldest `[urgent]`-tagged INSTRUCTION in DISPATCH_INBOX whose scope fits within one session budget (≤ ~3 hrs, ≤ 5 files touched, no external infra change). Implement it. Mark `## DONE` with `### Result` block citing commits + diffs.
- Don't-do list: do NOT pick INSTRUCTIONs requiring user secrets (PAT rotation, Razorpay plan setup, SMTP creds), live-service infra (DNS, Vercel project deletes), or multi-session efforts (PostgreSQL migration). Defer those with a note in `## RESPONDED` heading.
- Prompt template lives at: `scripts/agents/inbox-implementer.md` (write a draft along with this — see `scripts/agents/self-review.md:45` rule).
- Scheduler weight: base 45, best_dow [2, 4] (mid-week — gives Mon catalog + Sat self-review room).

**Why urgent:** without this agent, every future self-review run is write-only. The 7 INBOX items queued today will still be there next Saturday. Closing the loop is worth more than any single feature ship per CLAUDE.md Kaizen Principle.

**Done when:**

1. `scripts/agents/inbox-implementer.md` written (mirror existing agent-template structure)
2. Added to `scripts/scheduler_weights.json::agents` with `{ "base": 45, "best_dow": [2, 4] }`
3. First implementer run picks an INBOX item and marks it `## DONE` with attribution
4. STATUS.md `_LAST_RUN_JSON.inbox-implementer` row added

**Effort:** ~2 hrs for agent template + scheduler wiring + first dry-run. Item consumption ongoing.

---

## INSTRUCTIONS QUEUE

> _Add new `## INSTRUCTION` blocks above this divider. Claude marks them `## DONE` once handled._

(none yet)

---

## DONE / DEFERRED ARCHIVE

> _Claude moves processed instructions here. Trim periodically — git keeps the full history._

(none yet)
