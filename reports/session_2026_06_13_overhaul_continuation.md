# Session — 2026-06-13 (continuation of the interrupted "Motoquant project overhaul")

The prior chat (model `claude-fable-5`) executed the operator's multi-part brief
then went unavailable mid-flight. This session finished the remaining work.
Operator directives this session: **stay on Opus, ship live to `main`.**

## What the interrupted session had already shipped (verified on origin @ 04e0ef5)
- Gear-count audit (2 verified 5→6 fixes + regression pin).
- Duplicate-manufacturer part-name de-dup (234 rows normalized + `partLabel`
  guards across web sim/optimize/tune + desktop).
- +60 real-world benchmarks (coverage 31%→43%; BENCHMARKS now 216 rows).
Its physics work lived only in a stranded `/tmp` clone (origin = a dead FUSE
path) built on the pre-wave base ac0f7ad — obsolete vs current main, so NOT
re-applied. Only genuinely new idea (single-cyl high-RPM falloff) was evaluated
and rejected (current entry clusters are already centred; it would regress them).

## Shipped this session (origin/main 04e0ef5 → 0595dc6)
1. **a445008 — physics.** New `scripts/phys_weighted_sweep.py` (resumable,
   source-weighted: instrumented 1.0 … DERIVED 0.1). True current-main baseline:
   **236 matched, weighted mean|Δ| 0.263s, bias −0.014s.** Finding: the worst
   clusters are *data-quality* limited, not model limited — entry-150-200 raw
   |Δ| 1.64 collapses to 0.38 on high-confidence benchmarks. One defensible
   physics change: **cruiser-1300+ over-clutch 0.30→0.45 / decel 800→900**
   (uniform +0.36 slow bias on 3 muscle bikes → +0.31). Did NOT over-fit the
   thin/noisy clusters (prior 06-11 grid-search already at ceiling). Report:
   `reports/physics_audit_2026_06_13.md`.
2. **bc4edb9 — optimizer reliability (live-QA defect).** Build Optimizer reliably
   died at 97% with "Connection lost". Root cause: the surrogate-verification
   stage full-sims the picks for up to 3 rounds but emitted ONE 0.97 tick —
   on Render's 0.5-CPU tier those back-to-back sims starve the /api/jobs poll
   handler past the client's 60s window, though the job completes server-side.
   Fix: per-sim progress ticks (0.95→0.99) + 20ms CPU yield in build_optimizer;
   client poll tolerance 60s→150s.
3. **39dead9 — catalog cleanup.** 16 bikes had doubled year-range suffixes
   ("Tuono 457 (2025-2026) (2025-2026)"). Fixed the 16 DB rows + idempotent
   collapse guard in `bike_repo.create_model`.
4. **197bce8 — desktop hardening (task #30).** Auth refresh token moved from
   sessionStorage → OS keychain (keyring crate: Keychain/Credential Manager/
   Secret Service) via new `keychain_*` Tauri commands + `secureStore.ts` with
   graceful sessionStorage fallback. SECURITY.md updated. **NATIVE LAYER NOT
   BUILT — no cargo in sandbox; verified by release.yml's tag matrix. TS verified
   clean; only release.yml (v* tags) compiles the Rust, so push CI is unaffected.**
5. **0595dc6 — fact update.** New authoritative sweep
   `reports/acc_final_2026_06_13.json`; synced every headline stat + accuracy
   claim sitewide (landing, docs/validation, whitepaper, how-it-works blog,
   features, docs/physics, about, layout meta, CTAs): benchmark count 156→216,
   bias −0.007→−0.015s, top-10 ±0.010/±0.032→±0.006s, stale "342+ bikes"→501.
   `audit_headline_stats.py` clean.

## Verification
K5 10.0334 / R1 10.2859 / Hayabusa 10.4712 — **Δ+0.0000 after every change.**
Focused suites green (category_dispatch, power_boost_regression, validation,
submodel_kaizen, two_stroke, scraper, build_optimizer, import_idempotency).
`next build` 74/74 routes prerendered (twice). Live-QA in Chrome on motoquant.in:
landing/simulator/optimize/autotune/bikes/pricing all functional; manufacturer
de-dup confirmed live.

## Open / operator action
- **Desktop binaries** still blocked on a Rust toolchain + signing (release.yml
  tag build). The keychain Rust is unbuilt-in-sandbox — if the Linux build
  objects, the lever is the `keyring` feature set in `desktop/src-tauri/Cargo.toml`.
- Whitepaper/blog accuracy prose was refreshed to the 13-Jun sweep; if a future
  benchmark pass changes counts, re-run `audit_headline_stats.py` + this sync.
- OG image: content already says 501; `og_image_stale` heuristic flags mtime
  only — regenerate at leisure.
- PAT rotation overdue (06-03). Local FUSE folder: `git merge --ff-only origin/main`.
