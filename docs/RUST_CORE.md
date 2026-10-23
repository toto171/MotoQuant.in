# Rust physics core — `rust/motoquant-core`

> Written 2026-10-23. Status: **built, bit-parity proven on the full catalog,
> optional.** `motoquant/physics.py` remains the reference implementation; the
> Rust core is an accelerator (server, via PyO3) and an in-browser engine
> (wasm32) for client-side *full* simulations.

## TL;DR

| | Python reference | Rust native (PyO3) | Rust wasm32 (browser) |
|---|---|---|---|
| Quarter-mile, fixed dt | ~430 ms/sim | **5.1 ms** (loop) / 8.9 ms end-to-end | **5.2 ms** (summary) / 6.5 ms (+ all channels), node 22 |
| Parity vs Python | — | **bit-identical**: every channel, every step, all 541 catalog bikes (fixed + adaptive + top speed) + 240 stress variants | ET / trap / every split / sample count **identical** on all 1,082 catalog runs; position/velocity/rpm/temperature channels bit-identical; force-type channels carry 1-ULP noise (see below) |
| Size | — | 0.95 MB abi3 `.so` | **270 KB raw / 93 KB gzip** |

Numbers: `reports/native_parity_2026-10-23.json` (`make native-parity`) and
`node web/scripts/engine-parity.mjs` (`make wasm`). Host: 4-core Xeon
(AVX-512), Python 3.13, NumPy 2.4.6, rustc 1.97.

## Architecture: "Python resolves, Rust integrates"

```
BikeConfig ──► MotoQuantEngine(cfg)  ──►  native.resolve_engine(eng)  ──► JSON (schema 1)
 (Python)       _precompute()               every value run() reads,          │
                _init_submodels()           AFTER category dispatch,          ▼
                category profile            env corrections, tire mu    rust/motoquant-core
                env model, parts…           scale, ratios, shift rpms,  Engine::run()  (the loop)
                                            effective-mass terms, …           │
                                                                              ▼
                       SimResult (numpy) ◄── native._to_simresult ◄── channels + splits
                       extract_splits() — Python's own code
```

* **Everything that is policy stays Python**: category dispatch
  (`category_profiles.py`), defaults, parts application, venue/weather
  handling, profile knobs, `optimal_shift_rpm`, `EnvironmentalModel`. A knob or
  catalog change never needs a Rust change.
* **Only the integrator is ported**: `MotoQuantEngine.run()` and the sub-model
  methods it calls per step (`EngineModel.torque`, `ForcedInductionModel`,
  `TireModel.friction_coeff/thermal_rate/effective_radius`, `AeroModel`,
  `WeightTransferModel`, `WheelieModel`, `RollingResistanceModel`,
  `ParasiticModel`, `RiderDynamicsModel.cd_a`, `RiderParams.cog_offset`,
  `ChainModel`, the clutch slip/lock/lock-transition logic, the
  `EngineParams.get_torque` curves incl. the curve-less 2-stroke/4-stroke
  fallbacks) plus `SimResult.extract_splits`.
* `motoquant.native.NativeEngine` **subclasses** `MotoQuantEngine` and only
  overrides `run()`. `run_top_speed()` / `run_distance()` therefore reuse
  Python's plateau detection and LSR splits verbatim — no duplicated logic.

### Files

