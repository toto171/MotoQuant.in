"""
Sub-Model 12: Rolling Resistance
==================================
Speed-dependent and temperature-corrected rolling resistance.
"""

from ..constants import G
from ..models import BikeConfig


class RollingResistanceModel:
    """Rolling resistance force model."""

    def __init__(self, cfg: BikeConfig):
        self.cfg = cfg

    def force(self, v: float, T_tire: float, m_total: float) -> float:
        """Total rolling resistance force (N)."""
        tire = self.cfg.tires
        Crr = tire.crr_base + tire.crr_speed_coeff * v**2
        if T_tire > 30.0:
            Crr *= max(0.75, 1.0 + tire.crr_temp_coeff * (T_tire - 30.0))
        return Crr * m_total * G
