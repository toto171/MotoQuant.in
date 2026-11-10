"""
Sub-Model 14: Staging & Launch
================================
Encapsulates the procedural logic that happens *before* and *at* the start
of a drag run:

  • Rollout is NOT handled here: the single timing convention lives in
    MotoQuantEngine.run(rollout_m=constants.ROLLOUT_M) — integrate from rest
    at the start line, start the clock at x = rollout_m, finish at x = D.
    (2026-10 epoch round 2 removed this model's start_position_m() /
    rollout_m() and StagingParams.rollout_distance_mm: serialised but never
    read by run(), they described a third, contradictory convention.)

  • Reaction time & vehicle response lag (diagnostic only — run() times the
    pass from the start beam, so reaction time is not part of the ET) — total elapsed time before the
    rear wheel delivers torque = reaction_time_ms + vehicle_response_ms.
    During this window the engine is at launch_rpm but no drive force is
    applied.

  • Two-step / launch RPM window — if two_step is True the engine is held
    at staging.launch_rpm during the pre-launch window; otherwise it is
    held at peak_torque_rpm.

  • Launch RPM window validation — warn (but don't crash) if launch_rpm
    is outside the safe window for the tyre / clutch / power combination.

All values are read from StagingParams and EngineParams at construction;
no mutable state is stored so this model is stateless per timestep.
"""

from ..constants import RPM_TO_RADS
from ..models import BikeConfig


class StagingModel:
    """
    Provides staging values consumed by the physics loop.

    Typical usage
    ─────────────
        staging = StagingModel(cfg)

        # At loop initialisation (the only value run() reads):
        omega_e_0  = staging.initial_omega_e()     # rad/s

        # Diagnostics (not applied by run(): the ET clock starts at the
        # start beam, after the rider has already reacted):
        dead_time  = staging.total_dead_time_s()   # reaction + response, s
    """

    def __init__(self, cfg: BikeConfig):
        self.cfg = cfg
        s = cfg.staging
        e = cfg.engine

        self._reaction_s = s.reaction_time_ms / 1000.0
        self._vehicle_s = s.vehicle_response_ms / 1000.0
        self._two_step = s.two_step
        self._launch_rpm = s.launch_rpm
        self._peak_torque_rpm = e.peak_torque_rpm
        self._idle_rpm = e.idle_rpm
        self._redline_rpm = e.redline_rpm

        # Pro tree interval = 0.400 s per amber; sportsman = 0.500 s
        self._tree_interval_s = 0.400 if s.tree_type == "pro" else 0.500

    # ─────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────

    def initial_omega_e(self) -> float:
        """
        Engine angular velocity (rad/s) at t = 0.
        Two-step: launch_rpm.  No two-step: peak torque RPM.
        """
        if self._two_step:
            rpm = max(self._idle_rpm, min(self._launch_rpm, self._redline_rpm))
        else:
            rpm = self._peak_torque_rpm
        return rpm * RPM_TO_RADS

    def total_dead_time_s(self) -> float:
        """
        Total time (s) from t = 0 to the moment the rear wheel first receives
        drive torque (reaction + vehicle response lag).
        """
        return self._reaction_s + self._vehicle_s

    def launch_rpm(self) -> float:
        """Effective launch RPM (could be two-step or default)."""
        if self._two_step:
            return max(self._idle_rpm, min(self._launch_rpm, self._redline_rpm))
        return self._peak_torque_rpm

    def is_in_dead_band(self, t: float) -> bool:
        """True while the driver has not yet reacted and the clutch is still held."""
        return t < self.total_dead_time_s()

    def validate(self) -> list:
        """
        Return a list of warning strings for out-of-range staging parameters.
        Empty list means everything looks plausible.
        """
        warnings = []
        lr = self.launch_rpm()
        if lr < self._idle_rpm * 1.1:
            warnings.append(
                f"launch_rpm {lr:.0f} is very close to idle ({self._idle_rpm:.0f} RPM); "
                "clutch engagement will be sluggish."
            )
        if lr > self._redline_rpm * 0.95:
            warnings.append(
                f"launch_rpm {lr:.0f} is near redline ({self._redline_rpm:.0f} RPM); "
                "risk of excessive clutch slip heat."
            )
        if self._reaction_s < 0.050:
            warnings.append(
                f"reaction_time_ms {self._reaction_s * 1000:.0f} ms seems unrealistically fast "
                "(world-class pro-stock is ~100 ms)."
            )
        return warnings
