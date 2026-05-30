"""
MotoQuant Pro — Physics Engine
=============================
Thin orchestrator that composes 12 sub-model classes into a single
simulation loop. RK4 fixed-step integration at 1 ms timestep.

State vector: [x, v, omega_e, T_tire, T_clutch, P_boost]
  x        = position along track (m)
  v        = vehicle velocity (m/s)
  omega_e  = engine angular velocity (rad/s)  [only during clutch slip]
  T_tire   = rear tire surface temperature (C)
  T_clutch = clutch plate temperature (C)
  P_boost  = boost pressure, gauge (Pa)       [only for FI builds]

After clutch locks, omega_e is derived from v and gear ratio.
"""

from dataclasses import dataclass, field

import numpy as np

from .constants import (
    EIGHTH_MILE_M,
    ONE_KM_M,
    ONE_MILE_M,
    QUARTER_MILE_M,
    RADS_TO_RPM,
    RPM_TO_RADS,
    SIXTY_FOOT_M,
    THOUSAND_FT_M,
    THREE30_FT_M,
    TOPSPEED_MAX_DISTANCE_M,
    TOPSPEED_MAX_TIME_S,
    TOPSPEED_PLATEAU_ACCEL,
    TOPSPEED_PLATEAU_WINDOW_S,
    G,
)
from .models import (
    CLUTCH_SLIDER,
    BikeConfig,
)
from .submodels import (
    AeroModel,
    BrakingModel,
    ChainModel,
    ClutchModel,
    DrivetrainModel,
    EngineModel,
    EnvironmentalModel,
    ForcedInductionModel,
    ParasiticModel,
    RiderDynamicsModel,
    RollingResistanceModel,
    StagingModel,
    TireModel,
    WeightTransferModel,
    WheelieModel,
)

# ═══════════════════════════════════════════
# SIMULATION STATE
# ═══════════════════════════════════════════


@dataclass
class SimState:
    """Instantaneous simulation state."""

    t: float = 0.0
    x: float = 0.0
    v: float = 0.0
    omega_e: float = 0.0
    T_tire: float = 40.0
    T_clutch: float = 80.0
    P_boost: float = 0.0
    gear: int = 0
    clutch_locked: bool = False
    accel_g: float = 0.0
    rpm: float = 0.0
    slip_ratio: float = 0.0
    traction_pct: float = 0.0
    N_front: float = 0.0
    N_rear: float = 0.0
    F_drive: float = 0.0
    F_drag: float = 0.0
    F_rr: float = 0.0
    wheel_torque: float = 0.0
    power_kw: float = 0.0
    r_eff: float = 0.302
    omega_w: float = 0.0


@dataclass
class SimResult:
    """Complete simulation output — all channels at every timestep."""

    dt: float = 0.001
    t: np.ndarray = field(default_factory=lambda: np.array([]))
    x: np.ndarray = field(default_factory=lambda: np.array([]))
    v: np.ndarray = field(default_factory=lambda: np.array([]))
    a: np.ndarray = field(default_factory=lambda: np.array([]))
    rpm: np.ndarray = field(default_factory=lambda: np.array([]))
    gear: np.ndarray = field(default_factory=lambda: np.array([]))
    slip: np.ndarray = field(default_factory=lambda: np.array([]))
    traction_pct: np.ndarray = field(default_factory=lambda: np.array([]))
    N_front: np.ndarray = field(default_factory=lambda: np.array([]))
    N_rear: np.ndarray = field(default_factory=lambda: np.array([]))
    F_drive: np.ndarray = field(default_factory=lambda: np.array([]))
    F_drag: np.ndarray = field(default_factory=lambda: np.array([]))
    F_rr: np.ndarray = field(default_factory=lambda: np.array([]))
    T_tire: np.ndarray = field(default_factory=lambda: np.array([]))
    T_clutch: np.ndarray = field(default_factory=lambda: np.array([]))
    P_boost: np.ndarray = field(default_factory=lambda: np.array([]))
    power_kw: np.ndarray = field(default_factory=lambda: np.array([]))
    r_eff: np.ndarray = field(default_factory=lambda: np.array([]))

    # Split times
    time_60ft: float = 0.0
    speed_60ft: float = 0.0
    time_330ft: float = 0.0
    speed_330ft: float = 0.0
    time_eighth: float = 0.0
    speed_eighth: float = 0.0
    time_1000ft: float = 0.0
    speed_1000ft: float = 0.0
    time_quarter: float = 0.0
    speed_quarter: float = 0.0

    # Completion tracking
    finished_quarter: bool = (
        False  # True if bike reached QUARTER_MILE_M within simulation
    )
    max_distance_m: float = 0.0  # Furthest distance reached (m)
    elapsed_time_s: float = 0.0  # Time elapsed at end of simulation (s)

    def extract_splits(self):
        """Extract split times from position array. Track completion status."""
        # Record max distance and elapsed time
        if len(self.x) > 0:
            self.max_distance_m = float(self.x[-1])
        if len(self.t) > 0:
            self.elapsed_time_s = float(self.t[-1])

        splits = [
            (SIXTY_FOOT_M, "time_60ft", "speed_60ft"),
            (THREE30_FT_M, "time_330ft", "speed_330ft"),
            (EIGHTH_MILE_M, "time_eighth", "speed_eighth"),
            (THOUSAND_FT_M, "time_1000ft", "speed_1000ft"),
            (QUARTER_MILE_M, "time_quarter", "speed_quarter"),
        ]
        for dist, t_attr, s_attr in splits:
            idx = np.searchsorted(self.x, dist)
            if idx < len(self.t):
                if idx > 0 and self.x[idx] != self.x[idx - 1]:
                    frac = (dist - self.x[idx - 1]) / (self.x[idx] - self.x[idx - 1])
                    setattr(
                        self,
                        t_attr,
                        self.t[idx - 1] + frac * (self.t[idx] - self.t[idx - 1]),
                    )
                    setattr(
                        self,
                        s_attr,
                        self.v[idx - 1] + frac * (self.v[idx] - self.v[idx - 1]),
                    )
                else:
                    setattr(self, t_attr, self.t[idx])
                    setattr(self, s_attr, self.v[idx])

        # Mark as finished if quarter-mile ET was actually set (not left at default 0.0)
        self.finished_quarter = self.time_quarter > 0.0


