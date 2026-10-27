"""
MotoQuant — Parameter Models
============================
All input parameters organized into dataclasses by category.
Every parameter that affects prediction by >= 0.1% is represented.
"""

from dataclasses import dataclass, field

import numpy as np

# ═══════════════════════════════════════════
# CORE ENUMS (as string constants)
# ═══════════════════════════════════════════

CLUTCH_LOCKUP = "lockup"
CLUTCH_SLIDER = "slider"
CLUTCH_MULTISTAGE = "multistage"
CLUTCH_SLIPPER = "slipper"

BOOST_NA = "na"
BOOST_TURBO = "turbo"
BOOST_SC_ROOTS = "sc_roots"
BOOST_SC_CENTRIFUGAL = "sc_centrifugal"
BOOST_N2O = "n2o"

DRIVE_CHAIN = "chain"
DRIVE_BELT = "belt"
DRIVE_SHAFT = "shaft"

STAGING_SHALLOW = "shallow"
STAGING_DEEP = "deep"

SHIFT_CUT_IGN = "ignition"
SHIFT_CUT_FUEL = "fuel"
SHIFT_CUT_BOTH = "both"

RIDER_UPRIGHT = "upright"
RIDER_TUCK = "tuck"
RIDER_RACE = "race"
RIDER_CUSTOM = "custom"

TRACK_NONE = "none"
TRACK_VHT = "vht"
TRACK_PJ1 = "pj1"
TRACK_RUBBER = "rubber_buildup"

FUEL_GASOLINE = "gasoline"
FUEL_E85 = "e85"
FUEL_METHANOL = "methanol"
FUEL_RACE_GAS = "race_gas"


@dataclass
class DynoCurve:
    """Engine torque or power curve from dynamometer."""

    rpm: np.ndarray  # RPM points (ascending)
    torque_nm: np.ndarray  # Torque in N·m at each RPM
    is_at_wheel: bool = True  # True = chassis dyno (losses included), False = crank

    def interpolate(self, rpm_query: float) -> float:
        """Interpolate torque at arbitrary RPM. Clamp to range."""
        return float(np.interp(rpm_query, self.rpm, self.torque_nm))

    @classmethod
    def from_power_hp(
        cls, rpm: np.ndarray, power_hp: np.ndarray, is_at_wheel: bool = True
    ) -> "DynoCurve":
        """Create from power curve. T = P * 9549 / RPM."""
        torque_nm = power_hp * 745.7 / (rpm * 2 * np.pi / 60)
        return cls(rpm=rpm, torque_nm=torque_nm, is_at_wheel=is_at_wheel)


# ═══════════════════════════════════════════
# 1. CHASSIS & GEOMETRY
# ═══════════════════════════════════════════


@dataclass
class ChassisParams:
    """Chassis geometry and mass properties."""

    dry_mass_kg: float = 185.0  # Bike dry mass
    rider_mass_kg: float = 75.0  # Rider with gear
    fluid_mass_kg: float = 15.0  # Fuel + oil + coolant
    fuel_mass_kg: float = 16.0  # Full tank
    fuel_consumption_gs: float = 8.0  # g/s at WOT (decreasing mass)
    wheelbase_mm: float = 1405.0  # Stock wheelbase
    swingarm_extension_mm: float = 0.0  # Extension beyond stock
    cog_height_mm: float = 550.0  # Combined bike+rider CoG height
    front_weight_pct: float = 0.52  # Static front weight % (with rider)
    rake_deg: float = 24.0  # Steering head angle
    trail_mm: float = 100.0  # Trail
    seat_height_mm: float = 810.0  # Seat height

    @property
    def total_mass_kg(self) -> float:
        return self.dry_mass_kg + self.rider_mass_kg + self.fluid_mass_kg

    @property
    def wheelbase_m(self) -> float:
        return (self.wheelbase_mm + self.swingarm_extension_mm) / 1000.0

    @property
    def cog_height_m(self) -> float:
        return self.cog_height_mm / 1000.0

    @property
    def L_f(self) -> float:
        """Distance from front axle to CoG (m)."""
        return self.wheelbase_m * (1 - self.front_weight_pct)

    @property
    def L_r(self) -> float:
        """Distance from rear axle to CoG (m)."""
        return self.wheelbase_m * self.front_weight_pct


# ═══════════════════════════════════════════
# 2. ENGINE & POWERTRAIN
# ═══════════════════════════════════════════


