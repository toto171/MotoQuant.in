# Scope: next autonomous orchestrated run (Fable 5)

> **Date:** 2026-07-17 · **Author:** claude-fable-5 remote session on
> `claude/fable5-multi-agent-orchestration-t53mtj` · **Method:** 7-agent
> verification workflow (6 parallel dimension finders + adversarial
> completeness critic; 49 candidate items verified against the live tree at
> HEAD `39466ae`, every claim cited to file:line or a live command run).
> **Anchors re-proven this session:** pins K5 9.9331 / R1 10.1436 / Hayabusa
> 10.3633 bit-identical (`scripts/check_baselines.py` Δ +0.00e+00 ×3),
> `make health` HEALTHY (one sandbox-only pytest-count warn),
> `audit_headline_stats.py` in sync (541/593/254/1860/20/250), `/validation`
> data = the 277-match epoch sweep, verify-web 176 files clean, Vercel
> production READY on the rebrand head.
>
> Purpose: this file IS the work order for the next orchestrated session.
> Nothing here is speculative — every "open" item was re-verified on
> 2026-07-17; every stale prior claim found is corrected in §7.

---

## 1. Situation since July 13 (what the run must plan around)

Three operational facts discovered during verification, in severity order:

1. **GitHub Actions is 100% dead since July 13 09:38 UTC.** The repo is
   private; the minutes cap was crossed. Every job on every workflow
   insta-fails in 2–3s with `runner_id=0` (no runner assigned). Consequences:
   **PRs #109 (physics epoch), #110–#113 and the operator's direct rebrand
   commit all merged with zero CI**; the CI secret-scan gate is not executing
   on pushes (pre-commit is the only live layer); the CI-gated
   `deploy-production` job has not fired since July 13 (frontend ships only
   via Vercel's native push integration, ungated by tests). Keepalive cron was
   paused (PR #111) to stop the burn, but that doesn't restore this cycle's
   budget — that is operator billing action.
2. **Product analytics is completely dark — verified live, not inferred.**
   PostHog project "Motoquant" (EU, id 213355): `count() = 0` events over 90
   days, zero event types, ever. The server-side forwarder is code-complete
   but env-gated (`api.py:770-843`, no-op without `POSTHOG_API_KEY` — never
   set), and the web client has **no capture at all**
   (`web/lib/telemetry.js` is a stdout logger with a "reroute to PostHog
   later" comment). Every user-facing KPI in the north star is unmeasurable.
3. **Keep-alive is degraded but bounded.** With the GH cron paused, coverage
   is the 3×-daily Vercel `/api/wake` crons (00:05/07:00/12:00 UTC, active in
   both `vercel.json` copies) + in-app `keepwarm.py` (UTC 0-18 window).
   Practical exposure ≈ the IST evening band if the in-app loop drops the
   service after the 12:00 UTC wake (~6h failure-mode window, not a 12h
   expected outage). One-line fix queued in Wave 0.

Also: the operator's direct push `3d69f02` (identity kit, 25 files, 504K,
benign content, kit-consistent with IGNITION) had its Vercel production
deploy **BLOCKED** (`dpl_FdFDkn9…`) — harmless only because the IGNITION merge
2h later deployed READY. Worth an operator look at deployment-protection
settings.

## 2. Operator homework (issue at run START, not end)

None of these are session-doable; each unblocks a wave or a standing P0:

| # | Action | Unblocks |
|---|---|---|
| O1 | **GitHub Actions billing**: check Settings → Billing reset date / raise spending limit | CI on main again; Wave 0's hygiene PR keeps the restored budget alive |
| O2 | **Set `POSTHOG_API_KEY`** on Render (+ confirm `SENTRY_DSN` still set) | Wave 3 funnel instrumentation actually flows |
| O3 | **Oracle Steps 1–4** per `docs/ORACLE_MIGRATION.md` (account, A1 VM 4-OCPU/24GB, two-layer firewall, DNS `api.motoquant.in`, `compose up`; ~1–2h) | Retires keep-alive entirely + P0-2 persistent disk + 0.5-CPU optimizer latency in one move; session then does Step 5 (5 mechanical edits) |
| O4 | Check Vercel deployment-protection/spend settings that BLOCKED `3d69f02` | Direct pushes can't silently fail to ship |
| O5 | PAT + `VERCEL_TOKEN` rotation (both overdue per standing cadence) | Hygiene |
| O6 | When ready to charge: `docs/PAYMENTS_SETUP.md` runbook (P0-1) + Render paid disk (P0-2) — but see Wave 1's "before charging" engineering set first | Revenue |

## 3. The run plan (waves for one orchestrated session)

Structural constraint: **CI is dead, so the run is its own CI.** Wave 0 runs
the full local suite on main HEAD before anything merges, and every wave's PR
merges only after local `make check` (+ affected-suite pytest) is green.
Standard contract per AGENTS.md: baselines bit-identical unless a wave says
otherwise (none here does — **this run is deliberately epoch-free**), stat
sync + regen chain where data moves, explicit file staging, one PR per wave.

### Wave 0 — Green-main proof + CI hygiene (sequential, first)

1. `make check` + `make test` locally on main HEAD `39466ae` — the only
   available proof that the 5 un-CI'd merges (epoch + rebrand chain) are
   green. Any failure becomes the run's first fix.
2. **One CI-hygiene PR** (all verified, S/M, baseline-safe):
   - Delete or `workflow_dispatch`-gate the **desktop + sidecar-smoke jobs**
     (`ci.yml:104-214`) — ~25-35 min/run for a product scrapped July 6.
   - Path-filter the python job; run `--cov` + full suite on main pushes
     only; PRs get the fast tier (~3 min). Cuts per-PR cost ~100 min → <10.
   - Replace the stale inline benchmark check (`ci.yml:84-101` still pins
     PRE-epoch 10.034/10.286/10.472 — R1 passes by only 7.6ms) with
     `python scripts/check_baselines.py` (bit-identity, single source of truth).
   - **Restore the truncated `web` job** (`ci.yml:216-231` ends at
     Set-up-Node — no `npm ci`, no build; this is the job that gates
     production deploys) or delete it and gate `deploy.yml` on `web-verify`.
   - Add `hypothesis` to the CI install line — the 7 physics-invariant
     property tests have NEVER run in CI (`ci.yml:53` omits it; they'd have
     caught the historical dead-knob class).
   - Optional if minutes allow: a main-only `regression-full` job
     (`MOTOQUANT_SLOW_TESTS=1` catalog drift tier — currently never runs in CI).
   - `.github/PULL_REQUEST_TEMPLATE.md:37-45` still quotes the PRE-epoch
     pins/tolerances (10.034/10.286/10.472) — point it at
     `scripts/check_baselines.py` output instead of hardcoded numbers
     (found while opening this scoping PR).
3. **Keep-alive patch**: add 3–4 once-daily `/api/wake` Vercel crons
   (14:00/16:00/18:00 UTC) to both `vercel.json` copies. Free, no Actions
   minutes, shrinks the failure-mode gap to ≤2h. Do NOT re-enable the GH cron.
4. **PR housekeeping**: close #87 as superseded (main's 541-bike guard
   `b00aac5`/`eb6c68b` > its 501; its web-job repair is carried by this
   wave's CI PR); rebase + mark-ready #88 (Sentry activation visibility —
   verified still absent from main and still needed); rebase #102 onto
   post-epoch main (its PR table quotes old pins; prep is routing-inert so
   merging early is safe).

### Wave 1 — "Before charging money" hardening + one Pro-visible feature (parallel agents, file-ownership split)

All verified open, all baseline-safe; items a–c are the ROADMAP "before
charging money" set:

- **a. License-key policy call** (`subscriptions_repo.py:197`): omitting
  `device_id` bypasses binding; desktop is dead (ADR-0005) so the legacy
  tolerance's justification is gone. Reject unbound-device validates, update
  the pinned legacy test (`test_subscriptions.py:228`), add
  `rate_limit("license", …)` to the unauthenticated `/license-key/validate`
  route (currently unlimited). [S]
- **b. Razorpay idempotency ledger** (`subscriptions.py:265-339` never calls
  `record_payment_event`; a replayed `subscription.cancelled` can downgrade a
  re-activated user). Mirror the Stripe pattern + duplicate-drop test. [S]
- **c. `/api/jobs/outlaw` pro-gate** (`api.py:3967-3974`): composes the pro
  optimizer+autotune but carries no `require_tier("pro")` — an enforcement
  bypass at 6 req/min once billing flips. One `Depends` + a gating test.
  Not in any roadmap — found this pass. [S]
- **d. PyJWT migration** (`python-jose` CVE-bearing floor at
  `requirements-api.txt:20`; exactly 4 call sites in `auth.py`). Keep the
  jose-absent `dev.`-token gate semantics under the new flag; run the full
  auth/payments/subscriptions suite. [M]
- **e. Dockerfile non-root USER** (verify entrypoint DB-seed + SQLite journal
  write paths; own deploy, watch `/api/health`). [S]
- **f. `lastrowid==0` → `rowcount==0`** in `bike_repo.py:174` +
  `venue_repo.py:38` only (tire_repo already fixed July 6 — ROADMAP's mention
  is stale, trim it). Guarded by the idempotency suites + double `seed_all()`. [S]
- **g. sim_usage test residue**: one test module boots the API against the
  tracked DB and leaves metering rows after `make test`
  (July-6 report §241-247) — give it test_api's temp-copy setUpModule. [S]
- **h. Pro-visible feature — web PDF timeslip/build export.** Flipping
  enforcement today sells gates, not features (critic finding: the entire
  COMMERCIAL_LAUNCH ladder is unbuilt; `referral` greps zero). The cheapest
  real deliverable is the PDF export (desktop had jsPDF; port the concept to
  the web run page / optimizer result). [M]

### Wave 2 — Data + accuracy pass (parallel research, single regen chain at the end)

Everything here moves published numbers ⇒ **one** closing regen: fresh
weighted sweep JSON → `/validation` viz regen → sitewide stat sync →
`make baselines` Δ+0.0000 proof (corpus edits can't move pins by
construction).

- **a. Corpus honesty batch** (one commit): V-Rod Muscle DERIVED 11.80 →
  instrumented 11.875 (July-11 leftover, cross-matched in the scrape JSON);
  **Nightster contradiction** — corpus carries DERIVED 12.20 while the live
  blog quotes Cycle World instrumented 11.99 (`validation_sweep.py:2829` vs
  the Nightster blog page) → replace + refresh the blog's gap paragraph;
  apply the ~6 unambiguous duplicate weight-upgrades (Ninja 300/400, SV650,
  R3, Speed Triple 1050 aggregator→instrumented; VRSCA 0.3→0.7); skip
  same-source relabels. [M]
- **b. Entry-cluster instrumented-replacement research** — the two worst
  clusters are entry-150-200 (w|Δ| 0.754, 9/13 DERIVED) and single-300-500
  (0.492, 8/16 DERIVED). Targeted web/MotoStatz/TeamBHP pass over the ~15
  named worst-residual DERIVED bikes (RE Classic 350 family Δ−4.9, Xpulse
  −4.2/−4.5, MT-15 +2.8/+2.9, Apache RTR 200 4V +2.9, CB350RS, ZX-25R,
  Dominar 400, N250, FZ25, CB300F, F250…). **Folds and closes BOTH
  INBOX:164 and INBOX:688** (twin instructions, May 20/31). [L]
- **c. `speed_limiter_kmh` implementation** — the one physics-adjacent item
  that is explicitly NON-epoch: field exists nowhere in code (verified);
  quarter-mile traps (233–260 km/h) sit far below any 299 limiter, so ET
  pins are untouched by construction. Add `BikeSpec.speed_limiter_kmh` +
  validator bound → thread through importer/bridge (**round-trip it — the
  category_tag trap hit twice**) → clamp in `run_top_speed` → annotate the
  ~10 verified 299-limited rows (+5 needing limiter-vs-tested split) →
  re-run `scripts/topspeed_sweep.py` (expect the +28.5 km/h bias to
  collapse) → tests + stat sync. [M]
- **d. Dead CategoryProfile knobs — delete or pin** (S-sized now, the only
  dead-knob action worth taking outside an epoch): the 6 fields
  (`tuck_transition_time_s`/`cd_ceiling`/`pacejka_C`/`load_sensitivity_k`/
  `engine_inertia_mult`/`chain_efficiency_override`) still have zero
  consumers, yet profiles ASSIGN non-default values to them, and the
  July-10 "inventory pinned exactly" claim has **no actual test** (grep of
  tests/ = zero matches). Either delete (baseline-safe, grep-proven) or add
  an exact inertness test so accidental wiring fails loudly. [S]

### Wave 3 — Growth ignition + docs truth (parallel)

- **a. PostHog client capture + the 5 funnel events**
  (sim → save → share → signup → upgrade) in `web/lib/telemetry.js` +
  call sites; server forwarder already exists. Works the moment O2 lands;
  ships inert (env-gated) otherwise. [M]
- **b. Dragy timeslip-submission CTA on bike pages** (inventory A3-20): the
  scalable third path for the #1 accuracy bottleneck; `/api/calibrate/dragy`
  already exists, web has zero references. [S–M]
- **c. bike-suggest smoke check** (INBOX:79, filed 2026-05-31, never wired):
  the table is empty across every triage run and "no users" vs "form broken"
  is still indistinguishable. Verify the chat→estimator→`bike_suggestions`
  write path end-to-end once + add the synthetic check. [S]
- **d. Small web fixes**: sitemap fetch `limit=500` drops **41 of 541** bike
  pages (+ stale 310-ID fallback) → `limit=2000` + derived fallback ceiling;
  H2 SX blog line 93 rewrites BOTH stale figures in the sentence (present-
  tense "10.4712 s" pin AND the pre-epoch "~10.05 s" ZX-14R sim claim) +
  the table row at :101 + extend the audit regex to catch these prose forms;
  `web/DESIGN.md` v4 remnants (wordmark font §6 vs §4, old pins in footer
  example, ScoreboardDigits description, OG ownership) + a supersession
  banner atop `web/REDESIGN.md`. [S each]
- **e. Docs-truth pass**: `docs/KNOWN_TRAPS.md` gains T15 (every config
  serialization path must round-trip `category_tag` — hit twice), T16
  (enum-ish strings validate at construction or silently take a wrong
  branch — `boost_type`), T17 (every new DB patch joins the documented
  reseed chain — third occurrence). `CLAUDE.md` CURRENT STATE surgical sync:
  header date, surrogate **v2.4/89.2ms → v2.5/105.5ms/R² 0.9914**, test
  count, and **append `patch_2026_07_13_scrape_data.py` to the reseed
  chain** (as written, a fresh reseed silently drops 282 reprices + tire
  flags — real data-loss risk). ROADMAP touch-ups: cruiser-saturation claim
  stale (epoch resolved it — w bias +0.050), tire_repo mention stale,
  record A1-5/A1-6 (license revoke route, auth timing/bounded-tracker) as
  already-done so no session re-implements them. Full-file DISPATCH_INBOX
  archival sweep (~15 verified-stale blocks — the whole file, not just
  641+; :164/:79/:580/:618 are the only live ones and each is dispositioned
  by this plan). [S–M]

### Wave 4 — if capacity remains

- **Oracle Step 5** the moment O3's health check is green
  (`vercel.json` ×2 + `next.config.js` URL swap, postflight URL, retire
  keepalive/keepwarm/wake) + **automated DB backup** sidecar/cron
  (`sqlite3 .backup` to object storage — zero backup code exists today;
  durability currently ends at "disk persists").
- Fresh SEO pass: re-score the 53 unactioned opportunities
  (`data/seo_opportunities.json` stale since 2026-06-01) against the
  post-rebrand site; action top-3 metadata tweaks + 1 data-backed blog
  (Duke 390 vs RC 390 is fully in-catalog).

**Headline of the FOLLOWING session (not this one): MCP server +
`motoquant.skill`** — the only P2 distribution channel needing no operator
action, no billing, no physics; self-contained; markets itself.

## 4. Explicitly PARKED (conscious decisions, do not re-discover)

| Item | Why parked | Trigger to unpark |
|---|---|---|
| **Physics epoch 2 queue**: wheelie/launch-aggressiveness model (inversion is WORSE post-epoch: Hayabusa +55mm CoG now GAINS −0.141s; 8 lowering SKUs score backwards), 4-branch clutch dispatch (3 MTC lockup SKUs ET-neutral, verified Δ0.0000), staging dead-time/rollout, pacejka slip (needs wheel-speed ODE state), per-cluster tuck, R1 −0.16 residual | Each moves pins (ADR-0002); needs its own deliberate sweep-justified epoch with regen chain | Operator schedules epoch 2; clutch dispatch first (highest product value) |
| **models.py ~52-field implement-or-remove audit** (A4-26) | L-sized, reseed-coupled; July-13 proved the per-field pattern (headwind/crosswind kill + bridge filter) | Own session with golden gate + surrogate-regen budget |
| **Analysis-layer + api-jobs audit** (July-10 workflow dims never ran) | L-sized. Strongest seeded lead: **surrogate v2.5 is category-blind** (26 features, no cluster encoding) while `mu_peak_scale` now spans 1.0–1.30 — v2.5 MAE regressed 89.2→105.5ms and optimizer candidate RANKING can be cluster-biased (final numbers stay honest via the full-sim verify loop). Also seed: T14 shared-SQLite (per-thread `_get_db()`/`_get_db_facade` fix is well-scoped, gates scaling not launch) | Own audit session; surrogate v2.6 with category one-hot is the likely output |
| **Next.js 15/16 migration** (14.2.35; 2 advisories, no 14.x fix) | Breaking (async request APIs, caching defaults); needs Playwright + web-build session | Dedicated session — schedule soon; interacts with sitemap/rewrites |
| **EV physics branch** (A3-14) | 4 hard blockers incl. epoch-sensitive launch code; low revenue relevance | Deliberately parked — recorded so it isn't re-discovered |
| **0-100 corpus** (23 scrape finds unconsumed) | Needs a new sweep harness first; splits already exist in SimResult. Remember the et_s/value key-coalescing rule | M-sized future data+harness item |
| **Catalog wave** (QJ exhausts etc.) | Not justified alone: 240/18 substantively closed, CVT blocked by design, sub-500 wheelie bars low-physics-value | Bundle QJ/Kove/Zontes slip-ons into the next general catalog wave |

## 5. Corrections to prior records (found by this pass)

- **STALE**: "cruiser cluster saturates at +0.23 residual" (July 6) — the
  epoch resolved it (w|Δ| 0.210, bias +0.050, beat old-physics accuracy).
- **STALE**: ROADMAP P1 names tire_repo in the `lastrowid` item — tire_repo
  was fixed July 2/6 (normalized SELECT-then-UPDATE-or-INSERT).
- **ALREADY DONE** (don't re-implement): license-key revoke route
  (`/license-key/revoke` exists), auth timing side-channel (always-one-scrypt
  dummy verify) + bounded failed-login tracker (4096, expired-first).
- **WORSE than recorded**: the wheelie/CoG inversion grew from −0.113s
  (July 3) to −0.141s post-epoch (converged weight-transfer amplifies it).
- **MISLABELED**: surrogate line in CLAUDE.md CURRENT STATE still says
  v2.4/89.2ms; shipped artifact is v2.5/105.5ms (regression is real and
  explained by the epoch's cluster-dependent dynamics vs a category-blind
  feature schema). Also the artifact's `meta_json.data` label still names the
  v2.1 dataset file — fix on next regen.
- **UNVERIFIABLE HERE**: local `next build` (web/node_modules absent in
  sandbox; bare `npx next` fetches next@16 — never trust it). Health proven
  via verify-web + Vercel READY instead.

## 6. Run-shape notes for the orchestrator

- Waves 1–3 are agent-parallel with strict file ownership (Wave 1:
  `subscriptions*/auth/payments/api.py`-route-level split; Wave 2:
  `validation_sweep.py`+`topspeed_sweep.py`+spec/importer vs research-only
  agents; Wave 3: `web/` page-level split + docs). Wave 0 is sequential and
  first; its full-suite run doubles as the environment shakedown.
- Every merged PR this run is un-CI'd until O1 lands ⇒ the run's own local
  `make check`/`make test` IS the merge gate; say so in each PR body.
- Budget observed for this scoping pass: ~1.5M subagent tokens / 306 tool
  calls / 7 agents. The execution run above is a 4–6× larger session; if
  capacity forces cuts, cut Wave 4, then Wave 2b (research), never Wave 0.
- Standing contracts that apply: reseed chain (now 5 steps incl.
  `patch_2026_07_13_scrape_data.py`), surrogate = cache of the physics
  (regenerate on any reseed/retune in-session), stat sync gate before push,
  CLAUDE.md prepend-only.
