# Tech-Debt Pass — `Part.compatible_bikes` & `Part.fitment_rules` Typed Shapes
**Agent:** A9 technical-debt-pass
**Date:** 2026-05-20 (Wednesday)
**Source finding:** `reports/cleanup_subagent_5_types.md` finding #5 (high-confidence TS type strengthening)

## Goal (one sentence)

Replace `compatible_bikes?: unknown; fitment_rules?: unknown;` on the `Part`
interface in `desktop/src/types/api.ts` with concrete TypeScript shapes
mirroring the JSON payload that `/api/parts` actually returns, so future UI
work against these fields catches mistakes at compile time instead of failing
silently against an `unknown` type.

## Success criteria

- Concrete TypeScript shapes for both fields, with `string` fallback to match
  the API's "couldn't parse JSON" path.
- New `FitmentMatch` + `FitmentRule` interfaces matching
  `motoquant/database/schema.py::parts.fitment_rules` and the seed-catalog
  examples (e.g. `seed_catalogs/premium_universal.py:47-56`).
- `tsc --noEmit` passes cleanly across the whole desktop frontend.
- No UI code change needed (verified by grep — fields are declared but never
  read in `desktop/src/**`).
- Focused Python tests still pass and K5/R1/Hayabusa baselines preserved.
- LOC delta ≤ 50.

## Files modified

| File | Change |
|---|---|
| `desktop/src/types/api.ts` | +34 / -2 = **net +32 lines** |

That is the only file touched. No call-site edits were needed because the
existing `unknown` types meant the UI never read either field; the
strengthening is purely additive on a previously-anonymous shape.

## Before / after

**Before** (lines 134-135 of `Part`):
```ts
compatible_bikes?: unknown;
fitment_rules?: unknown;
```

**After**:
```ts
// Match clause inside fitment_rules (family/category-tier constraints).
// Schema documented at motoquant/database/schema.py::parts.fitment_rules.
// Every field is optional because each part declares only the constraints
// relevant to it (e.g. a "bodywork" universal part may omit all of them).
export interface FitmentMatch {
  manufacturers?: string[];
  engine_configs?: string[]; // "I1" | "I2" | "I3" | "I4" | "V2" | "V4" | ...
  categories?: string[];
  displacement_min_cc?: number;
  displacement_max_cc?: number;
  chain_pitch?: string;      // "428" | "520" | "525" | "530"
  stroke_type?: number;      // 2 or 4
  [extra: string]: unknown;  // tolerate future schema additions
}

// Shape of a parsed fitment_rules JSON blob as returned by /api/parts.
// `tier` is one of "exact" | "family" | "category" | "universal" (see
// motoquant/parts/compatibility.py). API may also return the raw JSON string
// if parsing fails; the union below documents that fallback explicitly.
export interface FitmentRule {
  tier: "exact" | "family" | "category" | "universal" | string;
  bike_ids?: number[];
  excluded_bike_ids?: number[];
  match?: FitmentMatch;
  description?: string;
  [extra: string]: unknown;
}

// ... inside Part:
compatible_bikes?: number[] | string | null;
fitment_rules?: FitmentRule | string | null;
```

## Why the `| string` fallback

`motoquant/api.py:1219-1232` parses each of these columns with
`json.loads(d[field])` inside a `try/except (json.JSONDecodeError, TypeError)`
that swallows parse errors and leaves the raw string in place. So the wire
type genuinely can be either the parsed structure OR the original string.
The TS union spells that out — TypeScript narrows correctly via `typeof
fitment_rules === "string"` checks at any future call site that consumes
these fields.

## Why `number[]` for `compatible_bikes`

`motoquant/database/schema.py:380` documents it as "JSON array of
bike_model_ids" and the only writer (legacy code path) stores integer IDs. No
seed catalog uses this field at all today; it is preserved for backwards
compat with older catalogs.

## Tests run

**TypeScript:**
```
cd desktop && ./node_modules/.bin/tsc --noEmit
# → exit 0 (clean)
```

**Python focused suite (per task gate):**
```
python3 -m pytest tests/test_scraper.py tests/test_validation.py \
                  tests/test_two_stroke.py tests/test_compatibility.py \
                  tests/test_submodel_kaizen.py tests/test_power_boost_regression.py
# → 192 passed, 523 warnings in 14.96s
```

