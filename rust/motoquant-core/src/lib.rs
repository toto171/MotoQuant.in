//! MotoQuant Rust core — a bit-parity port of the quarter-mile physics loop.
//!
//! Python (`motoquant/physics.py`) is the REFERENCE implementation; this crate
//! integrates a *resolved* config produced by `motoquant/native.py`
//! (see [`config`]). Three front doors:
//!
//! * Rust: [`simulate`] / [`engine::Engine`].
//! * Python (feature `python`): the `motoquant_core` extension module
//!   (PyO3, abi3) consumed by `motoquant/native.py`.
//! * Browser (`wasm32`): raw C ABI `alloc` / `dealloc` / `simulate`, consumed
//!   by `web/lib/engine.js`. No wasm-bindgen, so the committed `.wasm` needs no
//!   Rust toolchain at web build time.
//!
//! See docs/RUST_CORE.md for the schema + regen contract and parity results.

pub mod config;
pub mod engine;
pub mod error;
pub mod fmath;
pub mod interp;
pub mod splits;

pub use config::{ResolvedConfig, SCHEMA_VERSION};
pub use engine::{Engine, RunOutput, MAX_SAMPLES};
pub use error::{ErrorKind, SimError};
pub use splits::{Splits, ROLLOUT_M};

// `SOURCE_FINGERPRINT: u64` — FNV-1a 64 of this crate's sources, stamped by
// build.rs. native.py compares it with the checkout to detect a stale build.
include!(concat!(env!("OUT_DIR"), "/fingerprint.rs"));

/// [`SOURCE_FINGERPRINT`] as 16 lowercase hex digits.
pub fn source_fingerprint_hex() -> String {
    format!("{SOURCE_FINGERPRINT:016x}")
}

use serde::Deserialize;

/// Parse a resolved config and run it. `distance` / `max_time` /
/// `use_adaptive_dt` / `rollout_m` mirror `MotoQuantEngine.run()` (pass
/// [`ROLLOUT_M`] for the drag-strip default, 0.0 for "from first motion").
pub fn simulate(
    cfg: &ResolvedConfig,
    distance: f64,
    max_time: f64,
    use_adaptive_dt: bool,
    rollout_m: f64,
) -> Result<(RunOutput, Splits), SimError> {
    let eng = Engine::new(cfg)?;
    let out = eng.run(distance, max_time, use_adaptive_dt, rollout_m)?;
    let sp = splits::extract_splits(&out.ch.t, &out.ch.x, &out.ch.v, rollout_m);
    Ok((out, sp))
}

/// Request envelope for the byte-level API shared by wasm and Python.
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    config: ResolvedConfig,
    #[serde(default = "default_distance")]
    distance: f64,
    #[serde(default = "default_max_time")]
    max_time: f64,
    #[serde(default)]
    adaptive: bool,
    #[serde(default = "default_true")]
    channels: bool,
    /// Drag-strip rollout (m); defaults to constants.ROLLOUT_M (1 ft).
    #[serde(default = "default_rollout")]
    rollout_m: f64,
}

fn default_distance() -> f64 {
    splits::QUARTER_MILE_M
}
fn default_max_time() -> f64 {
    26.0
}
fn default_true() -> bool {
    true
}
fn default_rollout() -> f64 {
    splits::ROLLOUT_M
}

/// Binary result layout (little-endian), shared by the wasm ABI and
/// `motoquant_core.simulate_binary`:
///
/// ```text
/// u32 total_len | u32 header_len | u32 n_samples | u32 n_float_channels
/// header_len bytes of UTF-8 JSON  (ok, error, dt, steps, nan_break, splits,
///                                  channels: [names])
/// zero padding to an 8-byte boundary
/// n_float_channels × n_samples f64   (channel-major, FLOAT_CHANNELS order)
/// n_samples f64                       (gear, 1-based, only if channels)
/// ```
pub fn simulate_request_bytes(input: &[u8]) -> Vec<u8> {
    match run_request(input) {
        Ok(buf) => buf,
        Err(e) => encode(
            &serde_json::json!({ "ok": false, "error": e.msg, "kind": e.kind.as_str() }),
            0,
            &[],
            None,
        ),
    }
}

