"""
MotoQuant Pro — Parts Compatibility Tests
=========================================
Unit tests for the fitment rules engine (no DB required).
"""

import json

import pytest

from motoquant.parts.compatibility import (
    FitmentMatch,
    FitmentRules,
    FitmentTier,
    is_compatible,
)

# ═══════════════════════════════════════════════════════════
# FitmentMatch tests
# ═══════════════════════════════════════════════════════════


class TestFitmentMatch:
    def test_to_dict_all_fields(self):
        match = FitmentMatch(
            manufacturers=["Suzuki", "Honda"],
            engine_configs=["I4"],
            displacement_min_cc=600,
            displacement_max_cc=1000,
            categories=["sport"],
            year_min=2000,
            year_max=2025,
            chain_pitch="525",
        )
        d = match.to_dict()
        assert d["manufacturers"] == ["Suzuki", "Honda"]
        assert d["engine_configs"] == ["I4"]
        assert d["displacement_min_cc"] == 600
        assert d["displacement_max_cc"] == 1000
        assert d["categories"] == ["sport"]
        assert d["year_min"] == 2000
        assert d["year_max"] == 2025
        assert d["chain_pitch"] == "525"

    def test_to_dict_sparse(self):
        match = FitmentMatch(
            displacement_min_cc=600,
            displacement_max_cc=750,
        )
        d = match.to_dict()
        assert d == {
            "displacement_min_cc": 600,
            "displacement_max_cc": 750,
        }

    def test_from_dict(self):
        d = {
            "manufacturers": ["Yamaha"],
            "displacement_min_cc": 300,
            "displacement_max_cc": 500,
        }
        match = FitmentMatch.from_dict(d)
        assert match.manufacturers == ["Yamaha"]
        assert match.displacement_min_cc == 300
        assert match.displacement_max_cc == 500
        assert match.engine_configs == []


# ═══════════════════════════════════════════════════════════
# FitmentRules tests
# ═══════════════════════════════════════════════════════════


class TestFitmentRules:
    def test_exact_tier_to_dict(self):
        rules = FitmentRules(
            tier=FitmentTier.EXACT,
            bike_ids=[1, 2, 3],
            description="Fits Hayabusa only",
        )
        d = rules.to_dict()
        assert d["tier"] == "exact"
        assert d["bike_ids"] == [1, 2, 3]
        assert d["description"] == "Fits Hayabusa only"

    def test_family_tier_to_dict(self):
        rules = FitmentRules(
            tier=FitmentTier.FAMILY,
            match=FitmentMatch(
                engine_configs=["I4"],
                displacement_min_cc=600,
                displacement_max_cc=750,
            ),
            description="Fits 600cc I4s",
        )
        d = rules.to_dict()
        assert d["tier"] == "family"
        assert "match" in d
        assert d["match"]["displacement_min_cc"] == 600

    def test_to_json_and_from_json(self):
        rules = FitmentRules(
            tier=FitmentTier.UNIVERSAL,
            description="Universal fit",
        )
        json_str = rules.to_json()
        parsed = FitmentRules.from_json(json_str)
        assert parsed.tier == FitmentTier.UNIVERSAL
        assert parsed.description == "Universal fit"

    def test_from_dict_invalid_tier(self):
        with pytest.raises(ValueError, match="Invalid tier"):
            FitmentRules.from_dict({"tier": "invalid_tier"})

    def test_from_dict_missing_tier(self):
        with pytest.raises(ValueError, match="Missing 'tier'"):
            FitmentRules.from_dict({})

    def test_from_json_empty_string(self):
        with pytest.raises(ValueError):
            FitmentRules.from_json("")


# ═══════════════════════════════════════════════════════════
# is_compatible() tests
# ═══════════════════════════════════════════════════════════


