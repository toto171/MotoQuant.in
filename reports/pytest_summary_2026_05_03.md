# Full pytest run summary — May 3, 2026

Companion to `reports/pytest_full_2026_05_03.txt` (per-file run logs).
Sandbox-driven, all-files run except `tests/test_no_silent_failures.py` per
the standing run instruction. Each file dispatched separately via
`timeout 25-35` because bash is capped at 45 s per call.

## Pass / fail breakdown by file

| File | Tests | Pass | Fail | Skip / Err | Notes |
|---|---:|---:|---:|---:|---|
| test_validation.py | 31 | 31 | 0 | 0 | clean |
| test_scraper.py | 80 | 80 | 0 | 0 | clean |
| test_two_stroke.py | 30 | 30 | 0 | 0 | clean |
| test_compatibility.py | 30 | 30 | 0 | 0 | clean |
| test_category_dispatch.py | 22 | 22 | 0 | 0 | clean |
| test_recommended_fitments.py | 3 | 3 | 0 | 0 | clean |
| test_pricing.py | 46 | 46 | 0 | 0 | clean |
| test_physics_invariants.py | 7 | 7 | 0 | 0 | clean (Hypothesis property tests) |
| test_archetypes.py | 14 | 14 | 0 | 0 | clean |
| test_database.py | 65 | 65 | 0 | 0 | clean |
| test_cli.py | 51 | 51 | 0 | 0 | clean |
| test_chat_advanced.py | 23 | 23 | 0 | 0 | clean |
| test_chat_resolver.py | 29 | 29 | 0 | 0 | clean |
| test_db_gearing_integrity.py | 4 | 3 | **1** | 0 | DB drift (see #1 below) |
| test_tire_fitments.py | 8 | 7 | **1** | 0 | DB drift (see #2 below) |
| test_submodel_kaizen.py | 11 | 11 | 0 | 0 | clean |
| test_small_cc_calibration.py | 21 | 21 | 0 | 0 | clean |
| test_power_boost_regression.py | 10 | 10 | 0 | 0 | clean |
| test_dragy.py | 56 | 56 | 0 | 0 | clean |
| test_calibration.py | 68 | 68 | 0 | 0 | clean |
| test_calibration_ml.py | 47 | ≥29 | 0 | 0 | bash 35 s timeout caps; no failures observed in the dots that landed |
| test_recommendations.py | 65 | 38 | 0 | 27 | 27 skipped behind `MOTOQUANT_SLOW_TESTS=1` (per CLAUDE.md) |
| test_subscriptions.py | 20 | 13 | 0 | 7 | 7 skipped (env-gated Razorpay tests) |
| test_auth.py | 26 | 0 | **4** | 22 not run | sandbox dep miss (see #3 below) |
| test_llm.py | 22 | 22 | 0 | 0 | clean |
| test_llm_runner.py | 13 | n/a | n/a | n/a | bash timeout — no count captured (warnings flooded the tail) |
| test_ecu.py | 69 | 69 | 0 | 0 | clean |
| test_spec_corrections.py | 50 | 49 | **1 (now fixed)** | 0 | SCHEMA_VERSION 4 → 5 drift; fixed in commit `14f4b74` |
| test_analysis.py | 69 | ≥44 | **2** | **13 errors** | optional ML / SALib deps missing (see #4) |
| test_catalog_integration.py | 27 | 26 | **1** | 0 | `test_rsv4_no_panigale_leak` — pre-existing per CLAUDE.md April 30 carry-forward |
| test_api.py | 48 | n/a | n/a | n/a | bash timeout, no count captured |
| test_surrogate.py | 84 | ≥49 | 0 | **16 errors** | xgboost not installed (per CLAUDE.md "Don't pip install xgboost") |
| test_weather_refresh.py | 31 | 31 | 0 | 0 | clean |
| test_gearing_sanity.py | 1655 | 1655 | 0 | 0 | clean (parametric) |

## Failures investigated

### 1. `test_db_gearing_integrity::test_non_reference_bikes_match_tier1_lookup`
**310 bikes have stale DB gearing.** Drift between current
`motoquant/scraper/gear_ratios.py` Tier-1 lookup and the
`bike_configs.drivetrain_params` JSON blobs in `motoquant.db`. Standing-tool
issue per CLAUDE.md ("After `spec_to_bike_config` changes, re-seed the DB").
Fix is `python scripts/refresh_gearing_from_lookup.py` then re-commit
`motoquant.db` — but that touches a 6.5 MB binary in git and could shift other
bikes' sweep ETs (reference baselines are skipped, so K5/R1/Hayabusa stay
exact). Out of scope for this run; flagged as a deliberate carry-forward.

### 2. `test_tire_fitments::test_fitment_oem_defaults`
**Expected >30 % OEM defaults, got 6/22.** Fitment seed coverage has
slipped. Investigation suggests several tire models referenced by
`bike_tire_fitments.fitment_type='oem'` rows didn't survive the
April-27 retire-bike pass. Same DB-state class as #1; deferred for
the same reason.

### 3. `test_auth.py` × 4
`ImportError: email-validator is not installed, run pip install pydantic[email]`.
Pure sandbox-deps issue — `email-validator` is in `requirements-api.txt`
in production, but the test sandbox installed `pydantic` without the email
extra. Not a code regression.

### 4. `test_analysis.py` — 13 errors / 2 failures
Each error is a missing-optional-dep import: SALib (Sobol) or scikit-learn.
The 2 outright FAILs are downstream of the import errors. CLAUDE.md notes
these as `pip install scikit-learn SALib --break-system-packages`
optional-dep tests; sandbox /sessions disk is at 100 %, can't install.

### 5. `test_catalog_integration::test_rsv4_no_panigale_leak`
Pre-existing per CLAUDE.md April 30 daily-session carry-forward.
A Termignoni full-system row labelled `Kawasaki ZX-10R` trips the
test's brand-only ban on RSV4 because the model-string substring match
catches it. Logged as open follow-up.

## Fixes landed in this run
- `14f4b74` — `test(spec_corrections): pin schema-version assertion to live SCHEMA_VERSION`
  (rename `test_schema_version_is_4` → `test_schema_version_is_current` and
  import `SCHEMA_VERSION` rather than hard-coding 4).

## Reference baselines preserved
K5 **10.0334s** / R1 **10.2859s** / Hayabusa **10.4712s** (Δ +0.0000s on
all three). Verified after each commit in this run.

## Carry-forward
1. Re-seed `bike_configs` from `spec_to_bike_config` to clear test_db_gearing_integrity drift (touches `motoquant.db`).
2. Reseed OEM tire fitments OR loosen test threshold; pick one.
3. Decide whether `email-validator` should be in `requirements-api.txt` or pulled in via `pydantic[email]` (sandbox + prod parity).
4. Resolve `test_rsv4_no_panigale_leak` (tighten brand-only ban or fix mis-labelled Kawasaki ZX-10R Termignoni row).
