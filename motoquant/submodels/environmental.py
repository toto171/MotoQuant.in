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

import math
from ..models import BikeConfig

# ── Track surface grip multipliers (baseline, no prep compound) ──────────────
# Values are relative to clean dry asphalt = 1.00
_SURFACE_GRIP: dict = {
    "asphalt":   1.00,
    "concrete":  0.94,   # slightly less bite on concrete
    "prepped":   1.18,   # track prep compound on asphalt
    "wet":       0.55,   # rain
    "damp":      0.72,
    "dusty":     0.80,
}

# ── Track surface rolling-resistance multipliers ──────────────────────────────
_SURFACE_RR: dict = {
    "asphalt":   1.00,
    "concrete":  1.05,
    "prepped":   0.97,
    "wet":       1.15,
    "damp":      1.08,
    "dusty":     1.12,
}

# ── Power correction denominator at standard conditions (ISO 1585) ────────────
_RHO_SL_STD = 1.2250   # kg/m³  (sea level, 15 °C, 0 % RH)


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
        # Naturally aspirated: power ∝ ρ / ρ_std
        # Forced induction: boost compensates for density loss; apply a floor
        if not cfg.forced_induction.is_boosted:
            self.power_correction: float = self.rho / _RHO_SL_STD
        else:
            # Boosted engines still lose a little at extreme DA
            self.power_correction = max(0.97, self.rho / _RHO_SL_STD)

        # Informational: % power lost relative to sea level standard
        self.da_power_loss_pct: float = max(0.0, (1.0 - self.power_correction) * 100.0)

        # ── Wind ─────────────────────────────────────────────────────────────
        self.v_headwind: float = env.headwind_component()
        self.v_crosswind: float = env.crosswind_component()

        # ── Track surface ────────────────────────────────────────────────────
        surface = env.track_surface.lower().strip()
        self.grip_multiplier: float = _SURFACE_GRIP.get(surface, 1.00)
        self.rr_multiplier: float   = _SURFACE_RR.get(surface, 1.00)

        # ── Tyre launch-temperature adjustment ───────────────────────────────
        # Cold ambient → tyre stays cooler longer → slightly less grip early
        # This is a small correction; main tyre thermal is in TireModel.
        t_ref = 25.0  # reference ambient (°C)
        dt = env.ambient_temp_c - t_ref
        # +0.5 % grip per °C warmer (within ±20 °C of reference)
        dt_clamped = max(-20.0, min(20.0, dt))
        self.ambient_temp_grip_delta: float = dt_clamped * 0.005

        # Cache ambient for downstream models
        self.ambient_temp_c: float  = env.ambient_temp_c
        self.track_temp_c: float    = env.track_temp_c

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
            "rho_kg_m3":         round(self.rho, 4),
            "density_alt_ft":    round(self.density_alt_ft, 0),
            "power_correction":  round(self.power_correction, 4),
            "da_power_loss_pct": round(self.da_power_loss_pct, 2),
            "v_headwind_ms":     round(self.v_headwind, 2),
            "v_crosswind_ms":    round(self.v_crosswind, 2),
            "grip_multiplier":   round(self.total_grip_multiplier(), 4),
            "rr_multiplier":     round(self.rr_multiplier, 4),
            "ambient_temp_c":    self.ambient_temp_c,
            "track_temp_c":      self.track_temp_c,
        }
