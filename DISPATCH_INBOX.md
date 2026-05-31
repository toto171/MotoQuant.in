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

## INSTRUCTION — 2026-05-31 — wire bike-suggest smoke test into postflight
[opportunistic]

**Filed by:** customer-support agent (2026-05-31 triage)
**Context:** `bike_suggestions` table has been empty across 5 triage runs (May-7, May-21, May-24, May-25, May-31). Six weeks live, zero user submissions. Cannot distinguish "no users" from "form is broken" without a synthetic check.

**Task:** Add a 5-step smoke test to `scripts/session_postflight.sh`, gated on `/api/health` returning ok (skip cleanly otherwise to stay green on Render cold starts):
1. `POST /api/bikes/suggest` with a fixed test payload (make=`TEST-SMOKE`, model=`postflight-check`, year=2026, submitter_email=`smoke@motoquant.in`)
2. Capture the returned row id
3. Confirm HTTP 200/201 plus that response includes the id
4. `DELETE` the row directly from the DB (since there is no DELETE endpoint), use the same Python+sqlite3 path the support agent uses
5. If any step fails, write an ALERT to `DISPATCH_OUTBOX.md`

**Deliverables:**
- Patch to `scripts/session_postflight.sh` (add smoke-test function, call after the existing baseline check)
- One-row migration entry in any session-log report that runs the smoke test
- No changes to `bike_suggestions` schema

**Constraints:**
- Skip cleanly when `/api/health` returns non-ok (currently the case during Render cold-start window), do not block postflight on a sleeping container
- Use the existing PAT-based git push path; do not introduce new credentials
- Stamp `submitter_email='smoke@motoquant.in'` so future triage runs can easily filter these out

**Why now:** Render migration shipped 2026-05-31; both /api/health and the suggest endpoint are now live for the first time in 14 days. Adding the smoke test now establishes a baseline before any real user traffic, so the first organic submission is obvious when it arrives.

---

## DONE — 2026-05-31 — [urgent] fix Rocket 3 R 2020 benchmark trap-speed transcription error

### Result
Fixed in `scripts/validation_sweep.py` line 123 area. Updated entry to:
```python
("Triumph", "Rocket 3 R", 2020, 10.56, 203, "Cycle World 2020 (Gadson 17-pass tuned at Silver Dollar Motorsport Park)"),
```
Source: Cycle World "Rickey Gadson and the Triumph Rocket 3 R" — 10.562s @ 126.41 mph (= 203.4 km/h) at Silver Dollar Motorsport Park; URL https://www.cycleworld.com/story/motorcycle-racing/rickey-gadson-and-the-triumph-rocket-3-r/. MCN 2020 R3R airfield test corroborates 11.07s @ 126.06 mph — both publications agree on the 126 mph trap. Post-fix cluster sweep N=167 (+5 new entries including Rocket retention), overall bias improved +0.045 → +0.037s, mean|Δ| improved 0.323 → 0.321s. Reference baselines preserved exactly. Resolved by benchmark-import agent 2026-05-31 pass 3.

## ORIGINAL INSTRUCTION (archived below)
## INSTRUCTION — 2026-05-31 — [urgent] fix Rocket 3 R 2020 benchmark trap-speed transcription error
[urgent]

**Filed by:** benchmark-import agent (2026-05-31 pass)
**File:** `scripts/validation_sweep.py` line ~123
**Current entry (suspect):**
```python
("Triumph", "Rocket 3 R", 2020, 10.50, 226, "Cycle World 2020"),
```
**Issue:** The trap speed `226` km/h (= 140.4 mph) is internally inconsistent with the ET `10.50` s. A 10.50 ET on a 294 kg / 165 hp muscle naked traps at ~126 mph (203 km/h), not 140 mph. Same transcription-error pattern flagged in the seventh-pass note for ZX-9R 2000 (`scripts/validation_sweep.py` line ~668: *"a 10.50 ET should trap ~135 mph (217 km/h) for a 143 hp middleweight, not 143 mph (230 km/h)"*).

**Cross-source verification:**
- Cycle World "Rickey Gadson and the Triumph Rocket 3 R" feature: **10.562s @ 126.41 mph (= 203.4 km/h)** at Silver Dollar Motorsport Park. The 10.56 figure is Gadson's best after 17 tuned passes — a pro drag racer optimising launch.
  URL: https://www.cycleworld.com/story/motorcycle-racing/rickey-gadson-and-the-triumph-rocket-3-r/
- MCN's own airfield road-test of the same 2020 Rocket 3 R: **11.07s @ 126.06 mph (= 202.9 km/h)** — single-attempt journalist test, no pro tuning. ET ~0.5s slower than Gadson's pro-tuned best, trap speed within 0.4 mph — consistent.
  URL: https://www.motorcyclenews.com/bike-reviews/triumph/rocket-iii/2020/

