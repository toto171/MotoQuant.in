"""
Sub-Model 11: Parasitic Losses
================================
Power consumed by accessories (alternator, water pump, oil pump, etc.).
"""

from ..models import BikeConfig


class ParasiticModel:
    """Parasitic power loss model."""

    def __init__(self, cfg: BikeConfig):
        self.cfg = cfg

    def power_loss(self, rpm: float) -> float:
        """Power consumed by accessories (W) at given RPM."""
        rpm_frac = rpm / max(1.0, self.cfg.engine.redline_rpm)
        return self.cfg.parasitic.total_parasitic_w(rpm_frac)
