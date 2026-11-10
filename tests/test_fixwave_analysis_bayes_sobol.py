"""
Bayesian optimizer + Sobol fixes (October 2026 audit).

Bayesian: ``power_delta_hp`` bumped peak_power_hp without the dyno curve the
physics integrates (dead knob: +50 hp gave the base ET while costing ₹40k),
``rear_pressure_delta`` drove a field the physics never reads, and the
negative mass rate times |delta| made every mass change CHEAPER.

Sobol: absolute Cd / frontal-area / rolling-radius windows excluded the
nominal Cd of 36% of catalog bikes, so indices described a different bike.
"""

import sqlite3
from pathlib import Path

import numpy as np
import pytest

from motoquant import engine_select
from motoquant.analysis.bayesian_opt import BayesianBuildOptimizer
from motoquant.analysis.sobol import (
    DEFAULT_PARAM_BOUNDS,
    _apply_sample_row,
    _get_nested,
)
from motoquant.database.bridge import db_row_to_config
from motoquant.defaults import gsxr1000_k5

DB_PATH = Path(__file__).resolve().parents[1] / "motoquant.db"


def _et(cfg):
    return float(engine_select.make_engine(cfg).run().time_quarter)


class TestBayesianKnobs:
    @pytest.fixture(scope="class")
    def opt(self):
        return BayesianBuildOptimizer(gsxr1000_k5(), budget_inr=20_000)

    def _zero(self, opt):
        return dict.fromkeys(opt.PARAM_BOUNDS, 0.0)

    def test_power_delta_moves_the_et(self, opt):
        base = _et(opt._apply_params_to_config(self._zero(opt)))
        more = _et(
            opt._apply_params_to_config({**self._zero(opt), "power_delta_hp": 50})
        )
        assert more < base - 0.1, f"+50 hp is a dead knob ({base} -> {more})"

    def test_pressure_is_not_a_search_dimension(self, opt):
        # physics never reads tires.rear_pressure_psi
        assert "rear_pressure_delta" not in opt.PARAM_BOUNDS
        assert "rear_pressure_delta" not in opt.COST_PER_UNIT

    def test_mass_reduction_costs_and_ballast_is_free(self, opt):
        z = self._zero(opt)
        assert opt._estimate_cost({**z, "mass_delta_kg": -15}) == pytest.approx(22_500)
        assert opt._estimate_cost({**z, "mass_delta_kg": 5}) == 0.0
        # a mass change can never make a power build cheaper
        power_only = opt._estimate_cost({**z, "power_delta_hp": 40})
        power_light = opt._estimate_cost(
            {**z, "power_delta_hp": 40, "mass_delta_kg": -15}
        )
        assert power_only == pytest.approx(32_000)
        assert power_light > power_only


# Catalog bikes whose nominal value the OLD absolute windows excluded
# (Cd 0.55-0.95, area 0.38-0.62 m², rear radius 0.28-0.33 m).
_OUTSIDE_OLD_WINDOW = {
    "aero_cd": "json_extract(aero_params, '$.cd') < 0.45",
    "frontal_area": "(json_extract(aero_params, '$.frontal_area_m2') > 0.62 "
    "OR json_extract(aero_params, '$.frontal_area_m2') < 0.38)",
    "rolling_radius": "(json_extract(tire_params, '$.rear_rolling_radius_m') < 0.28 "
    "OR json_extract(tire_params, '$.rear_rolling_radius_m') > 0.33)",
}


def _catalog_config(where: str):
    if not DB_PATH.exists():
        pytest.skip("catalog DB not present")
    c = sqlite3.connect(f"file:{DB_PATH}?mode=ro&immutable=1", uri=True)
    c.row_factory = sqlite3.Row
    row = c.execute(
        f"SELECT * FROM bike_configs WHERE is_current=1 AND {where} LIMIT 1"
    ).fetchone()
    c.close()
    if row is None:
        pytest.skip("no matching catalog bike")
    return db_row_to_config(dict(row), name="catalog bike")


def _catalog_low_cd_config():
    return _catalog_config(_OUTSIDE_OLD_WINDOW["aero_cd"])


class TestSobolBoundsAroundTheBike:
    @pytest.mark.parametrize("key", ["aero_cd", "frontal_area", "rolling_radius"])
    def test_sample_range_brackets_the_nominal_value(self, key):
        cfg = _catalog_config(_OUTSIDE_OLD_WINDOW[key])
        spec = DEFAULT_PARAM_BOUNDS[key]
        nominal = float(_get_nested(cfg, spec.path))
        lo_cfg = _apply_sample_row(cfg, [spec], [nominal], np.array([spec.low]))
        hi_cfg = _apply_sample_row(cfg, [spec], [nominal], np.array([spec.high]))
        lo = float(_get_nested(lo_cfg, spec.path))
        hi = float(_get_nested(hi_cfg, spec.path))
        assert lo < nominal < hi, f"{key}: [{lo}, {hi}] excludes nominal {nominal}"

    def test_low_cd_bike_cd_samples_stay_near_it(self):
        cfg = _catalog_low_cd_config()
        spec = DEFAULT_PARAM_BOUNDS["aero_cd"]
        nominal = cfg.aero.cd
        hi_cfg = _apply_sample_row(cfg, [spec], [nominal], np.array([spec.high]))
        assert hi_cfg.aero.cd <= nominal * 1.2
