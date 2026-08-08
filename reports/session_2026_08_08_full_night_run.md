# Full-night agentic run — 2026-08-08

**Operator brief:** "orchestrate a full night agentic run … full freedom to
work on improving motoquant." Executed as an orchestrated multi-agent run
(9 implementation agents + orchestrator) against the 2026-07-25 weekly
audit's ordered 10-item queue (`reports/session_2026_07_25_weekly_audit.md`
§7) plus the CLAUDE.md next-session queue.

**Branch:** `claude/full-night-agentic-run-3hv2t1`.

---

## 0. The one-paragraph version

All ten of the July-25 audit's "suggested next session" items landed, plus
the MCP server + Claude skill from the roadmap's P2 list. The headline is a
**physics honesty pass that also improved accuracy**: synthetic catalog
curves now declare their true crank semantics (they are built from
manufacturer crank claims), which makes drivetrain-efficiency and parasitic
losses real for the whole catalog — 29 previously-inert priced SKUs now move
ET, shaft-drive bikes finally pay more loss than chain bikes, and the
per-cluster `parasitic_mult` knob is reachable — while the fresh weighted
sweep lands at **276 matched / w|Δ| 0.2629 / bias +0.0073**, better than the
published 0.2721/−0.0047. The three pinned references stayed **bit-identical
at every single step** (Δ +0.00e+00 ×3, checked after every change): this
epoch deliberately did NOT move the pins. The web app moved from EOL Next 14
to Next 15.5 + React 19 (27 npm advisories → 0), the production dependency
set is now lock-pinned, and the four 299-limited heavies got their real
gearboxes so their limiter annotations stopped being structurally inert.

---

## 1. The epoch: `is_at_wheel` crank semantics (audit §3.1/§3.3c/§3.6 + queued retune)

### The defect
All 542 catalog configs shipped synthetic torque curves built to reproduce
manufacturer **crank** ratings but flagged `is_at_wheel=True`. The engine
therefore skipped drivetrain efficiency (÷eta then ×eta cancels exactly) and
the parasitic subtraction — every catalog bike delivered full rated crank
power at the rear wheel. Consequences, all measured in the July-25 audit:
`parasitic_mult` dead for 100 % of the catalog; 21 chain-efficiency SKUs and
8 quickshifter SKUs moving ET by ~0; shaft-drive bikes paying zero extra
loss; and the queued cluster retune ill-posed.

### The design (three deliberate layers)
1. **Flip, scoped to the catalog path.** `_synthetic_torque_curve` /
   `_synthetic_2stroke_torque_curve` gained `is_at_wheel` parameters
   (default True); only the importer passes False. Real measured curves
   (`dyno_curves.py`, ~28 bikes in the matched corpus) stay at-wheel — a
   chassis dyno measures the wheel. The three hand-curated references build
   with the default, so the ADR-0002 pins are untouchable **by
   construction**, not by tolerance.
