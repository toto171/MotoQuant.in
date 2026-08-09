"""
Sub-Model 11: Parasitic Losses
================================
Power consumed by accessories (alternator, water pump, oil pump, etc.).

Apr 30, 2026: category-flavoured dispatch added. Reads
``self._mult`` from the resolved CategoryProfile so per-cluster tuning
can scale parasitic loss without touching the underlying ParasiticParams
(which are spec-derived). Default mult is 1.0 (legacy).
"""

from ..models import BikeConfig


class ParasiticModel:
    """Parasitic power loss model."""

    def __init__(self, cfg: BikeConfig):
        self.cfg = cfg
        # Resolve category profile mult (1.0 if no tag / unknown profile).
        from ..category_profiles import derive_category_tag, get_profile

        tag = cfg.category_tag
        if not tag:
            tag = derive_category_tag(
                manufacturer="",
                model_name="",
                displacement_cc=cfg.engine.displacement_cc,
                peak_power_hp=cfg.engine.peak_power_hp,
                stroke_type=cfg.engine.stroke_type,
                category=None,
                cylinders=cfg.engine.cylinder_count,
            )
        self._mult = get_profile(tag).parasitic_mult

    def power_loss(self, rpm: float) -> float:
        """Power consumed by accessories (W) at given RPM."""
        rpm_frac = rpm / max(1.0, self.cfg.engine.redline_rpm)
        return self.cfg.parasitic.total_parasitic_w(rpm_frac) * self._mult
