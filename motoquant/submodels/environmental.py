"""
Sub-Model 15: Environmental Corrections
=========================================
Consolidates all ambient-condition effects that modulate the simulation:

  • Air density (ρ) from altitude, temperature, humidity — already computed
    in EnvironmentParams.air_density(); this model caches it and provides
    the derived corrections in a single place.

  • Density-altitude penalty — summarised as a fractional power loss factor
    (SAE J1349 / NACA TN 1135 style).

  • Track surface grip baseline — rolling-resistance and friction multipliers
    for asphalt / concrete / prepped / wet surfaces.

  • Ambient temperature effect on tyre warm-up rate and launch grip.

  • Wind headwind / tailwind / crosswind correction (delegated to
    EnvironmentParams.headwind_component() but surfaced here for convenience).

All values are computed once at construction and are read-only during the
simulation loop.
"""

from ..models import BikeConfig

# ── Track surface grip multipliers (baseline, no prep compound) ──────────────
# Values are relative to clean dry asphalt = 1.00
_SURFACE_GRIP: dict = {
    "asphalt": 1.00,
    # Every "concrete" venue in the catalog (Santa Pod / Pomona / Gainesville /
    # Sydney Dragway) is a prepped NHRA/FIA-style concrete launch pad, not raw
    # highway concrete — those strips bite HARDER than street asphalt, so the
    # factor is >1.0. (An unprepped-concrete road would be ~0.94, but no such
    # venue exists here, and track_surface is fed only from venue.surface_type.)
    "concrete": 1.03,
    "prepped": 1.18,  # track prep compound on asphalt
    "wet": 0.55,  # rain
    "damp": 0.72,
    "dusty": 0.80,
    # ── Land speed record surfaces ──
    "salt": 0.62,  # Bonneville / Uyuni — wet salt = lower μ, gets worse late season
    "dry_lake_bed": 0.70,  # El Mirage — cracked playa, more bite than salt
}

# ── Track surface rolling-resistance multipliers ──────────────────────────────
_SURFACE_RR: dict = {
    "asphalt": 1.00,
    "concrete": 1.05,
    "prepped": 0.97,
    "wet": 1.15,
    "damp": 1.08,
    "dusty": 1.12,
    # ── Land speed record surfaces ──
    "salt": 1.35,  # Bonneville / Uyuni — salt crust absorbs energy
    "dry_lake_bed": 1.20,  # El Mirage — mild crust resistance
}

# ── Power correction denominator at standard conditions (ISO 1585) ────────────
_RHO_SL_STD = 1.2250  # kg/m³  (sea level, 15 °C, 0 % RH)

# ── Reference-anchored SAE J1349 power scaling ────────────────────────────────
# Brake power scales with DRY-air pressure and ~sqrt(absolute inlet temperature)
# (SAE J1349: CF = (99/Pd)·sqrt(Tm/298)); a density (P/T) scaling would count the
# temperature effect twice.  The absolute level at the reference day (the catalog
# calibration day: 0 m, 25 °C, 50 % RH, 1013.25 hPa) is the calibration constant
# K_ref = rho_ref / 1.225, so that day reproduces the catalog power exactly and
# only departures from it follow the SAE exponents.
_REF_TEMP_C = 25.0
_REF_RH_PCT = 50.0
_REF_ALT_M = 0.0
_REF_PRESSURE_HPA = 1013.25


def _reference_environment():
    from ..models import EnvironmentParams

    return EnvironmentParams(
        altitude_m=_REF_ALT_M,
        ambient_temp_c=_REF_TEMP_C,
        relative_humidity_pct=_REF_RH_PCT,
        barometric_pressure_hpa=_REF_PRESSURE_HPA,
    )


def sae_power_correction(env) -> float:
    """Engine power multiplier for ``env``: K_ref · (Pd/Pd_ref) · sqrt(T_ref/T).

    Equals ``rho_ref / 1.225`` on the reference day.  Single source for the
    simulation and for the weather/venue "power correction factor".
    """
    ref = _reference_environment()
    k_ref = ref.air_density() / _RHO_SL_STD
    t_ratio = (ref.ambient_temp_c + 273.15) / (env.ambient_temp_c + 273.15)
    return (
        k_ref * (env.dry_air_pressure_pa() / ref.dry_air_pressure_pa()) * t_ratio**0.5
    )


