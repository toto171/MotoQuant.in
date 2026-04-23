"""
MotoQuant Pro — Part Fitment Compatibility Engine
==================================================
Determines whether a performance part fits a given motorcycle,
using tiered fitment rules (exact, family, category, universal).
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

_logger = logging.getLogger(__name__)


class FitmentTier(str, Enum):
    """Fitment tier model: how specifically a part is matched to bikes."""
    EXACT = "exact"          # Fits only specific bike_ids
    FAMILY = "family"        # Fits engine family (config, displacement range, category)
    CATEGORY = "category"    # Fits broad category + displacement
    UNIVERSAL = "universal"  # Fits virtually every motorcycle


@dataclass
class FitmentMatch:
    """Constraints for family/category tier matching."""
    manufacturers: list[str] = field(default_factory=list)
    engine_configs: list[str] = field(default_factory=list)
    displacement_min_cc: Optional[float] = None
    displacement_max_cc: Optional[float] = None
    categories: list[str] = field(default_factory=list)
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    chain_pitch: Optional[str] = None
    # Stroke cycle: 2 or 4. When set, only bikes whose engine_params.stroke_type
    # matches will satisfy the rule. Prevents 2T-part → 4T-bike leaks (and vice
    # versa) in the same displacement / cylinder-config window. Introduced
    # April 20, 2026 alongside the 2-stroke expansion catalog.
    stroke_type: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = {}
        if self.manufacturers:
            d["manufacturers"] = self.manufacturers
        if self.engine_configs:
            d["engine_configs"] = self.engine_configs
        if self.displacement_min_cc is not None:
            d["displacement_min_cc"] = self.displacement_min_cc
        if self.displacement_max_cc is not None:
            d["displacement_max_cc"] = self.displacement_max_cc
        if self.categories:
            d["categories"] = self.categories
        if self.year_min is not None:
            d["year_min"] = self.year_min
        if self.year_max is not None:
            d["year_max"] = self.year_max
        if self.chain_pitch is not None:
            d["chain_pitch"] = self.chain_pitch
        if self.stroke_type is not None:
            d["stroke_type"] = self.stroke_type
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "FitmentMatch":
        """Deserialize from dict."""
        return cls(
            manufacturers=d.get("manufacturers", []),
            engine_configs=d.get("engine_configs", []),
            displacement_min_cc=d.get("displacement_min_cc"),
            displacement_max_cc=d.get("displacement_max_cc"),
            categories=d.get("categories", []),
            year_min=d.get("year_min"),
            year_max=d.get("year_max"),
            chain_pitch=d.get("chain_pitch"),
            stroke_type=d.get("stroke_type"),
        )


@dataclass
class FitmentRules:
    """
    Complete fitment rules for a part, matching the spec exactly.
    """
    tier: FitmentTier
    bike_ids: list[int] = field(default_factory=list)
    match: FitmentMatch = field(default_factory=FitmentMatch)
    excluded_bike_ids: list[int] = field(default_factory=list)
    description: str = ""

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = {
            "tier": self.tier.value,
        }
        if self.bike_ids:
            d["bike_ids"] = self.bike_ids
        match_dict = self.match.to_dict()
        if match_dict:
            d["match"] = match_dict
        if self.excluded_bike_ids:
            d["excluded_bike_ids"] = self.excluded_bike_ids
        if self.description:
            d["description"] = self.description
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "FitmentRules":
        """Deserialize from dict."""
        if not isinstance(d, dict):
            raise ValueError("fitment_rules must be a dict")

        tier_str = d.get("tier") if d else None
        if not tier_str:
            raise ValueError("Missing 'tier' field in fitment_rules")

        try:
            tier = FitmentTier(tier_str)
        except ValueError:
            raise ValueError(f"Invalid tier: {tier_str}")

        match_dict = d.get("match", {})
        match = FitmentMatch.from_dict(match_dict) if match_dict else FitmentMatch()

        return cls(
            tier=tier,
            bike_ids=d.get("bike_ids", []),
            match=match,
            excluded_bike_ids=d.get("excluded_bike_ids", []),
            description=d.get("description", ""),
        )

    @classmethod
    def from_json(cls, s: str) -> "FitmentRules":
        """Deserialize from JSON string."""
        if not s:
            raise ValueError("Cannot deserialize empty string to FitmentRules")
        d = json.loads(s)
        return cls.from_dict(d)


def is_compatible(part_row: dict, bike_row: dict) -> tuple[bool, str]:
    """
    Check if a part fits a motorcycle.

    Args:
        part_row: dict from parts table (must have fitment_rules, fitment_universal, compatible_bikes)
        bike_row: dict from bike_models table (must have id, manufacturer_id, cylinder_config,
                                               displacement_cc, category, year_from, chain_pitch)

    Returns:
        (compatible: bool, reason: str)
    """
    bike_id = bike_row.get("id")

    # ───────────────────────────────────────────────────
    # LEGACY FALLBACK: fitment_rules is NULL
    # ───────────────────────────────────────────────────
    fitment_rules_str = part_row.get("fitment_rules")
    if not fitment_rules_str:
        # Use old {compatible_bikes, fitment_universal} mechanism
        fitment_universal = part_row.get("fitment_universal", 0)
        if fitment_universal:
            return True, "legacy universal fitment"

        compatible_bikes_str = part_row.get("compatible_bikes")
        if compatible_bikes_str:
            try:
                compatible_ids = json.loads(compatible_bikes_str)
                if bike_id in compatible_ids:
                    return True, "legacy compatible_bikes list"
            except (json.JSONDecodeError, TypeError):
                pass

        return False, "not in legacy compatible_bikes list"

    # ───────────────────────────────────────────────────
    # PARSE fitment_rules
    # ───────────────────────────────────────────────────
    try:
        rules = FitmentRules.from_json(fitment_rules_str)
    except (json.JSONDecodeError, ValueError) as e:
        _logger.warning(f"Invalid fitment_rules JSON for part {part_row.get('id')}: {e}")
        return False, f"invalid fitment_rules: {e}"

    # ───────────────────────────────────────────────────
    # TIER: universal
    # ───────────────────────────────────────────────────
    if rules.tier == FitmentTier.UNIVERSAL:
        return True, "universal fitment"

    # ───────────────────────────────────────────────────
    # CHECK: excluded_bike_ids blocklist
    # ───────────────────────────────────────────────────
    if bike_id in rules.excluded_bike_ids:
        return False, "explicitly excluded"

    # ───────────────────────────────────────────────────
    # TIER: exact
    # ───────────────────────────────────────────────────
    if rules.tier == FitmentTier.EXACT:
        if bike_id in rules.bike_ids:
            return True, "listed for this model"
        return False, "not listed for this model"

    # ───────────────────────────────────────────────────
    # TIER: family or category
    # ───────────────────────────────────────────────────
    if rules.tier in (FitmentTier.FAMILY, FitmentTier.CATEGORY):
        # Safety check: if no match constraints at all, warn and assume universal
        if not _has_any_match_constraint(rules.match):
            _logger.warning(
                f"Part fitment tier '{rules.tier.value}' has no match constraints; treating as universal"
            )
            return True, f"tier {rules.tier.value} without constraints (treated as universal)"

        # Test each constraint
        result, reason = _test_match_constraints(rules.match, bike_row)
        return result, reason

    # Fallback (should not reach)
    return False, f"unknown tier: {rules.tier}"


def _has_any_match_constraint(match: FitmentMatch) -> bool:
    """Check if match has at least one constraint defined."""
    return bool(
        match.manufacturers
        or match.engine_configs
        or match.displacement_min_cc is not None
        or match.displacement_max_cc is not None
        or match.categories
        or match.year_min is not None
        or match.year_max is not None
        or match.chain_pitch is not None
    )


def _test_match_constraints(match: FitmentMatch, bike_row: dict) -> tuple[bool, str]:
    """
    Test all constraints in a FitmentMatch against a bike row.
    Returns (passed, first_failing_reason).
    """
    # Manufacturers — case-insensitive name match.
    # bike_row should include 'manufacturer' (preferred) or 'manufacturer_name'
    # populated by the caller's query. Repositories that use
    # `SELECT * FROM bike_models` alone will NOT have this — they must
    # enrich the row before calling is_compatible().
    if match.manufacturers:
        bike_mfr = (
            bike_row.get("manufacturer")
            or bike_row.get("manufacturer_name")
            or ""
        )
        bike_mfr_lc = bike_mfr.strip().lower()
        allowed = {m.strip().lower() for m in match.manufacturers}
        if bike_mfr_lc and bike_mfr_lc not in allowed:
            return False, f"manufacturer '{bike_mfr}' not in {match.manufacturers}"
        # If the bike row has no manufacturer info at all (shouldn't happen in
        # normal use), log and skip this constraint rather than silently pass.
        if not bike_mfr_lc:
            _logger.warning(
                "bike_row has no manufacturer/manufacturer_name; "
                "manufacturers constraint skipped"
            )

    # Engine config
    if match.engine_configs:
        config = bike_row.get("cylinder_config")
        if config not in match.engine_configs:
            return False, f"engine config {config} not in {match.engine_configs}"

    # Displacement range
    disp = bike_row.get("displacement_cc")
    if disp is not None:
        if match.displacement_min_cc is not None and disp < match.displacement_min_cc:
            return False, f"displacement {disp}cc below min {match.displacement_min_cc}cc"
        if match.displacement_max_cc is not None and disp > match.displacement_max_cc:
            return False, f"displacement {disp}cc above max {match.displacement_max_cc}cc"

    # Categories
    if match.categories:
        cat = bike_row.get("category")
        if cat not in match.categories:
            return False, f"category {cat} not in {match.categories}"

    # Year range
    year = bike_row.get("year_from")
    if year is not None:
        if match.year_min is not None and year < match.year_min:
            return False, f"year {year} before min {match.year_min}"
        if match.year_max is not None and year > match.year_max:
            return False, f"year {year} after max {match.year_max}"

    # Chain pitch (case-sensitive string equality)
    if match.chain_pitch:
        pitch = bike_row.get("chain_pitch")
        if pitch != match.chain_pitch:
            return False, f"chain pitch {pitch} does not match {match.chain_pitch}"

    # Stroke type (2 or 4) — caller must enrich bike_row with 'stroke_type' or
    # 'engine_stroke_type' (pulled from engine_params.stroke_type). Defaults to
    # 4-stroke when the bike row lacks the field (legacy rows pre-dating the 2T
    # expansion) — this keeps backwards compatibility for 4T parts that have not
    # declared a stroke_type filter.
    if match.stroke_type is not None:
        bike_stroke = (
            bike_row.get("stroke_type")
            or bike_row.get("engine_stroke_type")
            or 4
        )
        try:
            bike_stroke_int = int(bike_stroke)
        except (TypeError, ValueError):
            bike_stroke_int = 4
        if bike_stroke_int != int(match.stroke_type):
            return (
                False,
                f"stroke_type {bike_stroke_int} does not match required {match.stroke_type}",
            )

    return True, "all constraints satisfied"
