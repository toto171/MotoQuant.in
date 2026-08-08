"""
Sub-Model 8: Weight Transfer
==============================
Instantaneous front/rear normal load computation.
Includes static distribution, acceleration transfer,
aero lift, rider CoG offset, and anti-squat geometry.
"""

from ..constants import G
from ..models import BikeConfig


class WeightTransferModel:
    """Weight transfer and normal load computation."""

    def __init__(self, cfg: BikeConfig, anti_squat_frac: float, aero_model):
        self.cfg = cfg
        self.anti_squat_frac = anti_squat_frac
        self.aero = aero_model
        # Geometry
        self.L = cfg.chassis.wheelbase_m
        self.h = cfg.chassis.cog_height_m
        self.L_f = cfg.chassis.L_f

    def compute(self, accel: float, v: float, t: float, m_total: float):
        """
        Compute instantaneous front and rear normal loads (N).
        Returns (N_front, N_rear).
        """
        h = self.h
        L = self.L
        rider_offset = self.cfg.rider.cog_offset(t)
        L_f_eff = self.L_f - rider_offset
        L_r_eff = L - L_f_eff
        # Static loads
        N_f_static = m_total * G * L_r_eff / L
        N_r_static = m_total * G * L_f_eff / L
        # Acceleration weight transfer
        delta_N = m_total * accel * h / L
        # Anti-squat correction
        anti_squat_boost = 1.0 + (self.anti_squat_frac - 1.0) * 0.15
        delta_N *= anti_squat_boost
        # Aero lift
        F_lift = self.aero.lift(v)
        N_f = N_f_static - delta_N - F_lift * 0.4
        N_r = N_r_static + delta_N - F_lift * 0.6
        return max(0.0, N_f), max(0.0, N_r)
