# Subagent 5 — Type Strengthening Report
**Scanned:** 2026-05-05  
**Files scanned:** 18 (Python + TypeScript)

## High-confidence strengthenings (apply these)

### Python

1. **`motoquant/api.py:123` — `_bike_row_to_summary`**
   - Current: `def _bike_row_to_summary(row: dict) -> dict:`
   - Proposed: `def _bike_row_to_summary(row: dict[str, Any]) -> dict[str, int | str | None]:`
   - Justification: Returns a fixed-shape dict with `id`, `manufacturer`, `model`, `year`, `category`, `displacement_cc`, `peak_power_hp`, `dry_mass_kg`, `data_quality`. Schema at `schema.py` `bike_models` table confirms all are nullable except `id`.

2. **`motoquant/database/bridge.py:150` — `extract_headline_specs`**
   - Current: `def extract_headline_specs(config: BikeConfig) -> dict[str, Any]:`
   - Proposed: Return type `HeadlineSpecsDict` (TypedDict with 13 fields: `displacement_cc`, `bore_mm`, `stroke_mm`, `compression_ratio`, `peak_power_hp`, `peak_power_rpm`, `peak_torque_nm`, `peak_torque_rpm`, `cylinder_count`, `cylinder_config`, `dry_mass_kg`, `wheelbase_mm`, `seat_height_mm` — all `float | int | None`).
   - Justification: Function explicitly constructs a fixed dict at lines 159–173. TypedDict makes the shape discoverable.

3. **`motoquant/llm/runner.py:91–98` — `run_chat_pipeline`**
   - Current: `db: Any` parameter
   - Proposed: `db: MotoQuantDB` (or the actual type the caller passes)
   - Justification: Function only calls `db.get_bike_by_id()`, `db.query_bikes()`, `db.get_venue_by_id()` — all MotoQuantDB methods. Tracking `Any` loses those interface guarantees.

### TypeScript

4. **`desktop/src/types/api.ts:69, 84, 100, 113, 138` — Index signature `[extra: string]: unknown`**
   - Current: `[extra: string]: unknown` on `BikeDetail`, `Venue`, `Tire`, `PartsCategory`, `Part`
   - Proposed: Replace with `[extra: string]: never` (strict mode) or list explicit optional fields if the API does return extras.
   - Justification: `unknown` is too loose; TS strict mode should flag unmapped properties as errors, not silently allow them. If the API legitimately returns extra fields, they should either be enumerated or typed as `never` to catch client-side bugs where the field name is wrong.

5. **`desktop/src/types/api.ts:134–135` — Part fields**
   - Current: `compatible_bikes?: unknown; fitment_rules?: unknown;`
   - Proposed: Study the actual API response schema at `motoquant/api.py` and type these as `CompatibleBikes[] | null` and `FitmentRule[] | null` respectively.
   - Justification: UI code never reads these fields (verified via grep), so the unknown type hides whether they're even being used.

6. **`desktop/src/pages/BuildPage.tsx:80` — Type assertion**
   - Current: `const stockHp = (bike as unknown as { peak_power_hp?: number }).peak_power_hp ?? 100;`
   - Proposed: Use a type guard instead: `function hasPeakPower(b: BikeSummary): b is BikeSummary & { peak_power_hp: number } { return b.peak_power_hp != null; }` then `const stockHp = hasPeakPower(bike) ? bike.peak_power_hp : 100;`
   - Justification: The double-cast `as unknown as {...}` is a red flag that the true type is unknown. BikeSummary already declares `peak_power_hp: number | null`, so the guard pattern is safer.

7. **`desktop/src/pages/SimulatePage.tsx:213` — Type assertion**
   - Current: `splits: result.splits as unknown as Record<string, number>`
   - Proposed: Check `motoquant/api.py` `SimulateResult` schema and type `result.splits` correctly (likely `dict[str, float]` at the API boundary). If the field shape is uncertain, create `SplitsDict: Record<string, number>` and verify the API returns it.
   - Justification: Without knowing the real splits shape, the cast loses information. The shape should come from the schema definition, not from the UI's guess.

## Medium-confidence (worth a closer look)

1. **`motoquant/scraper/importer.py` — All `_build_*_from_spec()` helpers**
   - These return specific dataclass types (EngineParams, ChassisParams, etc.) but internally use loose dict constructions. Worth auditing for internal `dict[str, Any]` usage that could be tightened.
   - Example: `_build_engine_from_spec` constructs a dyno curve dict → should use `DynoCurve` directly instead of a dict passed to the constructor.

2. **`motoquant/llm/runner.py:71–75` — ChatResult fields**
   - Fields like `sim_result: dict[str, Any] | None`, `compare_result: dict[str, Any] | None` etc. should be typed as their actual Pydantic model equivalents (e.g., `SimResult | None`).
   - Justification: These come from the dispatch handlers (`_run_simulate()`, `_run_compare()`, etc.) which return structured dicts that could be Pydantic models for runtime validation.

## Boundary types where weak is correct

- `run_chat_pipeline(db: Any, ...)` — `Any` is intentionally permissive for backwards compat with test mocks that don't inherit from MotoQuantDB. Once test infrastructure is tightened, this can graduate to `MotoQuantDB | MockDB` protocol.
- `[extra: string]: unknown` on API response models — legitimately needed if the backend adds fields dynamically. Recommend documenting in the interface comment if that's intentional.

## Numerical summary

| Category | Count |
|----------|-------|
| Functions audited | 15 |
| Weak function signatures (`Any` params) | 3 |
| Untyped dict returns | 2 |
| TS `any` assertions | 0 |
| TS `unknown` index signatures | 5 |
| TS type assertions (`as X`) | 2 |

**Regressions prevented by fixing #1–3:** DB schema mismatches, lost type information in chat payload dispatch.  
**Regressions prevented by fixing #4–7:** Silent field-name typos in UI, wrong splits shape in PDF export.
