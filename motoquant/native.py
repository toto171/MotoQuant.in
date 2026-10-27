"""
MotoQuant Pro — optional Rust physics core (accelerator, NOT the reference)
===========================================================================

``motoquant/physics.py`` (``MotoQuantEngine.run``) is the reference
implementation and stays that way. This module is a thin bridge to the
``motoquant_core`` extension module built from ``rust/motoquant-core``
(``make native``), a float-op-for-float-op Rust transliteration of the run
loop that reproduces the Python trajectory bit-for-bit (see
docs/RUST_CORE.md for the parity evidence and its documented limits).

Division of labour — "Python resolves, Rust integrates":

* :func:`resolve_config` builds a real :class:`MotoQuantEngine` and serialises
  every quantity the loop reads AFTER ``_precompute`` / ``_init_submodels``
  (category-profile knobs, environment corrections, tire grip after the
  profile override/scale, per-gear ratios and shift points, effective-mass
  terms, launch state, …). Category dispatch, defaults, parts application and
  venue handling therefore stay Python-only: a knob or data change never needs
  a Rust change. Any change to the *shape* of that dict is a schema change —
  bump :data:`SCHEMA_VERSION` here AND ``SCHEMA_VERSION`` in
  ``rust/motoquant-core/src/config.rs``, rebuild (``make native wasm``) and
  regenerate the web fixtures (``scripts/gen_engine_web.py``).
* :func:`run_native` / :class:`NativeEngine` integrate in Rust and hand back
  the SAME :class:`~motoquant.physics.SimResult` (numpy arrays,
  ``extract_splits()`` called by Python). :class:`NativeEngine` subclasses
  ``MotoQuantEngine`` and only overrides ``run()``, so ``run_top_speed()`` /
  ``run_distance()`` reuse Python's post-processing verbatim.

Import of ``motoquant_core`` is lazy and failure-tolerant: when the extension
is not built, :func:`available` returns ``False`` and nothing else changes.
"""

from __future__ import annotations

import json
import logging
import math
from functools import lru_cache
from pathlib import Path

import numpy as np

from .constants import QUARTER_MILE_M, RADS_TO_RPM, ROLLOUT_M, RPM_TO_RADS, G
from .models import CLUTCH_SLIDER, DRIVE_CHAIN, BikeConfig
from .physics import MotoQuantEngine, SimResult

log = logging.getLogger(__name__)

#: Resolved-config schema version — must equal the Rust crate's SCHEMA_VERSION.
#: 1 = initial; 2 = ``mass.m_total_cfg`` (Python re-reads
#: ``cfg.chassis.total_mass_kg`` every step from step 1 on); 3 = the 2026-10
#: physics epoch (``rollout_m`` run parameter + start-beam-relative splits,
#: slip-phase effective mass, soft-cut rev limiter, continuous slip ratio,
#: intercooler-less charge-temp penalty, energy-consistent launch floor — the
#: resolved dict's shape is unchanged; the bump keeps a pre-epoch extension /
#: wasm from ever pairing with a post-epoch resolver or fixture).
SCHEMA_VERSION = 3

#: The crate whose sources the extension's ``SOURCE_FINGERPRINT`` hashes.
CRATE_DIR = Path(__file__).resolve().parent.parent / "rust" / "motoquant-core"

# Channel order produced by the Rust core (engine::FLOAT_CHANNELS) mapped to
# SimResult attribute names.
_FLOAT_CHANNELS = (
    ("t", "t"),
    ("x", "x"),
    ("v", "v"),
    ("a", "a"),
    ("rpm", "rpm"),
    ("slip", "slip"),
    ("traction_pct", "traction_pct"),
    ("N_front", "N_front"),
    ("N_rear", "N_rear"),
    ("F_drive", "F_drive"),
    ("F_drag", "F_drag"),
    ("F_rr", "F_rr"),
    ("T_tire", "T_tire"),
    ("T_clutch", "T_clutch"),
    ("P_boost", "P_boost"),
    ("power_kw", "power_kw"),
    ("r_eff", "r_eff"),
)