| Path | Role |
|---|---|
| `rust/Cargo.toml` | workspace; `release` (native, LTO) and `wasm-release` (opt-level "s", LTO, strip, panic=abort) profiles |
| `rust/motoquant-core/src/engine.rs` | the run loop + per-step sub-model math |
| `rust/motoquant-core/src/config.rs` | the resolved-config schema (serde, `deny_unknown_fields`) |
| `rust/motoquant-core/src/fmath.rs` | `pow`/`sin`/`exp` with CPython/NumPy semantics; scalar port of Intel SVML `__svml_exp8_ha` |
| `rust/motoquant-core/src/interp.rs` | `np.interp` / `np.searchsorted` ports (NumPy 2.4.6 `compiled_base.c`, `binsearch.cpp`) |
| `rust/motoquant-core/src/splits.rs` | `SimResult.extract_splits` |
| `rust/motoquant-core/src/lib.rs` | `simulate()`, byte-level API, wasm raw C ABI, PyO3 module (`--features python`) |
| `rust/motoquant-core/pyproject.toml` | maturin packaging (wheel `motoquant-core`, module `motoquant_core`, abi3-py39 → one wheel serves the 3.11 Docker image and 3.13 dev) |
| `rust/motoquant-core/tests/fixtures.rs` | native Rust vs Python-reference fixtures (no Python needed) + NaN-guard, schema, byte-API tests |
| `rust/fixtures/engine_parity.json` | 53 Python-reference cases (refs, ~3 bikes per category cluster, 2T/limiter/shaft/belt, boosted/stress) with a sha256 per output channel |
| `motoquant/native.py` | `available()`, `resolve_config()`, `run_native()`, `NativeEngine`, `run_top_speed_native()`, `summary_native()`, `host_math()` |
| `scripts/check_native_parity.py` | the full parity sweep + benchmarks → `reports/native_parity_<date>.json` |
| `scripts/gen_engine_web.py` | builds/copies the wasm, writes `web/public/engine/engine.json` + the fixtures |
| `web/lib/engine.js` | browser loader: `loadEngine()`, `simulate(resolved, {distance, maxTime, adaptive, channels})` |
| `web/scripts/engine-parity.mjs` | runs the REAL `engine.js` under node (fetch shim) against the fixtures |
| `web/public/engine/motoquant_core.wasm` | the committed browser engine (generated asset, like `web/public/surrogate/*`) |
| `tests/test_native_engine.py` | pytest gate (skips without the extension; freshness guards always run) |

## How bit-parity is achieved

IEEE-754 `+ - * /` are deterministic, so parity reduces to (1) evaluating every
expression in Python's order and (2) calling the *same* transcendental
functions. Concretely:

1. **Evaluation order.** `a * b * c` is `(a * b) * c`; nothing is
   re-associated, fused (Rust never contracts to FMA implicitly) or
   "simplified". Loop invariants come pre-resolved from Python using the exact
   expressions `run()` uses (`resolve_engine` even re-checks
   `DrivetrainModel.effective_mass` bit-for-bit at resolve time).
2. **`x ** 2` is NOT `x * x`.** CPython's `float ** 2` (and NumPy's
   `float64 ** 2`) call C `pow(x, 2.0)`; glibc `pow` is not correctly rounded
   and differs from `x * x` in ~0.09 % of inputs (measured). Every `**` in the
   loop goes through `fmath::pow`, with `black_box` on the exponent so LLVM's
   libcall simplifier cannot rewrite `pow(x, 2.0)` into `x * x`.
3. **`np.exp` is not `math.exp`.** The tire thermal factor uses `np.exp`. On an
   AVX512_SKX CPU with an SVML-linked NumPy (the PyPI wheels) that dispatches to
   Intel SVML `__svml_exp8_ha`, which differs from glibc `exp` in ~4.6 % of
   inputs. `fmath::exp_svml_ha` is an instruction-by-instruction scalar
   transliteration of that routine's main path (table + polynomial + one
   round-toward-zero FMA, emulated exactly). Elsewhere NumPy falls back to the C
   library `exp`. `native.host_math()` **probes the host at runtime** and puts
   `exp_impl: "svml_ha" | "libm"` into the resolved config, so the native engine
   tracks whatever the local Python reference does. Pinned by 16 captured
   NumPy bit patterns in `fmath.rs` tests and by `test_host_math_is_reproduced`.
4. **NumPy primitives.** `np.interp` (binary search with guess, exact-knot and
   last-knot branches, slope formula, NaN fallbacks) and `np.searchsorted`
   (NaN-aware `DOUBLE_LT`) are ported from the NumPy 2.4.6 C sources and
   fuzz-tested against NumPy (`test_np_interp_parity_random`).
5. **Python `min`/`max` semantics.** `max(a, b)` returns `a` unless `b > a` —
   this matters for NaN (`max(0.0, nan) == 0.0`, which is why NaN is laundered
   while the clutch slips) and for signed zeros. `py_max`/`py_min` replicate it.
6. **JSON transport is exact.** Python writes `repr` round-trip doubles;
   serde_json runs with `float_roundtrip` (its default parser can be 1 ULP off).
   `test_resolved_config_round_trips_exactly` proves Python → Rust → Python is
   the identity.
7. **Error behaviour.** `distance <= 0` raises `UnboundLocalError` in Python
   (loop locals never bound) — native re-raises the same class;
   `max_time < 0` → `ValueError` on both; zero wheelbase / CoG height →
   `ZeroDivisionError` at resolve (Python raises on its first step).

