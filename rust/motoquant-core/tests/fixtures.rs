//! Native-Rust parity against the Python-reference fixtures
//! (rust/fixtures/engine_parity.json, written by scripts/gen_engine_web.py).
//! Runs with plain `cargo test` — no Python needed.
//!
//! The contract is the repo's bit-identical bar: |dET|, |dtrap| <= 1e-9 s.
//! On Linux/glibc (the platform the fixtures are generated on) the native
//! engine calls the same C `pow`/`sin` as CPython, so ET/trap/splits are
//! asserted EXACTLY equal there.

use motoquant_core::{simulate, ErrorKind, ResolvedConfig, MAX_SAMPLES, ROLLOUT_M};
use serde::Deserialize;

#[derive(Deserialize)]
struct Fixture {
    schema: u32,
    tolerance_s: f64,
    cases: Vec<Case>,
}

#[derive(Deserialize)]
struct Req {
    distance: f64,
    max_time: f64,
    adaptive: bool,
    /// Schema 3 (2026-10 epoch): the rollout the Python reference ran with.
    rollout_m: f64,
}

#[derive(Deserialize)]
struct Expected {
    n: usize,
    steps: u64,
    dt: f64,
    finished_quarter: bool,
    time_60ft: f64,
    time_330ft: f64,
    time_eighth: f64,
    time_1000ft: f64,
    time_quarter: f64,
    speed_quarter: f64,
    max_distance_m: f64,
    elapsed_time_s: f64,
}

#[derive(Deserialize)]
struct Case {
    label: String,
    request: Req,
    config: ResolvedConfig,
    expected: Expected,
}

fn load() -> Fixture {
    let path = concat!(env!("CARGO_MANIFEST_DIR"), "/../fixtures/engine_parity.json");
    let s = std::fs::read_to_string(path).expect("fixtures missing — run scripts/gen_engine_web.py");
    serde_json::from_str(&s).expect("fixture JSON")
}

#[test]
fn native_matches_python_fixtures() {
    let fx = load();
    assert_eq!(fx.schema, motoquant_core::SCHEMA_VERSION, "fixture schema");
    let exact = cfg!(all(target_os = "linux", target_env = "gnu"));
    let mut worst = 0.0f64;
    for c in &fx.cases {
        let r = &c.request;
        let (out, sp) = simulate(&c.config, r.distance, r.max_time, r.adaptive, r.rollout_m)
            .unwrap_or_else(|e| panic!("{}: {e}", c.label));
        let e = &c.expected;
        let d_et = (sp.time_quarter - e.time_quarter).abs();
        let d_trap = (sp.speed_quarter - e.speed_quarter).abs();
        worst = worst.max(d_et);
        assert!(d_et <= fx.tolerance_s && d_trap <= fx.tolerance_s, "{}: dET={d_et:e} dtrap={d_trap:e}", c.label);
        assert_eq!(sp.finished_quarter, e.finished_quarter, "{}", c.label);
        if exact {
            assert_eq!(out.ch.len(), e.n, "{}: sample count", c.label);
            assert_eq!(out.steps, e.steps, "{}: step count", c.label);
            assert_eq!(out.dt, e.dt, "{}: final dt", c.label);
            for (got, want, what) in [
                (sp.rollout_m, r.rollout_m, "rollout"),
                (sp.time_60ft, e.time_60ft, "60ft"),
                (sp.time_330ft, e.time_330ft, "330ft"),
                (sp.time_eighth, e.time_eighth, "1/8"),
                (sp.time_1000ft, e.time_1000ft, "1000ft"),
                (sp.time_quarter, e.time_quarter, "1/4"),
                (sp.speed_quarter, e.speed_quarter, "trap"),
                (sp.max_distance_m, e.max_distance_m, "max x"),
                (sp.elapsed_time_s, e.elapsed_time_s, "elapsed"),
            ] {
                assert_eq!(got.to_bits(), want.to_bits(), "{}: {what} {got} != {want}", c.label);
            }
        }
    }
    eprintln!("{} fixture cases, worst |dET| = {worst:e} (exact mode: {exact})", fx.cases.len());
}

fn k5() -> ResolvedConfig {
    let fx = load();
    fx.cases.into_iter().find(|c| c.label == "gsxr1000_k5").expect("k5 fixture").config
}

fn kind_of(cfg: &ResolvedConfig, distance: f64, max_time: f64, adaptive: bool) -> Option<ErrorKind> {
    simulate(cfg, distance, max_time, adaptive, ROLLOUT_M).err().map(|e| e.kind)
}

fn run(
    cfg: &ResolvedConfig,
    distance: f64,
    max_time: f64,
    adaptive: bool,
) -> Result<(motoquant_core::RunOutput, motoquant_core::Splits), motoquant_core::SimError> {
    simulate(cfg, distance, max_time, adaptive, ROLLOUT_M)
}

