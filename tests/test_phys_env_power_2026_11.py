"""Environment power model, venue track prep and run() argument validation
(November 2026 physics-lane fixes, ported onto the Rust-core / rollout-timing
backend).

Port notes
----------
* The boosted density floor now applies only to a turbo / supercharger with a
  positive boost target (``boost_compensates_density``), so the floor test
  sets a target and a zero-boost twin pins the plain correction.
* The supercharger boost ratio deliberately still divides by standard
  pressure: see ``test_supercharger_ratio_is_venue_independent``.
* ``run()`` argument validation keeps the rollout rule (a finish line at or
  inside the 1-ft rollout is invalid) and adds the redesign branch's
  ceilings; the Rust core raises the same ValueError with the same message
  (tests/test_native_engine.py pins that side).
"""

import copy
import math

import pytest

from motoquant.database.weather_repo import compute_power_correction
from motoquant.defaults import gsxr1000_k5
from motoquant.models import (
    BOOST_N2O,
    BOOST_SC_CENTRIFUGAL,
    BOOST_SC_ROOTS,
    BOOST_TURBO,
    TRACK_NONE,
    TRACK_RUBBER,
    TRACK_VHT,
    BikeConfig,
    EnvironmentParams,
)
from motoquant.physics import MAX_RUN_DISTANCE_M, MAX_RUN_TIME_S, MotoQuantEngine
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from motoquant.submodels.environmental import EnvironmentalModel, sae_power_correction
from motoquant.submodels.forced_induction import ForcedInductionModel


def _env(**kw) -> EnvironmentParams:
    base = {
        "altitude_m": 0.0,
        "ambient_temp_c": 25.0,
        "relative_humidity_pct": 50.0,
        "barometric_pressure_hpa": 1013.25,
    }
    base.update(kw)
    return EnvironmentParams(**base)


def _model_pc(env: EnvironmentParams) -> float:
    cfg = BikeConfig()
    cfg.environment = env
    return EnvironmentalModel(cfg).power_correction


# ── 1. SAE-form power correction ─────────────────────────────────────────


def test_reference_day_factor_is_density_anchor():
    env = _env()
    assert _model_pc(env) == env.air_density() / 1.225  # exact


def test_temperature_exponent_is_one_half():
    """Dry air (RH 0) at fixed pressure: factor ratio = sqrt(T1/T2)."""
    cold = _model_pc(_env(ambient_temp_c=10.0, relative_humidity_pct=0.0))
    hot = _model_pc(_env(ambient_temp_c=40.0, relative_humidity_pct=0.0))
    assert cold / hot == pytest.approx(
        math.sqrt((40 + 273.15) / (10 + 273.15)), rel=1e-12
    )


def test_hot_sea_level_penalty_smaller_than_density_form():
    env = _env(ambient_temp_c=35.0)
    assert _model_pc(env) > env.air_density() / 1.225


@pytest.mark.parametrize("alt", [679.0, 1500.0, 2500.0])
def test_altitude_at_25c_close_to_density_form(alt):
    env = _env(altitude_m=alt)
    new, old = _model_pc(env), env.air_density() / 1.225
    assert abs(new - old) / old < 0.005


def test_boosted_floor_kept():
    cfg = gsxr1000_k5()
    cfg.forced_induction.boost_type = BOOST_TURBO
    cfg.forced_induction.target_boost_bar = 0.6
    cfg.environment = _env(altitude_m=2500.0)
    assert EnvironmentalModel(cfg).power_correction == 0.97


@pytest.mark.parametrize("bt", [BOOST_TURBO, BOOST_N2O])
def test_boost_that_compensates_nothing_takes_the_sae_correction(bt):
    """A 0-bar turbo and nitrous get the plain NA factor, in its SAE form."""
    cfg = gsxr1000_k5()
    cfg.forced_induction.boost_type = bt
    cfg.forced_induction.target_boost_bar = 0.0
    cfg.environment = _env(altitude_m=2500.0, ambient_temp_c=35.0)
    got = EnvironmentalModel(cfg).power_correction
    assert got == sae_power_correction(cfg.environment)
    assert got < 0.97


