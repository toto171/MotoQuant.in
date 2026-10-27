#!/usr/bin/env python3
"""
Browser-engine export: build/copy the wasm32 Rust core and regenerate the
parity fixtures that prove it reproduces the Python reference.

    python scripts/gen_engine_web.py            # fixtures only
    python scripts/gen_engine_web.py --build    # cargo build wasm32 + copy + fixtures
    python scripts/gen_engine_web.py --full-catalog /tmp/all.json
        # every catalog bike, fixed + adaptive (1,082 cases), for
        # `node web/scripts/engine-parity.mjs /tmp/all.json`

Outputs
-------
web/public/engine/motoquant_core.wasm   the in-browser engine (raw C ABI,
                                        loaded by web/lib/engine.js)
web/public/engine/engine.json           manifest: schema + source fingerprint READ
                                        FROM THE WASM'S OWN EXPORTS, sha256, sizes
rust/fixtures/engine_parity.json        resolved configs + Python reference
                                        results (ET/trap/splits/sample count +
                                        a sha256 per output channel). Consumed by
                                        web/scripts/engine-parity.mjs (wasm) and
                                        rust/motoquant-core/tests/fixtures.rs
                                        (native Rust, no Python needed).

Regen contract (docs/RUST_CORE.md): any resolved-config SCHEMA change, any
Rust engine change, or any physics/catalog change that moves a Python ET means
`make wasm` (this script with --build, then the node parity check).
"""

from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np  # noqa: E402

import motoquant as mq  # noqa: E402
from motoquant import native  # noqa: E402
from motoquant.constants import ROLLOUT_M  # noqa: E402
from motoquant.physics import MotoQuantEngine  # noqa: E402

RUST = ROOT / "rust"
WASM_SRC = (
    RUST / "target" / "wasm32-unknown-unknown" / "wasm-release" / "motoquant_core.wasm"
)
WEB_ENGINE = ROOT / "web" / "public" / "engine"
FIXTURES = RUST / "fixtures" / "engine_parity.json"

CHANNELS = (
    "t",
    "x",
    "v",
    "a",
    "rpm",
    "slip",
    "traction_pct",
    "N_front",
    "N_rear",
    "F_drive",
    "F_drag",
    "F_rr",
    "T_tire",
    "T_clutch",
    "P_boost",
    "power_kw",
    "r_eff",
)  # fmt: skip — the Rust FLOAT_CHANNELS order
SPLITS = (
    "time_60ft", "speed_60ft", "time_330ft", "speed_330ft", "time_eighth",
    "speed_eighth", "time_1000ft", "speed_1000ft", "time_quarter",
    "speed_quarter", "max_distance_m", "elapsed_time_s",
)  # fmt: skip


# ═══════════════════════════════════════════
# Static wasm reader (no runtime needed)
# ═══════════════════════════════════════════
#
# The manifest's schema/fingerprint must come from the BINARY, not from
# Python constants — otherwise a stale committed wasm would be certified by
# the very values it is supposed to be checked against. The four metadata
# exports are constant functions (`i32.const N; end`), so they can be read by
# parsing the module instead of instantiating it.


def _uleb(b: bytes, i: int) -> tuple[int, int]:
    val = shift = 0
    while True:
        byte = b[i]
        i += 1
        val |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            return val, i


def _sleb(b: bytes, i: int) -> tuple[int, int]:
    val = shift = 0
    while True:
        byte = b[i]
        i += 1
        val |= (byte & 0x7F) << shift
        shift += 7
        if not byte & 0x80:
            if byte & 0x40:
                val -= 1 << shift
            return val, i


