"""
Sub-Model 10: Wheelie Control
===============================
Maximum acceleration before front wheel lift-off.
Includes rider offset, aero lift, gyroscopic correction,
and wheelie bar extension.
"""

from ..constants import G
from ..models import BikeConfig


class WheelieModel:
    """Wheelie threshold computation."""

    def __init__(self, cfg: BikeConfig, aero_model):
        self.cfg = cfg
        self.aero = aero_model
        self.L = cfg.chassis.wheelbase_m
        self.h = cfg.chassis.cog_height_m
        self.L_f = cfg.chassis.L_f

    def max_accel(self, v: float, t: float, m_total: float) -> float:
        """Maximum acceleration before front wheel lifts off (m/s2)."""
        L = self.L
        h = self.h
        rider_offset = self.cfg.rider.cog_offset(t)
        L_f_eff = self.L_f - rider_offset
        L_r_eff = L - L_f_eff

        a_wheelie = G * L_r_eff / h

        # Aero lift correction
        F_lift = self.aero.lift(v)
        if m_total > 0:
            a_wheelie -= F_lift * 0.4 / (m_total * h / L)

        # Gyroscopic correction
        if not self.cfg.engine.counter_rotating:
            a_wheelie *= 0.985
        else:
            a_wheelie *= 1.01

        # Wheelie bar
        if self.cfg.wheelie.wheelie_bar:
            bar_ext = self.cfg.wheelie.bar_length_mm / 1000.0
            a_wheelie_bar = G * (L_r_eff + bar_ext) / h
            a_wheelie = max(a_wheelie, a_wheelie_bar)

        return a_wheelie
