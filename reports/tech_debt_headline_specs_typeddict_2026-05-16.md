# Tech-Debt Pass — HeadlineSpecsDict TypedDict
**Agent:** A9 technical-debt-pass
**Date:** 2026-05-16 (Saturday)
**Status:** Applied (uncommitted; caller will run postflight)

## Goal (one sentence)

Replace the loose `dict[str, Any]` return type of `motoquant.database.bridge.extract_headline_specs` with a concrete `HeadlineSpecsDict` TypedDict so the 13-key contract between this helper and `bike_repo.create_model(**headline_specs)` is discoverable and type-checkable.

## Success criteria

- `extract_headline_specs` returns a properly typed `HeadlineSpecsDict`
- All focused tests still pass (test_scraper / test_validation / test_two_stroke / test_compatibility / test_submodel_kaizen / test_power_boost_regression)
- `tests/test_database.py` still passes (it exercises the full bike-config round-trip path that uses `extract_headline_specs` under `bike_repo.upsert_from_config`)
- K5/R1/Hayabusa baselines preserved exactly
- LOC delta ≤ 50

## Files touched

- `motoquant/database/bridge.py` (+27 / -2 lines)

## Change summary

1. Added `from typing import ..., TypedDict` import.
2. Added `HeadlineSpecsDict` TypedDict directly above `extract_headline_specs`. Documents the 13 fields:
   - `displacement_cc`, `bore_mm`, `stroke_mm`, `compression_ratio` — chassis geometry / CR (`float | None`)
   - `peak_power_hp`, `peak_power_rpm`, `peak_torque_nm`, `peak_torque_rpm` — performance envelope (`float | None`)
   - `cylinder_count` (`int | None`), `cylinder_config` (`str | None`) — engine family discriminator used by the parts-compatibility engine
   - `dry_mass_kg`, `wheelbase_mm`, `seat_height_mm` — chassis (`float | None`)
3. Changed `extract_headline_specs` return type from `dict[str, Any]` → `HeadlineSpecsDict`.

The function body is unchanged. All values flow into `bike_models` columns as SQL nullable, hence `| None` on every field (matches the schema and the `getattr(..., None)` pattern already used for cylinder_count / cylinder_config).

## Tests run

```
python3 -m pytest tests/test_scraper.py tests/test_validation.py tests/test_two_stroke.py \
                  tests/test_compatibility.py tests/test_submodel_kaizen.py \
                  tests/test_power_boost_regression.py
# → 192 passed in 15.41s

python3 -m pytest tests/test_database.py
# → 65 passed in 2.35s
```

Total: **257 tests passed, 0 failed.**

## Baseline verification

| Bike | Baseline | This run | Δ |
|---|---|---|---|
| GSX-R 1000 K5 | 10.0334s | 10.0334s | +0.0000s |
| YZF-R1 4C8 | 10.2859s | 10.2859s | +0.0000s |
| Hayabusa Gen 1 | 10.4712s | 10.4712s | +0.0000s |

All three reference baselines preserved exactly to 4 decimals.

## Metrics

| Metric | Before | After |
|---|---|---|
| `extract_headline_specs` return type | `dict[str, Any]` (opaque) | `HeadlineSpecsDict` (13 named fields) |
| `bridge.py` LOC | 446 | 473 |
| Net LOC delta | — | +27 / −2 = **+25** |
| Tests run | 257 | 257 |
| Tests passed | 257 | 257 |
| K5 / R1 / Hayabusa baseline drift | n/a | 0.0000s on all three |

## Rationale

Flagged by `reports/cleanup_subagent_5_types.md` finding #2 as a high-confidence type-strengthening target. The function constructs a fixed-shape dict at lines 159-173 that gets `**`-unpacked into `bike_repo.create_model`, whose `**headline_specs` parameter feeds the keys straight into SQL `INSERT INTO bike_models (...)`. Before this change, a future contributor adding a new field to one side could silently break the other; now the TypedDict makes the contract explicit and the structural-typing rules will surface drift at type-check time.

The change is purely additive — no callers needed to be updated because `HeadlineSpecsDict` is a `dict` subtype at runtime (TypedDict is erased at runtime in Python). `**`-unpacking continues to work identically.

## Out of scope (deferred)

The same cleanup report (`cleanup_subagent_5_types.md`) lists six other high-confidence type-strengthening targets:

- `_bike_row_to_summary` in `api.py` — similar TypedDict candidate.
- `run_chat_pipeline` in `llm/runner.py` — `db: Any` → `db: MotoQuantDB`.
- TypeScript `[extra: string]: unknown` index signatures across `desktop/src/types/api.ts`.
- TypeScript `as unknown as { ... }` casts in `BuildPage.tsx` and `SimulatePage.tsx`.

These are independent refactors and explicitly out of scope per the "one narrow refactor PR" constraint.