class TestIsCompatible:
    # ─────────────────────────────────────────
    # UNIVERSAL tier
    # ─────────────────────────────────────────

    def test_universal_tier_always_compatible(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps({"tier": "universal"}),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 999, "category": "sport"}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True
        assert "universal" in reason

    # ─────────────────────────────────────────
    # EXACT tier
    # ─────────────────────────────────────────

    def test_exact_tier_hit(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps({"tier": "exact", "bike_ids": [1, 2, 3]}),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 2}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True
        assert "listed" in reason

    def test_exact_tier_miss(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps({"tier": "exact", "bike_ids": [1, 2, 3]}),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 999}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False
        assert "not listed" in reason

    # ─────────────────────────────────────────
    # EXCLUDED_BIKE_IDS blocklist
    # ─────────────────────────────────────────

    def test_excluded_bike_ids_blocks(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {
                    "tier": "family",
                    "excluded_bike_ids": [5, 6],
                    "match": {
                        "displacement_min_cc": 500,
                        "displacement_max_cc": 1000,
                    },
                }
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {
            "id": 5,
            "displacement_cc": 750,
        }
        compatible, reason = is_compatible(part, bike)
        assert compatible is False
        assert "excluded" in reason

    # ─────────────────────────────────────────
    # FAMILY tier constraint tests
    # ─────────────────────────────────────────

    def test_family_engine_config_hit(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"engine_configs": ["I4", "I2"]}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1, "cylinder_config": "I4"}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

    def test_family_engine_config_miss(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"engine_configs": ["I4"]}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1, "cylinder_config": "V2"}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False
        assert "engine config" in reason

    def test_family_displacement_min_boundary(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"displacement_min_cc": 600}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        # At boundary (inclusive)
        bike = {"id": 1, "displacement_cc": 600}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

        # Below boundary
        bike = {"id": 1, "displacement_cc": 599}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False

    def test_family_displacement_max_boundary(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"displacement_max_cc": 1000}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        # At boundary (inclusive)
        bike = {"id": 1, "displacement_cc": 1000}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

        # Above boundary
        bike = {"id": 1, "displacement_cc": 1001}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False

    def test_family_category_hit(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"categories": ["sport", "naked"]}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1, "category": "naked"}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

    def test_family_category_miss(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"categories": ["cruiser"]}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1, "category": "sport"}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False

    def test_family_year_min_boundary(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"year_min": 2000}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1, "year_from": 2000}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

        bike = {"id": 1, "year_from": 1999}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False

    def test_family_year_max_boundary(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"year_max": 2020}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1, "year_from": 2020}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

        bike = {"id": 1, "year_from": 2021}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False

    def test_family_chain_pitch_case_sensitive(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {"tier": "family", "match": {"chain_pitch": "525"}}
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1, "chain_pitch": "525"}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

        bike = {"id": 1, "chain_pitch": "530"}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False

    def test_family_all_constraints_must_pass(self):
        """If multiple constraints, all must pass."""
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {
                    "tier": "family",
                    "match": {
                        "engine_configs": ["I4"],
                        "displacement_min_cc": 600,
                        "displacement_max_cc": 1000,
                        "categories": ["sport"],
                        "chain_pitch": "525",
                    },
                }
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        # All pass
        bike = {
            "id": 1,
            "cylinder_config": "I4",
            "displacement_cc": 750,
            "category": "sport",
            "chain_pitch": "525",
        }
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

        # One fails (wrong config)
        bike = {
            "id": 1,
            "cylinder_config": "V2",
            "displacement_cc": 750,
            "category": "sport",
            "chain_pitch": "525",
        }
        compatible, reason = is_compatible(part, bike)
        assert compatible is False

    # ─────────────────────────────────────────
    # CATEGORY tier
    # ─────────────────────────────────────────

    def test_category_tier_basic(self):
        part = {
            "id": 1,
            "fitment_rules": json.dumps(
                {
                    "tier": "category",
                    "match": {
                        "categories": ["cruiser"],
                        "displacement_min_cc": 300,
                    },
                }
            ),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1, "category": "cruiser", "displacement_cc": 500}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True

    # ─────────────────────────────────────────
    # LEGACY fallback: fitment_rules is NULL
    # ─────────────────────────────────────────

    def test_legacy_fitment_universal_true(self):
        part = {
            "id": 1,
            "fitment_rules": None,
            "compatible_bikes": None,
            "fitment_universal": 1,
        }
        bike = {"id": 999}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True
        assert "legacy universal" in reason

    def test_legacy_compatible_bikes_hit(self):
        part = {
            "id": 1,
            "fitment_rules": None,
            "compatible_bikes": json.dumps([1, 2, 3]),
            "fitment_universal": 0,
        }
        bike = {"id": 2}
        compatible, reason = is_compatible(part, bike)
        assert compatible is True
        assert "legacy compatible_bikes" in reason

    def test_legacy_compatible_bikes_miss(self):
        part = {
            "id": 1,
            "fitment_rules": None,
            "compatible_bikes": json.dumps([1, 2, 3]),
            "fitment_universal": 0,
        }
        bike = {"id": 999}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False
        assert "not in legacy" in reason

    def test_legacy_fallback_both_false(self):
        part = {
            "id": 1,
            "fitment_rules": None,
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 999}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False

    # ─────────────────────────────────────────
    # Error handling
    # ─────────────────────────────────────────

    def test_invalid_json_in_fitment_rules(self):
        part = {
            "id": 1,
            "fitment_rules": "not valid json",
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {"id": 1}
        compatible, reason = is_compatible(part, bike)
        assert compatible is False
        assert "invalid" in reason.lower()

    def test_missing_bike_id(self):
        """Gracefully handle missing bike_id field."""
        part = {
            "id": 1,
            "fitment_rules": json.dumps({"tier": "exact", "bike_ids": [1, 2]}),
            "compatible_bikes": None,
            "fitment_universal": 0,
        }
        bike = {}  # No 'id' field
        compatible, reason = is_compatible(part, bike)
        # bike_id will be None, which won't match [1, 2]
        assert compatible is False


class TestStrokeTypeOnlyRule:
    """June 2026: a family rule whose ONLY constraint is stroke_type was
    treated as constraint-less (and therefore universal) because
    _has_any_match_constraint did not inspect stroke_type — a 2T-only part
    would match every 4T bike. Pins the production engine path."""

    def test_stroke_only_rule_blocks_other_stroke(self):
        from motoquant.parts.compatibility import is_compatible

        part = {
            "id": 9001,
            "fitment_rules": '{"tier": "family", "match": {"stroke_type": 2}}',
        }
        four_stroke_bike = {
            "id": 1,
            "manufacturer": "Suzuki",
            "displacement_cc": 999,
            "category": "sport",
            "stroke_type": 4,
        }
        ok, reason = is_compatible(part, four_stroke_bike)
        assert not ok, f"2T-only rule leaked to a 4T bike: {reason}"

    def test_stroke_only_rule_matches_same_stroke(self):
        from motoquant.parts.compatibility import is_compatible

        part = {
            "id": 9002,
            "fitment_rules": '{"tier": "family", "match": {"stroke_type": 2}}',
        }
        two_stroke_bike = {
            "id": 2,
            "manufacturer": "Yamaha",
            "displacement_cc": 347,
            "category": "sport",
            "stroke_type": 2,
        }
        ok, _ = is_compatible(part, two_stroke_bike)
        assert ok


class TestSearchLimitAfterCompatFilter:
    """June 2026: PartsRepository.search applied the SQL LIMIT *before* the
    compatibility filter, so with the catalog ordered by brand any compatible
    part whose brand sorted after the cut was silently never returned —
    the build optimizer was starved of ~2/3 of the catalog at limit=200."""

    def test_late_alphabet_brands_survive_limit(self):
        import os
        import sqlite3

        import pytest

        db_path = os.environ.get("MOTOQUANT_TEST_DB", "motoquant.db")
        if not os.path.exists(db_path):
            pytest.skip("no production DB in working tree")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        from motoquant.database.parts_repo import PartsRepository

        repo = PartsRepository(conn)
        rows = repo.search(bike_model_id=3, limit=200)  # Hayabusa Gen1
        assert rows, "expected compatible parts for the Hayabusa"
        brands = {r["brand"] for r in rows}
        late = [b for b in brands if b and b[0].upper() >= "S"]
        assert late, (
            "no compatible brand sorting at/after 'S' returned — the SQL LIMIT "
            f"is being applied before the compatibility filter again. Got: {sorted(brands)}"
        )
        conn.close()