fn run_request(input: &[u8]) -> Result<Vec<u8>, SimError> {
    let req: Request =
        serde_json::from_slice(input).map_err(|e| SimError::value(format!("request: {e}")))?;
    req.config.validate()?;
    let (out, sp) = simulate(&req.config, req.distance, req.max_time, req.adaptive, req.rollout_m)?;
    let n = out.ch.len();
    let names: Vec<&str> = if req.channels {
        engine::FLOAT_CHANNELS.to_vec()
    } else {
        vec![]
    };
    let header = serde_json::json!({
        "ok": true,
        "schema": SCHEMA_VERSION,
        "dt": out.dt,
        "steps": out.steps,
        "nan_break": out.nan_break,
        "n": n,
        "splits": sp,
        "channels": names,
        "gear": req.channels,
    });
    if req.channels {
        let gears: Vec<f64> = out.ch.gear.iter().map(|&g| g as f64).collect();
        Ok(encode(&header, n, &out.ch.float_channels(), Some(&gears)))
    } else {
        Ok(encode(&header, n, &[], None))
    }
}

fn encode(header: &serde_json::Value, n: usize, chans: &[&Vec<f64>], gear: Option<&Vec<f64>>) -> Vec<u8> {
    let h = serde_json::to_vec(header).unwrap_or_else(|_| b"{\"ok\":false}".to_vec());
    let pre = 16 + h.len();
    let pad = (8 - pre % 8) % 8;
    let body = 8 * n * (chans.len() + usize::from(gear.is_some()));
    let total = pre + pad + body;
    let mut buf = Vec::with_capacity(total);
    buf.extend_from_slice(&(total as u32).to_le_bytes());
    buf.extend_from_slice(&(h.len() as u32).to_le_bytes());
    buf.extend_from_slice(&(n as u32).to_le_bytes());
    buf.extend_from_slice(&(chans.len() as u32).to_le_bytes());
    buf.extend_from_slice(&h);
    buf.resize(pre + pad, 0);
    for c in chans {
        for v in c.iter() {
            buf.extend_from_slice(&v.to_le_bytes());
        }
    }
    if let Some(g) = gear {
        for v in g {
            buf.extend_from_slice(&v.to_le_bytes());
        }
    }
    debug_assert_eq!(buf.len(), total);
    buf
}

// ═══════════════════════════════════════════════════════════════════════════
// WASM raw C ABI (no wasm-bindgen)
// ═══════════════════════════════════════════════════════════════════════════
#[cfg(target_arch = "wasm32")]
mod wasm_abi {
    /// Allocate `len` bytes in linear memory for the caller to fill.
    #[no_mangle]
    pub extern "C" fn alloc(len: usize) -> *mut u8 {
        let b: Box<[u8]> = vec![0u8; len].into_boxed_slice();
        Box::into_raw(b) as *mut u8
    }

    /// Free a buffer returned by [`alloc`] or [`simulate`].
    ///
    /// # Safety
    /// `ptr`/`len` must come from `alloc(len)` or from a `simulate` result
    /// (whose length is its first u32), and be freed exactly once.
    #[no_mangle]
    pub unsafe extern "C" fn dealloc(ptr: *mut u8, len: usize) {
        if ptr.is_null() {
            return;
        }
        drop(Box::from_raw(core::ptr::slice_from_raw_parts_mut(ptr, len)));
    }

    /// Run a request (UTF-8 JSON at `ptr..ptr+len`); returns a pointer to the
    /// binary result (layout: `simulate_request_bytes`). Free it with
    /// `dealloc(result, total_len)` where total_len is its first u32.
    ///
    /// # Safety
    /// `ptr..ptr+len` must be a live allocation from [`alloc`].
    #[no_mangle]
    pub unsafe extern "C" fn simulate(ptr: *const u8, len: usize) -> *mut u8 {
        let input = core::slice::from_raw_parts(ptr, len);
        let out = crate::simulate_request_bytes(input).into_boxed_slice();
        Box::into_raw(out) as *mut u8
    }