_SPLIT_FIELDS = (
    "time_60ft",
    "speed_60ft",
    "time_330ft",
    "speed_330ft",
    "time_eighth",
    "speed_eighth",
    "time_1000ft",
    "speed_1000ft",
    "time_quarter",
    "speed_quarter",
)


# ═══════════════════════════════════════════
# Extension loading + host-math probing
# ═══════════════════════════════════════════


@lru_cache(maxsize=1)
def _core():
    """Import the extension once. Returns the module or None."""
    try:
        import motoquant_core  # type: ignore[import-not-found]
    except ImportError:
        return None
    except Exception as exc:  # pragma: no cover - broken build, not absence
        log.warning("motoquant_core failed to import: %s", exc)
        return None
    if getattr(motoquant_core, "SCHEMA_VERSION", None) != SCHEMA_VERSION:
        log.warning(
            "motoquant_core schema %s != native.py schema %s — rebuild with "
            "`make native`; the native engine is disabled until then.",
            getattr(motoquant_core, "SCHEMA_VERSION", None),
            SCHEMA_VERSION,
        )
        return None
    return motoquant_core


def available() -> bool:
    """True when the Rust extension is importable and schema-compatible."""
    return _core() is not None


_FNV_OFFSET = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3


def _fnv1a(h: int, data: bytes) -> int:
    for b in data:
        h = ((h ^ b) * _FNV_PRIME) & 0xFFFFFFFFFFFFFFFF
    return h


def fingerprint_sources(crate_dir: Path = CRATE_DIR) -> str | None:
    """FNV-1a 64 of the crate's sources — the exact scheme of
    ``rust/motoquant-core/build.rs`` (``Cargo.toml``, every ``src/**/*.rs`` and
    the workspace ``Cargo.lock``, sorted by relative POSIX path; each file
    contributes ``path \\0 bytes \\0``). ``None`` when the sources are not on
    disk (an installed wheel / the Docker runtime image)."""
    crate_dir = Path(crate_dir)
    src = crate_dir / "src"
    if not (crate_dir / "Cargo.toml").is_file() or not src.is_dir():
        return None
    files = [("Cargo.toml", crate_dir / "Cargo.toml")]
    files += [
        (p.relative_to(crate_dir).as_posix(), p)
        for p in src.rglob("*.rs")
        if p.is_file()
    ]
    lock = crate_dir.parent / "Cargo.lock"
    if lock.is_file():
        files.append(("../Cargo.lock", lock))
    h = _FNV_OFFSET
    for rel, path in sorted(files, key=lambda f: f[0]):
        h = _fnv1a(h, rel.encode())
        h = _fnv1a(h, b"\0")
        h = _fnv1a(h, path.read_bytes())
        h = _fnv1a(h, b"\0")
    return f"{h:016x}"


@lru_cache(maxsize=1)
def _checkout_fingerprint() -> str | None:
    try:
        return fingerprint_sources()
    except OSError as exc:  # unreadable checkout: unknown, not stale
        log.warning("native: could not fingerprint %s: %s", CRATE_DIR, exc)
        return None


def built_fingerprint() -> str | None:
    """The source fingerprint compiled into the loaded extension."""
    mc = _core()
    return None if mc is None else getattr(mc, "SOURCE_FINGERPRINT", None)


def is_stale() -> bool:
    """True when the loaded extension was built from different Rust sources
    than the ones in this checkout (edit ``engine.rs`` without ``make native``
    and this flips). False when either side is unknown — e.g. the Docker
    runtime image ships the wheel but not the sources."""
    built, here = built_fingerprint(), _checkout_fingerprint()
    return built is not None and here is not None and built != here


def _require_core():
    mc = _core()
    if mc is None:
        raise RuntimeError(
            "motoquant_core (the Rust physics core) is not available — build it "
            "with `make native` (needs a Rust toolchain + maturin)."
        )
    return mc


def _probe_points() -> list[float]:
    """Deterministic probe inputs spanning the tire thermal-factor domain."""
    pts = [-((i * 0.0731) % 30.0) - (i % 7) * 1e-3 for i in range(1, 600)]
    pts += [-((k / 25.0) ** 2) for k in range(400)]
    return pts


