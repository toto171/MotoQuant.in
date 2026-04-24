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
        """Maximum braking deceleration (m/s2) at given speed.

        Uses the actual tire peak friction coefficient from the config
        (``cfg.tires.mu_peak``) rather than hardcoded defaults.  Kaizen
        fix (April 2026): the old model had ``mu_front = 1.2`` and
        ``mu_rear = 1.0`` baked in, so a bike on CEAT Zoom Rad (mu ≈ 1.05)
        produced the same braking deceleration as a bike on Pirelli Diablo
        Supercorsa SP (mu ≈ 1.45) — a 40% mismatch that was invisible.
        Front tires typically carry slightly more braking load so we bias
        mu_front up 5% (a reasonable approximation: braking transfers
        weight forward, front tire runs at ideal slip while rear unloads).
        """
        h = self.cfg.chassis.cog_height_m
        L = self.cfg.chassis.wheelbase_m
        mu_peak = getattr(self.cfg.tires, "mu_peak", 1.1)
        mu_front = mu_peak * 1.05  # front carries most braking load
        mu_rear = mu_peak * 0.90  # rear unloads under deceleration
        a_est = 10.0
        for _ in range(5):
            N_f = self.N_f_static + m_total * a_est * h / L
            N_r = self.N_r_static - m_total * a_est * h / L
            N_r = max(0.0, N_r)
            F_brake = mu_front * N_f + mu_rear * N_r
            a_est = F_brake / m_total
        return a_est
