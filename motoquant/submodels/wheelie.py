"""
Sub-Model 10: Wheelie Control
===============================
Maximum acceleration before front wheel lift-off.
Includes rider offset, aero lift, gyroscopic correction,
and wheelie bar extension.

2026-10 epoch round 2: the limit acts at the COMBINED bike + rider centre of
mass (submodels/cog.py) — the bike-only ``chassis.cog_height_mm`` put the
ceiling at ~1.35-1.5 g, so it never bound and litre launches were (wrongly)
traction-limited instead. The rider's lean moves only the rider's share of
the mass. Aerodynamic drag, taken to act at the system CoG height (the
centre of pressure of a tucked rider + bike sits close to it — a modelling
assumption), adds its pitch-up moment F_drag * h, lowering the ceiling by
F_drag / m at speed.
"""

from ..constants import G
from ..models import BikeConfig
from .cog import system_cog


class WheelieModel:
    """Wheelie threshold computation."""

    def __init__(self, cfg: BikeConfig, aero_model):
        self.cfg = cfg
        self.aero = aero_model
        cog = system_cog(cfg)
        self.L = cog.wheelbase_m
        self.h = cog.height_m
        self.L_f = cog.l_f_m
        self.rider_shift_frac = cog.rider_shift_frac

    def max_accel(
        self, v: float, t: float, m_total: float, F_aero: float = 0.0
    ) -> float:
        """Maximum acceleration before front wheel lifts off (m/s2).

        ``F_aero`` is the aerodynamic drag acting on the bike this step (N);
        callers that omit it get the zero-drag (standing-start) ceiling.
        """
        L = self.L
        h = self.h
        rider_offset = self.cfg.rider.cog_offset(t) * self.rider_shift_frac
        L_f_eff = self.L_f - rider_offset
        L_r_eff = L - L_f_eff

        a_wheelie = G * L_r_eff / h

        # Aero lift correction
        F_lift = self.aero.lift(v)
        if m_total > 0:
            a_wheelie -= F_lift * 0.4 / (m_total * h / L)
            # Drag pitch moment (centre of pressure at the CoG height).
            a_wheelie -= F_aero / m_total

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
