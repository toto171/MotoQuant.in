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
    Rider-position aerodynamics: time-varying Cd*A from upright (staging)
    to full tuck.

    Usage in physics loop
    ─────────────────────
    At each timestep *t* (seconds since lights-out):

        cd_a_rider = rider.cd_a(t)
        # Full rider+bike Cd*A to use for aero drag this timestep.

    History (July 13, 2026): the never-called ``cog_shift()`` /
    ``wheelbase_weight_split()`` pair was DELETED — rider CoG shift is
    handled by the simpler live path ``RiderParams.cog_offset()`` consumed
    by WeightTransfer/Wheelie (see the July-10 physics-foundations review,
    epoch-gated item 5). Wiring a dynamic CoG-height model back in is a
    deliberate rebaseline-scale change, not a refactor.
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

    def cd_a(self, t: float) -> float:
        """
        Effective Cd*A (m²) for drag calculation at time *t*.
        Interpolates from upright (staging) to tuck.
        """
        frac = self._transition_frac(t)
        return self._cd_a_upright * (1.0 - frac) + self._cd_a_full * frac

    def _transition_frac(self, t: float) -> float:
        """Smooth sigmoid fraction [0→1] from launch to full tuck."""
        if t <= 0.0:
            return 0.0
        if t >= self._transition_s:
            return 1.0
        # Sine-ease for smoothness
        return math.sin((t / self._transition_s) * math.pi / 2.0) ** 2