def wasm_const_exports(data: bytes, names: tuple[str, ...]) -> dict[str, int]:
    """Return the u32 constant each named exported function returns.

    Raises ValueError if the module is malformed, an export is missing, or a
    function body is not exactly ``i32.const N; end`` (no locals).
    """
    if data[:8] != b"\0asm\x01\0\0\0":
        raise ValueError("not a wasm v1 module")
    i, n_imported_funcs = 8, 0
    exports: dict[str, int] = {}
    bodies: list[bytes] = []
    while i < len(data):
        sec_id = data[i]
        size, i = _uleb(data, i + 1)
        sec, i = data[i : i + size], i + size
        if sec_id == 2:  # imports: imported functions shift the index space
            count, j = _uleb(sec, 0)
            for _ in range(count):
                for _ in range(2):  # module name, field name
                    ln, j = _uleb(sec, j)
                    j += ln
                kind = sec[j]
                j += 1
                if kind == 0:
                    n_imported_funcs += 1
                    _, j = _uleb(sec, j)
                elif kind == 1:  # table: reftype + limits
                    j += 1
                    flags, j = _uleb(sec, j + 0)
                    _, j = _uleb(sec, j)
                    if flags & 1:
                        _, j = _uleb(sec, j)
                elif kind == 2:  # memory: limits
                    flags, j = _uleb(sec, j)
                    _, j = _uleb(sec, j)
                    if flags & 1:
                        _, j = _uleb(sec, j)
                elif kind == 3:  # global: valtype + mut
                    j += 2
                else:
                    raise ValueError(f"unknown import kind {kind}")
        elif sec_id == 7:  # exports
            count, j = _uleb(sec, 0)
            for _ in range(count):
                ln, j = _uleb(sec, j)
                name = sec[j : j + ln].decode()
                j += ln
                kind = sec[j]
                idx, j = _uleb(sec, j + 1)
                if kind == 0:
                    exports[name] = idx
        elif sec_id == 10:  # code
            count, j = _uleb(sec, 0)
            for _ in range(count):
                ln, j = _uleb(sec, j)
                bodies.append(sec[j : j + ln])
                j += ln
    out = {}
    for name in names:
        if name not in exports:
            raise ValueError(f"wasm has no exported function {name!r}")
        body = bodies[exports[name] - n_imported_funcs]
        n_locals, j = _uleb(body, 0)
        if n_locals != 0 or body[j] != 0x41:
            raise ValueError(f"{name}: body is not a bare i32.const")
        val, j = _sleb(body, j + 1)
        if body[j:] != b"\x0b":
            raise ValueError(f"{name}: body is not `i32.const N; end`")
        out[name] = val & 0xFFFFFFFF
    return out


def wasm_metadata(path: Path) -> dict:
    """``{"schema": int, "source_fingerprint": "16 hex"}`` read from the
    wasm's own ``schema_version`` / ``source_fingerprint_hi|lo`` exports."""
    c = wasm_const_exports(
        Path(path).read_bytes(),
        ("schema_version", "source_fingerprint_hi", "source_fingerprint_lo"),
    )
    fp = (c["source_fingerprint_hi"] << 32) | c["source_fingerprint_lo"]
    return {"schema": c["schema_version"], "source_fingerprint": f"{fp:016x}"}


def build_wasm() -> None:
    cmd = [
        "cargo", "build", "-p", "motoquant-core", "--profile", "wasm-release",
        "--target", "wasm32-unknown-unknown",
    ]  # fmt: skip
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=RUST, check=True)
    WEB_ENGINE.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(WASM_SRC, WEB_ENGINE / "motoquant_core.wasm")


def write_manifest(*, built: bool) -> dict:
    wasm = WEB_ENGINE / "motoquant_core.wasm"
    data = wasm.read_bytes()
    meta = wasm_metadata(wasm)
    if meta["schema"] != native.SCHEMA_VERSION:
        raise SystemExit(
            f"wasm exports schema {meta['schema']} but native.SCHEMA_VERSION is "
            f"{native.SCHEMA_VERSION} — the committed wasm is stale; run `make wasm`"
        )
    here = native.fingerprint_sources()
    if built and here is not None and meta["source_fingerprint"] != here:
        raise SystemExit(
            f"freshly built wasm fingerprint {meta['source_fingerprint']} != "
            f"checkout {here} (build.rs / native.fingerprint_sources drifted?)"
        )
    if here is not None and meta["source_fingerprint"] != here:
        print(
            f"WARNING: wasm was built from other Rust sources "
            f"({meta['source_fingerprint']} != {here}); rebuild with --build",
            file=sys.stderr,
        )
    manifest = {
        "schema": meta["schema"],
        "source_fingerprint": meta["source_fingerprint"],
        "file": "motoquant_core.wasm",
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
        "gzip_bytes": len(gzip.compress(data, compresslevel=9)),
        "abi": (
            "raw C ABI: alloc(len)->ptr, dealloc(ptr,len), simulate(ptr,len)->ptr, "
            "schema_version(), source_fingerprint_hi(), source_fingerprint_lo()"
        ),
        "note": "Generated by scripts/gen_engine_web.py --build; do not edit.",
    }
    (WEB_ENGINE / "engine.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def _digest(arr) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(np.asarray(arr, dtype="<f8")).tobytes()
    ).hexdigest()


