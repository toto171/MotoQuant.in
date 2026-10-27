//! The resolved-config schema (Python resolves, Rust integrates).
//!
//! `motoquant/native.py::resolve_config` builds a `MotoQuantEngine` in Python
//! and serialises every quantity the run loop reads AFTER `_precompute` /
//! `_init_submodels`: category-profile knobs, environment corrections, tire
//! grip after the profile override/scale, per-gear overall ratios and shift
//! points, effective-mass terms, launch state, … Category dispatch, defaults,
//! parts application and venue/weather handling therefore stay Python-only —
//! a knob or catalog change never needs a Rust change.
//!
//! Every struct uses `deny_unknown_fields`: if the Python side grows a field
//! this crate does not know, deserialisation FAILS instead of silently
//! ignoring it. Bump [`SCHEMA_VERSION`] (both sides) on any shape change.

use serde::{Deserialize, Serialize};

use crate::error::SimError;

/// Resolved-config schema version. Must equal `native.SCHEMA_VERSION`.
///
/// History: 1 = initial (2026-10-23); 2 = `mass.m_total_cfg` (the live
/// `chassis.total_mass_kg` Python re-reads from step 1 onward); 3 = the
/// 2026-10 physics epoch (no resolved-config shape change, but the run
/// contract changed: a `rollout_m` run parameter with start-beam-relative
/// splits, slip-phase effective mass, soft-cut rev limiter, continuous slip
/// ratio, intercooler-less charge-temp penalty, energy-consistent launch
/// floor — bumped so a pre-epoch engine/wasm can never be paired with a
/// post-epoch resolver or fixture).
pub const SCHEMA_VERSION: u32 = 3;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Constants {
    pub g: f64,
    pub rpm_to_rads: f64,
    pub rads_to_rpm: f64,
    pub pi: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Mass {
    /// `MotoQuantEngine.m_total` at run start — the mass step 0 uses. Python
    /// sets it at construction and restores it from the config after every
    /// run, so it can lag a config mutated after construction.
    pub m_total0: f64,
    /// `chassis.total_mass_kg` at run start: from step 1 on Python computes
    /// `self.m_total = cfg.chassis.total_mass_kg - fuel_burned` (schema 2).
    pub m_total_cfg: f64,
    pub fuel_consumption_gs: f64,
    /// `MotoQuantEngine.F_gradient` (frozen at the initial mass, as in Python).
    pub f_gradient: f64,
    /// Effective-mass terms per gear: `(I_e + I_basket)·(i_total/r_w)²` —
    /// added only once the clutch locks (2026-10 epoch).
    pub m_rot_engine: Vec<f64>,
    pub m_rot_rear: f64,
    pub m_rot_front: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Curve {
    /// `DynoCurve` — `np.interp(rpm, rpm, torque_nm)`.
    Dyno { rpm: Vec<f64>, torque_nm: Vec<f64> },
    /// `EngineParams._two_stroke_torque` (curve-less 2-stroke configs).
    TwoStroke {
        idle_rpm: f64,
        redline_rpm: f64,
        /// `tuned_rpm or peak_power_rpm`, resolved.
        tuned_rpm: f64,
        /// `cylinder_count or 1`, resolved.
        cylinders: i64,
        displacement_cc: Option<f64>,
        powervalve: bool,
        peak_torque_nm: f64,
    },
    /// The 4-stroke parabolic fallback in `EngineParams.get_torque`.
    Parabolic {
        idle_rpm: f64,
        redline_rpm: f64,
        peak_torque_rpm: f64,
        peak_torque_nm: f64,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Engine {
    pub idle_rpm: f64,
    pub redline_rpm: f64,
    pub coolant_temp_c: f64,
    pub eta_dt: f64,
    pub power_correction: f64,
    /// `dyno_curve is not None and dyno_curve.is_at_wheel`.
    pub at_wheel: bool,
    pub curve: Curve,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BoostType {
    Na,
    Turbo,
    ScRoots,
    ScCentrifugal,
    N2o,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ForcedInduction {
    pub boost_type: BoostType,
    pub target_boost_bar: f64,
    pub turbo_spool_time_s: f64,
    /// `intercooler_type != "none"` (false → eta_ic 0, the full charge-temp
    /// penalty, 2026-10 epoch).
    pub intercooler: bool,
    pub intercooler_effectiveness: f64,
    pub n2o_hp_per_stage: f64,
    /// Float on the wire: Python multiplies `hp * stages` (int → exact double).
    pub n2o_stages: f64,
    pub n2o_ramp_duration_s: f64,
    /// Initial boost pressure (Pa): prespool·1e5 when boosted, else 0.
    pub p_boost0: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Drivetrain {
    /// `DrivetrainParams.overall_ratio(g)` for every gear.
    pub overall_ratios: Vec<f64>,
    /// `optimal_shift_rpm(g, g+1)` for g < top, then redline (as in run()).
    pub shift_rpms: Vec<f64>,
    pub shift_time_s: f64,
    /// Speed limiter in m/s (None = unrestricted).
    pub v_limiter: Option<f64>,
    /// `drive_type == "chain"` (chain-slack launch dead zone).
    pub chain: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Clutch {
    /// `ClutchParams.max_torque()`.
    pub t_cap: f64,
    pub fade_temp_c: f64,
    /// `clutch.clutch_type == "slider"` (the only type run() distinguishes).
    pub slider: bool,
    pub engage_rpm: f64,
    pub engine_inertia_kgm2: f64,
    pub basket_inertia_kgm2: f64,
    pub thermal_mass_jk: f64,
    pub t_clutch0: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Launch {
    /// Staging initial omega_e incl. the profile launch_rpm_factor override.
    pub omega_e0: f64,
    pub over_clutch_factor: f64,
    pub max_engine_decel_rads2: f64,
    /// Launch-floor omega (None when the profile's launch_floor_factor <= 0).
    pub floor_omega: Option<f64>,
    pub lock_thresh: f64,
    pub idle_omega: f64,
    pub redline_omega_clip: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Tire {
    pub rear_rolling_radius_m: f64,
    pub growth_coeff: f64,
    /// TireModel's mu_peak (after the profile override/scale).
    pub mu_peak: f64,
    pub load_sensitivity_k: f64,
    pub optimal_temp_c: f64,
    pub reversion_temp_c: f64,
    pub t_ref_k: f64,
    /// Track-prep × surface grip multiplier.
    pub mu_prep: f64,
    pub crr_base: f64,
    pub crr_speed_coeff: f64,
    pub crr_temp_coeff: f64,
    pub thermal_conductivity: f64,
    pub contact_patch_cm2: f64,
    pub tread_mass_kg: f64,
    pub specific_heat_rubber: f64,
    pub t_tire_launch: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Env {
    pub rho: f64,
    pub v_wind: f64,
    pub ambient_temp_c: f64,
    /// `environment.track_temp_c` (None → ambient + 5 inside the thermal model).
    pub t_road: Option<f64>,
    pub rr_multiplier: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Aero {
    pub cl: f64,
    pub frontal_area_m2: f64,
    pub ram_air_efficiency: f64,
    pub cd_a_upright: f64,
    pub cd_a_full: f64,
    pub transition_s: f64,
    pub cd_a_floor: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Rider {
    pub launch_forward_shift_mm: f64,
    pub tuck_transition_time_s: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Chassis {
    pub wheelbase_m: f64,
    pub cog_height_m: f64,
    pub l_f: f64,
    pub anti_squat_frac: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Wheelie {
    pub counter_rotating: bool,
    pub wheelie_bar: bool,
    pub bar_length_mm: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Parasitic {
    pub alternator_present: bool,
    pub alternator_power_w: f64,
    pub water_pump_electric: bool,
    pub oil_pump_power_w: f64,
    pub valve_train_power_w: f64,
    pub parasitic_delta_hp: f64,
    pub mult: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResolvedConfig {
    pub schema: u32,
    pub name: String,
    /// "svml_ha" | "libm" — which `np.exp` the reference NumPy uses.
    pub exp_impl: String,
    pub constants: Constants,
    pub dt: f64,
    pub mass: Mass,
    pub engine: Engine,
    pub fi: ForcedInduction,
    pub drivetrain: Drivetrain,
    pub clutch: Clutch,
    pub launch: Launch,
    pub tire: Tire,
    pub env: Env,
    pub aero: Aero,
    pub rider: Rider,
    pub chassis: Chassis,
    pub wheelie: Wheelie,
    pub parasitic: Parasitic,
}

impl ResolvedConfig {
    /// Parse + validate a resolved config (schema version, array shapes).
    pub fn from_json(s: &str) -> Result<ResolvedConfig, SimError> {
        let cfg: ResolvedConfig = serde_json::from_str(s)
            .map_err(|e| SimError::value(format!("resolved config: {e}")))?;
        cfg.validate()?;
        Ok(cfg)
    }

    pub fn validate(&self) -> Result<(), SimError> {
        if self.schema != SCHEMA_VERSION {
            return Err(SimError::value(format!(
                "resolved-config schema {} != engine schema {} — rebuild the native \
                 module / wasm (see docs/RUST_CORE.md, regen contract)",
                self.schema, SCHEMA_VERSION
            )));
        }
        if crate::fmath::ExpImpl::parse(&self.exp_impl).is_none() {
            return Err(SimError::value(format!("unknown exp_impl {:?}", self.exp_impl)));
        }
        let n = self.drivetrain.overall_ratios.len();
        if n == 0 {
            return Err(SimError::value("drivetrain.overall_ratios is empty"));
        }
        if self.drivetrain.shift_rpms.len() != n || self.mass.m_rot_engine.len() != n {
            return Err(SimError::value(format!(
                "per-gear arrays disagree: ratios={} shift_rpms={} m_rot_engine={}",
                n,
                self.drivetrain.shift_rpms.len(),
                self.mass.m_rot_engine.len()
            )));
        }
        if let Curve::Dyno { rpm, torque_nm } = &self.engine.curve {
            if rpm.is_empty() || rpm.len() != torque_nm.len() {
                return Err(SimError::value(format!(
                    "dyno curve shape: rpm={} torque={}",
                    rpm.len(),
                    torque_nm.len()
                )));
            }
        }
        // Python: `int(max_time / dt)` — dt == 0 raises ZeroDivisionError;
        // a negative dt sizes a negative array (ValueError).
        if self.dt == 0.0 {
            return Err(SimError::zero_division("float division by zero (dt == 0)"));
        }
        if !(self.dt > 0.0) {
            return Err(SimError::value(format!("dt must be > 0 (got {})", self.dt)));
        }
        Ok(())
    }
}