@lru_cache(maxsize=1)
def host_math() -> dict:
    """Probe which ``np.exp`` the host NumPy dispatches to, and whether the
    extension's C ``pow`` / ``sin`` agree with CPython's.

    ``np.exp`` on a float64 scalar uses Intel SVML ``__svml_exp8_ha`` on
    AVX512_SKX CPUs with an SVML-linked NumPy (PyPI wheels) and the C library
    ``exp`` elsewhere; the two differ in ~4.6 % of inputs, so the Rust core is
    told which one to emulate (``exp_impl``). ``exact`` is False if neither
    candidate reproduces the host — results then agree only to ULP-level drift.
    """
    mc = _core()
    if mc is None:
        return {"exp_impl": "libm", "exact": False, "reason": "extension unavailable"}
    xs = _probe_points()
    ref = [float(np.exp(np.float64(x))) for x in xs]
    info: dict = {}
    for impl in ("svml_ha", "libm"):
        got = mc.exp_impl(xs, impl)
        info[impl] = all(a == b for a, b in zip(ref, got))
    if info["svml_ha"]:
        exp_impl = "svml_ha"
    elif info["libm"]:
        exp_impl = "libm"
    else:
        exp_impl = "libm"
    sq_ok = mc.pow(xs, 2.0) == [x**2 for x in xs]
    p3 = [abs(x) + 1.0 for x in xs]
    p3_ok = mc.pow(p3, 0.3) == [x**0.3 for x in p3]
    sin_xs = [i * 0.00271 for i in range(600)]
    sin_ok = mc.sin(sin_xs) == [math.sin(x) for x in sin_xs]
    exact = (info["svml_ha"] or info["libm"]) and sq_ok and p3_ok and sin_ok
    if not exact:
        log.warning(
            "native engine: host math not reproduced exactly (np.exp svml=%s libm=%s, "
            "pow2=%s pow0.3=%s sin=%s) — native results will carry ULP-level drift",
            info["svml_ha"],
            info["libm"],
            sq_ok,
            p3_ok,
            sin_ok,
        )
    return {
        "exp_impl": exp_impl,
        "exact": bool(exact),
        "np_exp_matches_svml_ha": info["svml_ha"],
        "np_exp_matches_libm": info["libm"],
        "pow_matches": bool(sq_ok and p3_ok),
        "sin_matches": bool(sin_ok),
    }


def native_info() -> dict:
    """Diagnostics: availability, versions, schema, host-math parity."""
    mc = _core()
    out = {"available": mc is not None, "schema": SCHEMA_VERSION}
    if mc is not None:
        out["version"] = getattr(mc, "__version__", "?")
        out["source_fingerprint"] = built_fingerprint()
        out["stale"] = is_stale()
        out.update(host_math())
    return out


# ═══════════════════════════════════════════
# Resolve: Python engine state → plain dict
# ═══════════════════════════════════════════


def _f(x) -> float:
    return float(x)


def _curve(eng: MotoQuantEngine) -> dict:
    e = eng.cfg.engine
    if e.dyno_curve is not None:
        rpm = np.asarray(e.dyno_curve.rpm, dtype=np.float64)
        tq = np.asarray(e.dyno_curve.torque_nm, dtype=np.float64)
        if rpm.ndim != 1 or tq.ndim != 1 or rpm.size == 0 or rpm.size != tq.size:
            raise ValueError(
                f"dyno curve must be two equal-length 1-D arrays "
                f"(got {rpm.shape} / {tq.shape})"
            )
        return {"kind": "dyno", "rpm": rpm.tolist(), "torque_nm": tq.tolist()}
    if e.stroke_type == 2:
        cyls = e.cylinder_count or 1
        if float(cyls) != int(cyls):
            raise ValueError(f"non-integral cylinder_count {cyls!r}")
        return {
            "kind": "two_stroke",
            "idle_rpm": _f(e.idle_rpm),
            "redline_rpm": _f(e.redline_rpm),
            "tuned_rpm": _f(e.tuned_rpm or e.peak_power_rpm),
            "cylinders": int(cyls),
            "displacement_cc": (
                None if e.displacement_cc is None else _f(e.displacement_cc)
            ),
            "powervalve": bool(e.powervalve),
            "peak_torque_nm": _f(e.peak_torque_nm),
        }
    return {
        "kind": "parabolic",
        "idle_rpm": _f(e.idle_rpm),
        "redline_rpm": _f(e.redline_rpm),
        "peak_torque_rpm": _f(e.peak_torque_rpm),
        "peak_torque_nm": _f(e.peak_torque_nm),
    }