## Baseline verification

| Bike | Baseline | This run | Δ |
|---|---|---|---|
| GSX-R 1000 K5 | 10.0334s | 10.0334s | +0.0000s |
| YZF-R1 4C8 | 10.2859s | 10.2859s | +0.0000s |
| Hayabusa Gen 1 | 10.4712s | 10.4712s | +0.0000s |

All three reference baselines preserved exactly to 4 decimals. (The change is
TypeScript-only and cannot affect Python physics, but the gate is mandatory
per `scripts/agents/technical-debt-pass.md`.)

## Metrics

| Metric | Before | After |
|---|---|---|
| `Part.compatible_bikes` type | `unknown` | `number[] \| string \| null` |
| `Part.fitment_rules` type | `unknown` | `FitmentRule \| string \| null` |
| New named interfaces | 0 | 2 (`FitmentMatch`, `FitmentRule`) |
| `desktop/src/types/api.ts` LOC | 254 | 286 |
| Net LOC delta | — | **+32** |
| TS compile errors | 0 | 0 |
| Python tests | 192 | 192 |
| K5 / R1 / Hayabusa drift | n/a | 0.0000s on all three |

## Kaizen checklist

- [x] **No silent failure** — runtime wire format unchanged; this is a type
  refinement only. The `| string` fallback documents the existing API JSON
  parse-failure path explicitly instead of letting it surface as a runtime
  surprise inside `unknown`.
- [x] **No data/model mismatch** — interfaces mirror the parts.fitment_rules
  JSON schema documented at `motoquant/database/schema.py:379-380` and the
  seed-catalog producers in `motoquant/database/seed_catalogs/*.py`.
- [x] **No bypass path** — single Part interface is the only shape declared
  for `/api/parts` rows; tightening it improves every future consumer at once.
- [x] **Test coverage** — TypeScript `tsc --noEmit` exercises every existing
  declaration site. No UI code reads these fields yet (verified via
  `Grep "compatible_bikes|fitment_rules" desktop/src`), so no behavioural
  test is required; future BuildPage / PartsPage work that reaches for these
  fields will get compile-time guidance.
- [x] **Numerical sanity** — physics untouched.
- [x] **No dead fields introduced.**
- [x] **Backwards compatibility** — TS structural typing means existing call
  sites that already worked with `unknown` continue to compile; this can
  only relax the burden on callers, not break them.

## Rationale

Flagged by `reports/cleanup_subagent_5_types.md` finding #5 as a
high-confidence TypeScript type-strengthening target. Both fields are
populated by the API (verified at `motoquant/api.py:1219-1232`) but
previously hidden behind `unknown`, which is just `any` without the
unsafe-method-call ergonomic — a future contributor who reaches for
`part.fitment_rules.match.engine_configs` would get a type error today but
no guidance, whereas with this change the editor auto-completes the path.

This continues the pattern of the prior tech-debt passes that strengthened
`extract_headline_specs` (TypedDict, 2026-05-16) and `_bike_row_to_summary`
(TypedDict, 2026-05-20) on the Python side — same approach, applied to the
TS surface this time so the contract is explicit on both ends of the wire.

## Out of scope (deferred to future passes)

From `cleanup_subagent_5_types.md`, still open:

- **#3** `run_chat_pipeline(db: Any, ...)` in `motoquant/llm/runner.py` —
  flagged as boundary type where weak is intentional (test-mock compat).
- **#4** TypeScript `[extra: string]: unknown` index signatures on
  `BikeDetail`, `Venue`, `Tire`, `PartsCategory`, `Part`. Each needs an
  independent audit of which extras are legitimately consumed by the UI;
  could break the catch-all that currently tolerates schema additions.
- **#6, #7** TypeScript double-cast patterns (`as unknown as { ... }`) in
  `BuildPage.tsx` and `SimulatePage.tsx`. Need type-guard refactor inside
  page logic; out of "types-only" scope.

These are separate refactors with their own blast radii.

## Ship or skip

**SHIP** — type-only refinement, TS clean, Python physics baselines exact,
192 focused tests green, +32 LOC. Zero runtime risk.
