"""
Sub-Model 13: Rider Dynamics
=============================
Models the physical effect of the rider on the motorcycle during a drag run:

  • Dynamic CoG shift — forward lean at launch transitions to race tuck over
    tuck_transition_time_s.  Shifts the static front/rear weight split and
    reduces the effective CoG height, both suppressing wheelie tendency.

  • Aerodynamic contribution — rider body frontal area and drag coefficient
    vary with position (upright staging stance → tuck).

All outputs are deltas / overrides consumed by WeightTransferModel and
AeroModel; this module does NOT duplicate their logic.
"""

import math

from ..models import BikeConfig


class RiderDynamicsModel:
    """
    Encapsulates how rider body movement influences weight distribution
    and aerodynamic drag during a drag run.

    Usage in physics loop
    ─────────────────────
    At each timestep *t* (seconds since lights-out):

        cog_x_shift, cog_h_delta = rider.cog_shift(t)
        # cog_x_shift  : signed offset (m) from nominal CoG along wheelbase.
        #                Positive → toward front axle.
        # cog_h_delta  : change in combined CoG height (m). Negative in tuck.

        cd_a_rider = rider.cd_a(t)
        # Full rider+bike Cd*A to use for aero drag this timestep.
    """

    def __init__(self, cfg: BikeConfig):
        self.cfg = cfg
        r = cfg.rider
        c = cfg.chassis

        # Rider mass fraction of total
        self.m_rider = r.mass_kg + r.gear_mass_kg
        self.m_total = c.total_mass_kg  # bike + rider + fluids

        # Nominal (static/tuck) combined CoG height — from ChassisParams
        self.h_nominal = c.cog_height_m  # metres

        # Rider CoG height change between upright staging and full tuck.
        # Heuristic: rider lowers CoG by ~15 % of their seated height when
        # going from upright to full race tuck.
        seated_h_m = r.cog_height_seated_mm / 1000.0
        self._rider_upright_h = seated_h_m
        self._rider_tuck_h = seated_h_m * 0.85  # 15 % reduction in tuck

        # Forward lean at launch
        self._launch_shift_m = r.launch_forward_shift_mm / 1000.0
        self._transition_s = max(0.01, r.tuck_transition_time_s)

        # Aero: rider contribution at different positions
        # Values derived from AeroParams; we scale the full bike Cd*A
        a = cfg.aero
        self._cd_a_full = a.cd_a_effective  # tuck (baseline)
        self._cd_a_upright = a.cd_a_effective * 1.18  # staging upright ~18 % more
        self._cd_a_race = a.cd_a_effective * 0.92  # race crouch ~8 % less

    # ─────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────

    def cog_shift(self, t: float):
        """
        Return (cog_x_shift_m, cog_h_delta_m) at time *t* (s from launch).

        cog_x_shift_m  — longitudinal shift along wheelbase (m).
                         Positive = toward front wheel.
        cog_h_delta_m  — change in combined bike+rider CoG height (m).
                         Negative means CoG moved lower (favourable for tuck).
        """
        frac = self._transition_frac(t)

        # Longitudinal: starts shifted forward, relaxes to slight rearward tuck
        cog_x_shift = self._launch_shift_m * (1.0 - frac) - 0.03 * frac

        # Height: rider CoG interpolates from upright to tuck
        rider_h = self._rider_upright_h * (1.0 - frac) + self._rider_tuck_h * frac
        # Combined CoG height weighted by rider mass fraction
        f_rider = self.m_rider / max(self.m_total, 1.0)
        h_combined = self.h_nominal + f_rider * (rider_h - self._rider_upright_h)
        cog_h_delta = h_combined - self.h_nominal

        return cog_x_shift, cog_h_delta

    def cd_a(self, t: float) -> float:
        """
        Effective Cd*A (m²) for drag calculation at time *t*.
        Interpolates from upright (staging) to tuck.
        """
        frac = self._transition_frac(t)
        return self._cd_a_upright * (1.0 - frac) + self._cd_a_full * frac

    def wheelbase_weight_split(self, t: float):
        """
        Return updated (front_weight_pct, rear_weight_pct) accounting for
        rider longitudinal CoG shift at time *t*.

        This is a *static* correction layered on top of the dynamic weight
        transfer computed by WeightTransferModel; it only captures the slow
        body-position change, not the inertial transfer during acceleration.
        """
        cog_x_shift, _ = self.cog_shift(t)
        c = self.cfg.chassis
        L = max(c.wheelbase_m, 0.01)

        # New front weight percentage
        # Front load = m*g*(L_r + cog_x_shift) / L  [standard 2-axle formula]
        # where L_r is distance from CoG to rear axle
        L_r_new = c.L_r - cog_x_shift  # shift forward → L_r shrinks
        front_pct = L_r_new / L
        front_pct = max(0.30, min(0.70, front_pct))  # physical bounds
        return front_pct, 1.0 - front_pct

    # ─────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────

    def _transition_frac(self, t: float) -> float:
        """Smooth sigmoid fraction [0→1] from launch to full tuck."""
        if t <= 0.0:
            return 0.0
        if t >= self._transition_s:
            return 1.0
        # Sine-ease for smoothness
        return math.sin((t / self._transition_s) * math.pi / 2.0) ** 2
