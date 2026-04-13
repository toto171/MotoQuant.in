"""
Sub-Model 7: Aerodynamics
===========================
Drag force, lift force, and ram air power multiplier.
"""

from ..models import BikeConfig


class AeroModel:
    """Aerodynamic forces and ram air model."""

    def __init__(self, cfg: BikeConfig, rho: float, cd_a: float, v_wind: float):
        self.cfg = cfg
        self.rho = rho
        self.cd_a = cd_a
        self.v_wind = v_wind

    def drag(self, v: float) -> float:
        """Aerodynamic drag force (N). Positive opposes motion."""
        v_rel = v + self.v_wind
        if v_rel <= 0:
            return 0.0
        return 0.5 * self.rho * v_rel ** 2 * self.cd_a

    def lift(self, v: float) -> float:
        """Aerodynamic lift force (N). Reduces wheel loads."""
        v_rel = v + self.v_wind
        if v_rel <= 0:
            return 0.0
        return 0.5 * self.rho * v_rel ** 2 * self.cfg.aero.cl * self.cfg.aero.frontal_area_m2

    def ram_air_power_mult(self, v: float) -> float:
        """Power multiplier from ram air effect. Significant above 100 km/h."""
        eta = self.cfg.aero.ram_air_efficiency
        if eta <= 0 or v < 20.0:
            return 1.0
        P_ram = 0.5 * self.rho * v ** 2 * eta
        P_atm = self.rho * 287.058 * (self.cfg.environment.ambient_temp_c + 273.15)
        if P_atm <= 0:
            P_atm = 101325.0
        k_ram = 0.5
        return 1.0 + k_ram * P_ram / P_atm
