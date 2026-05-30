"""
CorrectionTargets -- the 3-dim label space the calibrator learns.

Each factor is a *multiplicative* correction applied to a physics param.
1.0 = no change.

    mu_peak_factor     0.88 - 1.12  (tire grip varies w/ surface, prep, age)
    peak_torque_factor 0.88 - 1.12  (crank-claim vs wheel-actual)
    inertia_factor     0.85 - 1.20  (engine inertia, tightly bounded)

cd_factor was removed (R²=-0.06 in audit -- aero Cd is unlearnable from
a single ET measurement and was actively harming mu_peak_factor prediction).
Tightened inertia_factor from [0.6, 1.8] to [0.85, 1.20] based on audit
feedback (was too wide, causing bias toward fast-bike corrections).

Schema version 2: 3 targets (cd_factor dropped).
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

__all__ = ["CorrectionTargets"]


@dataclass
class CorrectionTargets:
    """Multiplicative correction factors learned from measured runs."""

    mu_peak_factor: float = 1.0
    peak_torque_factor: float = 1.0
    inertia_factor: float = 1.0

    def apply(self, config: Any) -> Any:
        """Return a new BikeConfig with these corrections applied (deep copy).

        Scales:
          - tires.mu_peak                      x mu_peak_factor
          - engine.peak_torque_nm + peak_power x peak_torque_factor
          - engine.dyno_curve.torque_nm        x peak_torque_factor (if present)
          - engine.engine_inertia_kgm2         x inertia_factor

        Power is scaled with torque since they're physically locked together
        (P = T * omega). Scaling dyno_curve in lockstep avoids the documented
        dead-knob bug where /api/simulate?bike_id=N silently uses the unscaled
        curve.

        cd_factor is intentionally NOT applied here (dropped from schema v2).
        """
        c = copy.deepcopy(config)

        # Tires
        if hasattr(c, "tires") and hasattr(c.tires, "mu_peak"):
            c.tires.mu_peak = float(c.tires.mu_peak) * self.mu_peak_factor

        # Engine torque + power (locked together)
        if hasattr(c, "engine"):
            e = c.engine
            if hasattr(e, "peak_torque_nm") and e.peak_torque_nm:
                e.peak_torque_nm = float(e.peak_torque_nm) * self.peak_torque_factor
            if hasattr(e, "peak_power_hp") and e.peak_power_hp:
                e.peak_power_hp = float(e.peak_power_hp) * self.peak_torque_factor
            if hasattr(e, "engine_inertia_kgm2") and e.engine_inertia_kgm2:
                e.engine_inertia_kgm2 = (
                    float(e.engine_inertia_kgm2) * self.inertia_factor
                )

            # Scale dyno curve so /api/simulate?bike_id picks up the boost
            dyno = getattr(e, "dyno_curve", None)
            torque = getattr(dyno, "torque_nm", None) if dyno is not None else None
            if torque is not None:
                try:
                    dyno.torque_nm = [
                        float(t) * self.peak_torque_factor for t in torque
                    ]
                except (TypeError, AttributeError):
                    pass  # non-iterable / immutable -- skip silently

        return c

    def to_array(self) -> np.ndarray:
        """Stable ordering: [mu_peak, peak_torque, inertia]."""
        return np.array(
            [
                self.mu_peak_factor,
                self.peak_torque_factor,
                self.inertia_factor,
            ],
            dtype=np.float32,
        )

    @classmethod
    def from_array(cls, arr) -> CorrectionTargets:
        """Inverse of to_array. Accepts list, tuple, or ndarray of length 3."""
        if len(arr) != 3:
            raise ValueError(f"CorrectionTargets requires 3 values, got {len(arr)}")
        return cls(
            mu_peak_factor=float(arr[0]),
            peak_torque_factor=float(arr[1]),
            inertia_factor=float(arr[2]),
        )

    def to_dict(self) -> dict[str, float]:
        return asdict(self)

    def is_identity(self, atol: float = 1e-6) -> bool:
        """True if all factors are within atol of 1.0 (no correction)."""
        return all(
            abs(v - 1.0) < atol
            for v in (
                self.mu_peak_factor,
                self.peak_torque_factor,
                self.inertia_factor,
            )
        )