2. **`_CRANK_MODE_RECAL = 1.08`** applied to every synthetic crank curve
   UNDER the existing claim-to-truth ladder. Swept {1.00…1.08} against the
   full corpus (overall 0.3332 → 0.2960, every ≥60 hp cluster bias inside
   ±0.065). Honest decomposition documented in code: wheel dynos support
   ~1.00–1.03 of pure claim conservatism; the remainder absorbs magazine
   ETs' 1-ft rollout convention + pro-rider launches, which the model
   deliberately does not yet carry (staging rollout is epoch-gated). When
   rollout is wired, this factor must be re-tuned DOWN in the same pass.
   What stays structurally honest regardless of the factor's value: the
   loss PATHS are live (chain-eff parts, parasitic wattages, per-bike eta
   differences — a shaft bike now runs ~0.83 vs a chain bike's ~0.93).
3. **The queued honest retune** against the July-17 instrumented rows,
   executed as per-cluster grid searches (evidence in each
   `category_profiles.py` comment):
   - `entry_150_200` decel 900 → **150**: bias −0.370 → **−0.011**. The
     five Indonesian Racelogic rows (MT-15 19.6, RTR 200 18.1 …) exposed
     the old value as fit to optimistic DERIVED data. Notably the <22 hp
     power rung is nearly inert here (rung 1.13→0.96 moved bias only
     −0.37→−0.33; these bikes are launch-limited in the sim), so the
     recentering honestly belongs to the launch knob.
   - `small_i4_screamer` mu 1.30 → **1.00**, decel 2800 → **1400**: w|Δ|
     1.184 → **0.962**. The 1.30 grip fudge was fit to the pre-instrumented
     ZX-25R row. Residual is the documented n=2 conflict (ZX-25R vs ZX-4RR
     pull opposite) — knob-unfixable, needs data.
   - `entry_200_300` mu **1.12** (newly active), decel 40 → **200**:
     0.300 → 0.231 in-grid.
   - `mid_twin_300_500` mu 1.12 → **1.20**, decel 150 → **400**: 0.407 → 0.361.
   - `two_stroke` par 0.20 → **0.10**, decel 1800 → **2400**: 0.669 → 0.642.
   - All other clusters were already centered (|bias| ≤ 0.034) and were
     deliberately left alone.

### Authoritative results (`reports/acc_final_2026_08_08.json`)
| | published (07-17) | tonight |
|---|---|---|
| matched | 277 | 276 (dedup removed one Versys row) |
| weighted \|Δ\| | 0.2721 s | **0.2629 s** |
| weighted bias | −0.0047 s | **+0.0073 s** |
| entry-150-200 bias | −0.402 | **−0.011** |
| small-i4 w\|Δ\| | 1.187 | **0.962** |
| K5 / R1 / Busa | 9.9331 / 10.1436 / 10.3633 | **identical, Δ +0.00e+00** |

Distribution: within ±0.05 s 42 · ±0.10 s 75 · ±0.20 s 138 · ±0.50 s 224 ·
±1.00 s 256 (of 276).

Test-pin consequences, all deliberate: `test_profile_knobs` ACTIVE_MU_SCALES
updated (the guard that forces conscious knob changes fired as designed);
the R15 V4 pin was widened to span the platform's two CONFLICTING
instrumented anchors (MotoStatz R15 V4 17.62 vs Racelogic MT-15 19.6 — same
155 VVA engine, 2 s apart at weight 1.0 each; the centered cluster
necessarily parks the sim between them at 18.37).

## 2. Gearing: the four heavies + limiter annotations (audit §3.2)

Hayabusa Gen2/Gen3, ZX-14R and ZZR1400 carried fabricated cassettes whose
top gears were 21–25 % short — they hit the REV limiter at 264–289 km/h, so
their `speed_limiter_kmh=299` annotations were structurally inert, and
`test_gearing_sanity.py` carried a whitelist entry actively protecting the
bug ("6th = 1.304 (confirmed service manual)" — it was not). Web-verified
real boxes now live in BOTH carriers (spec + Tier-1 lookup, which also
supplied a wrong primary): GSX1300R 2.615/1.937/1.526/1.285/1.136/1.043,
primary 1.596, final 18/43; ZX-14R/ZZR1400 2.611/1.947/1.545/1.333/1.154/
1.036, primary 1.556, final 42/17 / 41/17. The 25th-Anniversary's cassette
(0.871 6th — called "correct" by the July-25 audit) was also not a Suzuki
box and now matches Gen3. Whitelist entry removed.

**Verified: all four heavies + the 25th now terminal at exactly 299.0, and
the newly-annotated VMAX 1700 at exactly 220.0.** Annotation pass added 9
documented specs (ZX-10R ×5, ZX-10RR, S 1000 RR ×2 at 299; VMAX 1700 at
220) → 19 annotated total. Top-speed sweep (83 matched): mean |Δ| 32.0 →
**28.1 km/h**, within-10 17 → **24**, within-20 → 41.

## 3. Catalog data integrity (audit §3.3, §3.3b, §3.3c)

- **Dedup (W2-A):** 542 entries → 538 for 541 DB bikes. Four exact-key
  duplicates adjudicated on web evidence; ~6 impossible geometries fixed
  (V-Strom SX 250's fantasy 67×70.5 engine and height-as-wheelbase; the
  648 cc RE twins' 84×58; Hornet 2.0's nonexistent 194 cc variant; 848 EVO).
  Both regen paths now provably agree (hash-identical 541/541 across both
  orders). Guard test added.
- **OEM tire fitments (W2-B):** compound allowlist replaces the denylist
  that missed `'drag'` (mu 1.85 slicks were winning the OEM fallback on 24
  bikes, including via ordering); `link_bike_fitment` now supersedes stale
  defaults instead of INSERT OR REPLACE appending contradictory ones.
  Shipped-DB damage repaired by re-deciding all 97 slots through the fixed
  production picker: fitments 1860 → **1783**, zero dup-default groups, no
  bike lost OEM coverage, idempotent ×2.
- **Quickshifters (W2-C):** the 8 SKUs whose only override was the
  reader-less `drivetrain.quickshifter` flag now carry honest
  `total_shift_time_ms` values mirrored from same-brand siblings (Dynojet
  twin at the same street price = strongest case). All 8 measurably cut ET
  through the production part path; class guard added for every
  quickshifter/air_shifter SKU.

## 4. Security & product hardening (audit §3.4/§3.5 + §7 items 1, 5, 9)

- **Chat tier-gate settled and shipped (W1-A):** the executor inherits the
  caller's tier; the three pro tools return a typed `upgrade_required` tool
  result under enforcement; provably inert in beta. Chat metering now
  covers classic mode (was ~25 free RK4 sims/request) and heavy ops (18/36
  units, derived from autotune's own tick math); `/api/simulate/compare` +
  `/api/jobs/compare` metered; quick stays free by design (pinned).
  Telemetry beacon: rate-limited, size-capped, bounded thread pool.
  simulate/save: rate limit + notes cap. pricing refresh force: 1 h floor.
- **Dependency pinning (W1-D):** requirements-api.txt upper-bounded with
  CVE floors (python-multipart ≥0.0.18, requests ≥2.32.4, sentry-sdk
  ≥2.11); `requirements-api.lock` (40-pin clean-venv closure) is what the
  Docker image now installs; `make lock` regenerates.
- **Next.js 15.5.23 + React 19 (W4):** 27 advisories → **0**; route table
  byte-diffed identical (73 static / 3 dynamic); one real code change (the
  /r/[id] async-params migration the build cannot catch — verified against
  a stubbed API); caching-default flip verified no-op.
- **Scrapling gates fail closed (W1-B):** substance gate (≥6 page-parsed
  rows + displacement + power) before a spec can be import-ready; non-200s
  never cached as success (5xx escalates tiers, 404 negative-caches 15
  min, poisoned legacy entries self-heal); robots 5xx → full disallow per
  RFC 9309 + Crawl-delay honoured + first real robots test coverage;
  multi-word brand slugs fixed; stealth tier disclosed in docs.
- **Sentry noise:** the OpenAI/Anthropic auto-integrations are disabled at
  init — MOTOQUANT-API-1's Groq 400 was being captured at the SDK boundary
  as handled:no before our salvage path ran.

## 5. Gates that guarded nothing, made real (W1-C; audit §3.4)

- `test_patch_2026_07_13.py` was **17/17** vacuous (worse than the audit's
  16/17 — with all six mutation functions stubbed it passed completely).
  Rewritten to build pre-patch state and assert exact changed-counts; 24
  tests red with mutations stubbed.
- The JWT default-secret boot guard got the test INVARIANTS I7 claimed
  existed (6 subprocess tests against the real import-time guard); I7's
  wrong XFF-pin credit corrected.
- The July-13 fixed-point traction cap got its first revert-sensitive test
  (wet-K5 pinned at 14.8369 ± 0.01 — ~11× margin to the nearest
  alternative pass-count — plus a mechanism test through the production
  `weight_transfer`; 0/1/3-pass variants each fail 4 of 5 tests).

## 6. Web + growth (W1-E)

robots policy un-shadowed (the per-engine `Allow: /` groups that would have
re-exempted Googlebot et al. from every Disallow were deliberately NOT
carried over); sitemap fallback now emits the real 541 sparse IDs from a
committed manifest (was: 198 real pages omitted + 257 soft-404 phantoms);
funnel events paired via one `trackSimRun()` handle across all five sim
flows (the default quick-sim emitted NOTHING before; conversion was
structurally 0 %).

## 7. New distribution channel (W4b)

`motoquant/mcp_server.py` — stdlib-only stdio MCP server (newline-delimited
JSON-RPC 2.0, protocol 2025-06-18), 9 tools, HTTP + local backends where
local calls the SAME functions the FastAPI routes call. `gearing_impact` is
the headline demo; the skill (skills/motoquant/) teaches the glossary, the
sign convention, and forbids stating a gearing direction that hasn't been
simulated (it reverses between bikes: R15 14/48→14/52 gains 0.057 s of
60-foot; K5 17/42→17/47 loses 0.20 s). `docs/MCP.md` has the wire-up.
30 tests, zero network; K5's 9.9331 reproduced through the tool path.

## 8. Regen chain + artifacts

Reseed → 5 existing patches (all no-op, fixed point held) → 2 NEW patches
(fitment integrity: 97 slots repaired; quickshifters: 8 armed), both proven
idempotent ×2 against the tracked DB. Final DB: 541 models / 541 current
configs / 593 parts / 254 tires / **1783 fitments** / 20 venues. Golden
snapshot regenerated (references byte-exact) and green on BOTH tiers
including the full-catalog slow tier. Surrogate v2.6 dataset (9,126 rows)
regenerated + numpy MLP retrained (cache-of-physics contract).
`/validation` viz + sitewide stats synced. The reseed chain is now:
`reseed_configs_from_specs.py → patch_2026_07_06_reference_configs →
patch_2026_07_06_catalog_integrity → patch_2026_07_06_tire_dedup →
patch_2026_07_13_scrape_data → patch_2026_08_08_fitment_integrity →
patch_2026_08_08_quickshifter_overrides → golden + surrogate + viz regen`.

## 9. Honest limits & deferred

- `_CRANK_MODE_RECAL` is corpus-calibrated, not first-principles; its
  decomposition (claim conservatism vs unmodeled rollout/launch) is
  documented but not separable until staging rollout is wired (epoch-gated).
- Top-speed bias (+24.3) remains: the broad annotation pass only covers 19
  bikes with documented limiters; the rest of the overshoot is aero/data
  work (the sport-category Cd×0.55 normalisation from audit §3.4 is still
  open).
- small_i4 stays the worst cluster (0.962 on n=2 conflicting benchmarks) —
  data-limited by construction.
- Audit §3.4 items NOT taken tonight: rev-limiter zero-hysteresis cliff,
  slip_ratio discontinuity, Cd×0.55 normalisation (all epoch-gated physics
  with pin impact), bore/stroke-vs-displacement validator warnings, the
  848-EVO mislabel rename (needs a bike_models migration), sweep-binding
  shadowing (ZX-9R weight-1.0 row) — the last belongs with the next corpus
  pass.
- W1-A flags: prod DB still ships 3 historical sim_usage rows (16 phantom
  units — needs a one-line data pass); `pricing_refresh.fetch_live_price`'s
  14-day freshness string-comparison is unreliable (latent, side-stepped by
  the new floor).
- PR housekeeping for the operator: #117 is a real fix worth merging; #88's
  content landed in #114 (verify + close); #102 needs a rebase.

## 10. Operator items (unchanged from the audit, all still blocking)

O1 Actions billing (CI runnerless since 2026-07-13 — tonight's PR will show
no CI; the full suite was run locally instead). O2 `POSTHOG_API_KEY` (the
funnel events shipped tonight are wasted until this is set). O3 Oracle
steps. O4 Vercel BLOCKED-deploy setting. O5 PAT/`VERCEL_TOKEN` rotation.

## 11. Session mechanics (for future orchestrators)

9 agents (Opus per operator instruction), all completed; one required a
mid-flight status nudge (W1-A, the biggest bundle — 5,000 s) and one
concurrent-DB race was designed out by having data agents verify patches on
temp copies only, with the orchestrator applying everything to the tracked
DB in a single controlled integration step. That protocol caught a real
near-miss: W1-A ran `git checkout -- motoquant.db` during a leak hunt
minutes before the reseed landed; because the reseed happened after its
last checkout (verified by state inspection: 1783 fitments + 8 armed
quickshifters + crank blobs), nothing was lost. The retune's first grid
round was invalidated once by a mid-flight design upgrade (per-cluster
recal → global crank recal) — killing 90 %-wasted compute early beat
letting it finish.
