"""
Sub-Model 8: Weight Transfer
==============================
Instantaneous front/rear normal load computation.
Includes static distribution, acceleration transfer,
aero lift, rider CoG offset, and anti-squat geometry.

2026-10 epoch round 2: the load transfer acts at the COMBINED bike + rider
centre of mass (submodels/cog.py), the same point the wheelie limit uses —
and includes the pitch moment of aerodynamic drag, taken to act at that
height (a modelling assumption: a tucked rider + bike's centre of pressure
sits close to the CoG height). The drag moment transfers F_drag * h / L onto
the rear tyre: at 240 km/h on a litre bike that is ~350 N of rear load the
old net-acceleration-only transfer never counted, which is what left 200 hp
bikes traction-limited at top-gear speeds.
"""

from ..constants import G
from ..models import BikeConfig
from .cog import system_cog


class WeightTransferModel:
    """Weight transfer and normal load computation."""

    def __init__(self, cfg: BikeConfig, anti_squat_frac: float, aero_model):
        self.cfg = cfg
        self.anti_squat_frac = anti_squat_frac
        self.aero = aero_model
        # Geometry (system CoG)
        cog = system_cog(cfg)
        self.L = cog.wheelbase_m
        self.h = cog.height_m
        self.L_f = cog.l_f_m
        self.rider_shift_frac = cog.rider_shift_frac

    def compute(
        self, accel: float, v: float, t: float, m_total: float, F_aero: float = 0.0
    ):
        """
        Compute instantaneous front and rear normal loads (N).
        ``F_aero`` is this step's aerodynamic drag (N; 0 = standing start).
        Returns (N_front, N_rear).
        """
        h = self.h
        L = self.L
        rider_offset = self.cfg.rider.cog_offset(t) * self.rider_shift_frac
        L_f_eff = self.L_f - rider_offset
        L_r_eff = L - L_f_eff
        # Static loads
        N_f_static = m_total * G * L_r_eff / L
        N_r_static = m_total * G * L_f_eff / L
        # Acceleration + drag-moment weight transfer
        delta_N = (m_total * accel * h + F_aero * h) / L
        # Anti-squat correction
        anti_squat_boost = 1.0 + (self.anti_squat_frac - 1.0) * 0.15
        delta_N *= anti_squat_boost
        # Aero lift
        F_lift = self.aero.lift(v)
        N_f = N_f_static - delta_N - F_lift * 0.4
        N_r = N_r_static + delta_N - F_lift * 0.6
        return max(0.0, N_f), max(0.0, N_r)
