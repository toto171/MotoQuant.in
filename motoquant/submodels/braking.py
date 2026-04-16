"""
Sub-Model 9: Braking
======================
Maximum braking deceleration with iterative weight transfer.
Not used in acceleration simulation, available for future modes.
"""

from ..models import BikeConfig


class BrakingModel:
    """Braking deceleration model."""

    def __init__(self, cfg: BikeConfig, N_f_static: float, N_r_static: float):
        self.cfg = cfg
        self.N_f_static = N_f_static
        self.N_r_static = N_r_static

    def max_decel(self, v: float, m_total: float) -> float:
        """Maximum braking deceleration (m/s2) at given speed."""
        h = self.cfg.chassis.cog_height_m
        L = self.cfg.chassis.wheelbase_m
        mu_front = 1.2
        mu_rear = 1.0
        a_est = 10.0
        for _ in range(5):
            N_f = self.N_f_static + m_total * a_est * h / L
            N_r = self.N_r_static - m_total * a_est * h / L
            N_r = max(0.0, N_r)
            F_brake = mu_front * N_f + mu_rear * N_r
            a_est = F_brake / m_total
        return a_est
