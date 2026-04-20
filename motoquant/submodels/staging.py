"""
Sub-Model 14: Staging & Launch
================================
Encapsulates the procedural logic that happens *before* and *at* the start
of a drag run:

  • Rollout correction — clocks start after the front wheel clears the
    stage beam, so the bike is already moving by the time timing begins.
    The simulator positions the bike at x = –rollout_m at t = 0 so the
    clock equivalent at x = 0 is already included.

  • Reaction time & vehicle response lag — total elapsed time before the
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
    Provides staging corrections consumed by the physics loop.

    Typical usage
    ─────────────
        staging = StagingModel(cfg)

        # At loop initialisation:
        x_start    = staging.start_position_m()   # negative (behind beam)
        omega_e_0  = staging.initial_omega_e()     # rad/s
        dead_time  = staging.total_dead_time_s()   # seconds with zero drive force

        # Each timestep:
        if t < dead_time:
            T_drive = 0.0   # staging dead-band — clutch not yet dropped
        else:
            T_drive = <normal clutch logic>
    """

    def __init__(self, cfg: BikeConfig):
        self.cfg = cfg
        s = cfg.staging
        e = cfg.engine

        self._rollout_m = s.rollout_distance_mm / 1000.0
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

    def start_position_m(self) -> float:
        """
        Initial x position (m).  Negative because rollout means the bike is
        already 'rollout_m' ahead of the staging beam at the moment the clock
        starts at x = 0.  The simulation starts at x = -rollout_m and the
        quarter-mile distance is measured from x = 0.
        """
        return -self._rollout_m

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

    def rollout_m(self) -> float:
        """Rollout distance in metres."""
        return self._rollout_m

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