def resolve_engine(eng: MotoQuantEngine, *, exp_impl: str | None = None) -> dict:
    """Serialise a constructed engine's run-loop inputs (schema
    :data:`SCHEMA_VERSION`). Every derived value uses the exact expression
    ``run()`` / the sub-models use, so the Rust loop sees identical doubles.
    """
    c = eng.cfg
    e = c.engine
    dtp = c.drivetrain
    prof = eng._profile
    tire_t = eng._tire.cfg.tires  # profile mu override/scale applied here
    if exp_impl is None:
        exp_impl = host_math()["exp_impl"]

    n_gears = dtp.num_gears
    if n_gears < 1:
        raise ValueError("drivetrain has no gears")

    # ── launch state (mirrors the top of run()) ──
    omega_e0 = eng._staging.initial_omega_e()
    if prof.launch_rpm_factor is not None:
        _launch_rpm = max(
            e.idle_rpm,
            min(e.redline_rpm * prof.launch_rpm_factor, e.redline_rpm),
        )
        omega_e0 = _launch_rpm * RPM_TO_RADS
    shift_rpms = [eng.optimal_shift_rpm(g, g + 1) for g in range(n_gears - 1)]
    shift_rpms.append(e.redline_rpm)

    if prof.launch_floor_factor > 0.0:
        if e.stroke_type == 2 and e.tuned_rpm:
            floor_rpm = e.tuned_rpm * prof.launch_floor_factor
        else:
            floor_rpm = e.peak_torque_rpm * prof.launch_floor_factor
        floor_omega = _f(floor_rpm * RPM_TO_RADS)
    else:
        floor_omega = None

    lim = dtp.speed_limiter_kmh
    v_limiter = lim / 3.6 if lim is not None and lim > 0 else None

    # ── effective-mass terms (DrivetrainModel.effective_mass, split so the
    #    in-loop sum keeps Python's ((m + a) + b) + c order with m mutating) ──
    tires = c.tires
    r_w = tires.rear_rolling_radius_m
    m_rot_engine = [
        (e.engine_inertia_kgm2 + c.clutch.basket_inertia_kgm2)
        * (dtp.overall_ratio(g) / r_w) ** 2
        for g in range(n_gears)
    ]
    m_rot_rear = tires.rear_inertia_kgm2 / r_w**2
    r_f = tires.front_rolling_radius_m or r_w
    m_rot_front = tires.front_inertia_kgm2 / r_f**2
    m0 = eng.m_total
    for g in range(n_gears):
        if m0 + m_rot_engine[g] + m_rot_rear + m_rot_front != eng.effective_mass(g):
            raise AssertionError(
                "native resolve drifted from DrivetrainModel.effective_mass — "
                "update motoquant/native.py (and bump SCHEMA_VERSION)"
            )
    if m0 + m_rot_rear + m_rot_front != eng._drivetrain.effective_mass_slipping(m0):
        raise AssertionError(
            "native resolve drifted from DrivetrainModel.effective_mass_slipping — "
            "update motoquant/native.py + engine.rs (and bump SCHEMA_VERSION)"
        )
    wt, wh = eng._wt, eng._wheelie
    if (wt.L, wt.h, wt.L_f) != (wh.L, wh.h, wh.L_f):
        raise AssertionError("weight-transfer / wheelie geometry diverged")
    if wt.L == 0 or wt.h == 0:
        # Python divides by these with plain floats on the first step and
        # raises; IEEE inf/NaN in Rust would silently diverge instead.
        raise ZeroDivisionError("float division by zero (wheelbase or CoG height is 0)")

    fi = c.forced_induction
    par = c.parasitic
    env = c.environment
    t_road = getattr(env, "track_temp_c", None)

    return {
        "schema": SCHEMA_VERSION,
        "name": str(c.name),
        "exp_impl": exp_impl,
        "constants": {
            "g": _f(G),
            "rpm_to_rads": _f(RPM_TO_RADS),
            "rads_to_rpm": _f(RADS_TO_RPM),
            "pi": math.pi,
        },
        "dt": _f(eng.dt),
        "mass": {
            "m_total0": _f(m0),
            # run() re-reads the live config mass from step 1 on (schema 2).
            "m_total_cfg": _f(c.chassis.total_mass_kg),
            "fuel_consumption_gs": _f(c.chassis.fuel_consumption_gs),
            "f_gradient": _f(eng.F_gradient),
            "m_rot_engine": [_f(v) for v in m_rot_engine],
            "m_rot_rear": _f(m_rot_rear),
            "m_rot_front": _f(m_rot_front),
        },
        "engine": {
            "idle_rpm": _f(e.idle_rpm),
            "redline_rpm": _f(e.redline_rpm),
            "coolant_temp_c": _f(e.coolant_temp_c),
            "eta_dt": _f(eng._engine.eta_dt),
            "power_correction": _f(eng._engine.power_correction),
            "at_wheel": bool(e.dyno_curve is not None and e.dyno_curve.is_at_wheel),
            "curve": _curve(eng),
        },
        "fi": {
            "boost_type": str(fi.boost_type),
            "target_boost_bar": _f(fi.target_boost_bar),
            "turbo_spool_time_s": _f(fi.turbo_spool_time_s),
            "intercooler": fi.intercooler_type != "none",
            "intercooler_effectiveness": _f(fi.intercooler_effectiveness),
            "n2o_hp_per_stage": _f(fi.n2o_hp_per_stage),
            "n2o_stages": _f(fi.n2o_stages),
            "n2o_ramp_duration_s": _f(fi.n2o_ramp_duration_s),
            "p_boost0": _f(fi.prespool_boost_bar * 1e5 if fi.is_boosted else 0.0),
        },
        "drivetrain": {
            "overall_ratios": [_f(dtp.overall_ratio(g)) for g in range(n_gears)],
            "shift_rpms": [_f(v) for v in shift_rpms],
            "shift_time_s": _f(dtp.total_shift_time_ms / 1000.0),
            "v_limiter": None if v_limiter is None else _f(v_limiter),
            "chain": dtp.drive_type == DRIVE_CHAIN,
        },
        "clutch": {
            "t_cap": _f(c.clutch.max_torque()),
            "fade_temp_c": _f(c.clutch.fade_temp_c),
            "slider": c.clutch.clutch_type == CLUTCH_SLIDER,
            "engage_rpm": _f(c.clutch.engage_rpm),
            "engine_inertia_kgm2": _f(e.engine_inertia_kgm2),
            "basket_inertia_kgm2": _f(c.clutch.basket_inertia_kgm2),
            "thermal_mass_jk": _f(c.clutch.thermal_mass_jk),
            "t_clutch0": _f(e.coolant_temp_c),
        },
        "launch": {
            "omega_e0": _f(omega_e0),
            "over_clutch_factor": _f(prof.over_clutch_factor),
            "max_engine_decel_rads2": _f(prof.max_engine_decel_rads2),
            "floor_omega": floor_omega,
            "lock_thresh": _f(10.0 * RPM_TO_RADS),
            "idle_omega": _f(e.idle_rpm * RPM_TO_RADS),
            "redline_omega_clip": _f(e.redline_rpm * 1.02 * RPM_TO_RADS),
        },
        "tire": {
            "rear_rolling_radius_m": _f(tire_t.rear_rolling_radius_m),
            "growth_coeff": _f(tire_t.growth_coeff),
            "mu_peak": _f(tire_t.mu_peak),
            "load_sensitivity_k": _f(tire_t.load_sensitivity_k),
            "optimal_temp_c": _f(tire_t.optimal_temp_c),
            "reversion_temp_c": _f(tire_t.reversion_temp_c),
            "t_ref_k": _f(eng._tire.T_tire_ref_K),
            "mu_prep": _f(eng._tire.mu_prep),
            "crr_base": _f(tires.crr_base),
            "crr_speed_coeff": _f(tires.crr_speed_coeff),
            "crr_temp_coeff": _f(tires.crr_temp_coeff),
            "thermal_conductivity": _f(tire_t.thermal_conductivity),
            "contact_patch_cm2": _f(tire_t.contact_patch_cm2),
            "tread_mass_kg": _f(tire_t.tread_mass_kg),
            "specific_heat_rubber": _f(tire_t.specific_heat_rubber),
            "t_tire_launch": _f(eng.T_tire_launch),
        },
        "env": {
            "rho": _f(eng.rho),
            "v_wind": _f(eng.v_wind),
            "ambient_temp_c": _f(env.ambient_temp_c),
            "t_road": None if t_road is None else _f(t_road),
            "rr_multiplier": _f(eng._rr.surface_rr_multiplier),
        },
        "aero": {
            "cl": _f(c.aero.cl),
            "frontal_area_m2": _f(c.aero.frontal_area_m2),
            "ram_air_efficiency": _f(c.aero.ram_air_efficiency),
            "cd_a_upright": _f(eng._rider._cd_a_upright),
            "cd_a_full": _f(eng._rider._cd_a_full),
            "transition_s": _f(eng._rider._transition_s),
            "cd_a_floor": _f(eng._cd_a_floor),
        },
        "rider": {
            "launch_forward_shift_mm": _f(c.rider.launch_forward_shift_mm),
            "tuck_transition_time_s": _f(c.rider.tuck_transition_time_s),
        },
        "chassis": {
            "wheelbase_m": _f(wt.L),
            "cog_height_m": _f(wt.h),
            "l_f": _f(wt.L_f),
            "anti_squat_frac": _f(wt.anti_squat_frac),
        },
        "wheelie": {
            "counter_rotating": bool(e.counter_rotating),
            "wheelie_bar": bool(c.wheelie.wheelie_bar),
            "bar_length_mm": _f(c.wheelie.bar_length_mm),
        },
        "parasitic": {
            "alternator_present": bool(par.alternator_present),
            "alternator_power_w": _f(par.alternator_power_w),
            "water_pump_electric": bool(par.water_pump_electric),
            "oil_pump_power_w": _f(par.oil_pump_power_w),
            "valve_train_power_w": _f(par.valve_train_power_w),
            "parasitic_delta_hp": _f(par.parasitic_delta_hp),
            "mult": _f(eng._parasitic._mult),
        },
    }


