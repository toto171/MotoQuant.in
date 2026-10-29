"""
Sub-Model 6: Tire Forces
==========================
Pacejka Magic Formula + thermal grip + load sensitivity +
pressure-from-temperature + centrifugal growth + track prep.
"""

import math
import re

import numpy as np

from ..constants import (
    CONV_H_COEFF,
    CONV_H_EXP,
    CONV_H_STILL_AIR,
    DEFAULT_TREAD_WIDTH_M,
    ROAD_THERMAL_EFFUSIVITY,
    TREAD_RUBBER_DENSITY_KGM3,
)
from ..models import BikeConfig

_METRIC_WIDTH_RE = re.compile(r"^\s*(\d{2,3})\s*/")
_INCH_WIDTH_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-")


def tread_section_width_m(size: str | None) -> float:
    """Section width (m) from a tyre size string: metric ``190/50-17`` /
    ``180/55ZR17`` (mm) or inch bias-ply ``3.50-18`` (in). Unparseable →
    ``constants.DEFAULT_TREAD_WIDTH_M``."""
    if size:
        m = _METRIC_WIDTH_RE.match(str(size))
        if m:
            return float(m.group(1)) / 1000.0
        m = _INCH_WIDTH_RE.match(str(size))
        if m and float(m.group(1)) < 10.0:
            return float(m.group(1)) * 0.0254
    return DEFAULT_TREAD_WIDTH_M


def tread_heat_partition(thermal_conductivity: float, specific_heat: float) -> float:
    """Blok heat-partition share of contact-patch friction heat that enters
    the tread (constants.py): e_tread / (e_tread + e_road)."""
    e_tread = math.sqrt(
        max(0.0, thermal_conductivity * TREAD_RUBBER_DENSITY_KGM3 * specific_heat)
    )
    return e_tread / (e_tread + ROAD_THERMAL_EFFUSIVITY)


class TireModel:
    """Tire grip, thermal, and geometry model."""

    def __init__(self, cfg: BikeConfig, mu_prep: float, T_tire_ref_K: float):
        self.cfg = cfg
        self.mu_prep = mu_prep
        self.T_tire_ref_K = T_tire_ref_K
        tire = cfg.tires
        # Heat balance geometry / partition (2026-10 epoch round 2).
        self.heat_partition = tread_heat_partition(
            tire.thermal_conductivity, tire.specific_heat_rubber
        )
        self.conv_area_m2 = (
            2.0
            * math.pi
            * tire.rear_rolling_radius_m
            * tread_section_width_m(tire.rear_size)
        )

    def friction_coeff(self, N_rear: float, T_tire: float, v: float) -> float:
        """
        Effective friction coefficient at the rear tire contact patch.
        Includes: Pacejka peak, load sensitivity, thermal, pressure-from-temp, track prep.
        """
        tire = self.cfg.tires
        mu_base = tire.mu_peak
        # Load sensitivity
        mu_load = mu_base * (1.0 - tire.load_sensitivity_k * N_rear)
        mu_load = max(0.3, mu_load)
        # Thermal modifier
        sigma_T = 25.0
        T_opt = tire.optimal_temp_c
        thermal_factor = np.exp(-(((T_tire - T_opt) / sigma_T) ** 2))
        if T_tire > tire.reversion_temp_c:
            reversion_penalty = 1.0 - 0.01 * (T_tire - tire.reversion_temp_c)
            thermal_factor *= max(0.3, reversion_penalty)
        mu_thermal = mu_load * (0.85 + 0.15 * thermal_factor)
        # Tire pressure from temperature (Gay-Lussac)
        T_tire_K = T_tire + 273.15
        P_ratio = T_tire_K / max(self.T_tire_ref_K, 250.0)
        pressure_grip_factor = min(1.0, (1.0 / max(P_ratio, 1.0)) ** 0.3)
        mu_pressure = mu_thermal * pressure_grip_factor
        # Track prep
        mu_final = mu_pressure * self.mu_prep
        return mu_final

    def max_force(self, N_rear: float, T_tire: float, v: float) -> float:
        """Maximum longitudinal force the rear tire can deliver (N)."""
        mu = self.friction_coeff(N_rear, T_tire, v)
        return mu * N_rear

    def pacejka_force(self, slip_ratio: float, N_rear: float, T_tire: float) -> float:
        """Pacejka Magic Formula: longitudinal force as function of slip ratio."""
        tire = self.cfg.tires
        mu = self.friction_coeff(N_rear, T_tire, 0.0)
        D = mu * N_rear
        B = tire.pacejka_B
        C = tire.pacejka_C
        E = tire.pacejka_E
        x = B * slip_ratio
        F = D * np.sin(C * np.arctan(x - E * (x - np.arctan(x))))
        return F

    def thermal_rate(
        self,
        F_x: float,
        v: float,
        slip_ratio: float,
        T_tire: float,
        T_ambient: float,
        Q_rolling: float = 0.0,
    ) -> float:
        """dT_tire/dt -- rate of temperature change of the tire surface (C/s).

        Heat balance:
          Q_in   = beta × |F_x| × |v_slip|     (slip heat; Blok partition
                                               beta into the tread, the rest
                                               goes into the road)
                 + Q_rolling                   (the rear tyre's share of the
                                               rolling-resistance work: the
                                               hysteresis that IS rolling
                                               resistance ends up as tyre heat)
          Q_conv = h(v) × A_tread × (T_tire − T_air)
                   (McAdams forced convection over the tread band)
          Q_cond = k × A × (T_tire − T_road) / Δx   (conduction to road)

        2026-10 epoch round 2: the tread used to receive ALL the slip heat
        and shed it through h = 10 + 0.5 v over a fixed 0.15 m², so a
        bike holding speed for 30 s (top-speed mode) ran its tyre to
        400-570 °C. See constants.py (TYRE HEAT BALANCE) for the sources.

        Kaizen fix (April 2026): the old formula computed
        ``k × A × (T_tire − (T_tire − 5.0)) / 0.005`` which simplifies to a
        constant 5 K ΔT regardless of actual temperatures — a silent bug
        that made road conduction temperature-independent.  Now uses
        ``T_road ≈ T_ambient + 5 °C`` (track surface is typically warmer
        than ambient by a few °C in Indian track conditions).
        """
        tire = self.cfg.tires
        v_slip = abs(v * slip_ratio)
        Q_friction = self.heat_partition * (abs(F_x) * v_slip)
        h_conv = max(CONV_H_STILL_AIR, CONV_H_COEFF * abs(v) ** CONV_H_EXP)
        Q_conv = h_conv * self.conv_area_m2 * (T_tire - T_ambient)
        # Road-surface temperature proxy.  If the config carries an explicit
        # track_temp_c on env, use it; otherwise fall back to ambient+5.
        env = getattr(self.cfg, "environment", None)
        T_road = getattr(env, "track_temp_c", None) if env is not None else None
        if T_road is None:
            T_road = T_ambient + 5.0
        # Conduction through ~5 mm of rubber to the road surface.
        Q_cond = (
            tire.thermal_conductivity
            * (tire.contact_patch_cm2 * 1e-4)
            * (T_tire - T_road)
            / 0.005
        )
        dT = (Q_friction + Q_rolling - Q_conv - Q_cond) / max(
            1.0, tire.tread_mass_kg * tire.specific_heat_rubber
        )
        return dT

    def effective_radius(self, omega_w: float) -> float:
        """Effective rolling radius including centrifugal growth (m)."""
        return self.cfg.tires.effective_radius(omega_w)