@dataclass
class EngineParams:
    """Engine characteristics."""

    dyno_curve: DynoCurve | None = None  # Measured torque curve
    peak_power_hp: float = 160.0  # Fallback if no curve
    peak_torque_nm: float = 115.0  # Fallback
    peak_power_rpm: float = 11500.0  # RPM at peak power
    peak_torque_rpm: float = 9500.0  # RPM at peak torque
    redline_rpm: float = 13000.0  # Rev limiter
    launch_rpm: float = 8000.0  # Two-step hold RPM
    idle_rpm: float = 1100.0  # Idle
    displacement_cc: float = 999.0  # Displacement
    bore_mm: float = 73.4  # Bore
    stroke_mm: float = 59.0  # Stroke
    compression_ratio: float = 12.5  # CR
    engine_inertia_kgm2: float = 0.04  # Crankshaft + internals
    crank_rotation_cw: bool = True  # True = standard CW
    counter_rotating: bool = False  # Counter-rotating crank
    fuel_type: str = FUEL_GASOLINE  # Fuel
    afr_wot: float = 12.5  # Air-fuel ratio at WOT
    coolant_temp_c: float = 85.0  # At launch
    motoring_torque_nm: float = 40.0  # Engine braking torque
    # Cylinder metadata — used by parts compatibility engine to narrow
    # fitment to specific engine families (e.g. I4 vs V4 for exhaust systems).
    # Populated from BikeSpec at import time; None for pre-compatibility-era
    # configs (handled by enrich-on-read fallback).
    cylinder_count: int | None = None  # 1, 2, 3, 4, 6
    cylinder_config: str | None = None  # I1, I2, I3, I4, I6, V2, V4, flat_6
    # ── 2-stroke / 4-stroke discriminator ──────────────────────────────
    # stroke_type = 2 flips several physics branches:
    #   • get_torque() uses expansion-chamber resonance (narrow band)
    #   • parasitic oil-pump + valvetrain losses collapse (no valvetrain,
    #     pre-mix or separate oil-injection = tiny pump load)
    #   • engine braking torque is effectively zero (no compression braking)
    stroke_type: int = 4  # 2 or 4
    # Expansion chamber tuned RPM (2-stroke only). If None, defaults to
    # peak_power_rpm at get_torque() call time.
    tuned_rpm: float | None = None
    expansion_chamber: bool = False  # True = tuned pipe fitted (2T only)
    reed_valve: bool = False  # Reed-valve induction (2T only; adds ~3%)
    powervalve: bool = False  # YPVS/RC Valve/HPP etc. — widens 2T band
    # Induction type — useful for parts compatibility on carb jets etc.
    induction_type: str | None = None  # "carb" / "efi" / "tbi" / None = unknown

    def get_torque(self, rpm: float) -> float:
        """Get engine torque at given RPM."""
        if self.dyno_curve is not None:
            return self.dyno_curve.interpolate(rpm)
        # 2-stroke: expansion-chamber resonance envelope
        if self.stroke_type == 2:
            return self._two_stroke_torque(rpm)
        # 4-stroke: parabolic synthetic curve from peak torque
        # T(rpm) = T_peak * [1 - ((rpm - rpm_peak) / (rpm_range/2))^2] (clamped > 0)
        rpm_range = self.redline_rpm - self.idle_rpm
        if rpm_range <= 0:
            return 0.0
        x = (rpm - self.peak_torque_rpm) / (rpm_range * 0.6)
        return max(0.0, self.peak_torque_nm * (1.0 - x * x))

    # ─────────────────────────────────────────
    # 2-STROKE SYNTHETIC TORQUE CURVE
    # ─────────────────────────────────────────
    def _two_stroke_torque(self, rpm: float) -> float:
        """
        Expansion-chamber resonance envelope for 2-stroke engines.

        Model:
          • Strong narrow peak centred on `tuned_rpm` (falls back to
            peak_power_rpm, which for 2-strokes is ~ peak_torque_rpm).
          • Asymmetric: rises gradually below the pipe (bike "comes on pipe"),
            drops sharply above (pulse returns out of phase).
          • Powervalve (YPVS / RC Valve / HPP / ATAC) roughly doubles the
            usable width of the band.
          • Non-powervalve bikes still make some base torque off-pipe — 15%
            of peak, enough to pull through gears but clearly flat.
        """
        import math

        if rpm < self.idle_rpm * 1.05:
            return 0.0

        tuned = self.tuned_rpm or self.peak_power_rpm
        # Widths as fractions of the tuned RPM.  Band constants (band_lo /
        # band_hi / baseline per branch) are kept in sync with
        # `_synthetic_2stroke_torque_curve` in defaults.py.  NOTE (July 10,
        # 2026): the two paths are no longer value-identical — defaults.py
        # additionally applies calibration tail factors (×1.10 <50 hp,
        # ×1.07 <80 hp, plus the rated-HP rescale) that this continuous
        # fallback does not.  That is acceptable because every production
        # config carries a generated dyno_curve (verified: 541/541 current
        # bike_configs), so this fallback only serves hand-built test
        # configs; if you ever route curve-less 2T configs into production,
        # re-sync the tail factors too.  The cylinders>=3 vintage-triple
        # branch mirrors the GT750 / H2 Mach IV fix.
        cyls = self.cylinder_count or 1
        if self.powervalve:
            band_lo = 0.18
            band_hi = 0.12
            baseline = 0.20  # powervalve: good off-pipe
        elif cyls >= 3:
            # Vintage multi-cylinder piston-port triple (GT750, H2 Mach IV):
            # overlapping firing smooths the resonance into a wide, flat curve.
            band_lo = 0.55
            band_hi = 0.30
            baseline = 0.50
        elif cyls == 2:
            # Two-cylinder piston-port (RD350, RD400, NSR250 non-RC-valve,
            # RGV250 non-RAVE, H1 Mach III). Two independent pipes fired
            # 180° apart give much better cycle-to-cycle smoothing than a
            # single-cyl race pipe. Published RD350 dyno shows ~40 % of
            # peak at 2 500 rpm. Kept in sync with the scraper-side helper
            # in `_synthetic_2stroke_torque_curve` (defaults.py).
            band_lo = 0.30
            band_hi = 0.15
            baseline = 0.25
        elif (
            cyls == 1
            and self.displacement_cc is not None
            and self.displacement_cc < 200.0
        ):
            # Apr-24-PM kaizen: small commuter / cub piston-port single
            # (RX100/RX135/RXZ135 class). Mild OEM pipe -- wide soft curve,
            # NOT a race expansion chamber. Kept in sync with the scraper-
            # side small-cc-commuter branch in
            # ``_synthetic_2stroke_torque_curve`` (defaults.py).
            band_lo = 0.35
            band_hi = 0.25
            baseline = 0.35
        else:
            # Apr-27: Fixed piston-port race engines (>200cc 1-cyl, no YPVS).
            # Widened from 0.12/0.08/0.12 (too peaky for drag). Now 0.25/0.15/0.25.
            band_lo = 0.25
            band_hi = 0.15
            baseline = 0.25

        if rpm <= tuned:
            x = (tuned - rpm) / max(1.0, tuned * band_lo)
        else:
            x = (rpm - tuned) / max(1.0, tuned * band_hi)
        factor = math.exp(-1.5 * x * x)
        factor = max(baseline, factor)

        # 2026-10 epoch: the rev-limiter cliff that used to sit here (torque 0
        # above 1.02 x redline) was REMOVED. The limiter is modelled once, in
        # EngineModel.torque (soft cut, constants.REV_LIMITER_CUT_FACTOR) —
        # dyno-curve configs never had a cliff in get_torque, and a second
        # hard cut here re-created the slip-phase zero-torque freeze for
        # curve-less 2T configs. Direct callers (optimal_shift_rpm, the N2O
        # multiplier) only evaluate at or below redline / under the limiter.
        return self.peak_torque_nm * factor