/// Python sizes its output with `np.zeros(int(max_time / dt) + 1)`; every
/// error class it raises from that line is mirrored, and an oversized run is
/// a MemoryError-kind error — never an allocator abort.
#[test]
fn sizing_errors_mirror_python_classes() {
    let cfg = k5();
    assert_eq!(kind_of(&cfg, 402.336, f64::NAN, false), Some(ErrorKind::Value));
    assert_eq!(kind_of(&cfg, 402.336, f64::INFINITY, false), Some(ErrorKind::Overflow));
    assert_eq!(kind_of(&cfg, 402.336, f64::NEG_INFINITY, false), Some(ErrorKind::Overflow));
    assert_eq!(kind_of(&cfg, 402.336, -1.0, false), Some(ErrorKind::Value));
    // int(-1.5) + 1 == 0 -> np.zeros(0) is fine in Python: empty result.
    let (out, _) = run(&cfg, 402.336, -0.0015, false).expect("n_max == 0 is valid");
    assert!(out.ch.is_empty());
    // distance + rollout <= 0: Python's UnboundLocalError becomes a clear
    // ValueError (with the default 1-ft rollout, distance 0 is a valid run
    // to the start beam).
    assert_eq!(
        simulate(&cfg, 0.0, 26.0, false, 0.0).err().map(|e| e.kind),
        Some(ErrorKind::Value)
    );
    assert_eq!(kind_of(&cfg, -ROLLOUT_M, 26.0, false), Some(ErrorKind::Value));
    let (_, sp) = run(&cfg, 0.0, 26.0, false).expect("distance 0 runs to the beam");
    assert!(!sp.finished_quarter);
    // run(rollout_m=...) validation mirrors Python's ValueError.
    for bad in [-0.1, f64::NAN, f64::INFINITY] {
        assert_eq!(
            simulate(&cfg, 402.336, 26.0, false, bad).err().map(|e| e.kind),
            Some(ErrorKind::Value),
            "rollout {bad}"
        );
    }
    let mut zero_dt = cfg.clone();
    zero_dt.dt = 0.0;
    assert_eq!(kind_of(&zero_dt, 402.336, 26.0, false), Some(ErrorKind::ZeroDivision));
}

#[test]
fn huge_runs_hit_the_sample_cap_not_the_allocator() {
    let cfg = k5();
    // A huge max_time is fine when the bike finishes: buffers grow lazily.
    let (out, sp) = run(&cfg, 402.336, 1e13, false).expect("finishing run");
    assert!(sp.finished_quarter && out.ch.len() < 20_000);
    // A run that would store more than MAX_SAMPLES samples is refused.
    let e = run(&cfg, 1e12, 1e9, false).expect_err("must hit the cap");
    assert_eq!(e.kind, ErrorKind::Memory, "{e}");
    let e = run(&cfg, 1e12, 1e9, true).expect_err("adaptive must hit the cap");
    assert_eq!(e.kind, ErrorKind::Memory, "{e}");
    assert!(MAX_SAMPLES >= 240_001, "cap below the API's longest run");
}

#[test]
fn live_config_mass_is_used_from_step_one() {
    // Schema 2: m_total0 feeds step 0 only; later steps use m_total_cfg.
    let base = k5();
    let (a, _) = run(&base, 402.336, 26.0, false).unwrap();
    let mut heavier = base.clone();
    heavier.mass.m_total_cfg += 20.0;
    let (b, _) = run(&heavier, 402.336, 26.0, false).unwrap();
    assert_eq!(a.ch.v[1].to_bits(), b.ch.v[1].to_bits(), "step 0 must use m_total0");
    assert!(b.ch.t.len() > a.ch.t.len(), "a heavier bike must be slower");
}

#[test]
fn rollout_zero_is_timed_from_first_motion() {
    // rollout 0: the splits are read straight off the from-rest trajectory;
    // rollout 1 ft: ET = t(x = r + D) - t(x = r) on the SAME trajectory
    // (the integration itself is identical up to the extra 1 ft).
    let cfg = k5();
    let (a, sa) = simulate(&cfg, 402.336, 26.0, false, 0.0).unwrap();
    let (b, sb) = simulate(&cfg, 402.336, 26.0, false, ROLLOUT_M).unwrap();
    let n = a.ch.len().min(b.ch.len());
    assert_eq!(a.ch.x[..n - 1], b.ch.x[..n - 1], "same trajectory");
    assert!(sb.time_quarter < sa.time_quarter - 0.1, "rollout shortens ET");
    assert!((sb.speed_quarter - sa.speed_quarter).abs() < 0.1, "trap ~unchanged");
    assert_eq!(sa.rollout_m, 0.0);
    assert_eq!(sb.rollout_m, ROLLOUT_M);
}