def resolve_config(
    cfg: BikeConfig, dt: float = 0.001, *, exp_impl: str | None = None
) -> dict:
    """Resolve a :class:`BikeConfig` into the Rust core's input dict."""
    return resolve_engine(MotoQuantEngine(cfg, dt=dt), exp_impl=exp_impl)


def resolved_json(resolved: dict) -> str:
    """Serialise a resolved dict (NaN/inf are rejected — the JSON contract
    is finite doubles, repr round-trip exact)."""
    return json.dumps(resolved, allow_nan=False, separators=(",", ":"))


# ═══════════════════════════════════════════
# Run
# ═══════════════════════════════════════════


def _to_simresult(out: dict, rollout_m: float) -> SimResult:
    if "channels" not in out:
        res = SimResult(dt=out["dt"], rollout_m=rollout_m)
        for k in _SPLIT_FIELDS:
            setattr(res, k, out["splits"][k])
        res.finished_quarter = bool(out["splits"]["finished_quarter"])
        res.max_distance_m = out["splits"]["max_distance_m"]
        res.elapsed_time_s = out["splits"]["elapsed_time_s"]
        return res
    chans = out["channels"]
    kwargs = {
        attr: np.frombuffer(chans[name], dtype="<f8").copy()
        for name, attr in _FLOAT_CHANNELS
    }
    kwargs["gear"] = np.frombuffer(out["gear"], dtype="<i8").astype(int)
    # Splits are recomputed by Python's own SimResult.extract_splits() on the
    # native channels, under the same rollout convention the run used.
    res = SimResult(dt=out["dt"], rollout_m=rollout_m, **kwargs)
    res.extract_splits()
    return res