The per-step work is also *de-duplicated without changing a bit*: Python
recomputes the tire thermal factor, pressure-grip factor, aero lift and rider
CoG offset on every one of the up-to-three friction / weight-transfer calls in
a traction-limited step with identical arguments; Rust evaluates each once per
step (same expression, same inputs → same doubles).

## Parity results (2026-10-23)

`make native-parity` (= `scripts/check_native_parity.py --topspeed-sample 0`
for the full top-speed sweep). Each case runs Python and native in the same
worker and compares **every SimResult channel element-by-element** (t, x, v, a,
rpm, gear, slip, traction %, N_front, N_rear, F_drive, F_drag, F_rr, T_tire,
T_clutch, P_boost, power, r_eff), sample counts, the final `dt` and every
split.

| Section | Cases | Bit-identical (all channels) | worst \|ΔET\| |
|---|---|---|---|
| references (K5 / R1 / Hayabusa × fixed, adaptive, top speed) | 9 | 9 | 0 |
| catalog — every current `bike_config`, fixed dt, via `db_row_to_config` | 541 | 541 | 0 |
| adaptive dt — every catalog bike | 541 | 541 | 0 |
| top speed (`run_top_speed`, adaptive, plateau + LSR splits) — every catalog bike | 541 | 541 | 0 |
| stress (below) | 242 | 238 (+4 both-raise) | 0 |

Stress variants: turbo (with/without intercooler, near-instant spool),
Roots + centrifugal superchargers, N2O 1–2 stages incl. a 50 ms ramp — on a
litre bike, a sub-200 cc 4T and a 2-stroke; slider (engage 3,000 / 6,500
rpm), multistage, slipper and lockup clutches incl. heat fade; a slider that
never engages (stalls to `max_time` — exercises adaptive array growth); all 8
track surfaces + an unknown string; head/tail/cross wind, ram air ± headwind;
±3 % gradient; altitude/heat/humidity, cold, `track_temp_c = None`; VHT /
rubber prep; speed limiters (140 km/h engaging inside the quarter, 0 = off,
catalog limiter bikes in top-speed mode); dyno `is_at_wheel` flipped both
ways; curve-less 4T parabolic and every curve-less 2T band (powervalve,
1-cyl < 200 cc, 1-cyl 250 cc, twin, triple, `tuned_rpm=None`); rider 40 / 150
kg; wheelie bar; counter-rotating crank; belly pan / upright / race crouch;
parasitic deltas; coolant < 70 °C / > 100 °C; heavy fuel burn; chain → shaft;
two-step launch; zero tuck time; reversion-prone tire; **every one of the 13
category profiles** (and `None`) on two bikes; patched profile knobs
(`launch_rpm_factor`, over-clutch + launch floor on a litre bike); dt 0.5 ms
/ 2 ms; time caps; 60 ft / 1,000 m distances; custom plateau windows; the
degenerate `distance = 0` / `max_time < 0` error paths.

**Target met: worst |ΔET| = 0 s (≤ 1e-9 required) across 1,874 cases; there
is no residual to root-cause on this host.**

### wasm32 (browser) parity

`make wasm` → `node web/scripts/engine-parity.mjs` runs the real `engine.js`
against the committed 53-case fixture; `scripts/gen_engine_web.py
--full-catalog PATH` writes an every-bike fixture (fixed + adaptive, 1,082
runs) for the same harness.

* ET, trap speed, **every split**, `finished`, sample count and final `dt`:
  **identical (|Δ| = 0) on all 1,082 catalog runs and all 53 fixture cases.**
* Integrated state channels (t, x, v, rpm, gear, T_tire, T_clutch, P_boost,
  r_eff): bit-identical everywhere.
* Force-type channels (F_drag, F_rr, N_front/N_rear, slip, traction %, a,
  F_drive, power) differ by **1 ULP at a small fraction of steps**
  (e.g. K5: 27 of 9,935 F_drag samples). Root cause: wasm has no glibc, so
  Rust's pure-Rust libm (musl/FreeBSD-msun lineage) supplies `pow` and `sin`,
  and its `pow(x, 2.0)` rounds differently from glibc's in rare cases. Those
  1-ULP force differences are absorbed by the integrator: they enter `v`
  through `dt/6·(k1 + 2k2 + 2k3 + k4)`, i.e. scaled by ~1.7e-4 relative to `v`
  itself, far below one ULP of `v`, so the trajectory — and every reported
  time — is unchanged. A discrete event (gear-shift threshold, clutch lock)
  could in principle amplify a 1-ULP state difference; none occurred on the
  catalog. The SVML `exp` emulation is pure Rust (`f64::mul_add` → correctly
  rounded software FMA on wasm) and therefore bit-exact in the browser too.

