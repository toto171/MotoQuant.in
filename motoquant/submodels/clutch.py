"""
Sub-Model 4: Clutch
=====================
Lockup, slider (centrifugal), and multi-stage clutch engagement.
Computes transmitted torque and heat generation.
"""

import numpy as np
from typing import Tuple

from ..constants import RADS_TO_RPM
from ..models import BikeConfig, CLUTCH_LOCKUP, CLUTCH_SLIDER, CLUTCH_MULTISTAGE


class ClutchModel:
    """Clutch engagement and thermal model."""

    def __init__(self, cfg: BikeConfig, engine_torque_fn):
        self.cfg = cfg
        self._engine_torque = engine_torque_fn  # callback for slider clutch

    def torque(self, omega_e: float, omega_input: float,
               T_clutch_temp: float, t: float) -> Tuple[float, float]:
        """
        Returns (torque transmitted, heat generated in W).
        omega_e = engine speed, omega_input = gearbox input speed.
        """
        cl = self.cfg.clutch
        slip = omega_e - omega_input

        if cl.clutch_type == CLUTCH_LOCKUP:
            if abs(slip) < 5.0:
                return 1e6, 0.0
            T_max = cl.max_torque()
            if T_clutch_temp > cl.fade_temp_c:
                fade = max(0.3, 1.0 - 0.003 * (T_clutch_temp - cl.fade_temp_c))
                T_max *= fade
            T_transmitted = T_max * np.sign(slip)
            Q = abs(T_transmitted * slip)
            return T_transmitted, Q

        elif cl.clutch_type == CLUTCH_SLIDER:
            rpm_e = omega_e * RADS_TO_RPM
            if rpm_e < cl.engage_rpm:
                return 0.0, 0.0
            k_slider = cl.spring_preload_n / max(1.0, (self.cfg.engine.redline_rpm - cl.engage_rpm) ** 2)
            F_clamp = k_slider * (rpm_e - cl.engage_rpm) ** 2 + cl.spring_preload_n * 0.1
            n_surfaces = 2 * cl.plate_count
            T_max = n_surfaces * cl.mu_static * F_clamp * cl.mean_radius_m
            if abs(slip) < 5.0:
                return 1e6, 0.0
            T_transmitted = min(T_max, abs(self._engine_torque(rpm_e, t) * 1.5)) * np.sign(slip)
            Q = abs(T_transmitted * slip)
            return T_transmitted, Q

        elif cl.clutch_type == CLUTCH_MULTISTAGE:
            rpm_e = omega_e * RADS_TO_RPM
            F_spring = cl.spring_preload_n
            k_cent = cl.spring_preload_n / max(1.0, (self.cfg.engine.redline_rpm - cl.engage_rpm) ** 2)
            F_cent = k_cent * max(0.0, rpm_e - cl.engage_rpm) ** 2 if rpm_e > cl.engage_rpm else 0.0
            F_total = F_spring + F_cent
            n_surfaces = 2 * cl.plate_count
            T_max = n_surfaces * cl.mu_static * F_total * cl.mean_radius_m
            if abs(slip) < 5.0:
                return 1e6, 0.0
            T_transmitted = T_max * np.sign(slip)
            Q = abs(T_transmitted * slip)
            return T_transmitted, Q

        return 1e6, 0.0