# ═══════════════════════════════════════════
# 3. FORCED INDUCTION
# ═══════════════════════════════════════════


@dataclass
class ForcedInductionParams:
    """Turbo, supercharger, or nitrous parameters."""

    boost_type: str = BOOST_NA  # Type
    target_boost_bar: float = 0.0  # Target gauge pressure
    turbo_spool_time_s: float = 0.5  # Time constant
    prespool_boost_bar: float = 0.0  # Boost built at two-step
    wastegate_crack_bar: float = 0.8  # Wastegate opens
    intercooler_type: str = "none"  # none / a2a / a2w
    intercooler_effectiveness: float = 0.75  # eta_IC
    sc_parasitic_hp: float = 0.0  # SC power draw at redline
    n2o_hp_per_stage: float = 0.0  # NOS equivalent HP
    n2o_stages: int = 0  # Number of stages
    n2o_ramp_type: str = "time"  # time / rpm / tps
    n2o_ramp_duration_s: float = 1.5  # Ramp time
    injector_size_cc: float = 0.0  # Injector capacity
    injector_duty_limit: float = 0.85  # Max duty cycle

    @property
    def is_boosted(self) -> bool:
        return self.boost_type != BOOST_NA


# ═══════════════════════════════════════════
# 4. DRIVETRAIN
# ═══════════════════════════════════════════