def _python_case(
    label: str,
    cfg,
    *,
    adaptive=False,
    distance=None,
    max_time=None,
    dt=0.001,
    rollout_m=ROLLOUT_M,
) -> dict:
    kw = {"use_adaptive_dt": adaptive, "rollout_m": rollout_m}
    if distance is not None:
        kw["distance"] = distance
    if max_time is not None:
        kw["max_time"] = max_time
    r = MotoQuantEngine(copy.deepcopy(cfg), dt=dt).run(**kw)
    resolved = native.resolve_config(copy.deepcopy(cfg), dt=dt)
    dist = float(kw.get("distance", 402.336))
    # Python does not expose its step counter: every loop iteration stores one
    # sample, and the finish-line crossing stores one more (x >= x_end, the
    # finish line rollout_m + distance from rest).
    x_end = dist + float(rollout_m)
    n = int(len(r.t))
    steps = n - 1 if n and float(r.x[-1]) >= x_end else n
    return {
        "label": label,
        "request": {
            "distance": float(kw.get("distance", 402.336)),
            "max_time": float(kw.get("max_time", 26.0)),
            "adaptive": bool(adaptive),
            "rollout_m": float(rollout_m),
        },
        "config": resolved,
        "expected": {
            "n": n,
            "steps": steps,
            "dt": float(r.dt),
            "finished_quarter": bool(r.finished_quarter),
            **{k: float(getattr(r, k)) for k in SPLITS},
            "channel_sha256": {
                **{ch: _digest(getattr(r, ch)) for ch in CHANNELS},
                "gear": _digest(np.asarray(r.gear, dtype=np.float64)),
            },
        },
    }


def select_cases() -> list[tuple]:
    from check_native_parity import cfg_from_row, load_catalog_rows

    catalog = load_catalog_rows(ROOT / "motoquant.db")
    out: list[tuple] = []
    for f in ("gsxr1000_k5", "yzfr1_4c8", "hayabusa_gen1"):
        cfg = getattr(mq, f)()
        out.append((f, cfg, {}))
        out.append((f + " adaptive", cfg, {"adaptive": True}))

    # ~3 bikes per category cluster (deterministic: lowest bike_model_id first),
    # plus every special drivetrain/engine family the stress suite cares about.
    per_tag: dict = {}
    special = {"two_stroke": None, "limiter": None, "shaft": None, "belt": None}
    for label, row in catalog:
        tag = row.get("category_tag") or "none"
        per_tag.setdefault(tag, [])
        if len(per_tag[tag]) < 3:
            per_tag[tag].append((label, row))
        eng = json.loads(row["engine_params"] or "{}")
        drv = json.loads(row["drivetrain_params"] or "{}")
        if special["two_stroke"] is None and eng.get("stroke_type") == 2:
            special["two_stroke"] = (label, row)
        if special["limiter"] is None and drv.get("speed_limiter_kmh"):
            special["limiter"] = (label, row)
        if special["shaft"] is None and drv.get("drive_type") == "shaft":
            special["shaft"] = (label, row)
        if special["belt"] is None and drv.get("drive_type") == "belt":
            special["belt"] = (label, row)
    picked = {}
    for rows in per_tag.values():
        for label, row in rows:
            picked[label] = row
    for v in special.values():
        if v is not None:
            picked[v[0]] = v[1]
    for label, row in sorted(picked.items()):
        out.append((label, cfg_from_row(row, label), {}))

    busa = mq.hayabusa_gen1()

    def mut(**paths):
        c = copy.deepcopy(busa)
        for path, val in paths.items():
            obj = c
            parts = path.split("__")
            for p in parts[:-1]:
                obj = getattr(obj, p)
            setattr(obj, parts[-1], val)
        return c

    out += [
        ("busa turbo 1bar a2a", mut(forced_induction__boost_type="turbo", forced_induction__target_boost_bar=1.0,
                                    forced_induction__prespool_boost_bar=0.3, forced_induction__intercooler_type="a2a"), {}),
        ("busa n2o 2x75hp", mut(forced_induction__boost_type="n2o", forced_induction__n2o_hp_per_stage=75.0,
                                forced_induction__n2o_stages=2), {}),
        ("busa sc_centrifugal", mut(forced_induction__boost_type="sc_centrifugal", forced_induction__target_boost_bar=0.8), {}),
        ("busa slider clutch", mut(clutch__clutch_type="slider", clutch__engage_rpm=4000.0), {"adaptive": True}),
        ("busa wet", mut(environment__track_surface="wet"), {}),
        ("busa headwind + ram air", mut(environment__wind_speed_ms=6.0, aero__ram_air_efficiency=0.6), {}),
        ("busa limiter 140", mut(drivetrain__speed_limiter_kmh=140.0), {}),
        ("busa parabolic (no dyno)", mut(engine__dyno_curve=None), {}),
        ("busa downhill 3% wheelie bar", mut(environment__track_gradient_pct=-3.0, wheelie__wheelie_bar=True), {}),
        ("busa 1000m adaptive", busa, {"adaptive": True, "distance": 1000.0, "max_time": 60.0}),
        # 2026-10 physics epoch. web/scripts/engine-parity.mjs forwards
        # request.rollout_m, so the rollout-0 case is compared like any other.
        ("busa rollout 0 (from first motion)", busa, {"rollout_m": 0.0}),
        ("busa turbo 1.5bar weak clutch", mut(forced_induction__boost_type="turbo", forced_induction__target_boost_bar=1.5,
                                              clutch__spring_preload_n=400.0), {}),
        ("busa over-clutch launch above floor", mut(category_tag="other", staging__two_step=True,
                                                    staging__launch_rpm=9500.0), {}),
    ]  # fmt: skip
    return out


