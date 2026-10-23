//! The run loop — a float-op-for-float-op transliteration of
//! `MotoQuantEngine.run()` (motoquant/physics.py) and the sub-model methods it
//! calls (motoquant/submodels/*.py, models.py helpers).
//!
//! Rules that keep it bit-identical with Python:
//! * every binary expression is evaluated in Python's left-to-right order
//!   (`a * b * c` is `(a * b) * c`), never re-associated or fused;
//! * every `**` goes through [`fmath::pow`] (C `pow`, see fmath.rs);
//! * Python `max(a, b)` / `min(a, b)` keep their argument-order semantics
//!   ([`py_max`] / [`py_min`]: the first argument wins ties and NaN-vs-number
//!   comparisons that are false);
//! * loop invariants come pre-resolved from Python (config.rs), so no Python
//!   property is re-derived here.

use crate::config::{BoostType, Curve, ResolvedConfig};
use crate::fmath::{self, ExpImpl};

/// Python `max(a, b)`: returns `a` unless `b > a`.
#[inline(always)]
pub fn py_max(a: f64, b: f64) -> f64 {
    if b > a {
        b
    } else {
        a
    }
}

/// Python `min(a, b)`: returns `a` unless `b < a`.
#[inline(always)]
pub fn py_min(a: f64, b: f64) -> f64 {
    if b < a {
        b
    } else {
        a
    }
}

/// All per-step output channels of `SimResult` (struct of arrays).
#[derive(Debug, Clone, Default)]
pub struct Channels {
    pub t: Vec<f64>,
    pub x: Vec<f64>,
    pub v: Vec<f64>,
    pub a: Vec<f64>,
    pub rpm: Vec<f64>,
    pub gear: Vec<i64>,
    pub slip: Vec<f64>,
    pub traction_pct: Vec<f64>,
    pub n_front: Vec<f64>,
    pub n_rear: Vec<f64>,
    pub f_drive: Vec<f64>,
    pub f_drag: Vec<f64>,
    pub f_rr: Vec<f64>,
    pub t_tire: Vec<f64>,
    pub t_clutch: Vec<f64>,
    pub p_boost: Vec<f64>,
    pub power_kw: Vec<f64>,
    pub r_eff: Vec<f64>,
}

/// Float channel names in output order (gear is reported separately as i64).
pub const FLOAT_CHANNELS: [&str; 17] = [
    "t", "x", "v", "a", "rpm", "slip", "traction_pct", "N_front", "N_rear", "F_drive",
    "F_drag", "F_rr", "T_tire", "T_clutch", "P_boost", "power_kw", "r_eff",
];

impl Channels {
    fn with_capacity(n: usize) -> Channels {
        let v = || Vec::with_capacity(n);
        Channels {
            t: v(),
            x: v(),
            v: v(),
            a: v(),
            rpm: v(),
            gear: Vec::with_capacity(n),
            slip: v(),
            traction_pct: v(),
            n_front: v(),
            n_rear: v(),
            f_drive: v(),
            f_drag: v(),
            f_rr: v(),
            t_tire: v(),
            t_clutch: v(),
            p_boost: v(),
            power_kw: v(),
            r_eff: v(),
        }
    }

    pub fn len(&self) -> usize {
        self.t.len()
    }

    pub fn is_empty(&self) -> bool {
        self.t.is_empty()
    }

    fn pop(&mut self) {
        self.t.pop();
        self.x.pop();
        self.v.pop();
        self.a.pop();
        self.rpm.pop();
        self.gear.pop();
        self.slip.pop();
        self.traction_pct.pop();
        self.n_front.pop();
        self.n_rear.pop();
        self.f_drive.pop();
        self.f_drag.pop();
        self.f_rr.pop();
        self.t_tire.pop();
        self.t_clutch.pop();
        self.p_boost.pop();
        self.power_kw.pop();
        self.r_eff.pop();
    }

    /// Float channels in [`FLOAT_CHANNELS`] order.
    pub fn float_channels(&self) -> [&Vec<f64>; 17] {
        [
            &self.t,
            &self.x,
            &self.v,
            &self.a,
            &self.rpm,
            &self.slip,
            &self.traction_pct,
            &self.n_front,
            &self.n_rear,
            &self.f_drive,
            &self.f_drag,
            &self.f_rr,
            &self.t_tire,
            &self.t_clutch,
            &self.p_boost,
            &self.power_kw,
            &self.r_eff,
        ]
    }
}

