"""Environment power model, supercharger ambient pressure, venue track prep and
run() argument validation (November 2026 physics-lane fixes)."""

import copy
import math

import pytest

from motoquant.database.weather_repo import compute_power_correction
from motoquant.defaults import gsxr1000_k5
from motoquant.models import (
    BOOST_SC_CENTRIFUGAL,
    BOOST_SC_ROOTS,
    BOOST_TURBO,
    TRACK_NONE,
    TRACK_RUBBER,
    TRACK_VHT,
    BikeConfig,
    EnvironmentParams,
)
from motoquant.physics import MotoQuantEngine
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
    cfg.environment = _env(altitude_m=2500.0)
    assert EnvironmentalModel(cfg).power_correction == 0.97


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


# ── 2. Supercharger ambient pressure ─────────────────────────────────────


def _fi_cfg(boost_type, alt):
    cfg = gsxr1000_k5()
    cfg.forced_induction.boost_type = boost_type
    cfg.forced_induction.intercooler_type = "none"
    cfg.environment = _env(altitude_m=alt)
    return cfg


@pytest.mark.parametrize("bt", [BOOST_SC_ROOTS, BOOST_SC_CENTRIFUGAL])
def test_supercharger_ratio_uses_ambient_pressure(bt):
    p_boost = 0.5e5
    ratios = {}
    for alt in (0.0, 679.0):
        cfg = _fi_cfg(bt, alt)
        ratios[alt] = ForcedInductionModel(
            cfg, cfg.environment.air_density()
        ).torque_mult(9000.0, 1.0, p_boost)
    assert ratios[679.0] > ratios[0.0]
    # same ambient reference as the turbo branch (no intercooler)
    cfg = _fi_cfg(BOOST_TURBO, 679.0)
    turbo = ForcedInductionModel(cfg, cfg.environment.air_density()).torque_mult(
        9000.0, 1.0, p_boost
    )
    assert ratios[679.0] == pytest.approx(turbo, rel=1e-12)


# ── 3. Venue-level track prep ────────────────────────────────────────────


@pytest.fixture(scope="module")
def cat_cfg():
    return spec_to_bike_config(ALL_KNOWN_BIKES[100])


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


def test_run_nonpositive_max_time_is_a_clear_error():
    with pytest.raises(ValueError, match="max_time"):
        MotoQuantEngine(gsxr1000_k5()).run(max_time=0.0)
