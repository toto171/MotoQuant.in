"""
MotoQuant Pro — BikeSpec Dataclass
===================================
Intermediate representation between raw scraped data and BikeConfig.
Carries provenance (source URL, scrape timestamp) and per-field confidence.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime


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
    model_code: Optional[str] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    category: str = "sport"           # sport / naked / cruiser / adventure / touring

    # ── Engine ────────────────────────────────────────────────────────────
    displacement_cc: Optional[float] = None
    bore_mm: Optional[float] = None
    stroke_mm: Optional[float] = None
    compression_ratio: Optional[float] = None
    # Power: prefer crank HP; convert from kW if needed
    peak_power_hp: Optional[float] = None
    peak_power_rpm: Optional[int] = None
    peak_torque_nm: Optional[float] = None
    peak_torque_rpm: Optional[int] = None
    fuel_system: Optional[str] = None   # carb / fi / tbi
    cooling: Optional[str] = None       # air / liquid / oil
    valve_config: Optional[str] = None  # dohc / sohc / ohv
    cylinders: Optional[int] = None

    # ── Drivetrain ────────────────────────────────────────────────────────
    gears: Optional[int] = None
    gear_ratios: Optional[List[float]] = None
    primary_ratio: Optional[float] = None       # crank → gearbox input shaft
    front_sprocket: Optional[int] = None
    rear_sprocket: Optional[int] = None
    final_drive: Optional[str] = None           # chain / shaft / belt
    chain_pitch: Optional[str] = None           # 520 / 525 / 530

    # ── Chassis / Mass ────────────────────────────────────────────────────
    dry_mass_kg: Optional[float] = None
    wet_mass_kg: Optional[float] = None
    wheelbase_mm: Optional[float] = None
    seat_height_mm: Optional[float] = None
    fuel_capacity_l: Optional[float] = None
    cog_height_mm: Optional[float] = None       # centre of gravity height (static, laden)
    weight_dist_front_pct: Optional[float] = None  # % of weight on front wheel (static)
    swingarm_length_mm: Optional[float] = None  # pivot to axle, used for anti-squat calc

    # ── Engine dynamics ───────────────────────────────────────────────────
    engine_inertia_kgm2: Optional[float] = None # rotating assembly inertia

    # ── Aerodynamics (per-model; estimated from category if not available) ─
    cd: Optional[float] = None
    frontal_area_m2: Optional[float] = None

    # ── Tires ─────────────────────────────────────────────────────────────
    front_tire_size: Optional[str] = None   # e.g. "120/70ZR17"
    rear_tire_size: Optional[str] = None    # e.g. "190/55ZR17"

    # ── Provenance ────────────────────────────────────────────────────────
    source_name: str = "unknown"            # bikez / bikeswiki / manufacturer / manual
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None        # ISO datetime string
    raw_data: Optional[Dict[str, Any]] = None   # original key→value from source

    # Per-field confidence scores (0.0–1.0)
    field_confidence: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.utcnow().isoformat()


@dataclass
class ValidationResult:
    """Result of validating a BikeSpec against physical bounds."""

    is_valid: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    corrected_fields: Dict[str, Any] = field(default_factory=dict)
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