def test_cold_day_gain_smaller_than_density_form():
    env = _env(ambient_temp_c=5.0)
    assert _model_pc(env) < env.air_density() / 1.225
    assert _model_pc(env) > _model_pc(_env())


def test_humidity_lowers_power_through_dry_air_pressure():
    dry = _env(relative_humidity_pct=0.0)
    wet = _env(relative_humidity_pct=100.0)
    assert _model_pc(dry) > _model_pc(_env()) > _model_pc(wet)
    # exactly the dry-air pressure ratio at equal temperature
    assert _model_pc(wet) / _model_pc(dry) == pytest.approx(
        wet.dry_air_pressure_pa() / dry.dry_air_pressure_pa(), rel=1e-12
    )


def test_reference_bikes_run_on_the_anchor_day():
    """The three pinned references sit exactly on the anchor day, which is why
    the SAE form cannot move the pins."""
    from motoquant.defaults import hayabusa_gen1, yzfr1_4c8

    for fn in (gsxr1000_k5, yzfr1_4c8, hayabusa_gen1):
        env = fn().environment
        assert EnvironmentalModel(fn()).power_correction == env.air_density() / 1.225


@pytest.mark.parametrize(
    "temp,pres,rh,alt",
    [
        (15.0, 1013.25, 0.0, 0.0),
        (30.0, 1006.0, 70.0, 679.0),
        (38.0, 950.0, 20.0, 1200.0),
    ],
)
def test_weather_power_correction_matches_sim_model(temp, pres, rh, alt):
    """The weather/venue 'power correction factor' is the factor the sim applies."""
    env = _env(
        ambient_temp_c=temp,
        barometric_pressure_hpa=pres,
        relative_humidity_pct=rh,
        altitude_m=alt,
    )
    assert compute_power_correction(temp, pres, rh, alt) == sae_power_correction(env)
    assert compute_power_correction(temp, pres, rh, alt) == _model_pc(env)


# ── 2. Supercharger boost ratio (kept venue-independent) ─────────────────


def _fi_cfg(boost_type, alt):
    cfg = gsxr1000_k5()
    cfg.forced_induction.boost_type = boost_type
    cfg.forced_induction.intercooler_type = "none"
    cfg.environment = _env(altitude_m=alt)
    return cfg


@pytest.mark.parametrize("bt", [BOOST_SC_ROOTS, BOOST_SC_CENTRIFUGAL])
def test_supercharger_ratio_is_venue_independent(bt):
    """Port decision (2026-11): NOT switched to the venue's ambient pressure.

    A supercharger is a fixed pressure-RATIO device; ``target_boost_bar`` is
    its sea-level rating and the model holds that gauge boost at every venue.
    Dividing it by a thinner venue pressure would make the torque multiplier
    GROW with altitude (while the base correction is floored at 0.97), i.e. a
    supercharged bike would get quicker the higher the strip. Standard
    pressure in the denominator keeps the ratio the compressor's own.
    """
    p_boost = 0.5e5
    ratios = []
    for alt in (0.0, 679.0, 2500.0):
        cfg = _fi_cfg(bt, alt)
        ratios.append(
            ForcedInductionModel(cfg, cfg.environment.air_density()).torque_mult(
                9000.0, 1.0, p_boost
            )
        )
    assert ratios[0] == ratios[1] == ratios[2] == 1.0 + p_boost / 101325.0
    # A wastegated turbo holds gauge boost, so ITS ratio does rise with altitude.
    turbo = []
    for alt in (0.0, 2500.0):
        cfg = _fi_cfg(BOOST_TURBO, alt)
        turbo.append(
            ForcedInductionModel(cfg, cfg.environment.air_density()).torque_mult(
                9000.0, 1.0, p_boost
            )
        )
    assert turbo[1] > turbo[0]


