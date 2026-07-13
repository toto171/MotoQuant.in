"""
Sub-Model 3: Drivetrain
========================
Gear ratios, wheel torque, effective mass (rotational inertia),
RPM-speed mapping, and optimal shift point calculation.
"""

from ..constants import RADS_TO_RPM
from ..models import BikeConfig


class DrivetrainModel:
    """Drivetrain torque multiplication, effective mass, and shift logic."""

    def __init__(self, cfg: BikeConfig, eta_dt: float):
        self.cfg = cfg
        self.eta_dt = eta_dt

    def wheel_torque(self, T_engine: float, gear: int) -> float:
        """Torque at the rear wheel contact patch (N-m)."""
        i_total = self.cfg.drivetrain.overall_ratio(gear)
        return T_engine * i_total * self.eta_dt

    def effective_mass(self, gear: int, m_total: float) -> float:
        """Total effective mass including rotational inertia (kg)."""
        dt_params = self.cfg.drivetrain
        tire = self.cfg.tires
        eng = self.cfg.engine
        r_w = tire.rear_rolling_radius_m
        i_total = dt_params.overall_ratio(gear)
        m_rot_engine = (
            eng.engine_inertia_kgm2 + self.cfg.clutch.basket_inertia_kgm2
        ) * (i_total / r_w) ** 2
        m_rot_rear = tire.rear_inertia_kgm2 / r_w**2
        # July 13, 2026 (epoch): the front wheel spins at v/r_FRONT, so its
        # inertia contributes I_f/r_f² — it was divided by the REAR radius
        # (−1.2 ms on each reference when fixed; July-10 review item 4). The
        # CLI front-tire override writes front_rolling_radius_m expecting
        # exactly this effect. Guard: fall back to r_w when the front radius
        # is unset/zero (legacy configs).
        r_f = tire.front_rolling_radius_m or r_w
        m_rot_front = tire.front_inertia_kgm2 / r_f**2
        return m_total + m_rot_engine + m_rot_rear + m_rot_front

    def engine_rpm_from_speed(self, v: float, gear: int, r_eff: float) -> float:
        """Engine RPM derived from vehicle speed (clutch locked)."""
        if r_eff <= 0:
            return 0.0
        omega_w = v / r_eff
        i_total = self.cfg.drivetrain.overall_ratio(gear)
        omega_e = omega_w * i_total
        return omega_e * RADS_TO_RPM

    def optimal_shift_rpm(self, gear_from: int, gear_to: int) -> float:
        """Find the RPM where shifting to the next gear gives more wheel torque."""
        if gear_to >= self.cfg.drivetrain.num_gears:
            return self.cfg.engine.redline_rpm
        i_from = self.cfg.drivetrain.overall_ratio(gear_from)
        i_to = self.cfg.drivetrain.overall_ratio(gear_to)
        ratio = i_to / i_from
        best_rpm = self.cfg.engine.redline_rpm
        for rpm_test in range(
            int(self.cfg.engine.peak_torque_rpm),
            int(self.cfg.engine.redline_rpm) + 1,
            50,
        ):
            T_current = self.cfg.engine.get_torque(rpm_test) * i_from
            T_next = self.cfg.engine.get_torque(rpm_test * ratio) * i_to
            if T_next > T_current:
                best_rpm = rpm_test
                break
        return min(best_rpm, self.cfg.engine.redline_rpm)

    def should_shift(self, rpm: float, gear: int) -> bool:
        """Determine if a shift is needed."""
        if gear >= self.cfg.drivetrain.num_gears - 1:
            return False
        shift_rpm = self.optimal_shift_rpm(gear, gear + 1)
        return rpm >= shift_rpm