def _full_catalog_worker(item):
    from check_native_parity import cfg_from_row

    label, row, kw = item
    return _python_case(label, cfg_from_row(row, label), **kw)


def export_full_catalog(path: Path, workers: int | None = None) -> dict:
    """Every current catalog bike, fixed + adaptive, as a fixture file for
    the node harness (not committed: ~1,082 cases)."""
    import multiprocessing as mp
    import os

    from check_native_parity import load_catalog_rows

    items = []
    for label, row in load_catalog_rows(ROOT / "motoquant.db"):
        items.append((label, row, {}))
        items.append((label + " adaptive", row, {"adaptive": True}))
    with mp.get_context("fork").Pool(workers or os.cpu_count() or 2) as pool:
        cases = pool.map(_full_catalog_worker, items, chunksize=4)
    info = native.host_math() if native.available() else {"exp_impl": "libm"}
    fixture = {
        "schema": native.SCHEMA_VERSION,
        "tolerance_s": 1e-9,
        "generated_by": "scripts/gen_engine_web.py --full-catalog",
        "host": {"numpy": np.__version__, "exp_impl": info.get("exp_impl")},
        "cases": cases,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fixture, separators=(",", ":")) + "\n")
    return fixture


def export_fixtures() -> dict:
    cases = []
    for label, cfg, kw in select_cases():
        cases.append(_python_case(label, cfg, **kw))
        print(f"  {label:48s} ET={cases[-1]['expected']['time_quarter']:.6f}")
    info = (
        native.host_math()
        if native.available()
        else {"exp_impl": "libm", "exact": False}
    )
    fixture = {
        "schema": native.SCHEMA_VERSION,
        "tolerance_s": 1e-9,
        "generated_by": "scripts/gen_engine_web.py",
        "host": {"numpy": np.__version__, "exp_impl": info.get("exp_impl")},
        "note": (
            "Python reference results (motoquant/physics.py). channel_sha256 = sha256 of "
            "each output channel as little-endian float64 bytes (gear as float64)."
        ),
        "cases": cases,
    }
    FIXTURES.parent.mkdir(parents=True, exist_ok=True)
    FIXTURES.write_text(json.dumps(fixture, separators=(",", ":")) + "\n")
    return fixture


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--build",
        action="store_true",
        help="cargo build the wasm32 engine and copy it into web/public/engine/",
    )
    ap.add_argument("--no-fixtures", action="store_true")
    ap.add_argument(
        "--full-catalog",
        metavar="PATH",
        help="write an every-bike (fixed + adaptive) fixture to PATH and exit",
    )
    args = ap.parse_args()
    if args.full_catalog:
        fx = export_full_catalog(Path(args.full_catalog))
        print(f"full-catalog fixture: {len(fx['cases'])} cases -> {args.full_catalog}")
        return 0
    if args.build:
        build_wasm()
    if (WEB_ENGINE / "motoquant_core.wasm").exists():
        m = write_manifest(built=args.build)
        print(
            f"wasm: {m['bytes']} B raw / {m['gzip_bytes']} B gzip  sha256={m['sha256'][:16]}…"
        )
    if not args.no_fixtures:
        fx = export_fixtures()
        print(
            f"fixtures: {len(fx['cases'])} cases -> {FIXTURES.relative_to(ROOT)} "
            f"({FIXTURES.stat().st_size // 1024} KB)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