class EnvironmentalModel:
    """
    Pre-computes all ambient corrections needed by the physics loop.

    Attributes (read-only after construction)
    ─────────────────────────────────────────
    rho             : float — air density (kg/m³)
    density_alt_ft  : float — density altitude (ft)
    power_correction: float — multiplicative engine-power correction [0–1]
    v_headwind      : float — headwind component (m/s), positive = opposing
    grip_multiplier : float — track surface grip factor
    rr_multiplier   : float — rolling-resistance surface factor
    da_power_loss_pct: float — percentage power lost due to DA (informational)
    """

    def __init__(self, cfg: BikeConfig):
        env = cfg.environment

        # ── Air density ──────────────────────────────────────────────────────
        self.rho: float = env.air_density()

        # ── Density altitude ─────────────────────────────────────────────────
        self.density_alt_ft: float = env.density_altitude_ft()

        # ── Engine power correction ──────────────────────────────────────────
        # Naturally aspirated: SAE J1349 scaling (dry-air pressure, sqrt(T)),
        # anchored on the catalog reference day (see sae_power_correction).
        # Forced induction: boost compensates for density loss; apply a floor
        if not cfg.forced_induction.is_boosted:
            self.power_correction: float = sae_power_correction(env)
        else:
            # Boosted engines still lose a little at extreme DA
            self.power_correction = max(0.97, sae_power_correction(env))

        # Informational: % power lost relative to sea level standard
        self.da_power_loss_pct: float = max(0.0, (1.0 - self.power_correction) * 100.0)

        # ── Wind ─────────────────────────────────────────────────────────────
        self.v_headwind: float = env.headwind_component()
        self.v_crosswind: float = env.crosswind_component()

        # ── Track surface ────────────────────────────────────────────────────
        surface = env.track_surface.lower().strip()
        self.grip_multiplier: float = _SURFACE_GRIP.get(surface, 1.00)
        self.rr_multiplier: float = _SURFACE_RR.get(surface, 1.00)

        # ── Tyre launch-temperature adjustment ───────────────────────────────
        # Cold ambient → tyre stays cooler longer → slightly less grip early
        # This is a small correction; main tyre thermal is in TireModel.
        t_ref = 25.0  # reference ambient (°C)
        dt = env.ambient_temp_c - t_ref
        # +0.5 % grip per °C warmer (within ±20 °C of reference)
        dt_clamped = max(-20.0, min(20.0, dt))
        self.ambient_temp_grip_delta: float = dt_clamped * 0.005

        # Cache ambient for downstream models
        self.ambient_temp_c: float = env.ambient_temp_c
        self.track_temp_c: float = env.track_temp_c

    # ─────────────────────────────────────────
    # CONVENIENCE METHODS
    # ─────────────────────────────────────────

    def total_grip_multiplier(self) -> float:
        """
        Combined grip multiplier: surface type × ambient temperature effect.
        Used as an additional scale factor on top of TireModel's Pacejka/thermal.
        """
        return self.grip_multiplier * (1.0 + self.ambient_temp_grip_delta)

    def drag_density_factor(self) -> float:
        """
        ρ / ρ_SL_STD — multiplier for aerodynamic drag force.
        Lower density = less drag (but also less engine power).
        """
        return self.rho / _RHO_SL_STD

    def summary(self) -> dict:
        """Return key environmental conditions as a plain dict (for CLI display)."""
        return {
            "rho_kg_m3": round(self.rho, 4),
            "density_alt_ft": round(self.density_alt_ft, 0),
            "power_correction": round(self.power_correction, 4),
            "da_power_loss_pct": round(self.da_power_loss_pct, 2),
            "v_headwind_ms": round(self.v_headwind, 2),
            "v_crosswind_ms": round(self.v_crosswind, 2),
            "grip_multiplier": round(self.total_grip_multiplier(), 4),
            "rr_multiplier": round(self.rr_multiplier, 4),
            "ambient_temp_c": self.ambient_temp_c,
            "track_temp_c": self.track_temp_c,
        }
