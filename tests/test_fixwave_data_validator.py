"""
tests/test_fixwave_data_validator.py
====================================
October 2026 core-audit fix wave — ``scraper.validator.validate_spec``.

Pinned findings (reports/audit_core_2026_10_23_partial.md):
  * Physically impossible power/torque pairs passed with one soft warning,
    and HP_PER_CC_MAX = 3.0 hp/cc let a 599 cc / 450 hp typo through clean.
  * validate_spec() wrote generic I4 gear ratios and a car-like Cd 0.32 into
    the spec, bypassing the importer's Tier-1 service-manual lookup — the
    import path and the reseed path (which never validates) diverged.
  * The 'unit correction' converted in the wrong direction (hp -> kW for a
    too-high hp; 450 Nm -> 610 Nm) and accepted the out-of-bounds result.

The import tests drive ``importer.import_spec`` (what ``import --spec-json``,
``import --known-bikes`` and the chat estimator use) end to end.
"""

from __future__ import annotations

import copy
import logging

import pytest

from motoquant.database.bridge import db_row_to_config
from motoquant.database.connection import MotoQuantDB
from motoquant.scraper.importer import import_spec, spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES
from motoquant.scraper.validator import INCONSISTENT_TAG, score_spec, validate_spec


def _find(manufacturer, model_prefix):
    return next(
        s
        for s in ALL_KNOWN_BIKES
        if s.manufacturer == manufacturer and s.model_name.startswith(model_prefix)
    )


@pytest.fixture
def mdb():
    d = MotoQuantDB(":memory:")
    d.initialize()
    yield d
    d.close()


class TestNoSpecMutation:
    def test_validate_never_writes_defaults_into_the_spec(self):
        spec = copy.deepcopy(_find("Yamaha", "YZF-R15 V4"))
        spec.gear_ratios = None
        spec.cd = None
        spec.frontal_area_m2 = None
        snapshot = copy.deepcopy(spec.__dict__)
        result = validate_spec(spec)
        assert spec.__dict__ == snapshot
        assert {"cd", "frontal_area_m2", "gear_ratios"} <= set(result.defaulted_fields)
        assert result.corrected_fields == {}

    def test_import_path_equals_reseed_path_for_a_spec_without_ratios(self, mdb):
        """import_spec validates then converts; the reseed path converts
        without validating. They used to diverge (generic 6-speed I4 ratios +
        Cd 0.32 instead of the R15's service-manual cassette and category
        aero: 120.6 vs 144.9 km/h top speed)."""
        logging.disable(logging.CRITICAL)
        try:
            spec = copy.deepcopy(_find("Yamaha", "YZF-R15 V4"))
            spec.gear_ratios = None
            spec.cd = None
            reseed_cfg = spec_to_bike_config(copy.deepcopy(spec))
            _model_id, config_id = import_spec(mdb, spec)
            imported = db_row_to_config(mdb.bikes.get_config(config_id))
        finally:
            logging.disable(logging.NOTSET)
        assert imported.drivetrain.gear_ratios == reseed_cfg.drivetrain.gear_ratios
        assert imported.drivetrain.gear_ratios != [2.6, 2.105, 1.75, 1.5, 1.333, 1.2]
        assert imported.aero.cd == reseed_cfg.aero.cd
        assert imported.aero.cd != pytest.approx(0.32)


class TestPowerTorqueConsistency:
    @staticmethod
    def _old_r9():
        """The R9 as it was curated before the 2026-10 epoch fixed it: 93 Nm
        at 11500 rpm implies ~150 hp against the 117 hp rating."""
        spec = copy.deepcopy(_find("Yamaha", "YZF-R9"))
        spec.peak_power_rpm, spec.peak_torque_rpm = 12500, 11500
        return spec

    def test_r9_class_inconsistency_is_flagged_and_costs_confidence(self):
        spec = self._old_r9()
        result = validate_spec(spec)
        assert result.is_valid  # curated spec: confidence-gated, not rejected
        assert any(w.startswith(INCONSISTENT_TAG) for w in result.warnings)
        fixed = copy.deepcopy(_find("Yamaha", "YZF-R9"))  # real R9: 10000/7000
        assert (fixed.peak_power_rpm, fixed.peak_torque_rpm) == (10000, 7000)
        fixed_result = validate_spec(fixed)
        assert not any(w.startswith(INCONSISTENT_TAG) for w in fixed_result.warnings)
        assert score_spec(spec, result) < score_spec(fixed, fixed_result) - 0.05

    def test_gross_inconsistency_is_an_error(self):
        spec = self._old_r9()
        spec.peak_torque_nm = 160.0  # 160 Nm @ 11500 = 258 hp vs 117 hp rated
        result = validate_spec(spec)
        assert not result.is_valid
        assert any(INCONSISTENT_TAG in e for e in result.errors)

    def test_torque_peak_above_power_peak_is_an_error_for_a_4t(self):
        spec = copy.deepcopy(_find("Yamaha", "YZF-R9"))
        spec.peak_torque_rpm, spec.peak_power_rpm = 11000, 10000
        spec.peak_torque_nm = 70.0
        result = validate_spec(spec)
        assert not result.is_valid
        assert any("peak_torque_rpm" in e for e in result.errors)

    def test_599cc_450hp_typo_is_rejected(self):
        spec = copy.deepcopy(_find("Yamaha", "YZF-R9"))
        spec.displacement_cc, spec.peak_power_hp, spec.peak_torque_nm = (
            599.0,
            450.0,
            230.0,
        )
        spec.bore_mm = spec.stroke_mm = None
        result = validate_spec(spec)
        assert not result.is_valid
        assert any("HP/cc" in e for e in result.errors)

    def test_every_curated_spec_still_validates(self):
        """No curated catalog spec may be newly rejected (import would skip it)."""
        invalid = []
        for spec in ALL_KNOWN_BIKES:
            result = validate_spec(copy.deepcopy(spec))
            if not result.is_valid:
                invalid.append((spec.manufacturer, spec.model_name, result.errors))
        assert invalid == []


class TestUnitCorrectionDirection:
    def test_too_high_power_is_rejected_unconverted(self):
        spec = copy.deepcopy(_find("Yamaha", "YZF-R9"))
        spec.peak_power_hp = 600.0
        result = validate_spec(spec)
        assert not result.is_valid
        assert spec.peak_power_hp == 600.0

    def test_too_high_torque_is_rejected_not_inflated(self):
        spec = copy.deepcopy(_find("Yamaha", "YZF-R9"))
        spec.peak_torque_nm = 450.0
        result = validate_spec(spec)
        assert not result.is_valid
        assert spec.peak_torque_nm == 450.0

    def test_low_torque_in_ft_lb_converts_up_into_bounds(self):
        spec = copy.deepcopy(_find("Yamaha", "YZF-R9"))
        spec.peak_torque_nm = 4.0  # below the 5 Nm floor; 4 ft-lb = 5.4 Nm
        result = validate_spec(spec)
        assert spec.peak_torque_nm == pytest.approx(4.0 * 1.356)
        assert "peak_torque_nm" in result.corrected_fields