    /// Resolved-config schema version this engine understands.
    #[no_mangle]
    pub extern "C" fn schema_version() -> u32 {
        crate::SCHEMA_VERSION
    }

    /// High 32 bits of the build's source fingerprint (see build.rs).
    #[no_mangle]
    pub extern "C" fn source_fingerprint_hi() -> u32 {
        (crate::SOURCE_FINGERPRINT >> 32) as u32
    }

    /// Low 32 bits of the build's source fingerprint (see build.rs).
    #[no_mangle]
    pub extern "C" fn source_fingerprint_lo() -> u32 {
        crate::SOURCE_FINGERPRINT as u32
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Python extension module (PyO3, abi3)
// ═══════════════════════════════════════════════════════════════════════════
#[cfg(feature = "python")]
mod python {
    use pyo3::exceptions::{PyMemoryError, PyOverflowError, PyValueError, PyZeroDivisionError};
    use pyo3::prelude::*;
    use pyo3::types::{PyBytes, PyDict};

    use crate::config::ResolvedConfig;
    use crate::error::{ErrorKind, SimError};
    use crate::fmath::{self, ExpImpl};

    /// Re-raise with the exception class the Python reference raises.
    fn to_py(e: SimError) -> PyErr {
        match e.kind {
            ErrorKind::Value => PyValueError::new_err(e.msg),
            ErrorKind::Memory => PyMemoryError::new_err(e.msg),
            ErrorKind::Overflow => PyOverflowError::new_err(e.msg),
            ErrorKind::ZeroDivision => PyZeroDivisionError::new_err(e.msg),
        }
    }

    fn f64_bytes(v: &[f64]) -> Vec<u8> {
        let mut b = Vec::with_capacity(v.len() * 8);
        for x in v {
            b.extend_from_slice(&x.to_le_bytes());
        }
        b
    }

    /// Resolved-config schema version.
    #[pyfunction]
    fn schema_version() -> u32 {
        crate::SCHEMA_VERSION
    }

    /// Run one simulation. Returns a dict: dt, steps, nan_break, n, splits
    /// (dict), channels (dict name -> little-endian float64 bytes) and gear
    /// (int64 bytes). The GIL is released while integrating. `rollout_m`
    /// mirrors `MotoQuantEngine.run(rollout_m=...)` (default 1 ft).
    #[pyfunction]
    #[pyo3(signature = (config_json, distance, max_time, adaptive, channels=true, rollout_m=crate::splits::ROLLOUT_M))]
    fn simulate<'py>(
        py: Python<'py>,
        config_json: &str,
        distance: f64,
        max_time: f64,
        adaptive: bool,
        channels: bool,
        rollout_m: f64,
    ) -> PyResult<Bound<'py, PyDict>> {
        let owned = config_json.to_owned();
        let res = py.allow_threads(move || -> Result<_, SimError> {
            let cfg = ResolvedConfig::from_json(&owned)?;
            crate::simulate(&cfg, distance, max_time, adaptive, rollout_m)
        });
        let (out, sp) = res.map_err(to_py)?;
        let d = PyDict::new(py);
        d.set_item("dt", out.dt)?;
        d.set_item("steps", out.steps)?;
        d.set_item("nan_break", out.nan_break)?;
        d.set_item("n", out.ch.len())?;
        let s = PyDict::new(py);
        s.set_item("time_60ft", sp.time_60ft)?;
        s.set_item("speed_60ft", sp.speed_60ft)?;
        s.set_item("time_330ft", sp.time_330ft)?;
        s.set_item("speed_330ft", sp.speed_330ft)?;
        s.set_item("time_eighth", sp.time_eighth)?;
        s.set_item("speed_eighth", sp.speed_eighth)?;
        s.set_item("time_1000ft", sp.time_1000ft)?;
        s.set_item("speed_1000ft", sp.speed_1000ft)?;
        s.set_item("time_quarter", sp.time_quarter)?;
        s.set_item("speed_quarter", sp.speed_quarter)?;
        s.set_item("finished_quarter", sp.finished_quarter)?;
        s.set_item("max_distance_m", sp.max_distance_m)?;
        s.set_item("elapsed_time_s", sp.elapsed_time_s)?;
        s.set_item("rollout_m", sp.rollout_m)?;
        d.set_item("splits", s)?;
        if channels {
            let cd = PyDict::new(py);
            for (name, ch) in crate::engine::FLOAT_CHANNELS.iter().zip(out.ch.float_channels()) {
                cd.set_item(*name, PyBytes::new(py, &f64_bytes(ch)))?;
            }
            d.set_item("channels", cd)?;
            let mut gb = Vec::with_capacity(out.ch.gear.len() * 8);
            for g in &out.ch.gear {
                gb.extend_from_slice(&g.to_le_bytes());
            }
            d.set_item("gear", PyBytes::new(py, &gb))?;
        }
        Ok(d)
    }

