"""
Sub-Model 2: Forced Induction
===============================
Turbocharger, supercharger (roots/centrifugal), and N2O models.
Computes torque multiplier and boost pressure dynamics.
"""

from ..constants import RPM_TO_RADS
from ..models import (
    BOOST_N2O,
    BOOST_NA,
    BOOST_SC_CENTRIFUGAL,
    BOOST_SC_ROOTS,
    BOOST_TURBO,
    BikeConfig,
)

VALID_BOOST_TYPES = frozenset(
    {BOOST_NA, BOOST_TURBO, BOOST_SC_ROOTS, BOOST_SC_CENTRIFUGAL, BOOST_N2O}
)


class ForcedInductionModel:
    """Forced induction torque multiplier and boost dynamics."""

    def __init__(self, cfg: BikeConfig, rho: float):
        bt = cfg.forced_induction.boost_type
        if bt not in VALID_BOOST_TYPES:
            # An unrecognized string previously slipped through silently:
            # torque_mult fell through to 1.0 (zero boost) while is_boosted
            # still granted the x0.97 density-altitude floor — the config
            # simmed almost-but-not-quite like NA with no warning.
            raise ValueError(
                f"unknown boost_type {bt!r} — valid values: {sorted(VALID_BOOST_TYPES)}"
            )
        self.cfg = cfg
        self.rho = rho

    def torque_mult(self, rpm: float, t: float, P_boost: float) -> float:
        """Torque multiplier from forced induction. Returns 1.0 for NA."""
        fi = self.cfg.forced_induction
        if not fi.is_boosted:
            return 1.0

        if fi.boost_type == BOOST_TURBO:
            P_atm = self.rho * 287.058 * (self.cfg.environment.ambient_temp_c + 273.15)
            if P_atm <= 0:
                P_atm = 101325.0
            boost_ratio = 1.0 + P_boost / P_atm
            # Intercooler temperature correction
            if fi.intercooler_type != "none":
                eta_ic = fi.intercooler_effectiveness
                temp_penalty = 1.0 - 0.02 * (1.0 - eta_ic) * (P_boost / 100000.0)
                boost_ratio *= max(0.90, temp_penalty)
            return boost_ratio

        elif fi.boost_type in (BOOST_SC_ROOTS, BOOST_SC_CENTRIFUGAL):
            P_atm = 101325.0
            boost_ratio = 1.0 + P_boost / P_atm
            return boost_ratio

        elif fi.boost_type == BOOST_N2O:
            ramp = min(1.0, t / max(0.1, fi.n2o_ramp_duration_s))
            hp_add = fi.n2o_hp_per_stage * fi.n2o_stages * ramp
            if rpm > 1000:
                T_base = self.cfg.engine.get_torque(rpm)
                if T_base > 0:
                    T_add = hp_add * 745.7 / (rpm * RPM_TO_RADS)
                    return 1.0 + T_add / T_base
            return 1.0

        return 1.0

    def boost_rate(self, P_boost: float, rpm: float, t: float) -> float:
        """dP_boost/dt -- boost pressure rate of change (Pa/s)."""
        fi = self.cfg.forced_induction
        if fi.boost_type == BOOST_TURBO:
            P_target = fi.target_boost_bar * 1e5
            tau = fi.turbo_spool_time_s
            return (P_target - P_boost) / max(tau, 0.05)

        elif fi.boost_type == BOOST_SC_CENTRIFUGAL:
            rpm_frac = rpm / max(1.0, self.cfg.engine.redline_rpm)
            P_target = fi.target_boost_bar * 1e5 * rpm_frac**2
            return (P_target - P_boost) / 0.1

        elif fi.boost_type == BOOST_SC_ROOTS:
            P_target = fi.target_boost_bar * 1e5
            return (P_target - P_boost) / 0.05

        return 0.0