## Performance

Serial, single core, best-of-3 (`reports/native_parity_2026-10-23.json`
`bench`; 23 bikes = 3 references + 20 catalog picks):

| Mode | Python | native end-to-end (resolve + run + numpy) | native loop only | speed-up |
|---|---|---|---|---|
| fixed dt (≈12.6k steps) | 429 ms | 8.9 ms | 5.1 ms | 48× / 83× |
| adaptive dt (≈8.0k steps) | 324 ms | 6.2 ms | 3.6 ms | 52× / 91× |
| resolve only | — | 0.8 ms | — | — |

(Python timings vary ±10 % run-to-run on this shared box; an earlier run measured 387 / 288 ms with the same native numbers.)

wasm32 under node 22 (V8): 5.2 ms/sim summary-only, 6.5 ms with all 18
channels decoded. Opt-level sweep for the wasm profile: `z` 246 KB / 89 KB gz
/ 11.4 ms, **`s` 270 KB / 93 KB gz / 5.2 ms (chosen)**, `3` 291 KB / 108 KB
gz / 10.5 ms. About 40 % of the wasm per-step cost is the SVML-exact `exp`
(13 software FMAs); `exp_impl: "libm"` runs ~2× faster but no longer matches
an AVX-512 NumPy host bit-for-bit.

For comparison, the Pyodide route in `docs/CLIENT_COMPUTE.md` (Tier 2) costs a
~15 MB payload and is expected at 3–10× *slower* than native Python (~1–4 s
per sim); the Rust wasm engine is ~93 KB gzip and ~80× *faster* than
native Python.

## Build & use

```bash
make native          # maturin build --release (abi3 wheel) + pip install
make native-test     # cargo test (fixtures, NaN guard, byte API) + pytest gate
make native-parity   # full sweep → reports/native_parity_<date>.json
make wasm            # cargo build wasm32 + copy + manifest + fixtures + node parity
```

```python
from motoquant import native

if native.available():
    r = native.run_native(cfg)  # SimResult, identical to MotoQuantEngine(cfg).run()
    ts = native.run_top_speed_native(
        cfg
    )  # TopSpeedResult via Python's own post-processing
    eng = native.NativeEngine(cfg)  # drop-in MotoQuantEngine subclass
    s = native.summary_native(cfg)  # splits only, no channel arrays (fastest)
    native.native_info()  # version, schema, exp_impl, exact
```

```js
import { loadEngine, simulate } from '@/lib/engine';
await loadEngine();                            // fetches /engine/motoquant_core.wasm once
const r = await simulate(resolvedConfig, { adaptive: false });
r.et; r.trapKmh; r.splits; r.channels.v; r.gear;
```

The browser needs a *resolved* config. Today the fixtures carry them; the
production path is a server route that returns
`native.resolved_json(native.resolve_config(cfg))` for a bike/venue/parts
selection (≈ 5–9 KB JSON, cacheable per selection) — not wired yet (see
"Next steps").

## The regen contract

The Rust core is a cache of `run()`'s *code*, in the same way the surrogate is
a cache of its *outputs*. It must be kept in lock-step:

| You changed… | You must… | Gate that catches it |
|---|---|---|
| `physics.py` `run()` or any sub-model method it calls | port the same change to `engine.rs`, `make native wasm`, `make native-parity` | `test_engine_fixtures_are_fresh` (Python ET vs committed fixture), `tests/test_native_engine.py` bit-identity, `cargo test` fixtures |
| what `resolve_engine` must serialise (new knob read in the loop, renamed field) | bump `SCHEMA_VERSION` in **both** `native.py` and `config.rs`, `make native wasm` | `deny_unknown_fields`, schema check on both sides, `test_engine_fixtures_are_fresh` (resolve drift) |
| catalog data, category-profile values, defaults, parts | nothing for parity (resolved at run time); regenerate fixtures with `make wasm` only if a *fixture* bike's ET moved | `test_engine_fixtures_are_fresh` |
| the Rust code | `make native-test native-parity wasm` | all of the above |