    /// The wasm byte-level API (same encoder), for testing it from Python.
    #[pyfunction]
    fn simulate_binary<'py>(py: Python<'py>, request_json: &[u8]) -> Bound<'py, PyBytes> {
        let owned = request_json.to_vec();
        let out = py.allow_threads(move || crate::simulate_request_bytes(&owned));
        PyBytes::new(py, &out)
    }

    /// Parse a resolved config and serialise it back (JSON round-trip check).
    #[pyfunction]
    fn echo_config(config_json: &str) -> PyResult<String> {
        let cfg = ResolvedConfig::from_json(config_json).map_err(to_py)?;
        serde_json::to_string(&cfg).map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// `float(np.interp(x, xp, fp))` (unit-parity hook).
    #[pyfunction]
    fn np_interp(x: f64, xp: Vec<f64>, fp: Vec<f64>) -> PyResult<f64> {
        if xp.is_empty() || xp.len() != fp.len() {
            return Err(PyValueError::new_err("xp/fp must be non-empty and equal length"));
        }
        Ok(crate::interp::np_interp(x, &xp, &fp))
    }

    /// Batch `np.searchsorted(arr, key)` (left) for parity tests.
    #[pyfunction]
    fn searchsorted_left(arr: Vec<f64>, key: f64) -> usize {
        crate::interp::searchsorted_left(&arr, key)
    }

    /// The engine's exp under a given implementation ("svml_ha" | "libm").
    #[pyfunction]
    fn exp_impl(xs: Vec<f64>, which: &str) -> PyResult<Vec<f64>> {
        let imp = ExpImpl::parse(which)
            .ok_or_else(|| PyValueError::new_err(format!("unknown exp impl {which:?}")))?;
        Ok(xs.into_iter().map(|x| imp.exp(x)).collect())
    }

    /// The engine's `x ** y` (C pow).
    #[pyfunction]
    fn pow(xs: Vec<f64>, y: f64) -> Vec<f64> {
        xs.into_iter().map(|x| fmath::pow(x, y)).collect()
    }

    /// The engine's `math.sin`.
    #[pyfunction]
    fn sin(xs: Vec<f64>) -> Vec<f64> {
        xs.into_iter().map(fmath::sin).collect()
    }

    #[pymodule]
    #[pyo3(name = "motoquant_core")]
    fn motoquant_core_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add("__version__", env!("CARGO_PKG_VERSION"))?;
        m.add("SCHEMA_VERSION", crate::SCHEMA_VERSION)?;
        m.add("SOURCE_FINGERPRINT", crate::source_fingerprint_hex())?;
        m.add("MAX_SAMPLES", crate::MAX_SAMPLES)?;
        m.add_function(wrap_pyfunction!(schema_version, m)?)?;
        m.add_function(wrap_pyfunction!(simulate, m)?)?;
        m.add_function(wrap_pyfunction!(simulate_binary, m)?)?;
        m.add_function(wrap_pyfunction!(echo_config, m)?)?;
        m.add_function(wrap_pyfunction!(np_interp, m)?)?;
        m.add_function(wrap_pyfunction!(searchsorted_left, m)?)?;
        m.add_function(wrap_pyfunction!(exp_impl, m)?)?;
        m.add_function(wrap_pyfunction!(pow, m)?)?;
        m.add_function(wrap_pyfunction!(sin, m)?)?;
        Ok(())
    }
}