@dataclass
class DrivetrainParams:
    """Transmission, final drive, and shifting."""

    primary_ratio: float = 1.553  # Primary reduction
    gear_ratios: list[float] = field(
        default_factory=lambda: [2.562, 1.947, 1.565, 1.350, 1.208, 1.064]
    )
    final_drive_ratio: float = 2.471  # Sprocket ratio (rear/front)
    front_sprocket: int = 17  # Front teeth
    rear_sprocket: int = 42  # Rear teeth (overrides final_drive_ratio if set)
    chain_pitch_mm: float = 15.875  # 530 chain
    chain_pitch: str | None = (
        None  # Standard pitch code: "428", "520", "525", "530" (used by parts fitment)
    )
    chain_links: int = 110  # Number of links
    chain_slack_mm: float = 30.0  # Free play
    drive_type: str = DRIVE_CHAIN  # chain / belt / shaft
    primary_efficiency: float = 0.99  # Primary gear mesh
    trans_efficiency_per_mesh: float = 0.985  # Per gear pair
    chain_efficiency: float = 0.97  # Chain/belt efficiency
    # Shaft final drive: two bevel meshes (~0.97-0.98 each) plus the U-joint /
    # spline (~0.98) give ~0.93. The old 0.85 made every shaft bike ~0.3 s
    # slower than its benchmark (Oct 2026 epoch, data-agent attribution).
    shaft_efficiency: float = 0.93
    gear_oil_viscosity_cst: float = 12.0  # Gear oil @ 100C
    clutch_type: str = CLUTCH_LOCKUP  # Clutch type
    clutch_engage_rpm: float = 6000.0  # Engagement RPM
    air_shifter: bool = False  # Air shifter installed
    shift_cut_type: str = SHIFT_CUT_IGN  # Cut type
    shift_cut_duration_ms: float = 65.0  # Cut duration
    post_shift_retard_ms: float = 40.0  # Retard ramp after shift
    quickshifter: bool = False  # QS installed
    total_shift_time_ms: float = 100.0  # Total shift time
    # Factory top-speed limiter (July 17, 2026). None = unrestricted. When set,
    # the sim clamps net acceleration to <= 0 at/above this speed, so the
    # gentleman's-agreement 299 km/h fleet plateaus at the limiter instead of
    # running to its aero-limited 320-340 km/h. Lives inside the dataclass so
    # the DB bridge + config_io round-trip it via dataclasses.fields (the
    # category_tag top-level-field trap does not apply).
    speed_limiter_kmh: float | None = None

    @property
    def final_ratio(self) -> float:
        """Use sprocket teeth if explicitly set, else the ratio."""
        if self.rear_sprocket > 0 and self.front_sprocket > 0:
            return self.rear_sprocket / self.front_sprocket
        return self.final_drive_ratio

    def set_effective_final_drive(self, ratio: float) -> None:
        """Force the effective engine→wheel final-drive ratio to ``ratio``.

        ``final_ratio`` prefers sprocket teeth (rear/front) over
        ``final_drive_ratio`` whenever both sprockets are set — which is every
        chain-drive bike — so assigning ``final_drive_ratio`` alone is a silent
        no-op there. This clears the sprocket override so ``ratio`` actually
        takes effect. Used by the Sobol / Bayesian analysis tools, which
        perturb *gearing as a continuous ratio* rather than a discrete sprocket
        swap. Nothing in the physics loop reads sprocket teeth directly (only
        ``final_ratio`` does), so clearing them changes nothing but the ratio.
        """
        self.final_drive_ratio = ratio
        self.front_sprocket = 0
        self.rear_sprocket = 0

    def overall_ratio(self, gear_idx: int) -> float:
        """Total reduction from engine to wheel for a given gear (0-indexed)."""
        return self.primary_ratio * self.gear_ratios[gear_idx] * self.final_ratio

    def drivetrain_efficiency(self) -> float:
        """Overall efficiency from engine to wheel."""
        if self.drive_type == DRIVE_SHAFT:
            return (
                self.primary_efficiency
                * self.trans_efficiency_per_mesh
                * self.shaft_efficiency
            )
        return (
            self.primary_efficiency
            * self.trans_efficiency_per_mesh
            * self.chain_efficiency
        )

    @property
    def num_gears(self) -> int:
        return len(self.gear_ratios)


