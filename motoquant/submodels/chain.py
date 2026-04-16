"""
Sub-Model 5: Chain Dynamics
=============================
Chain slack dead-zone at launch.
Shaft-drive bikes bypass this model.
"""

from ..models import DRIVE_CHAIN, BikeConfig


class ChainModel:
    """Chain slack and engagement dynamics."""

    def __init__(self, cfg: BikeConfig):
        self.cfg = cfg

    def torque_modifier(self, T_wheel: float, v: float, t: float) -> float:
        """Apply chain slack dead-zone at launch."""
        if self.cfg.drivetrain.drive_type != DRIVE_CHAIN:
            return T_wheel
        if v < 1.0 and t < 0.1:
            slack_factor = min(1.0, t / 0.05)  # Ramps over 50ms
            return T_wheel * slack_factor
        return T_wheel
