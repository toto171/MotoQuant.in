# Daily Improvement Session — Saturday, May 2, 2026

**Focus area:** Test Hardening Day — Hypothesis property tests for the four
load-bearing physics monotonicity invariants.

## Summary

Added a new property-test module that pins direction (not exact value) for
the four invariants every drag-sim physics regression historically broke
first:

1. **More mass => slower ET** (catches stale chassis defaults like the April
   24 2026 R15-class fluid_mass_kg / basket_inertia drift)
2. **More peak power => faster ET** (catches the April 24 AM
   `power_boost_pct` dead-knob bug — peak_power_hp scaled but dyno_curve
   did not, so ET was unchanged 0..50% boost on R15 V3)
3. **Higher drag coefficient => slower ET** (catches accidental aero rewires)
4. **Larger frontal area => slower ET** (same)

Each property runs across all three reference platforms (K5, R1, Hayabusa
Gen1), exercising three distinct cluster code paths:
`litre_sport_195p`, `litre_sport_600_1000`, and the 1300+ Hayabusa class
under category-flavoured physics dispatch.

Property-based tests complement the existing pytest snapshot tests:
snapshots catch *exact-value* drift on recorded cases; property tests catch
*direction* drift across the entire input space.

## Files touched

- **NEW** `tests/test_physics_invariants.py` (269 lines)
  - 4 Hypothesis property tests, `max_examples=8` each, `deadline=None`
  - 1 parametrised baseline-pin test (3 references) — guards against
    accidental shared-mutation regressions in the property suite
  - Module-level `pytest.importorskip("hypothesis")` so the rest of the
    fast suite stays green on a vanilla checkout
- **NEW** `requirements-dev.txt` (16 lines)
  - Pins `pytest>=7.0,<10` + `hypothesis>=6.100,<7`
  - Production `requirements-api.txt` is untouched

## Test results

Focused subset (post-playbook gate):
```
tests/test_scraper.py
tests/test_validation.py
tests/test_two_stroke.py
tests/test_compatibility.py
tests/test_category_dispatch.py
tests/test_physics_invariants.py    <-- new
=> 200 passed in 35.94s
```

Property-test breakdown (verbose run):
```
test_more_mass_means_slower_et[<3 bikes>] ............. PASS
test_more_power_means_faster_et[<3 bikes>] ............ PASS
test_higher_cd_means_slower_et[<3 bikes>] ............. PASS
test_larger_frontal_area_means_slower_et[<3 bikes>] ... PASS
test_reference_baselines_pinned_after_property_runs[K5/R1/Hayabusa]  PASS
=> 7 passed in 22.39s
```

The four property tests each ran 8 Hypothesis examples × `assume()`
filter, covering the realistic input range of:
- mass: 150–200 kg (low) vs 240–320 kg (high), spread ≥30 kg
- power scale: 0.80–0.95 vs 1.05–1.20, spread ≥0.10
- Cd: 0.55–0.65 vs 0.75–0.95, spread ≥0.10
- frontal area: 0.35–0.42 vs 0.50–0.65 m^2, spread ≥0.07 m^2

## Reference baseline check

| Bike     | ET       | Target  | Delta      |
|----------|----------|---------|------------|
| K5       | 10.0334s | 10.0334 | +0.0000s   |
| R1       | 10.2859s | 10.2859 | +0.0000s   |
| Hayabusa | 10.4712s | 10.4712 | +0.0000s   |

All three within 0.001s tolerance — passes the pre-run AND post-run gate.

## Headline-stats audit

Pre-run audit reported "All headline numbers in sync. No action needed."
Source-of-truth values: 334 bikes / 232 tires / 562 parts / 861 fitments /
20 venues / 79 benchmarks. No drift to fix.

## Sanity-check: would the property tests catch a real regression?

Manually probed an inverted relationship to confirm signal-to-noise:
- 200 kg vs 250 kg on K5: ET 10.2195s vs 10.6065s, delta +0.387s
- The 1 ms `ET_TOLERANCE_S` is ~400× smaller than the smallest spread we
  enforce, so the property tests would unambiguously catch any genuine
  invariant violation.

A separate probe confirmed an interesting fact for future-me: on the
three reference bikes (which all carry hand-tuned `dyno_curve` objects),
scaling `peak_power_hp` *alone* without scaling `dyno_curve.torque_nm`
leaves ET unchanged. That's the exact failure mode of the April 24
power_boost_pct bug — the headline scalar is a dead knob whenever the
curve is populated. The new `test_more_power_means_faster_et` scales
both together, so it pins the *combined* invariant. If a future change
silently demotes one path, this test will fail loud.

## Open follow-ups for next daily run

(Carry-forward from previous CLAUDE.md sessions; not addressed today.)

1. Wheelie-bar sub-500cc gap (Apache RR 310 / Duke 390 / RE 650 class)
   needs partnership data from Pune/Narhe drag shops.
2. `tests/test_catalog_integration::test_rsv4_no_panigale_leak` —
   pre-existing failure, Termignoni full-system labelled
   "Kawasaki ZX-10R" trips the test's brand-only ban on RSV4. Tighten
   the test, or move that part's manufacturer constraint to a stricter
   tier.
3. Parts #469 + #472 have invalid `tier: model` fitment_rules left
   over from a missed normalize migration.
4. INR pricing on the 7 drag-prep specialty parts seeded April 30 still
   needs a real distributor confirmation pass (currently formula-priced).
5. May 1 pricing-refresh deferred 8 parts (Schnitz/DME/Brock's
   swingarms, EK 428 + RK 530 PRODR, Dynojet PCVI Stage 1, Akrapovic
   Panigale full system) — direct-vendor query needed.

## Suggestion for next Saturday

Consider adding `pytest-regressions` snapshots for the 334-bike sweep —
formalises the implicit baseline contract per CLAUDE.md
"Adopt this quarter" toolkit shortlist (highest ROI item). Current
pyproject.toml has `addopts = "-q"`; pinning every-bike ET to 4 decimals
in a versioned data_regression file would give CI a hard contract that
fails on any silent drift.