/// Result of [`Engine::run`]: channels + the loop's final `dt`.
#[derive(Debug, Clone, Default)]
pub struct RunOutput {
    pub dt: f64,
    pub ch: Channels,
    /// True when the NaN/inf guard broke the loop (Python logs an error).
    pub nan_break: bool,
    /// Integration steps executed (diagnostics / benchmarks).
    pub steps: u64,
}

/// Engine bound to one resolved config.
pub struct Engine<'a> {
    c: &'a ResolvedConfig,
    exp_impl: ExpImpl,
    g: f64,
    rpm_to_rads: f64,
    rads_to_rpm: f64,
    half_rho: f64,
    idle_half: f64,
    redline_102: f64,
}

impl<'a> Engine<'a> {
    pub fn new(c: &'a ResolvedConfig) -> Result<Engine<'a>, String> {
        c.validate()?;
        let exp_impl = ExpImpl::parse(&c.exp_impl).ok_or("bad exp_impl")?;
        Ok(Engine {
            c,
            exp_impl,
            g: c.constants.g,
            rpm_to_rads: c.constants.rpm_to_rads,
            rads_to_rpm: c.constants.rads_to_rpm,
            // `_half_rho = 0.5 * self.rho`
            half_rho: 0.5 * c.env.rho,
            // EngineModel.torque: `eng.idle_rpm * 0.5`, `eng.redline_rpm * 1.02`
            idle_half: c.engine.idle_rpm * 0.5,
            redline_102: c.engine.redline_rpm * 1.02,
        })
    }

    // ── models.py: EngineParams.get_torque ────────────────────────────────
    pub fn get_torque(&self, rpm: f64) -> f64 {
        match &self.c.engine.curve {
            Curve::Dyno { rpm: xp, torque_nm } => crate::interp::np_interp(rpm, xp, torque_nm),
            Curve::Parabolic {
                idle_rpm,
                redline_rpm,
                peak_torque_rpm,
                peak_torque_nm,
            } => {
                let rpm_range = redline_rpm - idle_rpm;
                if rpm_range <= 0.0 {
                    return 0.0;
                }
                let x = (rpm - peak_torque_rpm) / (rpm_range * 0.6);
                py_max(0.0, peak_torque_nm * (1.0 - x * x))
            }
            Curve::TwoStroke {
                idle_rpm,
                redline_rpm,
                tuned_rpm,
                cylinders,
                displacement_cc,
                powervalve,
                peak_torque_nm,
            } => {
                if rpm < idle_rpm * 1.05 {
                    return 0.0;
                }
                let tuned = *tuned_rpm;
                let cyls = *cylinders;
                let (band_lo, band_hi, baseline) = if *powervalve {
                    (0.18, 0.12, 0.20)
                } else if cyls >= 3 {
                    (0.55, 0.30, 0.50)
                } else if cyls == 2 {
                    (0.30, 0.15, 0.25)
                } else if cyls == 1 && matches!(displacement_cc, Some(d) if *d < 200.0) {
                    (0.35, 0.25, 0.35)
                } else {
                    (0.25, 0.15, 0.25)
                };
                let x = if rpm <= tuned {
                    (tuned - rpm) / py_max(1.0, tuned * band_lo)
                } else {
                    (rpm - tuned) / py_max(1.0, tuned * band_hi)
                };
                // math.exp(-1.5 * x * x)
                let mut factor = fmath::exp_libm(-1.5 * x * x);
                factor = py_max(baseline, factor);
                if rpm > redline_rpm * 1.02 {
                    return 0.0;
                }
                peak_torque_nm * factor
            }
        }
    }

    // ── submodels/engine.py: EngineModel.torque ───────────────────────────
    #[inline]
    pub fn engine_torque(&self, rpm: f64) -> f64 {
        let e = &self.c.engine;
        if rpm < self.idle_half {
            return 0.0;
        }
        if rpm > self.redline_102 {
            return 0.0;
        }
        let mut t_base = self.get_torque(rpm);
        if e.at_wheel {
            t_base /= e.eta_dt;
        }
        let mut t_corr = t_base * e.power_correction;
        let temp = e.coolant_temp_c;
        if temp < 70.0 {
            t_corr *= 0.97;
        } else if temp > 100.0 {
            t_corr *= 0.99;
        }
        t_corr
    }

    // ── submodels/aero.py ─────────────────────────────────────────────────
    #[inline]
    pub fn ram_air_power_mult(&self, v: f64) -> f64 {
        let eta = self.c.aero.ram_air_efficiency;
        let v_rel = v + self.c.env.v_wind;
        if eta <= 0.0 || v_rel < 20.0 {
            return 1.0;
        }
        let rho = self.c.env.rho;
        let p_ram = 0.5 * rho * fmath::sq(v_rel) * eta;
        let mut p_atm = rho * 287.058 * (self.c.env.ambient_temp_c + 273.15);
        if p_atm <= 0.0 {
            p_atm = 101325.0;
        }
        let k_ram = 0.5;
        1.0 + k_ram * p_ram / p_atm
    }

    #[inline]
    pub fn aero_lift(&self, v: f64) -> f64 {
        let v_rel = v + self.c.env.v_wind;
        if v_rel <= 0.0 {
            return 0.0;
        }
        0.5 * self.c.env.rho * fmath::sq(v_rel) * self.c.aero.cl * self.c.aero.frontal_area_m2
    }

    // ── submodels/forced_induction.py ─────────────────────────────────────
    #[inline]
    pub fn fi_torque_mult(&self, rpm: f64, t: f64, p_boost: f64) -> f64 {
        let fi = &self.c.fi;
        match fi.boost_type {
            BoostType::Na => 1.0,
            BoostType::Turbo => {
                let mut p_atm = self.c.env.rho * 287.058 * (self.c.env.ambient_temp_c + 273.15);
                if p_atm <= 0.0 {
                    p_atm = 101325.0;
                }
                let mut boost_ratio = 1.0 + p_boost / p_atm;
                if fi.intercooler {
                    let eta_ic = fi.intercooler_effectiveness;
                    let temp_penalty = 1.0 - 0.02 * (1.0 - eta_ic) * (p_boost / 100000.0);
                    boost_ratio *= py_max(0.90, temp_penalty);
                }
                boost_ratio
            }
            BoostType::ScRoots | BoostType::ScCentrifugal => {
                let p_atm = 101325.0;
                1.0 + p_boost / p_atm
            }
            BoostType::N2o => {
                let ramp = py_min(1.0, t / py_max(0.1, fi.n2o_ramp_duration_s));
                let hp_add = fi.n2o_hp_per_stage * fi.n2o_stages * ramp;
                if rpm > 1000.0 {
                    let t_base = self.get_torque(rpm);
                    if t_base > 0.0 {
                        let t_add = hp_add * 745.7 / (rpm * self.rpm_to_rads);
                        return 1.0 + t_add / t_base;
                    }
                }
                1.0
            }
        }
    }

    #[inline]
    pub fn boost_rate(&self, p_boost: f64, rpm: f64) -> f64 {
        let fi = &self.c.fi;
        match fi.boost_type {
            BoostType::Turbo => {
                let p_target = fi.target_boost_bar * 1e5;
                let tau = fi.turbo_spool_time_s;
                (p_target - p_boost) / py_max(tau, 0.05)
            }
            BoostType::ScCentrifugal => {
                let rpm_frac = rpm / py_max(1.0, self.c.engine.redline_rpm);
                let p_target = fi.target_boost_bar * 1e5 * fmath::sq(rpm_frac);
                (p_target - p_boost) / 0.1
            }
            BoostType::ScRoots => {
                let p_target = fi.target_boost_bar * 1e5;
                (p_target - p_boost) / 0.05
            }
            _ => 0.0,
        }
    }

    // ── submodels/parasitic.py + models.py ParasiticParams ────────────────
    #[inline]
    pub fn parasitic_power_loss(&self, rpm: f64) -> f64 {
        let p = &self.c.parasitic;
        let rpm_frac = rpm / py_max(1.0, self.c.engine.redline_rpm);
        let mut total = 0.0;
        if p.alternator_present {
            total += p.alternator_power_w;
        }
        if !p.water_pump_electric {
            total += 350.0 * rpm_frac;
        }
        total += p.oil_pump_power_w * rpm_frac;
        total += p.valve_train_power_w * rpm_frac;
        total -= p.parasitic_delta_hp * 745.7;
        py_max(0.0, total) * p.mult
    }

    // ── submodels/tire.py ─────────────────────────────────────────────────
    #[inline]
    pub fn tire_effective_radius(&self, omega_w: f64) -> f64 {
        let tr = &self.c.tire;
        let delta_r = tr.growth_coeff * fmath::sq(omega_w) * tr.rear_rolling_radius_m;
        tr.rear_rolling_radius_m + delta_r
    }

    #[inline]
    pub fn tire_friction_coeff(&self, n_rear: f64, t_tire: f64) -> f64 {
        let tr = &self.c.tire;
        let mu_base = tr.mu_peak;
        let mut mu_load = mu_base * (1.0 - tr.load_sensitivity_k * n_rear);
        mu_load = py_max(0.3, mu_load);
        let sigma_t = 25.0;
        let t_opt = tr.optimal_temp_c;
        // np.exp(-(((T_tire - T_opt) / sigma_T) ** 2))
        let mut thermal_factor = self.exp_impl.exp(-fmath::sq((t_tire - t_opt) / sigma_t));
        if t_tire > tr.reversion_temp_c {
            let reversion_penalty = 1.0 - 0.01 * (t_tire - tr.reversion_temp_c);
            thermal_factor *= py_max(0.3, reversion_penalty);
        }
        let mu_thermal = mu_load * (0.85 + 0.15 * thermal_factor);
        let t_tire_k = t_tire + 273.15;
        let p_ratio = t_tire_k / py_max(tr.t_ref_k, 250.0);
        let pressure_grip_factor = py_min(1.0, fmath::pow(1.0 / py_max(p_ratio, 1.0), 0.3));
        let mu_pressure = mu_thermal * pressure_grip_factor;
        mu_pressure * tr.mu_prep
    }

    #[inline]
    pub fn tire_max_force(&self, n_rear: f64, t_tire: f64) -> f64 {
        self.tire_friction_coeff(n_rear, t_tire) * n_rear
    }

    #[inline]
    pub fn tire_thermal_rate(&self, f_x: f64, v: f64, slip_ratio: f64, t_tire: f64) -> f64 {
        let tr = &self.c.tire;
        let t_ambient = self.c.env.ambient_temp_c;
        let v_slip = (v * slip_ratio).abs();
        let q_friction = f_x.abs() * v_slip;
        let h_conv = 10.0 + 0.5 * v;
        let a_surface = 0.15;
        let q_conv = h_conv * a_surface * (t_tire - t_ambient);
        let t_road = match self.c.env.t_road {
            Some(tr_) => tr_,
            None => t_ambient + 5.0,
        };
        let q_cond =
            tr.thermal_conductivity * (tr.contact_patch_cm2 * 1e-4) * (t_tire - t_road) / 0.005;
        (q_friction - q_conv - q_cond) / py_max(1.0, tr.tread_mass_kg * tr.specific_heat_rubber)
    }

    // ── submodels/rolling_resistance.py ───────────────────────────────────
    #[inline]
    pub fn rolling_resistance(&self, v: f64, t_tire: f64, m_total: f64) -> f64 {
        let tr = &self.c.tire;
        let mut crr = tr.crr_base + tr.crr_speed_coeff * fmath::sq(v);
        if t_tire > 30.0 {
            crr *= py_max(0.75, 1.0 + tr.crr_temp_coeff * (t_tire - 30.0));
        }
        crr * m_total * self.g * self.c.env.rr_multiplier
    }

    // ── models.py RiderParams.cog_offset ──────────────────────────────────
    #[inline]
    pub fn rider_cog_offset(&self, t: f64) -> f64 {
        let r = &self.c.rider;
        if t < 0.0 {
            return r.launch_forward_shift_mm / 1000.0;
        }
        if t < r.tuck_transition_time_s {
            let frac = t / r.tuck_transition_time_s;
            let forward = r.launch_forward_shift_mm / 1000.0;
            return forward * (1.0 - frac);
        }
        -0.03
    }

    // ── submodels/rider_dynamics.py ───────────────────────────────────────
    #[inline]
    pub fn rider_cd_a(&self, t: f64) -> f64 {
        let a = &self.c.aero;
        let frac = if t <= 0.0 {
            0.0
        } else if t >= a.transition_s {
            1.0
        } else {
            // math.sin((t / self._transition_s) * math.pi / 2.0) ** 2
            fmath::sq(fmath::sin((t / a.transition_s) * self.c.constants.pi / 2.0))
        };
        a.cd_a_upright * (1.0 - frac) + a.cd_a_full * frac
    }

    // ── submodels/weight_transfer.py ──────────────────────────────────────
    #[inline]
    pub fn weight_transfer(&self, accel: f64, v: f64, t: f64, m_total: f64) -> (f64, f64) {
        let ch = &self.c.chassis;
        let h = ch.cog_height_m;
        let l = ch.wheelbase_m;
        let rider_offset = self.rider_cog_offset(t);
        let l_f_eff = ch.l_f - rider_offset;
        let l_r_eff = l - l_f_eff;
        let n_f_static = m_total * self.g * l_r_eff / l;
        let n_r_static = m_total * self.g * l_f_eff / l;
        let mut delta_n = m_total * accel * h / l;
        let anti_squat_boost = 1.0 + (ch.anti_squat_frac - 1.0) * 0.15;
        delta_n *= anti_squat_boost;
        let f_lift = self.aero_lift(v);
        let n_f = n_f_static - delta_n - f_lift * 0.4;
        let n_r = n_r_static + delta_n - f_lift * 0.6;
        (py_max(0.0, n_f), py_max(0.0, n_r))
    }

    // ── submodels/wheelie.py ──────────────────────────────────────────────
    #[inline]
    pub fn max_accel_before_wheelie(&self, v: f64, t: f64, m_total: f64) -> f64 {
        let ch = &self.c.chassis;
        let l = ch.wheelbase_m;
        let h = ch.cog_height_m;
        let rider_offset = self.rider_cog_offset(t);
        let l_f_eff = ch.l_f - rider_offset;
        let l_r_eff = l - l_f_eff;
        let mut a_wheelie = self.g * l_r_eff / h;
        let f_lift = self.aero_lift(v);
        if m_total > 0.0 {
            a_wheelie -= f_lift * 0.4 / (m_total * h / l);
        }
        if !self.c.wheelie.counter_rotating {
            a_wheelie *= 0.985;
        } else {
            a_wheelie *= 1.01;
        }
        if self.c.wheelie.wheelie_bar {
            let bar_ext = self.c.wheelie.bar_length_mm / 1000.0;
            let a_wheelie_bar = self.g * (l_r_eff + bar_ext) / h;
            a_wheelie = py_max(a_wheelie, a_wheelie_bar);
        }
        a_wheelie
    }

    // ── submodels/drivetrain.py ───────────────────────────────────────────
    #[inline]
    fn engine_rpm_from_speed(&self, v: f64, gear: usize, r_eff: f64) -> f64 {
        if r_eff <= 0.0 {
            return 0.0;
        }
        let omega_w = v / r_eff;
        let i_total = self.c.drivetrain.overall_ratios[gear];
        let omega_e = omega_w * i_total;
        omega_e * self.rads_to_rpm
    }

    #[inline]
    fn effective_mass(&self, gear: usize, m_total: f64) -> f64 {
        let m = &self.c.mass;
        m_total + m.m_rot_engine[gear] + m.m_rot_rear + m.m_rot_front
    }

    #[inline]
    fn chain_torque_modifier(&self, t_wheel: f64, v: f64, t: f64) -> f64 {
        if !self.c.drivetrain.chain {
            return t_wheel;
        }
        if v < 1.0 && t < 0.1 {
            let slack_factor = py_min(1.0, t / 0.05);
            return t_wheel * slack_factor;
        }
        t_wheel
    }

    /// `MotoQuantEngine.run(distance, max_time, use_adaptive_dt)`.
    pub fn run(&self, distance: f64, max_time: f64, use_adaptive_dt: bool) -> Result<RunOutput, String> {
        let c = self.c;
        let g_const = self.g;
        let rpm_to_rads = self.rpm_to_rads;
        let rads_to_rpm = self.rads_to_rpm;
        let mut dt = c.dt;

        let dt_min = 0.0005;
        let dt_max = 0.005;

        let shift_rpms = &c.drivetrain.shift_rpms;
        let overall = &c.drivetrain.overall_ratios;

        let mut v: f64 = 0.001;
        let mut x: f64 = 0.0;
        let mut gear: usize = 0;
        let mut t_tire = c.tire.t_tire_launch;
        let mut t_clutch = c.clutch.t_clutch0;
        let mut p_boost = c.fi.p_boost0;
        let mut omega_e = c.launch.omega_e0;
        let mut r_eff = c.tire.rear_rolling_radius_m;
        let mut clutch_locked = false;
        let mut shifting = false;
        let mut shift_timer = 0.0;
        let mut shift_target_gear: usize = 0;
        let mut fuel_burned = 0.0;
        let mut m_total = c.mass.m_total0;

        let half_rho = self.half_rho;
        let v_wind = c.env.v_wind;
        let f_gradient = c.mass.f_gradient;
        let lock_thresh = c.launch.lock_thresh;
        let idle_omega = c.launch.idle_omega;
        let redline_omega_clip = c.launch.redline_omega_clip;
        let t_clutch_cap = c.clutch.t_cap;
        let top_gear_idx = overall.len() - 1;
        let shift_time_s = c.drivetrain.shift_time_s;
        let cd_a_floor = c.aero.cd_a_floor;
        let v_limiter = c.drivetrain.v_limiter;
        let at_wheel = c.engine.at_wheel;
        let boosted = c.fi.boost_type != BoostType::Na;
        let mut t_e_curve = 0.0;

        // n_max = int(max_time / dt) + 1  (Python int() truncates toward 0)
        let q = max_time / dt;
        if !(q > -1.0) {
            return Err(format!(
                "negative dimensions are not allowed (max_time={max_time}, dt={dt})"
            ));
        }
        let mut n_max: i64 = (q as i64).saturating_add(1);
        let cap = (n_max.clamp(0, 1 << 22)) as usize;
        let mut ch = Channels::with_capacity(cap);

        let mut step: i64 = 0;
        let mut t: f64 = 0.0;
        let mut nan_break = false;

        // Values carried out of the last iteration for the final-step store.
        let mut a_net = 0.0;
        let mut rpm = 0.0;
        let mut slip_ratio = 0.0;
        let mut f_drive = 0.0;
        let mut f_max_tire = 0.0;
        let mut n_f = 0.0;
        let mut n_r = 0.0;
        let mut f_aero = 0.0;
        let mut f_rr = 0.0;
        let mut ran_once = false;

        while x < distance && t < max_time && step < n_max - 1 {
            ran_once = true;
            // Step-budget growth (adaptive mode only).
            if use_adaptive_dt && step >= n_max - 2 {
                n_max *= 2;
            }

            // ── Current RPM and wheel speed ──
            let mut omega_w = v / py_max(r_eff, 0.15);
            r_eff = self.tire_effective_radius(omega_w);
            omega_w = v / py_max(r_eff, 0.15);

            if clutch_locked {
                rpm = self.engine_rpm_from_speed(v, gear, r_eff);
                omega_e = rpm * rpm_to_rads;
            } else {
                rpm = omega_e * rads_to_rpm;
            }

            // ── Shift logic ──
            if shifting {
                shift_timer -= dt;
                if shift_timer <= 0.0 {
                    gear = shift_target_gear;
                    shifting = false;
                    rpm = self.engine_rpm_from_speed(v, gear, r_eff);
                    omega_e = rpm * rpm_to_rads;
                }
            }
            if !shifting && clutch_locked && rpm >= shift_rpms[gear] && gear < top_gear_idx {
                shifting = true;
                shift_timer = shift_time_s;
                shift_target_gear = gear + 1;
            }

            // ── Engine torque ──
            let mut t_e;
            if shifting {
                t_e = 0.0;
            } else {
                t_e_curve = self.engine_torque(rpm);
                t_e = t_e_curve;
                t_e *= self.ram_air_power_mult(v);
                t_e *= self.fi_torque_mult(rpm, t, p_boost);
                if !at_wheel && omega_e > 10.0 {
                    let p_parasitic = self.parasitic_power_loss(rpm);
                    t_e -= p_parasitic / omega_e;
                }
            }

            // ── Clutch engagement (launch phase) ──
            if !clutch_locked && !shifting {
                let i_total = overall[gear];
                let omega_input = omega_w * i_total;
                let slip_speed = omega_e - omega_input;
                let q_clutch;

                if slip_speed.abs() < lock_thresh && v > 1.0 {
                    clutch_locked = true;
                    omega_e = omega_input;
                    let rpm_lock = omega_e * rads_to_rpm;
                    let mut t_e_crank = self.engine_torque(rpm_lock)
                        * self.ram_air_power_mult(v)
                        * self.fi_torque_mult(rpm_lock, t, p_boost);
                    if !at_wheel && omega_e > 10.0 {
                        t_e_crank -= self.parasitic_power_loss(rpm_lock) / omega_e;
                    }
                    t_e = t_e_crank;
                    q_clutch = 0.0;
                } else {
                    let mut t_clutch_max = t_clutch_cap;
                    if t_clutch > c.clutch.fade_temp_c {
                        let fade = py_max(0.3, 1.0 - 0.003 * (t_clutch - c.clutch.fade_temp_c));
                        t_clutch_max *= fade;
                    }
                    if c.clutch.slider {
                        let rpm_e = omega_e * rads_to_rpm;
                        if rpm_e < c.clutch.engage_rpm {
                            t_clutch_max = 0.0;
                        } else {
                            let ramp = py_min(
                                1.0,
                                fmath::sq(
                                    (rpm_e - c.clutch.engage_rpm)
                                        / py_max(1.0, c.engine.redline_rpm - c.clutch.engage_rpm),
                                ),
                            );
                            t_clutch_max *= ramp;
                        }
                    }

                    let mut t_e_crank = t_e_curve
                        * self.ram_air_power_mult(v)
                        * self.fi_torque_mult(rpm, t, p_boost);
                    if !at_wheel && omega_e > 10.0 {
                        t_e_crank -= self.parasitic_power_loss(rpm) / omega_e;
                    }

                    let i_e_local = c.clutch.engine_inertia_kgm2 + c.clutch.basket_inertia_kgm2;
                    let t_transmitted = if c.launch.over_clutch_factor > 0.0 && slip_speed > 0.0 {
                        let max_back_torque =
                            c.launch.max_engine_decel_rads2 * py_max(i_e_local, 0.001);
                        let headroom = py_max(0.0, t_clutch_max - t_e_crank.abs());
                        let over_clutch_extra =
                            py_min(headroom * c.launch.over_clutch_factor, max_back_torque);
                        py_min(t_e_crank.abs() + over_clutch_extra, t_clutch_max)
                    } else {
                        py_min(t_e_crank.abs(), t_clutch_max)
                    };
                    t_e = t_transmitted;

                    let i_e = i_e_local;
                    let t_net_engine = t_e_crank - t_transmitted;
                    let d_omega_e = t_net_engine / py_max(i_e, 0.001);
                    omega_e += d_omega_e * dt;
                    if let Some(floor_omega) = c.launch.floor_omega {
                        if omega_e < floor_omega {
                            omega_e = floor_omega;
                        }
                    }
                    omega_e = py_min(py_max(omega_e, idle_omega), redline_omega_clip);
                    q_clutch = t_transmitted * slip_speed.abs();
                }

                let d_t_clutch = q_clutch / py_max(1.0, c.clutch.thermal_mass_jk);
                t_clutch += d_t_clutch * dt;
            }

            // ── Wheel torque and drive force ──
            let mut t_w = t_e * overall[gear] * c.engine.eta_dt;
            t_w = self.chain_torque_modifier(t_w, v, t);
            f_drive = t_w / py_max(r_eff, 0.01);

            // ── Time-varying Cd*A ──
            let mut cd_a_t = self.rider_cd_a(t);
            if cd_a_t < cd_a_floor {
                cd_a_t = cd_a_floor;
            }

            // ── Weight transfer ──
            let m_eff = self.effective_mass(gear, m_total);
            let v_rel = v + v_wind;
            f_aero = half_rho * fmath::sq(py_max(0.0, v_rel)) * cd_a_t;
            f_rr = self.rolling_resistance(v, t_tire, m_total);
            let a_est = (f_drive - f_aero - f_rr) / m_eff;
            let (nf0, nr0) = self.weight_transfer(a_est, v, t, m_total);
            n_f = nf0;
            n_r = nr0;

            // ── Traction limit ──
            f_max_tire = self.tire_max_force(n_r, t_tire);
            if f_drive > f_max_tire {
                let f_demand = f_drive;
                let mut f_cap = f_max_tire;
                for _ in 0..2 {
                    let a_cap = (f_cap - f_aero - f_rr) / m_eff;
                    let (a, b) = self.weight_transfer(a_cap, v, t, m_total);
                    n_f = a;
                    n_r = b;
                    f_max_tire = self.tire_max_force(n_r, t_tire);
                    f_cap = py_min(f_demand, f_max_tire);
                }
                slip_ratio = py_min(0.3, (f_demand - f_max_tire) / py_max(f_max_tire, 1.0) * 0.1);
                f_drive = f_cap;
            } else {
                slip_ratio = f_drive.abs() / py_max(f_max_tire, 1.0) * 0.05;
            }

            // ── Wheelie limit ──
            let a_wheelie = self.max_accel_before_wheelie(v, t, m_total);
            let a_accel = (f_drive - f_aero - f_rr) / m_eff;
            if a_accel > a_wheelie {
                f_drive = a_wheelie * m_eff + f_aero + f_rr;
            }

            // ── Net acceleration ──
            a_net = (f_drive - f_aero - f_rr - f_gradient) / m_eff;
            if !clutch_locked {
                a_net = py_max(0.0, a_net);
            }
            if let Some(vl) = v_limiter {
                if v >= vl {
                    a_net = py_min(0.0, a_net);
                }
            }

            // ── Tire thermal update ──
            let d_t_tire = self.tire_thermal_rate(f_drive, v, slip_ratio, t_tire);
            t_tire += d_t_tire * dt;

            // ── Boost dynamics ──
            if boosted {
                let d_p = self.boost_rate(p_boost, rpm);
                p_boost += d_p * dt;
                p_boost = py_max(0.0, p_boost);
            }

            // ── Fuel mass decrease ──
            fuel_burned += c.mass.fuel_consumption_gs * dt / 1000.0;
            m_total = c.mass.m_total0 - fuel_burned;

            // ── Adaptive step size ──
            if use_adaptive_dt && clutch_locked && !shifting {
                dt = py_min(dt_max, dt * 1.25);
            } else if use_adaptive_dt {
                dt = py_max(dt_min, dt * 0.5);
            }

            // ── RK4 ──
            let k1 = a_net;
            let v_q1 = v + 0.5 * dt * k1;
            let mut vr_q = v_q1 + v_wind;
            let mut k2 = (f_drive - half_rho * fmath::sq(py_max(0.0, vr_q)) * cd_a_t - f_rr - f_gradient) / m_eff;
            if !clutch_locked {
                k2 = py_max(0.0, k2);
            }
            if let Some(vl) = v_limiter {
                if v_q1 >= vl {
                    k2 = py_min(0.0, k2);
                }
            }
            let v_q2 = v + 0.5 * dt * k2;
            vr_q = v_q2 + v_wind;
            let mut k3 = (f_drive - half_rho * fmath::sq(py_max(0.0, vr_q)) * cd_a_t - f_rr - f_gradient) / m_eff;
            if !clutch_locked {
                k3 = py_max(0.0, k3);
            }
            if let Some(vl) = v_limiter {
                if v_q2 >= vl {
                    k3 = py_min(0.0, k3);
                }
            }
            let v_q3 = v + dt * k3;
            vr_q = v_q3 + v_wind;
            let mut k4 = (f_drive - half_rho * fmath::sq(py_max(0.0, vr_q)) * cd_a_t - f_rr - f_gradient) / m_eff;
            if !clutch_locked {
                k4 = py_max(0.0, k4);
            }
            if let Some(vl) = v_limiter {
                if v_q3 >= vl {
                    k4 = py_min(0.0, k4);
                }
            }
            let v_new = v + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4);
            let x_new = x + (dt / 6.0) * (v + 2.0 * v_q1 + 2.0 * v_q2 + v_q3);

            // ── Store outputs ──
            ch.t.push(t);
            ch.x.push(x);
            ch.v.push(v);
            ch.a.push(a_net / g_const);
            ch.rpm.push(rpm);
            ch.gear.push(gear as i64 + 1);
            ch.slip.push(slip_ratio);
            ch.traction_pct.push(py_min(1.0, f_drive / py_max(f_max_tire, 1.0)) * 100.0);
            ch.n_front.push(n_f);
            ch.n_rear.push(n_r);
            ch.f_drive.push(f_drive);
            ch.f_drag.push(f_aero);
            ch.f_rr.push(f_rr);
            ch.t_tire.push(t_tire);
            ch.t_clutch.push(t_clutch);
            ch.p_boost.push(p_boost / 1e5);
            ch.power_kw.push(f_drive * v / 1000.0);
            ch.r_eff.push(r_eff);

            if !(v_new.is_finite() && x_new.is_finite()) {
                // Python logs + breaks; the record at index `step` is trimmed.
                ch.pop();
                nan_break = true;
                break;
            }
            v = py_max(0.05, v_new);
            x = x_new;
            t += dt;
            step += 1;
        }

        // Final state (the step that crossed the finish line).
        if step < n_max && x >= distance {
            if !ran_once {
                // Python reads loop locals (a_net, rpm, …) here that were
                // never bound → UnboundLocalError. Mirror it as an error.
                return Err(format!(
                    "distance must be > 0 (got {distance}): the loop never ran"
                ));
            }
            ch.t.push(t);
            ch.x.push(x);
            ch.v.push(v);
            ch.a.push(a_net / g_const);
            ch.rpm.push(rpm);
            ch.gear.push(gear as i64 + 1);
            ch.slip.push(slip_ratio);
            ch.traction_pct.push(py_min(1.0, f_drive / py_max(f_max_tire, 1.0)) * 100.0);
            ch.n_front.push(n_f);
            ch.n_rear.push(n_r);
            ch.f_drive.push(f_drive);
            ch.f_drag.push(f_aero);
            ch.f_rr.push(f_rr);
            ch.t_tire.push(t_tire);
            ch.t_clutch.push(t_clutch);
            ch.p_boost.push(p_boost / 1e5);
            ch.power_kw.push(f_drive * v / 1000.0);
            ch.r_eff.push(r_eff);
        }

        Ok(RunOutput {
            dt,
            ch,
            nan_break,
            steps: step as u64,
        })
    }
}