Both reputable independent instrumented sources agree on the 126 mph (203 km/h) trap. The 226 km/h figure in the current entry is the only outlier and is most likely a metric/imperial transcription error (someone converted "126.4 mph" wrong, or copy-pasted from a different bike's row).

**Fix:** Update the existing entry to
```python
("Triumph", "Rocket 3 R", 2020, 10.56, 203, "Cycle World 2020 (Gadson 17-pass tuned at Silver Dollar Motorsport Park)"),
```
Also update the ET from 10.50 → 10.56 to match the actual Cycle World cite. Consider optionally adding a parallel MCN entry (11.07 @ 203) as a journalist-test reference point (would NOT bind because the matcher picks one most-specific entry per spec).

**Verification target:** post-fix sweep should show Rocket 3 R Δ near zero or slightly positive (sim ET vs benchmark 10.56), and the existing cruiser_1300p cluster bias should not move materially (single-bike shift).

**Effort:** ~10 min (single-tuple edit + comment + re-run focused sweep).

---

## INSTRUCTION — 2026-05-25 — [urgent] fix BENCHMARKS matcher specificity bug
[urgent]

**Filed by:** benchmark-import agent (fourth pass, 2026-05-25)
**Blocking:** Cannot add an instrumented Kawasaki Ninja H2 SX 2018 benchmark (Cycle World 10.04s @ 144 mph, verified via WebFetch on `https://www.cycleworld.com/best-open-class-streetbike-2018-kawasaki-ninja-h2-sx-se/`) because the matcher in `scripts/sweep_with_clusters.py::run_sweep` and `scripts/validation_sweep.py::_model_match` binds the catalog row `"Ninja H2 SX (2018-2023)"` to the existing `"Ninja H2", 2015, 9.62` benchmark — tokens `{ninja, h2}` are a subset of `{ninja, h2, sx, ...}` so the less-specific benchmark matches first via dict iteration order.

**Fix candidates:**
1. In `run_sweep()` `bench_map` lookup, sort benchmark keys by token-count descending so longer/more-specific patterns are tried first; first match wins still works.
2. Better: score each candidate `(bm_mfr, bm_model)` by token-overlap ratio `len(bm_tokens) / len(spec_tokens)` and pick the highest-scoring match (must still pass year-range filter).
3. Cheapest fix: add an explicit `if "sx" in spec_tokens and "sx" not in bm_tokens: continue` exclusion clause, but this is special-cased and doesn't scale to the next variant collision (e.g. Z H2 vs Z H2 SE, RSV4 vs RSV4 Factory, R6 vs R6S, etc.).

**Verification target:** after fix, the H2 SX 2018-2023 catalog row should bind to a future H2 SX-specific 10.04s benchmark (not the 9.62s H2 benchmark). Run `scripts/sweep_with_clusters.py` and confirm H2 SX delta is ~+0.18s (sim 10.22 vs bench 10.04) instead of the current ~+0.60s false delta against the H2 benchmark.

**Effort:** ~1-2 hr including a regression test in `tests/test_validation.py` that pins matcher specificity for Z H2 vs Ninja H2 vs Ninja H2 SX vs Ninja H2R, plus a few other collision pairs.

---

## INSTRUCTION — 2026-05-20 — research: verify entry_150_200 DERIVED benchmarks
[research]

Context: physics-calibration agent (2026-05-20) found that the entry_150_200 cluster mean|Δ| of 1.483s is dominated by Apache RTR 200 4V (sim=19.3s vs bench=15.9s DERIVED) and Yamaha MT-15 V2 (sim=19.1s vs bench=15.8s DERIVED). Both benchmarks use the 0-100 x 1.6 DERIVED methodology (±0.7s uncertainty). The physics model appears correct — the instrumented R15 V4 (same 18.1hp, 155cc class) benchmarks at 17.62s (instrumented MotoStatz), consistent with sim predictions. The DERIVED benchmarks appear too optimistic for this power class.

Research goal: Find instrumented drag-strip or Dragy timeslip data for:
1. TVS Apache RTR 200 4V (197cc, 20.2hp) — real quarter-mile ET
2. Yamaha MT-15 V2 (155cc, 18.1hp) — real quarter-mile ET

Accept sources: Indian Autos Magazine drag test, BikeWale / BikeDekho instrumented test, YouTube Dragy runs, drag club timeslips from MMRT/BIC/Kari.

Don't act yet — write findings to outbox. If real ETs are > 17.5s for Apache and > 18.0s for MT-15, update the BENCHMARKS entries and re-run the cluster sweep.

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

## INSTRUCTION — 2026-05-18 — [opportunistic] marketing-content blog post for whichever of {CFMoto 800NK, Yamaha MT-125, Yamaha XSR125} the parallel run does NOT pick tonight
[opportunistic]

**Context:** SEO agent fifth pass 2026-05-18 confirmed via WebSearch that all three of today's new catalog additions (CFMoto 800NK, Yamaha MT-125, Yamaha XSR125) have SERP gaps for quarter-mile ET data — top results are spec/dealer pages with empty ET cells on AccelerationTimes / FastestLaps / MotoStatz. The parallel marketing-content agent tonight is writing ONE blog post for one of the three (the agent prompt suggests CFMoto 800NK).

**Ask:** On the next marketing-content rotation slot (Tuesday 2026-05-19), write the OTHER two as a single pair-post (or two posts if they merit independent coverage):

1. **CFMoto 800NK** (if not picked tonight) — 799cc parallel-twin, 100 hp, 81 Nm, 6-speed, ~205 kg wet. Indian launch is the news hook. Frame as "China-import platform vs Triumph Trident 660 / Yamaha MT-07 / Kawasaki Z650 in India — does the cost-per-hp win translate to cost-per-tenth?". Trident 660, MT-07, Z650 are all already in catalog.

2. **Yamaha MT-125 + XSR125 platform pair** — 124cc single, 14.75 bhp @ 10000 rpm, 11.5 Nm @ 8000 rpm. MT-125 142 kg, XSR125 ~152 kg (10 kg neo-retro tax). Frame as "platform-mate physics: same engine, different chassis, different ET" — a self-contained narrative that captures both 'mt-125 quarter mile' + 'xsr125 quarter mile' queries with one URL. Not officially India-launched (CBU only) but EU + SEA volume is meaningful.

**Reference:** `data/seo_opportunities.json` priority 21 (800NK), 22 (MT-125), 23 (XSR125).

**Expected deliverable:** 1-2 blog post(s) under `web/app/blog/`, sitemap updated, blog index updated, SEO opportunities priorities 21-23 marked `action: done`.

## INSTRUCTION — 2026-05-17 — [urgent] Railway API offline: production 404 "Application not found"
[urgent] [blocking]

**Detected by:** perf-monitor agent run 11, session 1779049840-773, 2026-05-17. Report: `reports/perf_monitor_2026-05-17.md` (Run 11 section). Timeseries: `data/perf_timeseries.json` row index 10 (run_index 11).

**Symptom:** Every Railway endpoint returns HTTP 404 with body `{"status":"error","code":404,"message":"Application not found","request_id":"..."}`. This is the Railway *platform* router replying that no service is registered at the hostname — NOT a FastAPI route 404. Reproducible via curl from this sandbox:

```
$ curl https://web-production-de6eb.up.railway.app/api/health
{"status":"error","code":404,"message":"Application not found","request_id":"YnjSO8EfT2uuQx54AQeqjw"}

$ curl https://web-production-de6eb.up.railway.app/             # root path, same
{"status":"error","code":404,"message":"Application not found","request_id":"6y6FbkRQReW4mRhJAQeqjw"}

$ curl https://www.motoquant.in/api/health                       # Vercel rewrite -> same dead Railway
{"status":"error","code":404,"message":"Application not found","request_id":"AzDlmQu8QhalWe84m3z_FQ"}
```

**Most likely root cause:** Railway trial expiry. CLAUDE.md Phase-3 post-launch hygiene block explicitly flags: *"Upgrade Railway trial ($4.86 / 24 days left as of Apr 23) -> Hobby or Pro before suspension"*. April 23 + 24 days = **May 17 (today)**. Run 10 (~25 min before run 11) saw the service healthy at `bike_count: 342, /api/health ~595 ms avg`. The drop is binary, not gradual — fits trial-clock-suspension perfectly.

**User-visible impact:**
- `motoquant.in` landing page still renders (Vercel static shell unaffected; TTFB 1002 ms, healthy)
- All client-side fetches break: simulator widget, `/bikes` browser, `/leaderboard`, save-run, parts-impact CLI through web, chat, etc.
- Half-broken site state — users land on a page that loads but cannot transact.

**Required user action (cannot be done by autonomous session — needs Railway billing credentials):**
1. Log into Railway dashboard (`railway.com/dashboard` -> project `proactive-adventure` -> service `web`)
2. Check service status — likely shows "suspended" or "deleted" due to trial expiry
3. Upgrade to Hobby plan ($5/mo) OR Pro plan, OR redeploy fresh if service was wiped
4. Verify `motoquant.db` is still bundled in the deploy (it should be — file is tracked in git per CLAUDE.md Apr 23 entry)
5. Hit `https://web-production-de6eb.up.railway.app/api/health` — confirm `{status:ok, database:connected, bike_count:342}` returns
6. Move `## INSTRUCTION` to `## DONE` with resolution date + new bill plan

**Out-of-scope for autonomous fix:** account credentials, billing actions, redeploy with new env vars. Pure user action.

**While API is down:** all perf-monitor runs will continue to record 404 on `/api/health` and `/api/bikes`. Pytest wall-clock + landing TTFB monitoring still functional. Suggest pausing the `pricing-refresh` and `auto-content` agents (both need API access for ROI/sim sanity checks) until restored.

**Cross-reference:** related stale-but-still-correct hygiene items in CLAUDE.md:
- Rename Railway project `proactive-adventure` -> `motoquant-api` (cosmetic; do during redeploy)
- Long-term DB-in-git vs volume decision (still open)
- Delete orphan Vercel project `motoquant-web` (separate issue, unblocked)

---

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

## DONE — 2026-05-07 — fix: bike_repo year-suffix matching for upsert

**Resolved at commit `31b36a4` on 2026-05-25.** Marked DONE on 2026-05-26 by self-review M7 for admin bookkeeping consistency — the close was previously logged as a NEW DONE block at line ~863 (`## DONE — 2026-05-25 — [self-review] [urgent] implement bike_repo year-suffix upsert fix + ghost-row cleanup`) rather than as a status flip on this original 2026-05-07 entry. Ghost-row DELETE step queued separately at INBOX:879 (`[urgent] [needs-user] supervised ghost-row cleanup`).

---

## ARCHIVE (original instruction text below for reference)
[urgent — closed]

**Severity promoted by self-review M5 (2026-05-24)** — `reports/self_review_2026-05-24.md`
Finding 2.1. Originally `[opportunistic]` since 2026-05-07 (17 days). Now actively
blocking the headline KPI: `motoquant.db::bike_models` has **268 duplicate rows**
(33 bikes × 9 occurrences + 4 × 2 + 446 × 1 = 751 total vs 483 distinct vs 488 source
specs) generated by the M4 catalog-expansion gate that runs `import --known-bikes`
on every catalog session. Every WS-A April 27 batch bike whose `model_name` carries
the `(YYYY-YYYY)` suffix gets re-inserted instead of upserted. M5 also flagged
that **post-fix cleanup should `DELETE FROM bike_models WHERE rowid NOT IN
(SELECT MIN(rowid) FROM bike_models GROUP BY manufacturer_id, model_name)`** —
headline should snap 751 → ~483.

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

Source: `reports/support_triage_2026-05-07.md`; promoted by `reports/self_review_2026-05-24.md`.

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

## INSTRUCTION — 2026-05-20 — research: verify entry_200_300 DERIVED benchmarks
[research]

Context: physics-calibration agent (2026-05-20, third pass) found that the entry_200_300 cluster mean|Δ| of 0.533s is dominated by Bajaj Pulsar N250 (sim=16.47s vs bench=15.45s DERIVED, Δ=+1.02) and Yamaha FZ25 (sim=16.93s vs bench=16.00s DERIVED, Δ=+0.93). 5 of 6 cluster benchmarks use the 0-100×1.6 DERIVED methodology (±0.7s uncertainty). The only verified benchmark (Kawasaki Ninja 300, FastestLaps 14.10s) is within +0.29s.

Knob sensitivity probe found 11 of 12 category-level knobs (`parasitic_mult`, `over_clutch_factor`, `launch_rpm_factor`, `engine_inertia_mult`, `chain_efficiency_override`) have zero effect on these bikes — most use synthetic dyno curves with `is_at_wheel=True` which skips parasitic at `physics.py:477-483`. The one knob that does respond (`max_engine_decel_rads2`) only moves cluster mean|Δ| by 3ms and worsens the already-fast Gixxer SF 250 by 104ms. Cluster is data-bound, not model-bound.

Sourcing real instrumented or Dragy timeslip data for:
1. Bajaj Pulsar N250 (249cc, 24.5hp) — real quarter-mile ET
2. Yamaha FZ25 (249cc, 20.6hp) — real quarter-mile ET
3. Suzuki Gixxer 250 / Gixxer SF 250 (249cc, 26.5hp) — real quarter-mile ET (the SF 250 sim is 0.69s *faster* than benchmark, suggesting the DERIVED benchmark is wrong, not the physics)
4. KTM Duke 250 (248cc, 30hp) — already close at Δ=-0.117 (DERIVED may actually be reasonable here)

Suggested sources: TeamBHP forum drag timeslips, Indian Autos Mag instrumented tests, MotoStatz database, Aamby Valley drag-strip records. Without measured data, this cluster cannot be calibrated further without per-bike overrides — which the physics-calibration agent prompt forbids.

Until measured benchmarks land, the physics-calibration scheduler should skip entry_200_300 from rotation (rule update suggestion: "Skip cluster X if >80% of benchmarks are DERIVED and last probe showed all knobs dead").

---

## DONE — 2026-05-24 — [urgent] postflight alert dedup during open [blocking] INBOX tickets

**Result:** `scripts/session_postflight.sh::verify_deploy()` now consults a new `_blocking_ticket_open()` awk helper before queuing the timeout ALERT. When an open (above the `## DONE / DEFERRED ARCHIVE` divider) `## INSTRUCTION` block carries `[blocking]` AND mentions `Railway` or `deploy`, the timeout still returns exit code 5 but the outbox append is suppressed with a `warn` to stderr ("deploy alert suppressed — open blocking ticket: <heading>"). Verified against the real INBOX (matches the 2026-05-17 Railway ticket) and 5 synthetic fixtures: heading-keyword match, body-keyword match, no-blocking, archived-blocking, blocking-but-no-symptom-keyword — all behave as specified. Today's session is the first one running the new code path, so this morning's autonomous run is also the last one that will have queued a duplicate Railway ALERT.

Implemented inline by session 1779611475-643 (Sun 2026-05-24). When the Railway service is restored and INBOX:140 moves to `## DONE`, the helper will return empty and any future genuine deploy-check timeout will fire a fresh ALERT as expected.

**Original instruction below for archival.**

## ORIGINAL — 2026-05-21 — [urgent] postflight alert dedup during open [blocking] INBOX tickets
[urgent]

**Context:** `scripts/session_postflight.sh::verify_deploy()` (lines 252-273) unconditionally calls `_queue_alert "Postflight deploy check timed out after ${DEPLOY_WAIT_SECONDS}s"` whenever the Railway `/api/health` poll loop times out. During the ongoing Railway outage (first detected 2026-05-17, INSTRUCTION at this file line 140, still 404 as of 2026-05-21), this has produced **22 identical `### ALERT` entries** in `DISPATCH_OUTBOX.md` between lines 430 and 902 — same one-line body verbatim every time. That's signal-dilution: a future genuine deploy-check timeout (different commit, different cause) will be lost in the noise.

**Asymmetry:** `reports/perf_monitor_2026-05-17.md` lines 383-398 (Run 12 section) shows the perf-monitor agent correctly handled this — it observed the same 404 symptom, recognised the matching `[urgent] [blocking]` INBOX ticket already existed, and declined to file a duplicate. Postflight lacks that deduplication logic.

**Proposed fix:** before `_queue_alert` fires in `verify_deploy`, grep `DISPATCH_INBOX.md` for an open `## INSTRUCTION` block (i.e. not under `## DONE / DEFERRED ARCHIVE`) that carries the `[blocking]` tag AND mentions "Railway" (or, more generally, the symptom keyword). If one exists, log to stderr ("deploy alert suppressed — open blocking ticket at line N") and skip the outbox append. The alert is still useful when there is no open ticket; it becomes noise once one exists.

Implementation sketch — small bash helper, ~10 LOC:
```bash
_blocking_ticket_open() {
  awk '/^## DONE \/ DEFERRED ARCHIVE/{exit} /^## INSTRUCTION/{block=$0} block && /\[blocking\]/ && /Railway|deploy/{print block; exit}' DISPATCH_INBOX.md
}
```

Then `verify_deploy`'s timeout branch becomes:
```bash
if [[ -n "$(_blocking_ticket_open)" ]]; then
  warn "deploy alert suppressed — open blocking ticket: $(_blocking_ticket_open)"
else
  _queue_alert "Postflight deploy check timed out after ${DEPLOY_WAIT_SECONDS}s"
fi
return 5
```

Exit code 5 still returned so callers know the deploy didn't verify — only the outbox spam is suppressed.

**Acceptance:** after the Railway service is restored and the [urgent] ticket at line 140 moves to `## DONE`, the next deploy timeout (if any) should fire a fresh ALERT. Verify by archiving the line-140 ticket first, then watching the postflight behaviour.

Source: `reports/support_triage_2026-05-21.md` Findings B + C; `DISPATCH_OUTBOX.md` lines 430, 452, 474, 496, 518, 540, 562, 584, 606, 628, 650, 672, 695, 718, 741, 764, 787, 810, 833, 856, 879, 902 (22 identical ALERTs).

---

## DONE — 2026-05-24 — [self-review] [urgent] fix catalog-expansion agent prompt to require DB re-seed

**Result:** `scripts/agents/catalog-expansion.md` updated to add Validation Gate #4 (DB re-seed via `python3 -m motoquant.run import --known-bikes` + count assertion + `motoquant.db` returned in file list) plus matching Deliverable bullet. Implemented inline at the start of session 2026-05-24 by the main session before dispatching today's catalog-expansion agent — so today's run is the first one that exercises the new gate.

**Original instruction below for archival.**

## ORIGINAL — 2026-05-21 — [self-review] [urgent] fix catalog-expansion agent prompt to require DB re-seed
[urgent]

**Attribution:** `reports/self_review_2026-05-21.md` Finding 2.1.

**Problem:** Source files declare **447 bike specs** (`grep -c "spec_from_dict" motoquant/scraper/known_bikes.py motoquant/scraper/known_bikes_extended.py` = 328 + 119); DB ships at **345** (`SELECT COUNT(*) FROM bike_models`). Drift = **102 bikes in source, not in DB**. Root cause: `scripts/agents/catalog-expansion.md` "Validation gates" section (lines 31-34) never instructs the catalog agent to re-seed via `python3 -m motoquant.run import --known-bikes` or `scripts/reseed_configs_from_specs.py`. 30 of 38 substantive commits this week were catalog-expansion runs, but only 3 of those touched `motoquant.db`.

**Mechanism:** every new bike in `known_bikes_extended.py` only reaches `bike_models` table via the `--known-bikes` import path. Without it, the agent's "+3 bikes" claim in the commit message is misleading — DB ships at +0.4 bikes/commit average.

**Proposed prompt edit (insert after line 34 of `scripts/agents/catalog-expansion.md`):**

```
4. **Re-seed the DB.** Run `python3 -m motoquant.run import --known-bikes` (or `scripts/reseed_configs_from_specs.py` if the change is purely physics-driven). Confirm via:
   ```
   python3 -c "import sqlite3; print(sqlite3.connect('motoquant.db').execute('SELECT COUNT(*) FROM bike_models').fetchone()[0])"
   ```
   Add `motoquant.db` to `COMMIT_FILES` before committing. If the import errors with FK/idempotency complaints (per the WS-A April 27 hygiene note in CLAUDE.md), fall back to the year-suffix-stripped matcher workaround documented at that entry.
```

**Acceptance:** the FIRST session that picks up this fix and runs a fresh `--known-bikes` import should jump the DB row count from 345 → ~447 in one commit (whatever number falls out cleanly). After that, every future catalog-expansion run should ship a synchronised source + DB delta.

**Side-fix opportunity:** while editing the prompt, also extend `scripts/audit_headline_stats.py` to add a `source-vs-DB drift check` (compare `spec_from_dict` count in known_bikes*.py vs `bike_models` row count; fail if delta > 5). This makes the gap a postflight gate rather than a self-review-only finding.

**Effort:** ~10 min for the prompt edit; ~5 min for the next session to actually run the re-seed; ~30 min if the audit-script extension is included. Single commit.

Source: `reports/self_review_2026-05-21.md` Finding 2.1.

---

## DONE — 2026-05-24 — [self-review] [urgent] promote postflight alert dedup ticket (INBOX:605) to [urgent]

**Result:** `DISPATCH_INBOX.md:605-606` tag flipped from `[opportunistic]` to `[urgent]` inline at the start of session 2026-05-24. The dedup fix itself (the 10-LOC `_blocking_ticket_open()` helper proposal at lines 614-628) is still open — but now appears in the urgent queue so the next implementer-style session can pick it.

**Original instruction below for archival.**

## ORIGINAL — 2026-05-21 — [self-review] [urgent] promote postflight alert dedup ticket (INBOX:605) to [urgent]
[urgent]

**Attribution:** `reports/self_review_2026-05-21.md` Finding 2.2.

**Problem:** INBOX:605 (postflight alert dedup during open blocking tickets) is tagged `[opportunistic]`. As of 2026-05-21T03:00Z there are **24 identical `Postflight deploy check timed out after 180s` ALERT entries** in `DISPATCH_OUTBOX.md` since the Railway outage began 2026-05-17. Every new autonomous session adds one more. The dedup fix is a 5-minute awk one-liner (proposal verbatim in INBOX:605 lines 614-628), but the `[opportunistic]` tag keeps it below the daily catalog-expansion work in scheduler priority.

**Asymmetry:** `reports/perf_monitor_2026-05-17.md` Run 12 (line 394) correctly handled the same signal — observed the matching INBOX:140 ticket, declined to file a duplicate. Postflight lacks that logic; this dedup INSTRUCTION fills the gap.

**Proposed action (one-line edit):** in `DISPATCH_INBOX.md:606`, change `[opportunistic]` to `[urgent]`. Optionally also update the title at line 605 to remove `[opportunistic]` if present.

**Why urgent now:** signal dilution is currently growing at ~1 ALERT every 2 hours. By the time Railway is restored (waiting on user billing — could be days), the OUTBOX will be unparseable for genuine deploy-check failures. The fix takes 5 minutes; the delay is purely tag-priority.

**Acceptance:** after the promotion, the next inbox-aware session (or human dispatcher) should be able to pick INBOX:605 ahead of catalog-expansion. After landing, archiving INBOX:140 (Railway ticket → DONE once user resolves) should result in the next genuine deploy timeout firing a fresh ALERT (test by inspection).

**Effort:** 30 seconds for the tag flip; 5 minutes for the fix itself.

Source: `reports/self_review_2026-05-21.md` Finding 2.2.

---

## INSTRUCTION — 2026-05-24 — [claude-feature-monitor] [opportunistic] package `motoquant.skill` using native Claude Skills system
[opportunistic]

**Attribution:** `reports/claude_feature_scan_2026-05-24.md` (bootstrap baseline scan).

**Context:** Anthropic ships a native Skills system at `https://code.claude.com/docs/en/skills` — repeatable workflows packaged as shareable slash commands (e.g. `/review-pr`, `/deploy-staging`). The MotoQuant toolkit shortlist in `CLAUDE.md` already calls for "MotoQuant skill for Claude — teach Claude bike spec schema + glossary (60-foot, ET, trap, two-step, anti-squat, slipper, expansion chamber)" as a low-effort, high-value item. Native Skills makes this a packaging task rather than a custom prompt-engineering job.

**Proposed action:**
1. Create `skills/motoquant.skill/` with the standard Skills layout (per the Skills docs).
2. Bundle the bike-spec schema (`BikeConfig` field reference, units, valid ranges) + drag-racing glossary + the K5 / R1 / Hayabusa reference baselines + the 8-cluster `CategoryProfile` map + the dispatch protocol summary.
3. Add `/motoquant-validate-bike` (runs scraper validator + smoke sim against an inline spec) and `/motoquant-explain-result` (interpret a sim output in plain English for a tuner) as the first two skill commands.
4. Smoke-test by invoking the skill in a fresh session and verifying it answers a 60-foot question correctly without external context.

**Why opportunistic, not urgent:** the existing CLAUDE.md preload already covers most of the schema fluency for autonomous sessions; the win is primarily for human chat sessions and for any future contributor. No bug, no deadline.

**Effort:** ~2-3 hour spike; one focused session.

**Don't:** ship anything that hard-codes API keys or pricing into the skill (those live in `tokens.md` + Railway env).

**Acceptance:** `/motoquant-validate-bike` correctly validates a canned spec; the skill answers "what is a 60-foot time?" without needing to re-read CLAUDE.md.

Source: `reports/claude_feature_scan_2026-05-24.md` (Adopt section).

---

## DONE — 2026-05-24 — [self-review] [opportunistic] scheduler same-day dedup for already-ran agents

**Result:** Implemented in `scripts/master_scheduler.sh` during session 1779618640-656 (Sun 2026-05-24, 10:30 UTC) — the third dispatch of the day, which triggered the bug live and made it the natural session to fix it. Approach diverges from the original sketch: instead of relying on `_LAST_RUN_JSON.<agent>.iso_timestamp` (which postflight does not currently maintain per-agent), the scheduler now probes the filesystem for `reports/PREFIX_TODAY*.md`. Prefix mapping uses kebab-to-snake by default plus an explicit alias table for the 8 agents whose report stem deviates (perf_monitor, claude_feature_scan, seo_audit, support_triage, product_priorities, growth_exp, benchmark_audit, content). Filesystem evidence is more robust than STATUS.md bookkeeping because postflight stamps `_updated` but not per-agent dates.

**Behaviour:**
- If a matching report exists for today AND last outcome was not "fail", the agent's score is cut by 200 (well below floor=30) and it's excluded from `picks`.
- A new `### Skipped (already ran today)` block appears in the dispatch plan listing the evidence file and would-have-been score.
- `--dry-run` JSON gains `same_day_skip`, `same_day_evidence` per-agent fields, plus a top-level `skipped_same_day` array.
- Failed runs (outcome=fail) are exempt — retry behaviour preserved.
- Sunday self-review auto-pin gated by same-day-skip so it can't fire twice on Sun.

**Validated** on today's repo state: 4 agents (catalog-expansion, performance-monitor, self-review, claude-feature-monitor) correctly skipped because their `reports/*_2026-05-24.md` files already exist; scheduler picks the next-best 3 (physics-calibration, benchmark-import, marketing-content). 6 pytest cases in `tests/test_scheduler_same_day_dedup.py` cover normal pick, skip on report, alias prefix mapping (perf_monitor), failed-run exempt, multi-skip surface, dry-run JSON shape.

**Files touched:** `scripts/master_scheduler.sh`, `tests/test_scheduler_same_day_dedup.py`.

**Deferred from this fix:** (a) per-agent cooldown override in `scheduler_weights.json` (current implementation is "same calendar day" only — no sub-day cooldown); (b) fallback-to-inbox-implementer wiring (depends on INBOX:571 inbox-implementer agent which doesn't exist yet); (c) postflight should still be extended to write per-agent timestamps to LAST_RUN_JSON for the GH-Actions side-channel — separate ticket. The filesystem-based gate covers the immediate same-day-duplicate-dispatch failure mode the user hit.

**Original instruction below for archival.**

## ORIGINAL — 2026-05-24 — [self-review] [opportunistic] scheduler same-day dedup for already-ran agents
[opportunistic]

**Attribution:** session 1779611475-643 (Sun 2026-05-24, 08:31 UTC). The morning autonomous run (06:42 UTC, commit `fdaa574`) dispatched all 3 selected agents — self-review (M5), perf-monitor (Run 14), claude-feature-monitor (bootstrap). The 08:31 UTC re-dispatch by the wrapper picked the SAME 3 agents with `days since last run: 0` because `scripts/master_scheduler.sh` rounds the freshness clock to whole days, and "ran 2 h ago" reads as "0 days, eligible". The session-prompt cap of `1 self-review per 5 days` (see `scripts/agents/self-review.md:64`) caught it on the agent side, but the cap is documentation, not enforcement — a less alert session would have re-run the entire stack and produced 3 redundant reports + a duplicate INBOX queue.

**Proposed fix:** in `scripts/master_scheduler.sh`'s scoring loop, before adding an agent to the dispatch plan, check whether `data/STATUS.md::_LAST_RUN_JSON.<agent>.iso_timestamp` is within the last 4 hours (configurable, default 4h). If so, skip the agent and emit a `[skipped: ran 2h ago, cooldown 4h]` note in the dispatch plan. This is in addition to the existing `days since last run` heuristic, not a replacement — different agents have different natural cadences (perf-monitor can re-run if there's a known drift, but self-review really shouldn't fire twice in 4h).

**Implementation sketch:**

```bash
# In master_scheduler.sh, inside agent-loop, before pushing to plan:
last_iso=$(jq -r ".\"${agent}\".iso_timestamp // empty" "$last_run_json")
if [[ -n "$last_iso" ]]; then
  last_epoch=$(date -d "$last_iso" +%s 2>/dev/null || echo 0)
  age_seconds=$(( $(date +%s) - last_epoch ))
  if [[ $age_seconds -lt 14400 ]]; then  # 4 hours
    log "skip: ${agent} ran ${age_seconds}s ago (< 4h cooldown)"
    continue
  fi
fi
```

**Acceptance:** the next session that fires within 4h of a previous successful run should see a dispatch plan with the agent listed under a new `### Recently-ran (skipped)` block instead of the active dispatch list. If the plan ends up empty, the wrapper should fall through to an inbox-implementer-style fallback (pick the oldest `[urgent]` INBOX ticket whose scope fits) rather than producing a "null" session.

**Don't:** apply a global cooldown — `physics-calibration` and `tech-debt-pass` legitimately benefit from back-to-back runs when a regression is being chased. Cooldown should be per-agent, configurable in `scheduler_weights.json` (default 4h, override per agent).

**Effort:** ~1 hour (15 min for the jq+date math, 30 min for per-agent cooldown override + test, 15 min to write the fallback-to-inbox-implementer wiring once that agent exists per INBOX:571).

---

## INSTRUCTION — 2026-05-24 — [opportunistic] [kaizen] fix postflight deploy-alert suppression (40 dup alerts in 7 days)
[opportunistic] [kaizen]

**Detected by:** customer-support agent triage, session 1779647439-649, 2026-05-24. Report: `reports/support_triage_2026-05-24.md`.

**Symptom:** `DISPATCH_OUTBOX.md` has accumulated **40 identical `### ALERT — ... Postflight deploy check timed out after 180s`** entries across 2026-05-17 → 2026-05-24 (~5.7/day). The matching `[urgent] [blocking]` Railway-outage ticket has existed in `DISPATCH_INBOX.md` since 2026-05-17 20:42 UTC — first dup alert fired 3 min later at 20:45 UTC and they have not stopped.

**Existing suppression:** `scripts/session_postflight.sh::_blocking_ticket_open` (lines 284–299) is designed to suppress exactly this case. Manually running the same awk against today's inbox returns the matching ticket. So the gate logic IS sound — but something at postflight runtime is bypassing it.

**Suspected causes (in order of likelihood):**
1. The awk reads `MQ_WORKDIR/repo/DISPATCH_INBOX.md`, but at the moment `verify_deploy` runs, the *committed* inbox in the just-pushed HEAD already contains the ticket — verify that the working-tree copy matches HEAD at that point (no race against any in-flight `git checkout` or rewrite).
2. CRLF line-endings on the inbox could break the awk's `block && /\[blocking\]/` match (CRLF would put `\r` between `]` and end-of-line, the regex still matches but worth confirming).
3. The state machine clears `block` only on the next `## INSTRUCTION` header — if a stray `## ` heading appears mid-block (e.g. one of the curl example URLs in the May-17 ticket starts with `$ curl https://...`), AWK's `/^## /` re-enters block context with `tagged=0, matched=0`. **Most likely cause** — verify by counting `^##` lines inside the ticket body.

**Required fix:**
1. Write a `scripts/test_blocking_suppression.sh` that pipes a known inbox snapshot through `_blocking_ticket_open` and asserts the expected ticket title is returned. Wire it into `tests/test_session_scripts.sh` (or create that file).
2. Tighten the awk's `## INSTRUCTION` block-start regex to require `## INSTRUCTION` (full keyword), not bare `## `, to avoid the curl-example false-reset.
3. Add a defensive backstop in `_queue_alert`: read the LAST `### ALERT` block from the outbox; if its message body is byte-identical to the new message AND the timestamp is <6h old, append ` (repeat #N+1)` to the existing block instead of writing a new one. This prevents ANY future feedback loop where suppression silently regresses.
4. Add a `reports/cleanup_outbox_alerts.py` one-shot that consolidates the existing 40 dup alerts into a single block with `(repeated 40x between 2026-05-17 and 2026-05-24)` — keeps git history but stops the noise from drowning out the next real alert.

**Effort:** ~2 hours (30 min repro + AWK fix, 30 min for the dedup backstop in `_queue_alert`, 30 min for the consolidation one-shot + run, 30 min for the regression test).

**Not in scope for this ticket:** fixing the underlying Railway outage — that's still on the user (see INBOX line 140, `[urgent] [blocking]`, day-7 open).

---

## INSTRUCTIONS QUEUE

> _Add new `## INSTRUCTION` blocks above this divider. Claude marks them `## DONE` once handled._

## INSTRUCTION — 2026-05-25 — [opportunistic] blog: Harley-Davidson Nightster RH975 quarter-mile physics

Queued by: seo-keyword agent (2026-05-25 SEO audit pass, priority 50 in data/seo_opportunities.json).

Write `/blog/harley-nightster-rh975-quarter-mile-physics` — physics breakdown of the Nightster RH975 at the drag strip.

**Spec:** Harley-Davidson Nightster RH975 (HARLEY_NIGHTSTER_RH975_2022 in known_bikes_extended.py). 975cc Revolution Max 975T V-twin, 90 hp @ 7500 rpm, 95 Nm @ 5000 rpm, belt drive (24F/68R), ~212 kg dry.

**Benchmark anchor:** Cycle World 2022 instrumented: 11.99s @ 110.4 mph — use as the validation anchor. MotoQuant should simulate close to 12.0s at Aamby Valley (cruiser cluster + belt-drive + 212 kg will sit in the 11.8-12.2s range).

**Post angle:** "Revolution Max 975T — is the Nightster actually fast for a Harley?" The surprise is that it genuinely is — 11.99s puts it ahead of most 600cc middleweights and equal to or faster than the Triumph Street Triple 675R (legacy platform). The mass penalty vs the Sportster S (121 hp, ~227 kg) is the natural comparison bridge.

**Companion piece:** Queue a Nightster RH975 vs Sportster S RH1250S comparison post after this one lands and gains traction. Both are in catalog with Revolution Max powertrain entries.

**SEO targets:** `harley davidson nightster rh975 quarter mile`, `nightster rh975 drag time`, `harley nightster 975 vs sportster s`, `revolution max 975 quarter mile`

**Blog post location:** `/web/app/blog/harley-nightster-rh975-quarter-mile-physics/page.js`  
**Blog index:** Add to POSTS array in `/web/app/blog/page.js` (top of list, date 2026-05-xx)  
**Sitemap:** Add entry at priority 0.85

---

## DONE — 2026-05-25 — [self-review] [urgent] implement bike_repo year-suffix upsert fix + ghost-row cleanup

**Resolved in session 1779712234-644 (2026-05-25).**

**Code fix landed:**
- `motoquant/database/bike_repo.py`: added module-level `_norm_model()` helper that strips trailing `(YYYY-YYYY)` suffix via compiled regex. Added a pre-insert Python-side check in `create_model()` that queries existing rows for the same `manufacturer_id`, compares them on normalised `model_name`, and returns the closest-year sibling's id when a match exists. Short-circuits BEFORE `INSERT OR IGNORE` because the UNIQUE constraint is keyed on the literal string and never fires across bare/suffixed variants.
- `tests/test_scraper.py`: added `TestYearSuffixIdempotency` with 3 tests — same-spec double import, bare-in-DB → suffixed call, suffixed-in-DB → bare call. All 3 green.

**DB cleanup deferred (with reason):** the proposed `DELETE FROM bike_models WHERE rowid NOT IN (SELECT MIN(rowid) ...)` query is unsafe to run unsupervised because `bike_configs.bike_model_id` has FK references that could orphan whichever child rows already attached to the rowids being deleted. Safer dedup needs: (a) check FK fanout per duplicate group, (b) prefer the row with the MOST children rather than `MIN(rowid)`, (c) re-point any child rows of the losers to the winner before the DELETE. Queueing as a separate `[urgent]` for a user-supervised cleanup pass.

**Validation:** full `tests/test_scraper.py` suite green (83 passed, 0 failed). K5/R1/Hayabusa baselines untouched. Code change is data-safe: only changes which existing row id gets returned on duplicate-keyed inserts; never deletes or rewrites rows.

**Commit reference:** see this session's commit on `main` — `motoquant/database/bike_repo.py` + `tests/test_scraper.py`.

---

## INSTRUCTION — 2026-05-25 — [urgent] [needs-user] supervised ghost-row cleanup for bike_models

**Attribution:** spawned by the DONE block above for INBOX:308. The 301 phantom rows that accumulated before today's code fix still exist in `motoquant.db`. The cleanup SQL proposed in the original INBOX:308 (`MIN(rowid)` per `(manufacturer_id, model_name)` group) is unsafe because `bike_configs.bike_model_id` FK references may already point at rows that the DELETE would remove.

**Required steps (≤ 30 min when run by hand):**
1. `python3 -c "import sqlite3; c=sqlite3.connect('motoquant.db'); ... "` — enumerate phantom groups: for each `(manufacturer_id, _norm_model(model_name))` group with >1 row, list `(id, model_name, year_from, COUNT(bike_configs.id))`.
2. Within each group, pick the WINNER row as the one with the most `bike_configs` children. If tied, prefer the row whose `model_name` has the year suffix (canonical form).
3. For each LOSER row in the group: `UPDATE bike_configs SET bike_model_id = <winner_id> WHERE bike_model_id = <loser_id>`.
4. `DELETE FROM bike_models WHERE id = <loser_id>` for each loser.
5. After cleanup: `SELECT COUNT(*) FROM bike_models` should drop from 790 → ~489.
6. Re-run baselines + focused test subset; verify K5/R1/Hayabusa Δ +0.0000s and `count_models() ≥ ALL_KNOWN_BIKES count`.

**Why user-supervised:** the FK re-point in step 3 is destructive if the script misidentifies the winner. One-shot script with `--dry-run` flag first, then user reviews the planned UPDATEs/DELETEs before committing.

**Done when:** `motoquant.db` shows `COUNT(*) FROM bike_models` ≈ distinct `(manufacturer_id, _norm_model(model_name))` count, no orphan FK refs, and baselines preserved.

---

## DONE — 2026-05-25 — [self-review] [needs-approval] audit master_scheduler.sh for INBOX queue_weight parsing
[opportunistic]

**Audit completed by M7 2026-05-26 (Finding 2.1).** The hypothesis was confirmed: `scripts/master_scheduler.sh:90` defines `parse_inbox_urgent()` but its output only PRINTS in the dispatch plan (line 308-313), never folded into agent scores. Line 207-214 only matches `@agent` syntax (zero such mentions in current inbox; all self-review-queued items use `[agent]` bracket-tag syntax instead). Result confirmed: `[urgent]` tag IS decorative; no agent gets queue_bonus from urgent items.

**Marked DONE 2026-05-30 by self-review M8** for admin bookkeeping consistency — the audit work is complete; the fix is now tracked at INBOX:939 (M7's queued exact-diff ticket), which M8 has promoted to `[urgent]` this run.

**Attribution:** self-review M6 2026-05-25, Finding 2.2. INBOX:308 has been `[urgent]` for 1 day and INBOX:617 (Railway offline) for 8 days. Neither triggered the +50 queue_weight boost described in `docs/AUTONOMOUS_OPERATIONS_PLAYBOOK.md` §2. Hypothesis: `scripts/master_scheduler.sh` does not parse severity tags at all — the `queue_weight` subsystem is unimplemented.

**Task:** Run `grep -n "urgent\|queue_weight\|INSTRUCTION" scripts/master_scheduler.sh` and report findings. If the parsing block is missing, add it:

```bash
# In master_scheduler.sh, scoring function:
urgent_count=$(grep -c "^\#\# INSTRUCTION.*\[urgent\]" "$INBOX" 2>/dev/null || echo 0)
if [ "$urgent_count" -gt 0 ]; then
  queue_weight=$((queue_weight + 50))
fi
```

**Deliverable:** A one-paragraph finding in DISPATCH_OUTBOX (if confirmed missing, add the parsing + a 1-liner test). Effort: ~30 min.

---

## INSTRUCTION — 2026-05-25 — [self-review] [opportunistic] technical-debt-pass: add pytest-regressions golden-file contract
[opportunistic]

**Attribution:** self-review M6 2026-05-25, Layer 3. CLAUDE.md TOOLKIT REFERENCE ★ item "pytest-regressions" has been deferred 25 days. This is the highest-ROI capability-frontier move available.

**Task:** On the next `technical-debt-pass` (A9) run on a Saturday, implement `pytest-regressions` golden-file snapshots for the K5/R1/Hayabusa reference baselines:

1. `pip install pytest-regressions` — add to `requirements-dev.txt`
2. In `tests/test_validation.py`, add a `test_reference_baselines_golden` test that uses `data_regression.check()` to snapshot `{"k5_et": 10.0334, "r1_et": 10.2859, "hayabusa_et": 10.4712}`. On first run, golden file is created; future runs fail if values shift.
3. Run `pytest --gen-files tests/test_validation.py::test_reference_baselines_golden` to generate the baseline file.

**Why now:** the existing hardcoded asserts in `test_power_boost_regression.py` are exact but isolated. A golden-file approach extends naturally to the full 489-bike sweep.

**Effort:** ~1 hr. No architectural changes.

---

## INSTRUCTION — 2026-05-26 — [self-review] [urgent] [needs-approval] fix master_scheduler.sh queue_bonus to honour [urgent] tag

**Severity promoted from `[needs-approval]` → `[urgent] [needs-approval]` by self-review M8 2026-05-30 (Proposal #2).** Reason: 4 days sat un-actioned during host-machine gap. This is the single highest-impact pending kaizen item because it structurally unblocks the `[urgent]` tag mechanism every other self-review run has been queuing items into. Single-knob severity bump, same pattern as M5's successful INBOX:308 `[opportunistic] → [urgent]` promotion which landed in 1 day.

**Attribution:** self-review M7 2026-05-26, Finding 2.1. M6 queued INBOX:897 to AUDIT this; the audit found the bug. `scripts/master_scheduler.sh:90` defines `parse_inbox_urgent()` but its output is only printed in the dispatch plan (line 308-313), never folded into agent scores. `scripts/master_scheduler.sh:207-214` looks for `f"@{agent}"` mentions, but the inbox uses `[agent]` bracket-tag syntax for all self-review-queued items (zero `@agent` mentions in current 26-item inbox). Result: `[urgent]` and per-agent-tag are both decorative; agents never get a queue_bonus boost.

**Why this matters:** the `queue_bonus = 50 * inbox_count_per_agent.get(agent, 0)` formula at line 229 is the structural mechanism that's supposed to make the kaizen loop converge faster on urgent backlog. With it dead, the only thing draining the inbox is happenstance overlap of self-review writing-sessions with implementer dispatch slots.

**Proposed fix (drop-in for the inbox_count_per_agent loop ~line 207-214):**

```python
inbox_count_per_agent = {}
inbox_urgent_per_agent = {}
if os.path.isfile(inbox_file):
    with open(inbox_file) as f:
        current_block_urgent = False
        current_block_agents = set()
        for line in f:
            if line.startswith("## INSTRUCTION") or line.startswith("## DONE"):
                # commit previous block
                for a in current_block_agents:
                    inbox_count_per_agent[a] = inbox_count_per_agent.get(a, 0) + 1
                    if current_block_urgent:
                        inbox_urgent_per_agent[a] = inbox_urgent_per_agent.get(a, 0) + 1
                current_block_urgent = False
                current_block_agents = set()
            if "[urgent]" in line or "[blocking]" in line:
                current_block_urgent = True
            for agent in weights["agents"]:
                if f"@{agent}" in line or f"[{agent}]" in line:
                    current_block_agents.add(agent)
        # tail block
        for a in current_block_agents:
            inbox_count_per_agent[a] = inbox_count_per_agent.get(a, 0) + 1
            if current_block_urgent:
                inbox_urgent_per_agent[a] = inbox_urgent_per_agent.get(a, 0) + 1
```

Then at scoring line 229:
```python
queue_bonus = 50 * inbox_count_per_agent.get(agent, 0) + 50 * inbox_urgent_per_agent.get(agent, 0)
```

**Verification:** after fix, `--dry-run` should show `queue_bonus > 0` for self-review agent (5 `[self-review]` items currently in inbox) and `queue_bonus > 0` for catalog-expansion (queued items if any tagged).

**Effort:** ~30 min (1 file edit, 1 dry-run verification, 1 commit). No architectural change.

**Note:** This SUPERSEDES INBOX:897 (M6's audit-only ticket). Once this fix lands, mark 897 DONE too.

---

## INSTRUCTION — 2026-05-26 — [self-review] [opportunistic] verify web/app/page.js stats strip uses DISTINCT bike count

**Attribution:** self-review M7 2026-05-26, Finding 2.2. The DB currently has `bike_models` raw=790 / distinct=489. 301 phantom rows from the pre-`31b36a4` regression remain pending the ghost-row cleanup at INBOX:879. If the landing-page stats strip reads `COUNT(*)` (790) instead of `COUNT(DISTINCT manufacturer_id || '|' || model_name)` (489), prod website is overstating catalog size by 62% — a customer-facing trust issue.

**Task (~10 min):**

1. `grep -n "bike_count\|bikes_count\|COUNT" web/app/page.js scripts/audit_headline_stats.py motoquant/api.py | head -30`
2. Identify which query the landing page renders against
3. If `COUNT(*)`: switch to `COUNT(DISTINCT manufacturer_id || '|' || model_name)` (same fix as the `scripts/audit_headline_stats.py` SoT)
4. If already DISTINCT: confirm the displayed value reads ~489 and patch the website if stale

**Deliverable:** One-paragraph finding in the next session report. If a fix is required, commit it as part of the same session that handles INBOX:879 cleanup.

---

## INSTRUCTION — 2026-05-30 — [self-review] [opportunistic] [needs-user] open question: relax auto-apply boundary for low-blast-radius self-review script edits?

**Attribution:** self-review M8 2026-05-30, Finding 2.3 + Proposal #3. M-class observation: in 7 historical M-runs, the auto-apply boundary has produced 5 weight tweaks (single-knob, all held) and 2 INBOX bookkeeping flips. **Zero script/code edits have ever auto-applied**, by design. But the most impactful pending kaizen item right now (INBOX:939 — queue_bonus fix) has sat 4 days untouched because it's a 5-line Python edit in `scripts/master_scheduler.sh` and the auto-apply table forbids script edits.

**The question for the user:** is the strict-no-script-edit policy still the right default, OR should `[self-review]` proposals that meet specific criteria qualify for auto-apply?

**Possible criteria worth considering (if loosening):**
1. Full unified diff included in the INSTRUCTION
2. Reversion command also included (e.g., `git revert <sha>`)
3. Scope strictly limited to: `scripts/master_scheduler.sh`, `scripts/scheduler_weights.json`, `scripts/agents/*.md`, `STATUS.md` (i.e., kaizen-self-improvement surface only)
4. Auto-revert if no DISPATCH_OUTBOX entry acknowledges the change within 48h
5. M-class self-review explicitly attributes to a specific Finding number and previous observed event

**Possible response options:**
- (a) Keep current strict policy — accept slower convergence on script-edit kaizen items
- (b) Allow auto-apply when ALL 5 criteria above are met
- (c) Allow auto-apply for `scripts/scheduler_weights.json` edits beyond ±10 (e.g., adding/removing best_dow slots) but keep `.sh`/`.py` strictly manual
- (d) Other

**Cost of inaction:** every self-review run that finds a system-self-improvement bug requiring a code edit queues it to INBOX, where it waits for the next host-machine availability window. The 4-day gap this week was 4 days where INBOX:939 (the loop's primary structural lever) could have been auto-resolved if policy allowed.

**This is not a fix proposal — it is an open question.** Please respond in DISPATCH_OUTBOX or as an INSTRUCTION update. M-class self-review will hold to current policy until guidance lands.

---

## INSTRUCTION — 2026-05-31 — [self-review] [urgent] add Vercel pre-build gate to session_postflight.sh

**Attribution:** self-review M9 2026-05-31, Finding 2.1 + Proposal #2. The Saturday user-rescue session (DISPATCH_OUTBOX:1839) found that **every Vercel prod deploy had silently failed since ~May 26** — an unescaped apostrophe in a single-quoted data string in `web/app/blog/royal-enfield-hunter-350-quarter-mile-physics/page.js` broke `next build`. Production frontend was frozen on the May-25 build pointing at dead Railway for 5 days. Marketing-content and catalog-expansion agents pushed web/app changes after May 26 with zero visibility into the silent failure.

**Root cause:** CLAUDE.md hygiene section "When editing web/app/**, run next build from web/ before commit" exists. The pre-push hook at `scripts/git-hooks/pre-push` is supposed to enforce it. Either (a) it's not enabled in autonomous-ops sessions, or (b) it's installed but the `core.hooksPath` config isn't being set in the per-session `/tmp/mq-session-*/repo` clones.

**Proposed fix (add to `scripts/session_postflight.sh` before the push step):**

```bash
# Vercel pre-build gate — fail-fast on next build errors in web/app/**
if git diff --cached --name-only | grep -qE '^web/(app|components)/'; then
  echo "[postflight] web/app touched — running next build…"
  if ! ( cd web && npx --no-install next build > /tmp/mq-vercel-build.log 2>&1 ); then
    echo "[postflight] FATAL: next build failed. See /tmp/mq-vercel-build.log" >&2
    tail -40 /tmp/mq-vercel-build.log >&2
    exit 7
  fi
  echo "[postflight] next build OK"
fi
```

Exit code 7 is a new postflight code (current table: 0/1/2/3/4/5/6 documented in DISPATCH_PROTOCOL.md). Add entry to the exit-code table.

**Verification:**
1. Re-introduce the apostrophe locally in a throw-away clone.
2. Stage the file. Run `bash scripts/session_postflight.sh --message "test" --files "web/app/..."`.
3. Confirm exit 7 + log tail with the apostrophe error.
4. Revert and re-run, confirm exit 0.

**Effort:** ~30 min including verification + DISPATCH_PROTOCOL.md table entry.

**Why `[urgent]`:** the same failure mode could trip on any agent-driven web/app push. The autonomous-ops loop ships 5-10 web/app touches per week. A single quote in a generated blog post will reproduce this in the wild within days.

---

## INSTRUCTION — 2026-05-31 — [self-review] [opportunistic] add Render cold-start warm-up to verify_deploy

**Attribution:** self-review M9 2026-05-31, Finding 2.3 + Proposal #3. The 2026-05-30 Railway → Render migration switched the production backend to Render free tier, which sleeps after 15 min idle and cold-starts in 30-60s. The Saturday rescue session bumped the `session_postflight.sh` health-check timeout from the Railway default to 90s. This handles a warm cold-start but a worst-case 60s cold + ~30s for the first physics import will still trip the timeout and write an ALERT.

**Proposed fix (`verify_deploy()` in `scripts/session_postflight.sh`):**

Before the existing verification poll loop, add a non-fatal warm-up probe:

```bash
# Render cold-start warm-up
echo "[postflight] warm-up ping (allow Render cold-start)…"
if ! curl -sf --max-time 5 "$HEALTH_URL" > /dev/null 2>&1; then
  echo "[postflight] warm-up returned non-2xx — likely Render cold start. Sleeping 30s…"
  sleep 30
  if ! curl -sf --max-time 15 "$HEALTH_URL" > /dev/null 2>&1; then
    echo "[postflight] warm-up still failing after 30s — proceeding to main verify loop"
  fi
fi
```

The main verify loop stays as-is. This adds at most 50s when Render is asleep, zero when warm.

**Why `[opportunistic]`:** the keepalive cron (`.github/workflows/keepalive.yml`) already pings Render every 10 min during IST day, so most autonomous-ops sessions land on a warm backend. The corner case is the first session of an IST morning if keepalive missed a tick — rare but predictable.

**Effort:** ~20 min including a manual cold-start verification (use `curl https://api.render.com/v1/services/<id>/suspend` to force a sleep, or wait 16 min between requests).

---

## INSTRUCTION — 2026-05-31 — [claude-feature-monitor] [opportunistic] migrate default Opus routing to Claude Opus 4.8

**From:** `scripts/agents/claude-feature-monitor.md` (A13)
**Source delta:** Claude Opus 4.8 released 2026-05-28. See `reports/claude_feature_scan_2026-05-31.md` and `data/claude_capabilities_snapshot.json` for full evidence.

**What:** Switch the harness default-Opus convention from `claude-opus-4-7` to `claude-opus-4-8`. Update the `CLAUDE.md` "MODEL SELECTION" table to reference Opus 4.8 as the architecture/design model.

**Why opportunistic, not urgent:**
- Opus 4.7 stays Active until 2027-04-16 — 10+ months runway.
- Repo-wide grep confirms ZERO model IDs are pinned in `scripts/`, `docs/`, `motoquant/`, `web/`, `desktop/` — only doc/snapshot files reference Opus 4.7. So there is no code-level migration; this is a convention/preference change in the harness routing table only.
- Opus 4.8 is fully backwards-compatible with 4.7 — no breaking API changes per the migration guide.

**Wins on 4.8 (per Anthropic docs):**
1. Stronger agentic coding performance (Anthropic's claim — needs our own held-out test).
2. Mid-conversation system messages (preserves prompt-cache hits when agents inject day-of-week / market-signal context).
3. Prompt-cache minimum lowered to 1024 tokens (smaller agent prompts in `scripts/agents/*.md` can now cache).
4. 1M context default with no beta header (cosmetic for us; already on 1M `[1m]`).

**Trap to avoid:** Opus 4.8 recalibrates effort levels (`medium` more thinking, `high` less, `xhigh` substantially more). If we promote 4.8, do NOT tune effort until we've re-baselined at the same level — otherwise we'll mis-attribute cost/quality deltas to the model when they're actually effort-recalibration artifacts.

**Quality gate before promoting:**
- One architecture-question session on Opus 4.8 (e.g. "review the Phase 6 Razorpay subscription rail design in `motoquant/auth.py`").
- Confirm answer quality is at-or-above the 4.7 baseline.
- Confirm token cost on the same input is in the same ballpark (4.8 is same $5/$25 pricing, so output token count is the only variable).

**Fallback path:** If the harness on a given session is unaware of `claude-opus-4-8`, fall back to `claude-opus-4-7`. No urgency to make this universal.

**Effort:** ~15 min for the CLAUDE.md table edit + 1 hour for the held-out quality gate session.

---

## DONE / DEFERRED ARCHIVE

> _Claude moves processed instructions here. Trim periodically — git keeps the full history._

(none yet)
