"""
MotoQuant Pro — Physics Monotonicity Invariants (Property-Based)
================================================================
Hypothesis-driven property tests that pin the four most load-bearing
physical invariants of the simulation:

    1. mass increases       => ET increases  (more mass is slower)
    2. peak power increases => ET decreases  (more power is faster)
    3. drag coefficient up  => ET increases  (more drag is slower)
    4. frontal area up      => ET increases  (more drag is slower)

These are the kind of regressions that historically slipped past the
project's snapshot tests:
  - April 24 2026 the `power_boost_pct` knob was silently dead on
    the DB-seeded simulate path (R15 V3 ET unchanged 0..50% boost) —
    a classic monotonicity violation that property-based testing
    would have caught immediately.
  - April 22 2026 a stale fluid_mass_kg / basket_inertia carried
    K5 defaults onto every R15-class spec, masking the mass invariant
    on small-cc bikes.

Property testing complements pytest-regressions snapshots: snapshots
catch *exact-value* drift, but only on the cases recorded; property
tests catch *direction* drift across the entire input space.

Each test runs across all three reference platforms (K5, R1, Hayabusa
Gen1) so it exercises three distinct cluster code paths
(litre_sport_195p, litre_sport_600_1000, and the 1300+ Hayabusa
class via category-flavoured physics dispatch).

The tests are gated on Hypothesis being installed; they silently skip
otherwise so the rest of the fast test suite stays green on a vanilla
`pip install -r requirements-api.txt` checkout.

Tolerance: a 1 ms tolerance is applied on the ET comparison to absorb
adaptive-solver / timestep noise (the fixed-step RK4 at 1 ms
default has bit-stable output, but we keep the buffer so future
adaptive-dt mode toggles don't flake the suite).
"""

from __future__ import annotations

import pytest

# Gate the whole module on Hypothesis. Skips gracefully on any checkout
# that hasn't installed the dev dependency yet.
hypothesis = pytest.importorskip("hypothesis")
from hypothesis import (  # noqa: E402
    HealthCheck,
    assume,
    given,
    settings,
    strategies as st,  # noqa: E402
)

from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8  # noqa: E402
from motoquant.physics import QUARTER_MILE_M, MotoQuantEngine  # noqa: E402

# ---------------------------------------------------------------------------
# Test budget
# ---------------------------------------------------------------------------
# Each call to _run_et below executes a full 15s-cap RK4 simulation at
# dt=1ms — about 0.5s of wall-time on the CI runner. Keep example counts
# low so the property suite finishes inside the focused-test budget.
# `deadline=None` because per-example variance in solver time can spike
# above Hypothesis' 200ms default deadline on shared CI hardware.
_PROPERTY_SETTINGS = settings(
    max_examples=8,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)

# Reference bike factories. Each is hand-curated in defaults.py and
# protected from `reseed_configs_from_specs.py` so these stay stable
# across importer changes.
REF_BIKES = [gsxr1000_k5, yzfr1_4c8, hayabusa_gen1]
REF_BIKE_NAMES = {
    gsxr1000_k5: "K5",
    yzfr1_4c8: "R1",
    hayabusa_gen1: "Hayabusa",
}

# 1ms tolerance on ET ordering — well above any solver-noise floor.
ET_TOLERANCE_S = 1e-3


def _run_et(cfg) -> float:
    """Run a quarter-mile sim and return ET in seconds.

    Uses fixed-step RK4 at dt=1ms with the same settings as the
    K5/R1/Hayabusa baseline pin in test_validation.py, so any
    monotonicity violation here implies a real physics regression
    (not a solver-config drift).
    """
    return (
        MotoQuantEngine(cfg, dt=0.001)
        .run(distance=QUARTER_MILE_M, max_time=15.0)
        .time_quarter
    )


# ---------------------------------------------------------------------------
# Invariant 1 — more mass => slower ET
# ---------------------------------------------------------------------------
@given(
    bike_factory=st.sampled_from(REF_BIKES),
    mass_low=st.floats(min_value=150.0, max_value=200.0),
    mass_high=st.floats(min_value=240.0, max_value=320.0),
)
@_PROPERTY_SETTINGS
def test_more_mass_means_slower_et(bike_factory, mass_low, mass_high):
    """Adding chassis mass must monotonically increase ET.

    Spread is forced ≥30 kg so the predicted ET delta (≈5 ms/kg on the
    K5 class) dwarfs the 1 ms tolerance even after solver noise.
    """
    assume(mass_high - mass_low >= 30.0)

    cfg_low = bike_factory()
    cfg_low.chassis.dry_mass_kg = mass_low
    et_low = _run_et(cfg_low)

    cfg_high = bike_factory()
    cfg_high.chassis.dry_mass_kg = mass_high
    et_high = _run_et(cfg_high)

    assert et_high >= et_low - ET_TOLERANCE_S, (
        f"{REF_BIKE_NAMES[bike_factory]}: mass "
        f"{mass_low:.1f}->{mass_high:.1f} kg gave ET "
        f"{et_low:.4f}s -> {et_high:.4f}s "
        f"(expected non-decreasing)"
    )