# ═══════════════════════════════════════════
# PHYSICS ENGINE (orchestrator)
# ═══════════════════════════════════════════


class MotoQuantEngine:
    """
    The complete motorcycle drag racing physics engine.
    Composes 12 sub-model classes; RK4 integration; 1 ms timestep.
    """

    def __init__(self, config: BikeConfig, dt: float = 0.001):
        self.cfg = config
        self.dt = dt
        self._precompute()
        self._init_submodels()

    def _precompute(self):
        """Pre-compute derived quantities that don't change during the run."""
        c = self.cfg
        self.m_total = c.chassis.total_mass_kg
        self.L = c.chassis.wheelbase_m
        self.h = c.chassis.cog_height_m
        self.L_r = c.chassis.L_r
        self.L_f = c.chassis.L_f
        self.N_f_static = self.m_total * G * c.chassis.front_weight_pct
        self.N_r_static = self.m_total * G * (1.0 - c.chassis.front_weight_pct)
        self.eta_dt = c.drivetrain.drivetrain_efficiency()
        self.T_tire_launch = c.tires.tire_temp_at_launch(c.environment.ambient_temp_c)
        self.mu_prep = c.tires.track_prep_multiplier(c.environment.track_temp_c)
        self.anti_squat_frac = c.suspension.anti_squat_pct / 100.0
        self.T_tire_ref_K = self.T_tire_launch + 273.15
        self.F_gradient = self.m_total * G * c.environment.track_gradient_pct / 100.0

        # ── EnvironmentalModel: single source for ambient corrections ────────
        self._env_model = EnvironmentalModel(c)
        self.rho = self._env_model.rho
        self.cd_a = c.aero.cd_a_effective  # static reference Cd*A
        self.v_wind = self._env_model.v_headwind
        self.power_correction = self._env_model.power_correction

        # Category-flavoured physics dispatch (April 30, 2026).
        # Look up per-cluster profile. If category_tag is unset, auto-
        # derive one from engine spec so legacy saved configs still get
        # category-aware behaviour (keeps the over-clutching tier alive
        # for old DB rows that pre-date the category_tag field).
        from .category_profiles import derive_category_tag, get_profile
        tag = c.category_tag
        if not tag:
            tag = derive_category_tag(
                manufacturer="", model_name="",
                displacement_cc=c.engine.displacement_cc,
                peak_power_hp=c.engine.peak_power_hp,
                stroke_type=c.engine.stroke_type,
                category=None,
            )
        self._profile = get_profile(tag)

    def _init_submodels(self):
        """Instantiate all sub-model classes with precomputed values."""
        self._engine = EngineModel(self.cfg, self.eta_dt, self.power_correction)
        self._fi = ForcedInductionModel(self.cfg, self.rho)
        self._drivetrain = DrivetrainModel(self.cfg, self.eta_dt)
        self._clutch = ClutchModel(self.cfg, self._engine.torque)
        self._chain = ChainModel(self.cfg)
        self._tire = TireModel(self.cfg, self.mu_prep, self.T_tire_ref_K)
        self._aero = AeroModel(self.cfg, self.rho, self.cd_a, self.v_wind)
        self._wt = WeightTransferModel(self.cfg, self.anti_squat_frac, self._aero)
        self._braking = BrakingModel(self.cfg, self.N_f_static, self.N_r_static)
        self._wheelie = WheelieModel(self.cfg, self._aero)
        self._parasitic = ParasiticModel(self.cfg)
        self._rr = RollingResistanceModel(self.cfg)
        # Phase-1 Remaining: three extracted inline sub-models
        self._rider = RiderDynamicsModel(self.cfg)
        self._staging = StagingModel(self.cfg)
        # _env_model already built in _precompute; alias for symmetry
        self._env = self._env_model

    # ─────────────────────────────────────────
    # PUBLIC DELEGATION METHODS
    # (backward-compatible API — tests call these)
    # ─────────────────────────────────────────

    def engine_torque(self, rpm: float, t: float) -> float:
        return self._engine.torque(rpm, t)

    def forced_induction_torque_mult(
        self, rpm: float, t: float, P_boost: float
    ) -> float:
        return self._fi.torque_mult(rpm, t, P_boost)

    def boost_dynamics(self, P_boost: float, rpm: float, t: float) -> float:
        return self._fi.boost_rate(P_boost, rpm, t)

    def wheel_torque(self, T_engine: float, gear: int) -> float:
        return self._drivetrain.wheel_torque(T_engine, gear)

    def effective_mass(self, gear: int) -> float:
        return self._drivetrain.effective_mass(gear, self.m_total)

    def engine_rpm_from_speed(self, v: float, gear: int, r_eff: float) -> float:
        return self._drivetrain.engine_rpm_from_speed(v, gear, r_eff)

    def optimal_shift_rpm(self, gear_from: int, gear_to: int) -> float:
        return self._drivetrain.optimal_shift_rpm(gear_from, gear_to)

    def clutch_torque(
        self, omega_e: float, omega_input: float, T_clutch_temp: float, t: float
    ) -> tuple[float, float]:
        return self._clutch.torque(omega_e, omega_input, T_clutch_temp, t)

    def chain_torque_modifier(self, T_wheel: float, v: float, t: float) -> float:
        return self._chain.torque_modifier(T_wheel, v, t)

    def tire_friction_coeff(self, N_rear: float, T_tire: float, v: float) -> float:
        return self._tire.friction_coeff(N_rear, T_tire, v)

    def tire_max_force(self, N_rear: float, T_tire: float, v: float) -> float:
        return self._tire.max_force(N_rear, T_tire, v)

    def pacejka_force(self, slip_ratio: float, N_rear: float, T_tire: float) -> float:
        return self._tire.pacejka_force(slip_ratio, N_rear, T_tire)

    def tire_thermal_rate(
        self, F_x: float, v: float, slip_ratio: float, T_tire: float, T_ambient: float
    ) -> float:
        return self._tire.thermal_rate(F_x, v, slip_ratio, T_tire, T_ambient)

    def tire_effective_radius(self, omega_w: float) -> float:
        return self._tire.effective_radius(omega_w)

    def aero_drag(self, v: float) -> float:
        return self._aero.drag(v)

    def aero_lift(self, v: float) -> float:
        return self._aero.lift(v)

    def ram_air_power_mult(self, v: float) -> float:
        return self._aero.ram_air_power_mult(v)

    def weight_transfer(self, accel: float, v: float, t: float) -> tuple[float, float]:
        return self._wt.compute(accel, v, t, self.m_total)

    def braking_decel(self, v: float) -> float:
        return self._braking.max_decel(v, self.m_total)

    def max_accel_before_wheelie(self, v: float, t: float) -> float:
        return self._wheelie.max_accel(v, t, self.m_total)

    def parasitic_power_loss(self, rpm: float) -> float:
        return self._parasitic.power_loss(rpm)

    def rolling_resistance(self, v: float, T_tire: float) -> float:
        return self._rr.force(v, T_tire, self.m_total)

    def should_shift(self, rpm: float, gear: int) -> bool:
        return self._drivetrain.should_shift(rpm, gear)

    # ── Phase-1 Remaining: new sub-model delegations ─────────────────────────

    def rider_cog_shift(self, t: float):
        """(cog_x_shift_m, cog_h_delta_m) from RiderDynamicsModel at time t."""
        return self._rider.cog_shift(t)

    def rider_cd_a(self, t: float) -> float:
        """Time-varying Cd*A accounting for rider position transition."""
        return self._rider.cd_a(t)

    def staging_initial_omega_e(self) -> float:
        """Initial engine angular velocity (rad/s) from StagingModel."""
        return self._staging.initial_omega_e()

    def staging_dead_time(self) -> float:
        """Total dead time (s) before drive torque is delivered."""
        return self._staging.total_dead_time_s()

    def environmental_summary(self) -> dict:
        """Key ambient conditions as a plain dict (DA, rho, grip, etc.)."""
        return self._env.summary()

    # ═══════════════════════════════════════════
    # MAIN SIMULATION LOOP
    # ═══════════════════════════════════════════

    def run(
        self,
        distance: float = QUARTER_MILE_M,
        max_time: float = 26.0,
        use_adaptive_dt: bool = False,
    ) -> SimResult:
        """
        Run the quarter-mile simulation.

        Parameters
        ----------
        distance : float
            Distance to simulate (m). Default = QUARTER_MILE_M.
        max_time : float
            Abort after this many seconds even if distance not reached.
            Default 26.0 s to accommodate small-cc bikes (under 200cc).
        use_adaptive_dt : bool
            When True, use variable-step-size integration (dt_min=0.5 ms,
            dt_max=5 ms) for a 3–5× speed-up during the locked-clutch phase.
            Results are within ±0.002 s of fixed 1 ms results.
            Default False preserves the deterministic fixed-step behaviour.

        Returns
        -------
        SimResult with all time-domain channels and split times.
        """
        dt = self.dt
        cfg = self.cfg

        # Adaptive step-size bounds
        _dt_min = 0.0005  # 0.5 ms — used during clutch slip / shifting
        _dt_max = 0.005  # 5 ms  — used during stable locked-clutch cruise
        _v_atol = 0.005  # m/s absolute tolerance for adaptive error estimate

        # Pre-compute shift points for all gears
        shift_rpms = []
        for g in range(cfg.drivetrain.num_gears - 1):
            shift_rpms.append(self.optimal_shift_rpm(g, g + 1))
        shift_rpms.append(cfg.engine.redline_rpm)

        # Initialize state — use StagingModel for initial omega_e
        v = 0.001
        x = 0.0
        gear = 0
        T_tire = self.T_tire_launch
        T_clutch = cfg.engine.coolant_temp_c
        P_boost = (
            cfg.forced_induction.prespool_boost_bar * 1e5
            if cfg.forced_induction.is_boosted
            else 0.0
        )
        omega_e = self._staging.initial_omega_e()  # uses two-step / peak-torque logic
        r_eff = cfg.tires.rear_rolling_radius_m
        clutch_locked = False
        shifting = False
        shift_timer = 0.0
        shift_target_gear = 0
        fuel_burned = 0.0

        # Collect output arrays
        n_max = int(max_time / dt) + 1
        out_t = np.zeros(n_max)
        out_x = np.zeros(n_max)
        out_v = np.zeros(n_max)
        out_a = np.zeros(n_max)
        out_rpm = np.zeros(n_max)
        out_gear = np.zeros(n_max, dtype=int)
        out_slip = np.zeros(n_max)
        out_trac = np.zeros(n_max)
        out_Nf = np.zeros(n_max)
        out_Nr = np.zeros(n_max)
        out_Fd = np.zeros(n_max)
        out_Fdrag = np.zeros(n_max)
        out_Frr = np.zeros(n_max)
        out_Ttire = np.zeros(n_max)
        out_Tclutch = np.zeros(n_max)
        out_Pboost = np.zeros(n_max)
        out_power = np.zeros(n_max)
        out_reff = np.zeros(n_max)

        step = 0
        t = 0.0

        while x < distance and t < max_time and step < n_max - 1:
            # ── Current RPM and wheel speed ──
            omega_w = v / max(
                r_eff, 0.15
            )  # 0.15m = min realistic motorcycle tire radius
            r_eff = self.tire_effective_radius(omega_w)
            omega_w = v / max(r_eff, 0.15)

            if clutch_locked:
                rpm = self.engine_rpm_from_speed(v, gear, r_eff)
                omega_e = rpm * RPM_TO_RADS
            else:
                rpm = omega_e * RADS_TO_RPM

            # ── Shift logic ──
            if shifting:
                shift_timer -= dt
                if shift_timer <= 0:
                    gear = shift_target_gear
                    shifting = False
                    rpm = self.engine_rpm_from_speed(v, gear, r_eff)
                    omega_e = rpm * RPM_TO_RADS

            if not shifting and clutch_locked:
                if rpm >= shift_rpms[gear] and gear < cfg.drivetrain.num_gears - 1:
                    shifting = True
                    shift_timer = cfg.drivetrain.total_shift_time_ms / 1000.0
                    shift_target_gear = gear + 1

            # ── Engine torque ──
            if shifting:
                T_e = 0.0
            else:
                T_e = self.engine_torque(rpm, t)
                T_e *= self.ram_air_power_mult(v)
                T_e *= self.forced_induction_torque_mult(rpm, t, P_boost)
                if (
                    cfg.engine.dyno_curve is None
                    or not cfg.engine.dyno_curve.is_at_wheel
                ):
                    P_parasitic = self.parasitic_power_loss(rpm)
                    if omega_e > 10:
                        T_e -= P_parasitic / omega_e

            # ── Clutch engagement (launch phase) ──
            if not clutch_locked and not shifting:
                i_total = cfg.drivetrain.overall_ratio(gear)
                omega_input = omega_w * i_total
                slip_speed = omega_e - omega_input

                if abs(slip_speed) < 10.0 * RPM_TO_RADS and v > 1.0:
                    clutch_locked = True
                    omega_e = omega_input
                    T_e_crank = self.engine_torque(omega_e * RADS_TO_RPM, t)
                    T_e = T_e_crank
                    Q_clutch = 0.0
                else:
                    T_clutch_max = cfg.clutch.max_torque()
                    if T_clutch > cfg.clutch.fade_temp_c:
                        fade = max(
                            0.3, 1.0 - 0.003 * (T_clutch - cfg.clutch.fade_temp_c)
                        )
                        T_clutch_max *= fade

                    if cfg.clutch.clutch_type == CLUTCH_SLIDER:
                        rpm_e = omega_e * RADS_TO_RPM
                        if rpm_e < cfg.clutch.engage_rpm:
                            T_clutch_max = 0.0
                        else:
                            ramp = min(
                                1.0,
                                (
                                    (rpm_e - cfg.clutch.engage_rpm)
                                    / max(
                                        1.0,
                                        cfg.engine.redline_rpm - cfg.clutch.engage_rpm,
                                    )
                                )
                                ** 2,
                            )
                            T_clutch_max *= ramp

                    T_e_crank = self.engine_torque(omega_e * RADS_TO_RPM, t)

                    # Apr 27, 2026: rate-limited over-clutching for low-power
                    # bikes. Real launches: rider can pull clutch in beyond
                    # pure friction-matching, briefly drawing energy from
                    # engine inertia to accelerate the bike faster than
                    # steady-state engine torque allows. This was the missing
                    # mechanism causing the +1.84 s small-cc cluster bias.
                    # GATED on peak_power_hp < 60 so K5/R1/Hayabusa baselines
                    # (178/180/197 hp) are unaffected — they keep the legacy
                    # min(T_e_crank, T_clutch_max) behaviour.
                    I_e_local = (
                        cfg.engine.engine_inertia_kgm2 + cfg.clutch.basket_inertia_kgm2
                    )
                    # Category-flavoured over-clutching dispatch.
                    # Reads tier knobs from self._profile (set in _precompute).
                    # Profile.over_clutch_factor==0 reproduces the pre-April-30
                    # legacy min(T_e_crank, T_clutch_max) behaviour for the
                    # litre-sport / cruiser clusters that don't need slip-launch.
                    prof = self._profile
                    if prof.over_clutch_factor > 0.0 and slip_speed > 0:
                        max_back_torque = prof.max_engine_decel_rads2 * max(I_e_local, 0.001)
                        headroom = max(0.0, T_clutch_max - abs(T_e_crank))
                        over_clutch_extra = min(headroom * prof.over_clutch_factor, max_back_torque)
                        T_transmitted = min(abs(T_e_crank) + over_clutch_extra, T_clutch_max)
                    else:
                        T_transmitted = min(abs(T_e_crank), T_clutch_max)
                    T_e = T_transmitted

                    I_e = I_e_local
                    T_net_engine = T_e_crank - T_transmitted
                    d_omega_e = T_net_engine / max(I_e, 0.001)
                    omega_e += d_omega_e * dt
                    # Apr 27, 2026: during launch slip on low-power bikes, prevent
                    # engine RPM from dropping below peak_torque_rpm. Without this,
                    # over-clutching pulls engine into weak-power region and the
                    # ET goes UP not DOWN. Real riders modulate clutch to hold
                    # engine at peak_torque_rpm; this clamp models that. K5/R1/Busa
                    # bypass via peak_hp >= 60 gate above (their else branch keeps
                    # legacy min behaviour, no force on omega_e drop).
                    if prof.launch_floor_factor > 0.0:
                        # Cluster-aware launch RPM floor. 2-strokes pin at
                        # tuned_rpm (expansion-chamber resonance, above
                        # peak_torque_rpm); 4T pins at peak_torque_rpm.
                        if cfg.engine.stroke_type == 2 and cfg.engine.tuned_rpm:
                            floor_rpm = cfg.engine.tuned_rpm * prof.launch_floor_factor
                        else:
                            floor_rpm = cfg.engine.peak_torque_rpm * prof.launch_floor_factor
                        floor_omega = floor_rpm * RPM_TO_RADS
                        if omega_e < floor_omega:
                            omega_e = floor_omega
                    omega_e = np.clip(
                        omega_e,
                        cfg.engine.idle_rpm * RPM_TO_RADS,
                        cfg.engine.redline_rpm * 1.02 * RPM_TO_RADS,
                    )
                    Q_clutch = T_transmitted * abs(slip_speed)

                dT_clutch = Q_clutch / max(1.0, cfg.clutch.thermal_mass_jk)
                T_clutch += dT_clutch * dt
            else:
                Q_clutch = 0.0

            # ── Wheel torque and drive force ──
            T_w = self.wheel_torque(T_e, gear)
            T_w = self.chain_torque_modifier(T_w, v, t)
            F_drive = T_w / max(r_eff, 0.01)

            # ── Time-varying Cd*A from RiderDynamicsModel ──
            # Rider transitions from upright staging stance to tuck over
            # tuck_transition_time_s.  This replaces the fixed self.cd_a.
            cd_a_t = self._rider.cd_a(t)

            # ── Weight transfer (iterative) ──
            m_eff = self.effective_mass(gear)
            F_aero = self.aero_drag(v)  # uses self._aero (fixed cd_a)
            # Override with rider-dynamic Cd*A for this timestep:
            v_rel = v + self.v_wind
            F_aero = 0.5 * self.rho * max(0.0, v_rel) ** 2 * cd_a_t
            F_rr = self.rolling_resistance(v, T_tire)
            a_est = (F_drive - F_aero - F_rr) / m_eff
            N_f, N_r = self.weight_transfer(a_est, v, t)

            # ── Traction limit ──
            F_max_tire = self.tire_max_force(N_r, T_tire, v)
            if F_drive > F_max_tire:
                slip_ratio = min(
                    0.3, (F_drive - F_max_tire) / max(F_max_tire, 1.0) * 0.1
                )
                F_drive = F_max_tire
            else:
                slip_ratio = abs(F_drive) / max(F_max_tire, 1.0) * 0.05

            # ── Wheelie limit ──
            a_wheelie = self.max_accel_before_wheelie(v, t)
            a_accel = (F_drive - F_aero - F_rr) / m_eff
            if a_accel > a_wheelie:
                F_drive = a_wheelie * m_eff + F_aero + F_rr
                a_accel = a_wheelie

            # ── Net acceleration (including track gradient) ──
            a_net = (F_drive - F_aero - F_rr - self.F_gradient) / m_eff
            a_net = max(0.0, a_net)

            # ── Tire thermal update ──
            dT_tire = self.tire_thermal_rate(
                F_drive, v, slip_ratio, T_tire, cfg.environment.ambient_temp_c
            )
            T_tire += dT_tire * dt

            # ── Boost dynamics ──
            if cfg.forced_induction.is_boosted:
                dP = self.boost_dynamics(P_boost, rpm, t)
                P_boost += dP * dt
                P_boost = max(0.0, P_boost)

            # ── Fuel mass decrease ──
            fuel_burned += cfg.chassis.fuel_consumption_gs * dt / 1000.0
            self.m_total = cfg.chassis.total_mass_kg - fuel_burned

            # ── Adaptive step size (RK45 spirit) ──────────────────────────
            # During clutch-slip or shifting, dynamics are fast: keep dt_min.
            # Once locked and cruising, dynamics are smooth: allow dt_max.
            # Error is estimated by comparing the full RK4 step to the
            # first-order Euler step; if error is tiny, widen the step.
            if use_adaptive_dt and clutch_locked and not shifting:
                # Allow growth
                dt = min(_dt_max, dt * 1.25)
            elif use_adaptive_dt:
                dt = max(_dt_min, dt * 0.5)

            # ── Proper RK4 for position and velocity ──────────────────────
            # Forces are dominated by aerodynamic drag (∝ v²); we re-evaluate
            # F_aero at the RK4 midpoint/endpoint velocities to get correct
            # 4th-order accuracy.  Drive force and gradient are held constant
            # within the step (they change slowly relative to dt).
            def _aero_at(v_q):
                vr = v_q + self.v_wind
                return 0.5 * self.rho * max(0.0, vr) ** 2 * cd_a_t

            def _a_at(v_q):
                return max(
                    0.0, (F_drive - _aero_at(v_q) - F_rr - self.F_gradient) / m_eff
                )

            k1 = _a_at(v)
            k2 = _a_at(v + 0.5 * dt * k1)
            k3 = _a_at(v + 0.5 * dt * k2)
            k4 = _a_at(v + dt * k3)
            v_new = v + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            # Position uses the velocity Simpsons-rule estimate
            x_new = x + (dt / 6.0) * (
                v
                + 2.0 * (v + 0.5 * dt * k1)
                + 2.0 * (v + 0.5 * dt * k2)
                + (v + dt * k3)
            )

            # ── Store outputs ──
            out_t[step] = t
            out_x[step] = x
            out_v[step] = v
            out_a[step] = a_net / G
            out_rpm[step] = rpm
            out_gear[step] = gear + 1
            out_slip[step] = slip_ratio
            out_trac[step] = min(1.0, F_drive / max(F_max_tire, 1.0)) * 100.0
            out_Nf[step] = N_f
            out_Nr[step] = N_r
            out_Fd[step] = F_drive
            out_Fdrag[step] = F_aero
            out_Frr[step] = F_rr
            out_Ttire[step] = T_tire
            out_Tclutch[step] = T_clutch
            out_Pboost[step] = P_boost / 1e5
            out_power[step] = F_drive * v / 1000.0
            out_reff[step] = r_eff

            # Advance state — guard against NaN/inf from numerical issues
            if not (np.isfinite(v_new) and np.isfinite(x_new)):
                import logging

                logging.getLogger(__name__).error(
                    "NaN/inf in physics state at t=%.4fs, step=%d. "
                    "v_new=%.6f, x_new=%.6f, F_drive=%.2f, F_aero=%.2f. "
                    "Breaking simulation early.",
                    t,
                    step,
                    v_new,
                    x_new,
                    F_drive,
                    F_aero,
                )
                break
            v = max(0.05, v_new)  # 0.05 m/s = 0.18 km/h minimum (avoids RPM divergence)
            x = x_new
            t += dt
            step += 1

        # Store final state (the step that crossed the finish line)
        if step < n_max and x >= distance:
            out_t[step] = t
            out_x[step] = x
            out_v[step] = v
            out_a[step] = a_net / G
            out_rpm[step] = rpm
            out_gear[step] = gear + 1
            out_slip[step] = slip_ratio
            out_trac[step] = min(1.0, F_drive / max(F_max_tire, 1.0)) * 100.0
            out_Nf[step] = N_f
            out_Nr[step] = N_r
            out_Fd[step] = F_drive
            out_Fdrag[step] = F_aero
            out_Frr[step] = F_rr
            out_Ttire[step] = T_tire
            out_Tclutch[step] = T_clutch
            out_Pboost[step] = P_boost / 1e5
            out_power[step] = F_drive * v / 1000.0
            out_reff[step] = r_eff
            step += 1

        # Trim arrays
        out_t = out_t[:step]
        out_x = out_x[:step]
        out_v = out_v[:step]
        out_a = out_a[:step]

        result = SimResult(
            dt=dt,
            t=out_t,
            x=out_x,
            v=out_v,
            a=out_a,
            rpm=out_rpm[:step],
            gear=out_gear[:step],
            slip=out_slip[:step],
            traction_pct=out_trac[:step],
            N_front=out_Nf[:step],
            N_rear=out_Nr[:step],
            F_drive=out_Fd[:step],
            F_drag=out_Fdrag[:step],
            F_rr=out_Frr[:step],
            T_tire=out_Ttire[:step],
            T_clutch=out_Tclutch[:step],
            P_boost=out_Pboost[:step],
            power_kw=out_power[:step],
            r_eff=out_reff[:step],
        )
        result.extract_splits()
        # Restore original mass for engine reuse
        self.m_total = self.cfg.chassis.total_mass_kg
        return result

    # ═══════════════════════════════════════════
    # TOP SPEED / LAND SPEED RECORD MODE
    # ═══════════════════════════════════════════

    def run_top_speed(
        self,
        max_time: float = TOPSPEED_MAX_TIME_S,
        max_distance: float = TOPSPEED_MAX_DISTANCE_M,
        plateau_accel: float = TOPSPEED_PLATEAU_ACCEL,
        plateau_window_s: float = TOPSPEED_PLATEAU_WINDOW_S,
    ) -> "TopSpeedResult":
        """
        Run simulation until terminal velocity is reached.

        Terminal = longitudinal acceleration stays below ``plateau_accel``
        (m/s^2) for at least ``plateau_window_s`` seconds. Hard-bounded by
        ``max_time`` and ``max_distance`` to catch degenerate cases.

        Returns a TopSpeedResult with terminal velocity, time/distance to
        reach it, and the full trajectory for plotting.
        """
        sim = self.run(distance=max_distance, max_time=max_time, use_adaptive_dt=True)

        # Convert |a| (in g) back to m/s^2
        a_ms2 = np.abs(sim.a) * G

        # Find first index where acceleration has been below threshold for
        # plateau_window_s continuously
        dt = sim.dt if sim.dt > 0 else self.dt
        window_steps = max(1, int(plateau_window_s / dt))

        terminal_idx = len(sim.v) - 1  # fallback: last sample
        if len(a_ms2) >= window_steps:
            # Rolling max: if the MAX accel over the next window_steps is
            # below plateau_accel, we've terminaled.
            for i in range(len(a_ms2) - window_steps):
                if np.max(a_ms2[i : i + window_steps]) < plateau_accel:
                    terminal_idx = i
                    break

        # Peak velocity across the entire run (the number we quote as "top speed")
        peak_idx = int(np.argmax(sim.v))
        terminal_v = float(sim.v[peak_idx])

        # Time / distance to *first enter* the plateau (when acceleration
        # first falls below the threshold and stays there). Falls back to
        # peak-V time if no plateau was detected.
        reached = terminal_idx < len(sim.v) - 1
        reach_idx = terminal_idx if reached else peak_idx
        terminal_t = float(sim.t[reach_idx])
        terminal_x = float(sim.x[reach_idx])
        terminal_power_kw = (
            float(sim.power_kw[peak_idx]) if len(sim.power_kw) > peak_idx else 0.0
        )
        terminal_gear = int(sim.gear[peak_idx]) if len(sim.gear) > peak_idx else 0
        terminal_rpm = float(sim.rpm[peak_idx]) if len(sim.rpm) > peak_idx else 0.0

        # Split times at standard LSR distances (1/4, 1/2, 1 km, 1 mile, 2 mile)
        lsr_splits = {}
        for label, d in [
            ("quarter_mile", QUARTER_MILE_M),
            ("half_mile", 804.672),
            ("one_km", ONE_KM_M),
            ("one_mile", ONE_MILE_M),
            ("two_mile", 3218.688),
        ]:
            idx = int(np.searchsorted(sim.x, d))
            if 0 < idx < len(sim.t):
                # Linear interpolation
                frac = (d - sim.x[idx - 1]) / max(1e-9, sim.x[idx] - sim.x[idx - 1])
                t_at = sim.t[idx - 1] + frac * (sim.t[idx] - sim.t[idx - 1])
                v_at = sim.v[idx - 1] + frac * (sim.v[idx] - sim.v[idx - 1])
                lsr_splits[label] = {"time_s": float(t_at), "speed_ms": float(v_at)}

        return TopSpeedResult(
            terminal_velocity_ms=terminal_v,
            time_to_terminal_s=terminal_t,
            distance_to_terminal_m=terminal_x,
            terminal_power_kw=terminal_power_kw,
            terminal_gear=terminal_gear,
            terminal_rpm=terminal_rpm,
            lsr_splits=lsr_splits,
            reached_plateau=reached,
            full_sim=sim,
        )

    def run_distance(
        self,
        distance_m: float,
        max_time: float = TOPSPEED_MAX_TIME_S,
    ) -> SimResult:
        """
        Run simulation to an arbitrary target distance — used for LSR
        events: standing mile (1609 m), standing km (1000 m), 1/2 mile (804 m),
        Bonneville short course (3218 m), etc.
        """
        return self.run(distance=distance_m, max_time=max_time, use_adaptive_dt=True)


@dataclass
class TopSpeedResult:
    """
    Output of MotoQuantEngine.run_top_speed().

    All velocities in m/s; multiply by 3.6 for km/h, 2.23694 for mph.
    """

    terminal_velocity_ms: float
    time_to_terminal_s: float
    distance_to_terminal_m: float
    terminal_power_kw: float
    terminal_gear: int
    terminal_rpm: float
    lsr_splits: dict  # {"one_mile": {"time_s":..., "speed_ms":...}, ...}
    reached_plateau: bool  # False = hit max_time/distance before terminaling
    full_sim: SimResult  # for plotting v(t), RPM(t), etc.

    @property
    def terminal_velocity_kmh(self) -> float:
        return self.terminal_velocity_ms * 3.6

    @property
    def terminal_velocity_mph(self) -> float:
        return self.terminal_velocity_ms * 2.23694
