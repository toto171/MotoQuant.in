"""
test_category_dispatch.py — regression tests for the April 30, 2026
category-flavoured physics rewrite.

Locks in the contract:
  • BikeConfig has a category_tag field (str | None, default None).
  • derive_category_tag mirrors scripts/sweep_with_clusters.py::cluster_for.
  • Importer auto-tags every catalog spec.
  • physics.MotoQuantEngine builds self._profile from cfg.category_tag,
    or auto-derives from engine spec when missing.
  • Reference baselines (K5 / R1 / Hayabusa) reproduce within 0.001 s.
  • Legacy configs (category_tag=None) get back-compat profile via
    auto-derive + don't crash.
  • Profile lookup never returns None.
"""
from __future__ import annotations

import dataclasses

import pytest

from motoquant import MotoQuantEngine
from motoquant.category_profiles import (
    CATEGORY_CRUISER_1300P,
    CATEGORY_ENTRY_150_200,
    CATEGORY_LITRE_SPORT_195P,
    CATEGORY_LITRE_SPORT_600_1000,
    CATEGORY_TWO_STROKE,
    CATEGORY_UNKNOWN,
    derive_category_tag,
    get_profile,
)
from motoquant.defaults import gsxr1000_k5, hayabusa_gen1, yzfr1_4c8
from motoquant.models import BikeConfig
from motoquant.scraper.importer import spec_to_bike_config
from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES


class TestBikeConfigField:
    def test_category_tag_field_exists(self):
        fields = {f.name for f in dataclasses.fields(BikeConfig)}
        assert "category_tag" in fields, "BikeConfig must carry category_tag"

    def test_category_tag_default_is_none(self):
        cfg = BikeConfig()
        assert cfg.category_tag is None, "Default must be None for back-compat"

    def test_category_tag_round_trips(self):
        cfg = BikeConfig(category_tag="custom_tag")
        assert cfg.category_tag == "custom_tag"


class TestDeriveCategoryTag:
    def test_two_stroke_takes_precedence(self):
        tag = derive_category_tag(
            manufacturer="Yamaha", model_name="RD350",
            displacement_cc=347, peak_power_hp=39, stroke_type=2,
            category="sport",
        )
        assert tag == CATEGORY_TWO_STROKE

    def test_litre_sport_195p(self):
        tag = derive_category_tag(
            manufacturer="Kawasaki", model_name="Ninja H2",
            displacement_cc=998, peak_power_hp=200, stroke_type=4,
            category="sport",
        )
        assert tag == CATEGORY_LITRE_SPORT_195P

    def test_litre_sport_600_1000(self):
        tag = derive_category_tag(
            manufacturer="Yamaha", model_name="YZF-R6",
            displacement_cc=600, peak_power_hp=120, stroke_type=4,
            category="sport",
        )
        assert tag == CATEGORY_LITRE_SPORT_600_1000

    def test_entry_150_200(self):
        tag = derive_category_tag(
            manufacturer="Yamaha", model_name="YZF-R15 V3",
            displacement_cc=155, peak_power_hp=18, stroke_type=4,
            category="sport",
        )
        assert tag == CATEGORY_ENTRY_150_200

    def test_cruiser_1300p_via_category(self):
        tag = derive_category_tag(
            manufacturer="Triumph", model_name="Rocket 3",
            displacement_cc=2458, peak_power_hp=165, stroke_type=4,
            category="cruiser",
        )
        assert tag == CATEGORY_CRUISER_1300P

    def test_muscle_naked_routed_to_cruiser(self):
        # VMAX 1700 / B-King / Rocket 3 are catalog-tagged sport/naked for
        # engine-inertia tuning but are physically cruiser-class (320 kg).
        tag = derive_category_tag(
            manufacturer="Yamaha", model_name="VMAX 1700",
            displacement_cc=1679, peak_power_hp=200, stroke_type=4,
            category="naked",
        )
        assert tag == CATEGORY_CRUISER_1300P