# ═══════════════════════════════════════════
# 5. CLUTCH
# ═══════════════════════════════════════════


@dataclass
class ClutchParams:
    """Clutch engagement and thermal properties."""

    clutch_type: str = CLUTCH_LOCKUP  # Type
    plate_count: int = 8  # Friction plates
    plate_od_mm: float = 120.0  # Outer diameter
    plate_id_mm: float = 85.0  # Inner diameter
    friction_material: str = "organic"  # organic / sintered / kevlar
    mu_static: float = 0.38  # Static friction coeff
    spring_preload_n: float = 1200.0  # Spring force
    slider_weight_g: float = 0.0  # Centrifugal weight (slider)
    engage_rpm: float = 6000.0  # Engagement RPM
    basket_inertia_kgm2: float = 0.01  # Clutch basket inertia
    thermal_mass_jk: float = 500.0  # J/K (plates + basket)
    fade_temp_c: float = 250.0  # Fade onset
    slipper_ratio: float = 0.4  # Back-torque limit ratio
    hydraulic_compliance: float = 0.0  # mm3/bar (line flex)

    @property
    def mean_radius_m(self) -> float:
        return (self.plate_od_mm + self.plate_id_mm) / 4000.0

    def max_torque(self) -> float:
        """Maximum transmittable torque before slip."""
        r_mean = self.mean_radius_m
        # T = n_surfaces * mu * F_clamp * r_mean
        n_surfaces = 2 * self.plate_count  # Both sides of each plate
        return n_surfaces * self.mu_static * self.spring_preload_n * r_mean


# ═══════════════════════════════════════════
# 6. TIRES
# ═══════════════════════════════════════════


@dataclass
class TireParams:
    """Tire properties — the most critical sub-model."""

    # Rear tire
    rear_model: str = "Generic drag slick"
    rear_size: str = "190/50-17"
    rear_rolling_radius_m: float = 0.302  # Static rolling radius
    rear_pressure_psi: float = 24.0  # Cold pressure
    rear_mass_kg: float = 6.0  # Tire mass
    rear_inertia_kgm2: float = 0.55  # Wheel + tire
    # Front tire
    front_size: str = "120/70-17"
    front_rolling_radius_m: float = 0.305  # Static
    front_pressure_psi: float = 33.0  # Cold
    front_mass_kg: float = 4.0  # Tire mass
    front_inertia_kgm2: float = 0.35  # Wheel + tire
    # Friction model (Pacejka-simplified)
    mu_peak: float = 1.4  # Peak friction coefficient
    mu_slide: float = 1.1  # Sliding friction
    load_sensitivity_k: float = (
        0.00003  # mu decreases with load (1/N) — calibrated for sport radials
    )
    pacejka_B: float = 10.0  # Stiffness factor
    pacejka_C: float = 1.65  # Shape factor
    pacejka_D: float = 1.4  # Peak (= mu_peak at ref load)
    pacejka_E: float = -0.5  # Curvature factor
    # Thermal
    optimal_temp_c: float = 65.0  # Peak grip temperature
    reversion_temp_c: float = 105.0  # Permanent damage threshold
    thermal_conductivity: float = 0.2  # W/(m·K) rubber
    tread_mass_kg: float = 1.0  # Tread surface mass
    specific_heat_rubber: float = 1500.0  # J/(kg·K)
    # Tire growth
    growth_coeff: float = 2e-9  # s2/rad2 (centrifugal growth)
    tire_construction: str = "radial"  # bias / radial / ntec
    # Contact patch
    contact_patch_cm2: float = 80.0  # Static, measured
    tread_depth_mm: float = 0.0  # 0 for slicks
    # Burnout/prep
    burnout_end_temp_c: float = 55.0  # Tire temp after burnout
    time_burnout_to_launch_s: float = 8.0  # Cooling time
    # Track prep
    track_prep_type: str = TRACK_NONE  # Prep compound
    track_prep_passes: int = 0  # Freshness
    track_surface_roughness: str = "medium"  # smooth / medium / rough
    # Rolling resistance
    crr_base: float = 0.010  # Base rolling resistance coeff
    crr_speed_coeff: float = 5e-6  # Speed-dependent term (s2/m2)
    crr_temp_coeff: float = -0.005  # Per degree C above 30C

    def effective_radius(self, omega_wheel: float) -> float:
        """Rolling radius including centrifugal growth."""
        delta_r = self.growth_coeff * omega_wheel**2 * self.rear_rolling_radius_m
        return self.rear_rolling_radius_m + delta_r

    def tire_temp_at_launch(self, ambient_temp_c: float) -> float:
        """Tire surface temp at green light after burnout cooling."""
        # Exponential decay toward ambient
        tau = (
            self.tread_mass_kg * self.specific_heat_rubber / (10.0 * 0.02)
        )  # h*A estimate
        decay = np.exp(-self.time_burnout_to_launch_s / max(tau, 1.0))
        return ambient_temp_c + (self.burnout_end_temp_c - ambient_temp_c) * decay

    def track_prep_multiplier(self, track_temp_c: float) -> float:
        """Grip multiplier from track prep compound."""
        if self.track_prep_type == TRACK_NONE:
            return 1.0
        # Base multiplier decreases with passes and degrades above 50C
        if self.track_prep_type in (TRACK_VHT, TRACK_PJ1):
            freshness = max(0.0, 1.0 - self.track_prep_passes / 200.0)
            temp_penalty = max(0.0, 1.0 - max(0.0, track_temp_c - 50.0) / 30.0)
            return (
                1.0 + 0.12 * freshness * temp_penalty
            )  # 12% max grip boost from VHT/PJ1
        if self.track_prep_type == TRACK_RUBBER:
            return 1.0 + 0.10 * max(0.0, 1.0 - self.track_prep_passes / 500.0)
        return 1.0