# ---------------------------------------------------------------------------
# Invariant 2 — more peak power => faster ET
# ---------------------------------------------------------------------------
@given(
    bike_factory=st.sampled_from(REF_BIKES),
    power_scale_low=st.floats(min_value=0.80, max_value=0.95),
    power_scale_high=st.floats(min_value=1.05, max_value=1.20),
)
@_PROPERTY_SETTINGS
def test_more_power_means_faster_et(bike_factory, power_scale_low, power_scale_high):
    """Scaling the dyno torque curve up must monotonically decrease ET.

    Both the scalar peak_power_hp / peak_torque_nm headline values AND
    the dyno_curve.torque_nm array are scaled together — this is the
    invariant that the April 24 power_boost_pct dead-knob bug
    violated (one path scaled, the other did not).

    Spread forced ≥0.10 (10 percentage points) so the ET delta is
    clearly larger than ET_TOLERANCE_S.
    """
    assume(power_scale_high - power_scale_low >= 0.10)

    def _scale(cfg, factor):
        cfg.engine.peak_power_hp = cfg.engine.peak_power_hp * factor
        cfg.engine.peak_torque_nm = cfg.engine.peak_torque_nm * factor
        if cfg.engine.dyno_curve is not None:
            cfg.engine.dyno_curve.torque_nm = cfg.engine.dyno_curve.torque_nm * factor
        return cfg

    cfg_low = _scale(bike_factory(), power_scale_low)
    cfg_high = _scale(bike_factory(), power_scale_high)

    et_low = _run_et(cfg_low)
    et_high = _run_et(cfg_high)

    assert et_high <= et_low + ET_TOLERANCE_S, (
        f"{REF_BIKE_NAMES[bike_factory]}: power scale "
        f"{power_scale_low:.3f}->{power_scale_high:.3f} gave ET "
        f"{et_low:.4f}s -> {et_high:.4f}s "
        f"(expected non-increasing)"
    )


# ---------------------------------------------------------------------------
# Invariant 3 — higher drag coefficient => slower ET
# ---------------------------------------------------------------------------
@given(
    bike_factory=st.sampled_from(REF_BIKES),
    cd_low=st.floats(min_value=0.55, max_value=0.65),
    cd_high=st.floats(min_value=0.75, max_value=0.95),
)
@_PROPERTY_SETTINGS
def test_higher_cd_means_slower_et(bike_factory, cd_low, cd_high):
    """Increasing aero.cd must monotonically increase ET.

    Cd range tracks realistic motorcycle Cd_d values (0.55 race tuck
    through 0.95 fully upright cruiser); ≥0.10 spread keeps the
    ET delta dominant over the tolerance.
    """
    assume(cd_high - cd_low >= 0.10)

    cfg_low = bike_factory()
    cfg_low.aero.cd = cd_low
    et_low = _run_et(cfg_low)

    cfg_high = bike_factory()
    cfg_high.aero.cd = cd_high
    et_high = _run_et(cfg_high)

    assert et_high >= et_low - ET_TOLERANCE_S, (
        f"{REF_BIKE_NAMES[bike_factory]}: cd "
        f"{cd_low:.3f}->{cd_high:.3f} gave ET "
        f"{et_low:.4f}s -> {et_high:.4f}s "
        f"(expected non-decreasing)"
    )


# ---------------------------------------------------------------------------
# Invariant 4 — larger frontal area => slower ET
# ---------------------------------------------------------------------------
@given(
    bike_factory=st.sampled_from(REF_BIKES),
    fa_low=st.floats(min_value=0.35, max_value=0.42),
    fa_high=st.floats(min_value=0.50, max_value=0.65),
)
@_PROPERTY_SETTINGS
def test_larger_frontal_area_means_slower_et(bike_factory, fa_low, fa_high):
    """Increasing aero.frontal_area_m2 must monotonically increase ET.

    Range tracks realistic supersport tuck (0.35 m^2) through upright
    naked / cruiser (0.65 m^2). ≥0.07 m^2 spread keeps the ET delta
    well above tolerance.
    """
    assume(fa_high - fa_low >= 0.07)

    cfg_low = bike_factory()
    cfg_low.aero.frontal_area_m2 = fa_low
    et_low = _run_et(cfg_low)

    cfg_high = bike_factory()
    cfg_high.aero.frontal_area_m2 = fa_high
    et_high = _run_et(cfg_high)

    assert et_high >= et_low - ET_TOLERANCE_S, (
        f"{REF_BIKE_NAMES[bike_factory]}: frontal_area "
        f"{fa_low:.3f}->{fa_high:.3f} m^2 gave ET "
        f"{et_low:.4f}s -> {et_high:.4f}s "
        f"(expected non-decreasing)"
    )


# ---------------------------------------------------------------------------
# Invariant 5 — reference baselines remain pinned during the property run
# ---------------------------------------------------------------------------
# The four property tests above each clone bike_factory() before mutating,
# so the canonical defaults objects must NOT be mutated in-place. This
# explicit baseline pin guards against an accidental shared-mutation
# regression — if any of the property tests above ever stops cloning,
# this will fail loud.
@pytest.mark.parametrize(
    ("factory", "target"),
    [
        (gsxr1000_k5, 9.9331),
        (yzfr1_4c8, 10.1436),
        (hayabusa_gen1, 10.3633),
    ],
)
def test_reference_baselines_pinned_after_property_runs(factory, target):
    """K5/R1/Hayabusa ETs must still match the pinned baselines after
    the property tests have mutated copies of these configs. Catches
    accidental shared-mutation regressions (deepcopy gone wrong, or a
    factory returning a cached singleton)."""
    et = _run_et(factory())
    assert abs(et - target) < ET_TOLERANCE_S, (
        f"reference baseline drift: {factory.__name__} "
        f"ET {et:.4f}s vs target {target:.4f}s "
        f"(delta {et - target:+.4f}s)"
    )