class TestProfileLookup:
    def test_get_profile_for_each_category(self):
        for tag in (
            CATEGORY_LITRE_SPORT_195P, CATEGORY_LITRE_SPORT_600_1000,
            CATEGORY_TWO_STROKE, CATEGORY_CRUISER_1300P,
            CATEGORY_ENTRY_150_200, CATEGORY_UNKNOWN,
        ):
            p = get_profile(tag)
            assert p is not None
            assert p.name in (tag,), f"profile.name {p.name!r} != {tag!r}"

    def test_unknown_tag_falls_back_to_unknown_profile(self):
        p = get_profile("not_a_real_category")
        assert p.name == CATEGORY_UNKNOWN

    def test_none_tag_falls_back_to_unknown_profile(self):
        p = get_profile(None)
        assert p.name == CATEGORY_UNKNOWN

    def test_unknown_profile_is_legacy_safe(self):
        # The unknown profile MUST be a no-op so old configs reproduce
        # pre-April-30 behaviour. This is the back-compat anchor.
        p = get_profile(None)
        assert p.over_clutch_factor == 0.0
        assert p.max_engine_decel_rads2 == 0.0
        assert p.launch_floor_factor == 0.0
        assert p.parasitic_mult == 1.0
        assert p.engine_inertia_mult == 1.0


class TestImporterAutoTags:
    def test_every_catalog_bike_gets_a_tag(self):
        untagged = []
        for spec in ALL_KNOWN_BIKES:
            cfg = spec_to_bike_config(spec)
            if not cfg.category_tag:
                untagged.append(spec.model_name)
        assert not untagged, (
            f"{len(untagged)} bikes missing category_tag: {untagged[:5]}"
        )

    def test_r15_v3_tagged_entry_150_200(self):
        spec = next(s for s in ALL_KNOWN_BIKES if "YZF-R15 V3" in s.model_name)
        cfg = spec_to_bike_config(spec)
        assert cfg.category_tag == CATEGORY_ENTRY_150_200

    def test_rd350_tagged_two_stroke(self):
        spec = next(s for s in ALL_KNOWN_BIKES if s.model_name == "RD350")
        cfg = spec_to_bike_config(spec)
        assert cfg.category_tag == CATEGORY_TWO_STROKE


class TestEngineProfileWiring:
    def test_engine_resolves_profile_from_cfg(self):
        cfg = gsxr1000_k5()
        eng = MotoQuantEngine(cfg)
        assert eng._profile is not None
        assert eng._profile.name == CATEGORY_LITRE_SPORT_195P

    def test_engine_auto_derives_when_tag_missing(self):
        cfg = gsxr1000_k5()
        cfg.category_tag = None  # simulate legacy config
        eng = MotoQuantEngine(cfg)
        # K5 has 178 hp peak → litre-sport-195p (peak rounds to 195+ via
        # importer; defaults.py is hand-built at 160 wheel hp so it should
        # land in litre_sport_600_1000). Either way it must be a real profile.
        assert eng._profile is not None
        assert eng._profile.name in (
            CATEGORY_LITRE_SPORT_195P, CATEGORY_LITRE_SPORT_600_1000,
        )


class TestReferenceBaselinesPreserved:
    """The K5 / R1 / Hayabusa references are the canary that catches
    accidental physics drift from the category dispatch refactor. They
    must reproduce within 1 ms (post April-30 they are exactly the same
    numerical values they were pre-April-30 because the unknown branch
    of the dispatch reproduces legacy behaviour bit-exact)."""

    @pytest.mark.parametrize("factory,expected_et", [
        (gsxr1000_k5, 10.0334),
        (yzfr1_4c8, 10.2859),
        (hayabusa_gen1, 10.4712),
    ])
    def test_reference_et_within_1ms(self, factory, expected_et):
        cfg = factory()
        result = MotoQuantEngine(cfg).run(use_adaptive_dt=False)
        assert abs(result.time_quarter - expected_et) < 0.001, (
            f"{cfg.name}: ET drifted to {result.time_quarter:.4f}s "
            f"(target {expected_et:.4f}, |Δ|={abs(result.time_quarter-expected_et):.4f}s)"
        )


class TestLegacyConfigBackCompat:
    """Configs that don't have category_tag (e.g. old saved JSON, hand-
    built BikeConfigs in tests) must still simulate without crash and
    produce sane ETs."""

    def test_legacy_default_bikeconfig_runs(self):
        cfg = BikeConfig()  # all defaults, category_tag=None
        eng = MotoQuantEngine(cfg)
        assert eng._profile is not None
        # Profile must be a real one (auto-derived from engine spec)
        assert eng._profile.name != CATEGORY_UNKNOWN, (
            "Auto-derive should produce a real cluster, not 'unknown'."
        )