# ── 3. Venue-level track prep ────────────────────────────────────────────


def _v_rod_muscle():
    """The catalog bike these tests were written against (crank-referenced
    curve, no cluster grip override). Looked up by name: a list index moves
    whenever a bike is added or removed, and on 2026-11-10 index 100 silently
    became a different motorcycle."""
    return next(
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == "Harley-Davidson" and s.model_name == "V-Rod Muscle"
    )


@pytest.fixture(scope="module")
def cat_cfg():
    return spec_to_bike_config(_v_rod_muscle())


def _et(cfg):
    return MotoQuantEngine(cfg).run().time_quarter


def test_environment_track_prep_is_live(cat_cfg):
    assert cat_cfg.tires.track_prep_type == TRACK_NONE
    base = _et(cat_cfg)
    cfg = copy.deepcopy(cat_cfg)
    cfg.environment.track_prep = TRACK_VHT
    assert _et(cfg) < base
    cfg.environment.track_prep = TRACK_NONE
    assert repr(_et(cfg)) == repr(base)


def test_tyre_level_prep_wins_over_environment(cat_cfg):
    a = copy.deepcopy(cat_cfg)
    a.tires.track_prep_type = TRACK_VHT
    b = copy.deepcopy(a)
    b.environment.track_prep = TRACK_RUBBER
    assert repr(_et(a)) == repr(_et(b))


def test_prep_multiplier_uses_venue_fallback():
    t = copy.deepcopy(BikeConfig().tires)
    assert t.track_prep_multiplier(30.0) == 1.0
    assert t.track_prep_multiplier(30.0, TRACK_VHT, 0) == pytest.approx(1.12)
    t.track_prep_type = TRACK_RUBBER
    assert t.track_prep_multiplier(30.0, TRACK_VHT, 0) == pytest.approx(1.10)


# ── 4. run() argument validation ─────────────────────────────────────────


@pytest.mark.parametrize("dist", [0.0, -5.0])
def test_run_nonpositive_distance_is_a_clear_error(dist):
    with pytest.raises(ValueError, match="distance"):
        MotoQuantEngine(gsxr1000_k5()).run(distance=dist)


@pytest.mark.parametrize(
    "dist", [0.3048, 0.2, float("nan"), float("inf"), 1e12, MAX_RUN_DISTANCE_M * 2]
)
def test_run_bad_distance_is_a_clear_error(dist):
    """At/inside the 1-ft rollout, NaN, infinite or absurd: ValueError."""
    with pytest.raises(ValueError, match="distance"):
        MotoQuantEngine(gsxr1000_k5()).run(distance=dist)


@pytest.mark.parametrize(
    "max_time",
    [0.0, -1.0, -0.0015, float("nan"), float("inf"), 1e9, MAX_RUN_TIME_S * 2],
)
def test_run_bad_max_time_is_a_clear_error(max_time):
    """Not an empty 0.0-s 'run' (0 / negative), an OverflowError (inf) or a
    MemoryError from sizing the output arrays (huge): a ValueError, raised
    before anything is allocated."""
    with pytest.raises(ValueError, match="max_time"):
        MotoQuantEngine(gsxr1000_k5()).run(max_time=max_time)


def test_run_validation_reaches_top_speed_and_distance_modes():
    eng = MotoQuantEngine(gsxr1000_k5())
    with pytest.raises(ValueError, match="max_time"):
        eng.run_top_speed(max_time=float("inf"))
    with pytest.raises(ValueError, match="distance"):
        eng.run_distance(1e12)


def test_run_accepts_the_ceilings_and_leaves_a_valid_run_unchanged():
    eng = MotoQuantEngine(gsxr1000_k5())
    r = eng.run(distance=MAX_RUN_DISTANCE_M, max_time=0.5)
    assert len(r.t) > 100 and not r.finished_quarter
    # validation is argument-only: the pinned K5 reference is untouched
    assert repr(float(eng.run().time_quarter)) == "10.043600805570911"
