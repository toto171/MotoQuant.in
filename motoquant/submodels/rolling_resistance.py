"""
Sub-Model 12: Rolling Resistance
==================================
Speed-dependent and temperature-corrected rolling resistance.
"""

from ..constants import G
from ..models import BikeConfig


class RollingResistanceModel:
    """Rolling resistance force model."""

    def __init__(self, cfg: BikeConfig, surface_rr_multiplier: float = 1.0):
        self.cfg = cfg
        # Track-surface rolling-resistance factor (asphalt = 1.00). Defaults to
        # 1.0 so any direct instantiation is behaviour-preserving; the physics
        # engine passes EnvironmentalModel.rr_multiplier so salt / dry-lake-bed
        # surfaces (which absorb energy) correctly raise rolling drag.
        self.surface_rr_multiplier = surface_rr_multiplier

    def force(self, v: float, T_tire: float, m_total: float) -> float:
        """Total rolling resistance force (N)."""
        tire = self.cfg.tires
        Crr = tire.crr_base + tire.crr_speed_coeff * v**2
        if T_tire > 30.0:
            Crr *= max(0.75, 1.0 + tire.crr_temp_coeff * (T_tire - 30.0))
        return Crr * m_total * G * self.surface_rr_multiplier
