"""
Sub-Model 1: Engine Torque
===========================
Crank torque lookup with altitude/density correction,
temperature derating, and rev limiter.
"""

from ..models import BikeConfig


class EngineModel:
    """Engine torque production model."""

    def __init__(self, cfg: BikeConfig, eta_dt: float, power_correction: float):
        self.cfg = cfg
        self.eta_dt = eta_dt
        self.power_correction = power_correction

    def torque(self, rpm: float, t: float) -> float:
        """
        Engine torque (N-m) at given RPM, corrected for conditions.
        Returns CRANK torque regardless of dyno type.
        """
        eng = self.cfg.engine
        if rpm < eng.idle_rpm * 0.5:
            return 0.0
        if rpm > eng.redline_rpm * 1.02:
            return 0.0  # Rev limiter

        T_base = eng.get_torque(rpm)

        # If dyno curve is at wheel, convert to crank torque
        if eng.dyno_curve is not None and eng.dyno_curve.is_at_wheel:
            T_base /= self.eta_dt

        # Altitude/density correction
        T_corrected = T_base * self.power_correction

        # Engine temperature correction
        temp = eng.coolant_temp_c
        if temp < 70:
            T_corrected *= 0.97
        elif temp > 100:
            T_corrected *= 0.99

        return T_corrected