# ═══════════════════════════════════════════
# 7. AERODYNAMICS
# ═══════════════════════════════════════════


@dataclass
class AeroParams:
    """Aerodynamic properties."""

    cd: float = 0.70  # Drag coefficient
    frontal_area_m2: float = 0.45  # Frontal area
    cd_a: float = 0.0  # Combined (overrides cd*A if >0)
    cl: float = 0.08  # Lift coefficient
    rider_position: str = RIDER_TUCK  # Default position
    belly_pan: bool = False  # Reduces Cd by 10%
    ram_air_efficiency: float = 0.0  # Scoop efficiency (0 = no ram air)
    ram_air_area_cm2: float = 0.0  # Scoop area
    # NOTE (July 13, 2026): headwind_ms/crosswind_ms were REMOVED — they were
    # dead knobs no physics read. The live wind path is
    # EnvironmentParams.wind_speed_ms + wind_direction_deg (0 = headwind).
    # Old DB blobs carrying the keys are filtered by bridge.db_row_to_config.

    @property
    def cd_a_effective(self) -> float:
        """Effective Cd*A accounting for rider position and belly pan."""
        base = self.cd_a if self.cd_a > 0 else self.cd * self.frontal_area_m2
        if self.belly_pan:
            base *= 0.90  # 10% reduction
        # Rider position modifier
        if self.rider_position == RIDER_UPRIGHT:
            base *= 1.35  # Upright is ~35% more drag than tuck
        elif self.rider_position == RIDER_RACE:
            base *= 0.92  # Race crouch is ~8% less than standard tuck
        return base


# ═══════════════════════════════════════════
# 8. SUSPENSION
# ═══════════════════════════════════════════


@dataclass
class SuspensionParams:
    """Suspension and weight transfer dynamics."""

    front_spring_rate_nmm: float = 10.0  # N/mm
    rear_spring_rate_nmm: float = 85.0  # N/mm
    front_comp_damping: float = 1.5  # N·s/mm
    front_reb_damping: float = 2.0  # N·s/mm
    rear_comp_damping: float = 2.5  # N·s/mm
    rear_reb_damping: float = 3.0  # N·s/mm
    front_fork_length_mm: float = 550.0  # Fork tube length
    rear_shock_stroke_mm: float = 58.0  # Shock travel
    swingarm_pivot_height_mm: float = 300.0  # Pivot above ground
    swingarm_length_mm: float = 590.0  # Stock length
    swingarm_extension_mm: float = 0.0  # Additional length
    anti_squat_pct: float = 90.0  # % (100 = neutral)
    static_sag_mm: float = 30.0  # Rear sag with rider
    front_preload_mm: float = 5.0  # Preload spacer


# ═══════════════════════════════════════════
# 9. BRAKING
# ═══════════════════════════════════════════