A schema mismatch never produces a silently wrong number: the extension
refuses (`available()` is False on a schema mismatch), and the wasm loader
throws.

## Limitations (honest list)

* **Bit-parity is host-relative.** Python's own results depend on the host's
  libm and NumPy dispatch (glibc `pow`, SVML vs libm `exp`). The native engine
  calls the same libm and probes the NumPy `exp` path, so it matches the
  *local* Python bit-for-bit; two different machines can still disagree with
  *each other* at the ULP level. `native_info()["exact"]` reports whether the
  probe reproduced the host; if a NumPy build dispatches `np.exp` to something
  else (e.g. NumPy's AVX512F Tang kernel on a non-SVML build), `exact` is
  False and results carry ULP-level drift (not yet ported; the probe makes it
  visible).
* **wasm uses Rust's libm**, not glibc: 1-ULP force-channel noise, reported
  times identical on the catalog (see above).
* **Non-finite inputs are refused.** The JSON contract is finite doubles; a
  NaN/inf config raises `ValueError` on the native path where Python would
  propagate it into garbage. The NaN/inf *guard* (break + trim) is ported and
  pinned by a Rust unit test, but it is unreachable from finite inputs.
* **`progress_cb`** is honoured coarsely (0.0 at start, 1.0 at end) — a native
  sim takes milliseconds, so there is nothing to report in between.
* **Python-float exceptions in degenerate configs** (`OverflowError` from
  `float ** 2`, `ZeroDivisionError` mid-loop) become IEEE inf/NaN in Rust;
  only the two divisors that are config constants (wheelbase, CoG height) are
  pre-checked.
* `pacejka_force`, `BrakingModel`, `ClutchModel.torque` and
  `StagingModel.total_dead_time_s` are **not** ported — `run()` does not call
  them.

## Decision record (proposed ADR-0007 — amends ADR-0003 and CLIENT_COMPUTE)

* **ADR-0003's re-open criteria are met.** It rejected Numba because a JIT
  rewrite "voids the bit-identical baseline pin" and asked for "a prototype
  that demonstrates a JIT path producing bit-identical baselines AND a
  measured end-to-end win on a real workload". This core is bit-identical on
  the three pins and on every channel of all 541 catalog bikes in three modes,
  with a 48–91× measured win (end-to-end / loop-only). Numba itself stays rejected (heavy dependency,
  and it cannot express the libm/SVML call-for-call semantics).
* **CLIENT_COMPUTE's "JS port" rejection is answered, not ignored.** The
  objection was a second implementation that must track the baseline forever.
  Mitigations: (1) the port surface is only the integrator — all policy stays
  in Python via the resolved config; (2) drift is *mechanically* detected
  (fixture freshness test in the always-on pytest suite, full-catalog parity
  sweep, cargo fixture test, node parity); (3) it is one Rust source compiled
  to both targets, not a JS rewrite. It also beats Pyodide on payload (93 KB
  vs ~15 MB) and speed (~5 ms vs seconds).
* **Python remains the reference.** No route switches to native by default in
  this change; adoption is a separate, reviewable step.

## Next steps (not done here)

1. **Server adoption.** In `api.py`, use `native.run_native` when
   `native.available()` (fall back to Python otherwise) for `/api/simulate`,
   top speed and the optimizer/autotune verification sims; add the wheel build
   to the Dockerfile (`pip install maturin && maturin build` in a builder
   stage, ~40 s; the abi3 wheel is `manylinux_2_34` and fits the Debian
   bookworm image). Gate with `make native-parity` in CI.
2. **Resolved-config route** (`GET /api/resolve?bike_id=&venue_id=&parts=`)
   so the simulator page can run exact full sims client-side with
   `web/lib/engine.js` (labelled "exact — computed on your device"); keep
   leaderboard saves server-authoritative (recompute on save).
3. **Sweeps / surrogate data generation** through `summary_native` +
   `multiprocessing` (~50–80× fewer CPU-seconds for `phys_weighted_sweep`,
   `tune_cluster_knobs`, surrogate regen).
4. CI: `cargo test` + `make native-test` on PRs touching `physics.py`,
   `submodels/`, `models.py`, `native.py` or `rust/`; nightly
   `make native-parity`.
5. Optional: port NumPy's AVX512F Tang `exp` as a third `exp_impl` for
   non-SVML NumPy builds.