def run_resolved(
    resolved: dict | str,
    distance: float = QUARTER_MILE_M,
    max_time: float = 26.0,
    use_adaptive_dt: bool = False,
    *,
    channels: bool = True,
    rollout_m: float = ROLLOUT_M,
) -> SimResult:
    """Integrate an already-resolved config (dict or JSON string)."""
    mc = _require_core()
    payload = resolved if isinstance(resolved, str) else resolved_json(resolved)
    out = mc.simulate(
        payload,
        float(distance),
        float(max_time),
        bool(use_adaptive_dt),
        channels,
        float(rollout_m),
    )
    if out["nan_break"]:
        log.error(
            "NaN/inf in native physics state — simulation stopped early "
            "(mirrors MotoQuantEngine.run)."
        )
    return _to_simresult(out, float(rollout_m))


class NativeEngine(MotoQuantEngine):
    """``MotoQuantEngine`` whose ``run()`` integrates in Rust.

    Construction, pre-computation and every other method are the Python
    reference's, so ``run_top_speed()`` / ``run_distance()`` reuse Python's
    post-processing (plateau detection, LSR splits) verbatim. The config is
    re-resolved on every ``run()`` because the Python loop also reads the
    live config at run time — and, like ``MotoQuantEngine.run``, ``run()``
    leaves ``self.m_total`` restored from the config afterwards, so a reused
    engine starts its next run from the same mass in both implementations.
    """

    def run(
        self,
        distance: float = QUARTER_MILE_M,
        max_time: float = 26.0,
        use_adaptive_dt: bool = False,
        progress_cb=None,
        progress_every_steps: int = 250,
        rollout_m: float = ROLLOUT_M,
    ) -> SimResult:
        if progress_cb is not None:
            progress_cb(0.0)
        res = run_resolved(
            resolve_engine(self),
            distance,
            max_time,
            use_adaptive_dt,
            rollout_m=rollout_m,
        )
        # MotoQuantEngine.run: "Restore original mass for engine reuse".
        self.m_total = self.cfg.chassis.total_mass_kg
        if progress_cb is not None:
            progress_cb(1.0)
        return res