@dataclass
class BrakingParams:
    """Brake system properties."""

    front_disc_dia_mm: float = 310.0
    front_disc_thickness_mm: float = 5.0
    front_caliper_pistons: int = 4
    front_piston_dia_mm: float = 30.0
    rear_disc_dia_mm: float = 220.0
    rear_caliper_pistons: int = 1
    rear_piston_dia_mm: float = 38.0
    front_mc_bore_mm: float = 16.0
    rear_mc_bore_mm: float = 12.0
    pad_mu: float = 0.42
    pad_fade_temp_c: float = 400.0
    abs_equipped: bool = True
    abs_modulation_hz: float = 12.0
    slipper_ratio: float = 0.4


# ═══════════════════════════════════════════
# 10. WHEELIE CONTROL
# ═══════════════════════════════════════════


@dataclass
class WheelieParams:
    """Wheelie bar and electronic control."""

    wheelie_bar: bool = False
    bar_length_mm: float = 450.0
    bar_spring_rate_nmm: float = 10.0
    bar_damping: float = 2.0
    bar_contact_angle_deg: float = 2.0
    electronic_control: bool = False
    control_sensitivity: int = 5  # 0-9

    # Gyroscopic (derived from engine + wheel inertias)
    # These are computed by the simulation, not user-set


# ═══════════════════════════════════════════
# 11. RIDER
# ═══════════════════════════════════════════


@dataclass
class RiderParams:
    """Rider body dynamics."""

    mass_kg: float = 75.0  # With gear
    height_cm: float = 175.0  # Rider height
    cog_height_seated_mm: float = 700.0  # Rider CoG when seated
    launch_forward_shift_mm: float = 80.0  # Forward lean at launch
    tuck_transition_time_s: float = 2.0  # Time to go from launch to tuck
    gear_mass_kg: float = 5.0  # Helmet, suit, boots
    experience_level: str = "intermediate"  # novice / intermediate / expert

    def cog_offset(self, t: float) -> float:
        """Rider CoG offset (m) as function of time since launch.
        Positive = forward of neutral (helps prevent wheelie).
        """
        if t < 0:
            return self.launch_forward_shift_mm / 1000.0
        if t < self.tuck_transition_time_s:
            # Linear transition from forward lean to neutral/slightly back
            frac = t / self.tuck_transition_time_s
            forward = self.launch_forward_shift_mm / 1000.0
            return forward * (1.0 - frac)
        return -0.03  # Slight rearward in tuck


# ═══════════════════════════════════════════
# 12. PARASITIC
# ═══════════════════════════════════════════


@dataclass
class ParasiticParams:
    """Accessory and parasitic losses."""

    alternator_present: bool = True
    alternator_power_w: float = 150.0  # At full load
    water_pump_electric: bool = False  # Electric = no parasitic
    oil_pump_power_w: float = 500.0  # At redline
    valve_train_power_w: float = 250.0  # At redline
    parasitic_delta_hp: float = 0.0  # User override (+ = removed accessories)

    def total_parasitic_w(self, rpm_fraction: float) -> float:
        """Total parasitic power draw (W) at given RPM fraction (0-1)."""
        total = 0.0
        if self.alternator_present:
            total += self.alternator_power_w
        if not self.water_pump_electric:
            total += 350.0 * rpm_fraction  # Scales with RPM
        total += self.oil_pump_power_w * rpm_fraction
        total += self.valve_train_power_w * rpm_fraction
        total -= self.parasitic_delta_hp * 745.7  # User override
        return max(0.0, total)


# ═══════════════════════════════════════════
# 13. STAGING & LAUNCH
# ═══════════════════════════════════════════


@dataclass
class StagingParams:
    """Staging procedure and launch setup."""

    staging_type: str = STAGING_SHALLOW
    rollout_distance_mm: float = 350.0  # Distance before clock starts
    launch_rpm: float = 8000.0  # Two-step hold RPM
    prespool_boost_bar: float = 0.0  # Boost at staging
    reaction_time_ms: float = 300.0  # Human RT
    vehicle_response_ms: float = 50.0  # ECU + fuel + ignition lag
    tree_type: str = "pro"  # pro (0.400s) / sportsman (0.500s)
    two_step: bool = False  # Two-step rev limiter

    @property
    def rollout_m(self) -> float:
        return self.rollout_distance_mm / 1000.0


# ═══════════════════════════════════════════
# 14. ENVIRONMENT
# ═══════════════════════════════════════════


