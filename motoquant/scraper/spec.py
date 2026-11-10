"""
MotoQuant — BikeSpec Dataclass
==============================
Intermediate representation between raw scraped data and BikeConfig.
Carries provenance (source URL, scrape timestamp) and per-field confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class BikeSpec:
    """
    Raw specification scraped from an external source.

    All numeric fields are Optional — None means data was not found
    on the source page (vs. zero which would be a real value).

    Confidence scores are stored in `field_confidence` keyed by field name.
    Default confidence for scraped fields is 0.55 (scraped, unverified).
    Manufacturer-confirmed specs get 0.80+.
    """

    # ── Identity ──────────────────────────────────────────────────────────
    manufacturer: str = ""
    model_name: str = ""
    model_code: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    category: str = "sport"  # sport / naked / cruiser / adventure / touring

    # ── Engine ────────────────────────────────────────────────────────────
    displacement_cc: float | None = None
    bore_mm: float | None = None
    stroke_mm: float | None = None
    compression_ratio: float | None = None
    # Power: prefer crank HP; convert from kW if needed
    peak_power_hp: float | None = None
    peak_power_rpm: int | None = None
    peak_torque_nm: float | None = None
    peak_torque_rpm: int | None = None
    fuel_system: str | None = None  # carb / fi / tbi
    cooling: str | None = None  # air / liquid / oil
    valve_config: str | None = None  # dohc / sohc / ohv / 2T_reed / 2T_piston
    cylinders: int | None = None
    # 2-stroke / 4-stroke discriminator. 2 = two-stroke cycle (expansion-chamber
    # resonance physics kicks in), 4 = four-stroke (default). Set explicitly for
    # 2T bikes (RD350, RGV250, RS125, KTM 300 EXC, etc.) so the importer wires
    # in the right torque curve, parasitic losses, and parts fitment rules.
    stroke_type: int | None = None  # 2 or 4 (None → inferred as 4-stroke)
    expansion_chamber: bool = False
    reed_valve: bool = False
    powervalve: bool = False
    tuned_rpm: int | None = None

    # ── Drivetrain ────────────────────────────────────────────────────────
    gears: int | None = None
    gear_ratios: list[float] | None = None
    primary_ratio: float | None = None  # crank → gearbox input shaft
    front_sprocket: int | None = None
    rear_sprocket: int | None = None
    final_drive: str | None = None  # chain / shaft / belt
    chain_pitch: str | None = None  # 520 / 525 / 530
    # Factory electronic top-speed limiter in km/h (299 for the gentleman's-
    # agreement hyperbike fleet). None = unrestricted / unknown. Annotate ONLY
    # when the published top-speed figure is credibly the limiter itself.
    speed_limiter_kmh: float | None = None

    # ── Chassis / Mass ────────────────────────────────────────────────────
    dry_mass_kg: float | None = None
    wet_mass_kg: float | None = None
    wheelbase_mm: float | None = None
    seat_height_mm: float | None = None
    fuel_capacity_l: float | None = None
    cog_height_mm: float | None = None  # centre of gravity height (static, laden)
    weight_dist_front_pct: float | None = None  # % of weight on front wheel (static)
    swingarm_length_mm: float | None = None  # pivot to axle, used for anti-squat calc

    # ── Engine dynamics ───────────────────────────────────────────────────
    engine_inertia_kgm2: float | None = None  # rotating assembly inertia

    # ── Aerodynamics (per-model; estimated from category if not available) ─
    cd: float | None = None
    frontal_area_m2: float | None = None

    # ── Tires ─────────────────────────────────────────────────────────────
    front_tire_size: str | None = None  # e.g. "120/70ZR17"
    rear_tire_size: str | None = None  # e.g. "190/55ZR17"

    # ── Provenance ────────────────────────────────────────────────────────
    source_name: str = "unknown"  # bikez / bikeswiki / manufacturer / manual
    source_url: str | None = None
    scraped_at: str | None = None  # ISO datetime string
    raw_data: dict[str, Any] | None = None  # original key→value from source

    # Per-field confidence scores (0.0–1.0)
    field_confidence: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.scraped_at is None:
            # Python 3.12+ deprecates the implicit-UTC ``datetime.utcnow``;
            # build a timezone-aware UTC value and strip the tzinfo so the
            # serialised string remains a naive ISO timestamp (matches the
            # pre-3.12 behaviour byte-for-byte).
            self.scraped_at = (
                datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
            )


@dataclass
class ValidationResult:
    """Result of validating a BikeSpec against physical bounds."""

    is_valid: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    corrected_fields: dict[str, Any] = field(default_factory=dict)
    # Fields left None that the importer will default itself (validate_spec
    # never writes defaults into the spec — see its docstring).
    defaulted_fields: dict[str, Any] = field(default_factory=dict)
    overall_confidence: float = 0.0

    def __str__(self):
        status = "VALID" if self.is_valid else "INVALID"
        parts = [f"[{status}] conf={self.overall_confidence:.2f}"]
        if self.errors:
            parts.append(f"  Errors: {'; '.join(self.errors)}")
        if self.warnings:
            parts.append(f"  Warnings: {'; '.join(self.warnings)}")
        if self.corrected_fields:
            parts.append(f"  Auto-corrected: {list(self.corrected_fields.keys())}")
        return "\n".join(parts)
