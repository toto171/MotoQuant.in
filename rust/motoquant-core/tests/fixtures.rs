//! Native-Rust parity against the Python-reference fixtures
//! (rust/fixtures/engine_parity.json, written by scripts/gen_engine_web.py).
//! Runs with plain `cargo test` — no Python needed.
//!
//! The contract is the repo's bit-identical bar: |dET|, |dtrap| <= 1e-9 s.
//! On Linux/glibc (the platform the fixtures are generated on) the native
//! engine calls the same C `pow`/`sin` as CPython, so ET/trap/splits are
//! asserted EXACTLY equal there.

use motoquant_core::{simulate, ResolvedConfig};
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
}

#[derive(Deserialize)]
struct Expected {
    n: usize,
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
        let (out, sp) = simulate(&c.config, c.request.distance, c.request.max_time, c.request.adaptive)
            .unwrap_or_else(|e| panic!("{}: {e}", c.label));
        let e = &c.expected;
        let d_et = (sp.time_quarter - e.time_quarter).abs();
        let d_trap = (sp.speed_quarter - e.speed_quarter).abs();
        worst = worst.max(d_et);
        assert!(d_et <= fx.tolerance_s && d_trap <= fx.tolerance_s, "{}: dET={d_et:e} dtrap={d_trap:e}", c.label);
        assert_eq!(sp.finished_quarter, e.finished_quarter, "{}", c.label);
        if exact {
            assert_eq!(out.ch.len(), e.n, "{}: sample count", c.label);
            assert_eq!(out.dt, e.dt, "{}: final dt", c.label);
            for (got, want, what) in [
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