@dataclass
class EnvironmentParams:
    """Atmospheric and track conditions."""

    venue_name: str = "Aamby Valley (TVR)"
    altitude_m: float = 679.0  # Venue altitude
    ambient_temp_c: float = 22.0  # Air temperature
    relative_humidity_pct: float = 40.0  # RH
    barometric_pressure_hpa: float = 1013.25  # Station pressure (sea level ref)
    wind_speed_ms: float = 0.0  # Total wind speed
    wind_direction_deg: float = 0.0  # 0 = headwind, 180 = tailwind
    track_surface: str = "asphalt"  # concrete / asphalt / prepped
    track_temp_c: float = 30.0  # Surface temperature
    track_prep: str = TRACK_NONE  # Prep compound
    track_prep_passes: int = 0  # Freshness
    track_heading_deg: float = 0.0  # Track direction for wind calc
    track_gradient_pct: float = 0.0  # % grade (positive = uphill)

    def air_density(self) -> float:
        """Compute air density from altitude, temp, humidity using barometric formula."""
        T_K = self.ambient_temp_c + 273.15
        # Pressure at altitude (barometric formula)
        P_sea = self.barometric_pressure_hpa * 100.0  # Pa
        g = 9.80665
        M = 0.0289644  # kg/mol (dry air)
        R = 8.31447
        L = 0.0065  # Lapse rate K/m
        # Pressure at altitude
        P_alt = P_sea * (1.0 - L * self.altitude_m / 288.15) ** (g * M / (R * L))
        # Humidity correction (water vapor is lighter than dry air)
        # Saturation vapor pressure (August-Roche-Magnus)
        e_sat = 610.78 * np.exp(
            17.27 * self.ambient_temp_c / (self.ambient_temp_c + 237.3)
        )
        e = e_sat * self.relative_humidity_pct / 100.0
        # Virtual temperature correction
        T_virtual = T_K / (1.0 - 0.378 * e / P_alt)
        # Air density
        rho = P_alt / (287.058 * T_virtual)
        return rho

    def density_altitude_ft(self) -> float:
        """Compute density altitude in feet."""
        rho = self.air_density()
        rho_sl = 1.225  # Sea level standard density
        # DA = 44330 * (1 - (rho/rho_sl)^0.234969)
        if rho <= 0:
            return 0.0
        da_m = 44330.0 * (1.0 - (rho / rho_sl) ** 0.234969)
        return da_m * 3.28084

    def headwind_component(self) -> float:
        """Headwind component along track (m/s). Positive = opposing motion."""
        # Wind direction 0 = directly opposing (headwind), 180 = tailwind
        angle_rad = np.radians(self.wind_direction_deg - self.track_heading_deg)
        return self.wind_speed_ms * np.cos(angle_rad)

    def crosswind_component(self) -> float:
        """Crosswind component perpendicular to track (m/s)."""
        angle_rad = np.radians(self.wind_direction_deg - self.track_heading_deg)
        return abs(self.wind_speed_ms * np.sin(angle_rad))


# ═══════════════════════════════════════════
# MASTER CONFIGURATION
# ═══════════════════════════════════════════


@dataclass
class BikeConfig:
    """Complete motorcycle configuration — all parameters in one place."""

    name: str = "Generic Litre-Class"
    # Canonical category tag for dispatch into category-flavoured sub-models.
    # Values are defined in motoquant.category_profiles (string constants).
    # When None / "unknown", the legacy pre-April-30 hard-coded physics
    # behaviour is preserved (backwards-compat anchor).
    category_tag: str | None = None
    chassis: ChassisParams = field(default_factory=ChassisParams)
    engine: EngineParams = field(default_factory=EngineParams)
    forced_induction: ForcedInductionParams = field(
        default_factory=ForcedInductionParams
    )
    drivetrain: DrivetrainParams = field(default_factory=DrivetrainParams)
    clutch: ClutchParams = field(default_factory=ClutchParams)
    tires: TireParams = field(default_factory=TireParams)
    aero: AeroParams = field(default_factory=AeroParams)
    suspension: SuspensionParams = field(default_factory=SuspensionParams)
    braking: BrakingParams = field(default_factory=BrakingParams)
    wheelie: WheelieParams = field(default_factory=WheelieParams)
    rider: RiderParams = field(default_factory=RiderParams)
    parasitic: ParasiticParams = field(default_factory=ParasiticParams)
    staging: StagingParams = field(default_factory=StagingParams)
    environment: EnvironmentParams = field(default_factory=EnvironmentParams)