def run_native(
    cfg: BikeConfig,
    distance: float = QUARTER_MILE_M,
    max_time: float = 26.0,
    use_adaptive_dt: bool = False,
    *,
    dt: float = 0.001,
    rollout_m: float = ROLLOUT_M,
) -> SimResult:
    """Native equivalent of ``MotoQuantEngine(cfg, dt).run(...)``."""
    return NativeEngine(cfg, dt=dt).run(
        distance=distance,
        max_time=max_time,
        use_adaptive_dt=use_adaptive_dt,
        rollout_m=rollout_m,
    )


def run_top_speed_native(cfg: BikeConfig, *, dt: float = 0.001, **kwargs):
    """Native equivalent of ``MotoQuantEngine(cfg).run_top_speed(**kwargs)``
    (the plateau / LSR post-processing is Python's own code)."""
    return NativeEngine(cfg, dt=dt).run_top_speed(**kwargs)


def run_distance_native(cfg: BikeConfig, distance_m: float, *, dt: float = 0.001, **kw):
    """Native equivalent of ``MotoQuantEngine(cfg).run_distance(...)``."""
    return NativeEngine(cfg, dt=dt).run_distance(distance_m, **kw)


def summary_native(
    cfg: BikeConfig,
    distance: float = QUARTER_MILE_M,
    max_time: float = 26.0,
    use_adaptive_dt: bool = False,
    *,
    dt: float = 0.001,
    rollout_m: float = ROLLOUT_M,
) -> dict:
    """Splits only (no channel arrays) — the fastest path for sweeps.
    Splits follow the start-beam convention (``rollout_m``; the dict carries
    it as ``splits["rollout_m"]``)."""
    mc = _require_core()
    out = mc.simulate(
        resolved_json(resolve_config(cfg, dt=dt)),
        float(distance),
        float(max_time),
        bool(use_adaptive_dt),
        False,
        float(rollout_m),
    )
    d = dict(out["splits"])
    d["dt"] = out["dt"]
    d["steps"] = out["steps"]
    return d
