# Rust physics core — `rust/motoquant-core`

> Written 2026-10-23; updated 2026-10-24 (schema 2, production wiring).
> Status: **bit-parity proven on the full catalog; serves every production
> simulation when installed** (selected by `motoquant/engine_select.py`,
> decision record [ADR-0007](adr/0007-rust-physics-core.md)).
> `motoquant/physics.py` remains the **reference implementation**. The Rust
> core is an accelerator for the server (via PyO3) and an in-browser engine
> (wasm32) for client-side *full* simulations.

## TL;DR

| | Python reference | Rust native (PyO3) | Rust wasm32 (browser) |
|---|---|---|---|
| Quarter-mile, fixed dt | 430–650 ms/sim | **8.5 ms** (loop) / 13.6 ms end to end (busy host); 5.1 / 8.9 ms on a quiet one | ~5–16 ms/sim under node 22, host-dependent |
| Parity vs Python | — | **bit-identical**: every channel, every step, all 541 catalog bikes (fixed + adaptive + top speed) + 262 stress variants, 1,894/1,894 cases | ET / trap / every split / sample count / loop step count / final dt **identical** on all 53 fixture cases and all 1,082 catalog runs; position, velocity, rpm and temperature channels bit-identical; force-type channels carry 1-ULP noise (see below) |
| Size | — | 0.96 MB abi3 `.so` | **274 KB raw / 94 KB gzip** |

Numbers: `make native-parity` (full sweep, 2026-10-24, host Xeon AVX-512,
Python 3.13, NumPy 2.4.6, rustc 1.97) and `node web/scripts/engine-parity.mjs`
(`make wasm`). The 2026-10-23 sweep is kept as
`reports/native_parity_2026-10-23.json`.

## Architecture: "Python resolves, Rust integrates"

```
BikeConfig ──► MotoQuantEngine(cfg)  ──►  native.resolve_engine(eng)  ──► JSON (schema 2)
 (Python)       _precompute()               every value run() reads,          │
                _init_submodels()           AFTER category dispatch,          ▼
                category profile            env corrections, tire mu    rust/motoquant-core
                env model, parts…           scale, ratios, shift rpms,  Engine::run()  (the loop)
                                            effective-mass terms, …           │
                                                                              ▼
                       SimResult (numpy) ◄── native._to_simresult ◄── channels + splits
                       extract_splits() — Python's own code
```

* **Everything that is policy stays Python:**
  - category dispatch (`category_profiles.py`) and the profile knobs;
  - defaults and parts application;
  - venue and weather handling, `EnvironmentalModel`;
  - `optimal_shift_rpm`.

  A knob or catalog change never needs a Rust change.
* **Only the integrator is ported:**
  - `MotoQuantEngine.run()` itself;
  - the sub-model methods it calls on every step: `EngineModel.torque`,
    `ForcedInductionModel`, `TireModel.friction_coeff/thermal_rate/effective_radius`,
    `AeroModel`, `WeightTransferModel`, `WheelieModel`,
    `RollingResistanceModel`, `ParasiticModel`, `RiderDynamicsModel.cd_a`,
    `RiderParams.cog_offset` and `ChainModel`;
  - the clutch slip, lock and lock-transition logic;
  - the `EngineParams.get_torque` curves, including the curve-less 2-stroke
    and 4-stroke fallbacks;
  - `SimResult.extract_splits`.
* `motoquant.native.NativeEngine` **subclasses** `MotoQuantEngine` and only
  overrides `run()`. `run_top_speed()` / `run_distance()` therefore reuse
  Python's plateau detection and LSR splits verbatim; nothing is duplicated.
  Like Python, `run()` restores `self.m_total` from the config after every
  run, so a reused engine starts its next run from the same mass in both
  implementations.

### Engine selection (production)

`motoquant/engine_select.py` is the only place that decides which integrator
runs. `make_engine(cfg)` returns a `NativeEngine` or a `MotoQuantEngine`, and
`run_quarter(cfg, …)` is a convenience wrapper. `MOTOQUANT_ENGINE` is read on
every call:

| Value | Behaviour |
|---|---|
| `auto` (default) | Native when the extension imports, its schema matches, it is **not stale** (`native.is_stale()`) and `native.host_math()["exact"]` is true. Otherwise Python; `engine_info()["fallback_reason"]` says why |
| `python` | Always the reference engine. The kill switch: no rebuild needed, set it in the host's dashboard |
| `native` | Require the Rust core: `RuntimeError` if it is unavailable or stale |

Wired into every simulation call site of:

- `api.py`: simulate; quick, both the build and its stock baseline; top
  speed; distance; compare; the Dragy overlay;
- the jobs that wrap those routes;
- `llm/agent.py` and `llm/runner.py`;
- `mcp_server.py`.

`tests/test_engine_select.py` pins this through the real routes. Each route
returns identical JSON under `python` and `auto`, and a spy on
`NativeEngine.run` proves that every one of the route's simulations ran on
the Rust core under `auto`.

`GET /api/health` carries `engine` (mode, live engine, native availability,
schema, source fingerprint, staleness, host-math probe). It stays well under
the 1 KB gzip floor, and every probe it runs is cached per process.

### Files

| Path | Role |
|---|---|
| `rust/Cargo.toml` | workspace; `release` (native, LTO) and `wasm-release` (opt-level "s", LTO, strip, panic=abort) profiles |
| `rust/motoquant-core/src/engine.rs` | the run loop + per-step sub-model math; output buffers grow on demand under a `MAX_SAMPLES` cap |
| `rust/motoquant-core/src/config.rs` | the resolved-config schema (serde, `deny_unknown_fields`) |
| `rust/motoquant-core/src/error.rs` | typed errors carrying the Python exception class (`ValueError` / `MemoryError` / `OverflowError` / `ZeroDivisionError`) |
| `rust/motoquant-core/src/fmath.rs` | `pow`/`sin`/`exp` with CPython/NumPy semantics; scalar port of Intel SVML `__svml_exp8_ha` |
| `rust/motoquant-core/src/interp.rs` | `np.interp` / `np.searchsorted` ports (NumPy 2.4.6 `compiled_base.c`, `binsearch.cpp`) |
| `rust/motoquant-core/src/splits.rs` | `SimResult.extract_splits` |
| `rust/motoquant-core/src/lib.rs` | `simulate()`, byte-level API, wasm raw C ABI, PyO3 module (`--features python`) |
| `rust/motoquant-core/build.rs` | stamps `SOURCE_FINGERPRINT` (FNV-1a 64 of `Cargo.toml` + `src/**/*.rs` + `Cargo.lock`) into both builds |
| `rust/motoquant-core/pyproject.toml` | maturin packaging: wheel `motoquant-core`, module `motoquant_core`, abi3-py39, so one wheel serves the 3.11 Docker image and 3.13 dev |
| `rust/motoquant-core/tests/fixtures.rs` | native Rust vs the Python-reference fixtures (no Python needed): splits, sample and step counts, final dt, error classes, the sample cap, the schema-2 mass rule |
| `rust/fixtures/engine_parity.json` | 53 Python-reference cases with a sha256 per output channel and the loop step count: the references, ~3 bikes per category cluster, 2T / limiter / shaft / belt bikes, boosted and stress cases |
| `motoquant/native.py` | `available()`, `resolve_config()`, `run_native()`, `NativeEngine`, `run_top_speed_native()`, `summary_native()`, `host_math()`, `fingerprint_sources()`, `is_stale()` |
| `motoquant/engine_select.py` | `make_engine()`, `run_quarter()`, `native_active()`, `fallback_reason()`, `engine_info()` |
| `scripts/check_native_parity.py` | the full parity sweep + benchmarks → `reports/native_parity_<date>.json` (`--quick` = the CI slice, no report) |
| `scripts/gen_engine_web.py` | builds/copies the wasm; reads its schema + fingerprint **from the binary's own exports**; writes `web/public/engine/engine.json` + the fixtures |
| `web/lib/engine.js` | browser loader: `loadEngine(url)` (cached per URL), `simulate(resolved, {distance, maxTime, adaptive, channels, url})` |
| `web/scripts/engine-parity.mjs` | runs the REAL `engine.js` under node (fetch shim) against the fixtures; fails on ET/trap/split/step/dt/sample drift; self-checks that the loader caches per URL |
| `web/public/engine/motoquant_core.wasm` | the committed browser engine (generated asset, like `web/public/surrogate/*`) |
| `tests/test_native_engine.py` | pytest parity gate (skips without the extension unless `MOTOQUANT_REQUIRE_NATIVE=1`; freshness guards always run) |
| `tests/test_engine_select.py` | selector rules + production-path python-vs-auto parity |
| `.github/workflows/native.yml` | the CI gate (see ADR-0007) |
| `Dockerfile` | stage 1 builds the wheel (`maturin --locked`), stage 2 installs it; `--build-arg MOTOQUANT_NATIVE=0` builds a Python-only image |

## How bit-parity is achieved

IEEE-754 `+ - * /` are deterministic, so parity reduces to two things: (1)
evaluating every expression in Python's order and (2) calling the *same*
transcendental functions. Concretely:

1. **Evaluation order.**
   - `a * b * c` is `(a * b) * c`. Nothing is re-associated, fused (Rust never
     contracts to FMA implicitly) or "simplified".
   - Loop invariants come pre-resolved from Python, using the exact
     expressions `run()` uses. `resolve_engine` even re-checks
     `DrivetrainModel.effective_mass` bit for bit at resolve time.
2. **`x ** 2` is NOT `x * x`.**
   - CPython's `float ** 2` (and NumPy's `float64 ** 2`) call C
     `pow(x, 2.0)`.
   - glibc `pow` is not correctly rounded, and it differs from `x * x` in
     ~0.09 % of inputs (measured).
   - Every `**` in the loop therefore goes through `fmath::pow`.
     `black_box` on the exponent stops LLVM's libcall simplifier from
     rewriting `pow(x, 2.0)` into `x * x`.
3. **`np.exp` is not `math.exp`.** The tire thermal factor uses `np.exp`.
   - On an AVX512_SKX CPU with an SVML-linked NumPy (the PyPI wheels),
     `np.exp` dispatches to Intel SVML `__svml_exp8_ha`. That differs from
     glibc `exp` in ~4.6 % of inputs.
   - `fmath::exp_svml_ha` is an instruction-by-instruction scalar
     transliteration of that routine's main path: table + polynomial + one
     round-toward-zero FMA, emulated exactly.
   - Elsewhere NumPy falls back to the C library `exp`.
   - `native.host_math()` **probes the host at runtime** and puts
     `exp_impl: "svml_ha" | "libm"` into the resolved config, so the native
     engine tracks whatever the local Python reference does.
   - Pinned by 16 captured NumPy bit patterns in `fmath.rs` tests and by
     `test_host_math_is_reproduced`.
4. **NumPy primitives.** These are ported from the NumPy 2.4.6 C sources and
   fuzz-tested against NumPy (`test_np_interp_parity_random`):
   - `np.interp`: binary search with guess, the exact-knot and last-knot
     branches, the slope formula, the NaN fallbacks;
   - `np.searchsorted`: NaN-aware `DOUBLE_LT`.
5. **Python `min`/`max` semantics.** `max(a, b)` returns `a` unless `b > a`.
   This matters for NaN (`max(0.0, nan) == 0.0`, which is why NaN is
   laundered while the clutch slips) and for signed zeros. `py_max`/`py_min`
   replicate it.
6. **JSON transport is exact.** Python writes `repr` round-trip doubles, and
   serde_json runs with `float_roundtrip` (its default parser can be 1 ULP
   off). `test_resolved_config_round_trips_exactly` proves that
   Python → Rust → Python is the identity.
7. **Live config reads.** Python's loop reads the engine's `self.m_total` on
   step 0. From step 1 on it uses the LIVE `cfg.chassis.total_mass_kg - fuel`,
   and it restores `self.m_total` afterwards. Schema 2 carries both
   (`mass.m_total0`, `mass.m_total_cfg`), so a config edited after
   construction (rider mass, dry mass, fuel burn) and a reused engine both
   stay bit-identical. Before schema 2, native silently ignored such edits
   (reproduced 2026-10-24).
8. **Error behaviour.** For the same input, the native path raises the
   exception class Python raises. The output sizing
   `np.zeros(int(max_time / dt) + 1)` is mirrored exactly:

   | Input | Python | Native |
   |---|---|---|
   | `max_time` NaN | `ValueError` | `ValueError` |
   | `max_time` ±inf | `OverflowError` | `OverflowError` |
   | negative array size (e.g. `max_time = -1`) | `ValueError` | `ValueError` |
   | `int(q) + 1 == 0` (e.g. `max_time = -0.0015`) | empty result | empty result |
   | `dt == 0` | `ZeroDivisionError` | `ZeroDivisionError` |
   | zero wheelbase / CoG height | `ZeroDivisionError` on the first step | `ZeroDivisionError` at resolve |
   | **`distance <= 0`** | `UnboundLocalError` (accidental: the loop's locals are never bound) | **`ValueError` with a clear message** (intentional, the one documented difference) |
   | oversized run | `MemoryError` from `np.zeros` | `MemoryError` past `MAX_SAMPLES`, see Limitations |

   The parity sweep treats only the `distance <= 0` pair as equivalent
   (`EXC_EQUIV`). Any other class mismatch fails it.

The per-step work is also *de-duplicated without changing a bit*. In a
traction-limited step, Python recomputes the tire thermal factor,
pressure-grip factor, aero lift and rider CoG offset on every one of up to
three friction / weight-transfer calls, with identical arguments. Rust
evaluates each once per step: same expression, same inputs, same doubles.

## Parity results (2026-10-24, schema 2)

`make native-parity` (= `scripts/check_native_parity.py`, which now defaults
to the full top-speed sweep; `--topspeed-sample N` subsamples it). Each case
runs Python and native in the same worker and compares **every SimResult
channel element by element**: t, x, v, a, rpm, gear, slip, traction %,
N_front, N_rear, F_drive, F_drag, F_rr, T_tire, T_clutch, P_boost, power and
r_eff. It also compares sample counts, the final `dt` and every split.

| Section | Cases | Bit-identical (all channels) | worst \|ΔET\| |
|---|---|---|---|
| references (K5 / R1 / Hayabusa × fixed, adaptive, top speed) | 9 | 9 | 0 |
| catalog — every current `bike_config`, fixed dt, via `db_row_to_config` | 541 | 541 | 0 |
| adaptive dt — every catalog bike | 541 | 541 | 0 |
| top speed (`run_top_speed`, adaptive, plateau + LSR splits) — every catalog bike | 541 | 541 | 0 |
| stress (below) | 262 | 253 (+9 both-raise) | 0 |

The stress variants cover:

- **Forced induction:** turbo (with and without intercooler, near-instant
  spool), Roots and centrifugal superchargers, and N2O with 1–2 stages
  including a 50 ms ramp. Each runs on a litre bike, a sub-200 cc 4T and a
  2-stroke.
- **Clutches:** slider (engage 3,000 / 6,500 rpm), multistage, slipper and
  lockup, including heat fade. A slider that never engages stalls to
  `max_time`, which exercises adaptive array growth.
- **Environment:** all 8 track surfaces plus an unknown string;
  head/tail/cross wind; ram air with and without headwind; ±3 % gradient;
  altitude, heat, humidity and cold; `track_temp_c = None`; VHT / rubber
  prep.
- **Speed limiters:** 140 km/h engaging inside the quarter, 0 = off, and the
  catalog limiter bikes in top-speed mode.
- **Engines:** dyno `is_at_wheel` flipped both ways; the curve-less 4T
  parabolic; every curve-less 2T band (powervalve, 1-cyl < 200 cc, 1-cyl
  250 cc, twin, triple, `tuned_rpm=None`); counter-rotating crank; parasitic
  deltas; coolant below 70 °C and above 100 °C; heavy fuel burn.
- **Rider and chassis:** rider 40 / 150 kg; wheelie bar; belly pan, upright
  and race crouch; chain → shaft; two-step launch; zero tuck time; a
  reversion-prone tire.
- **Category profiles:** every one of the 13 profiles (and `None`) on two
  bikes; patched profile knobs (`launch_rpm_factor`, over-clutch + launch
  floor on a litre bike).
- **Integration settings:** dt 0.5 ms / 2 ms; time caps; 60 ft / 1,000 m
  distances; custom plateau windows.
- **New on 2026-10-24:**
  - configs edited AFTER engine construction (rider +20 kg, dry −15 kg,
    10× fuel burn), on both the first and a second run of the same engine,
    plus top speed;
  - every error path: `distance = 0`, `max_time` −1 / NaN / inf / −0.0015,
    `dt = 0`.

**Target met: worst |ΔET| = 0 s (≤ 1e-9 required) across 1,894 cases.** The 9
non-bit-identical cases are the ones where both engines raise the same
class, so there are no channels to compare. There is no residual to
root-cause on this host.

### wasm32 (browser) parity

`make wasm` → `node web/scripts/engine-parity.mjs` runs the real `engine.js`
against the committed 53-case fixture. `scripts/gen_engine_web.py
--full-catalog PATH` writes an every-bike fixture (fixed + adaptive, 1,082
runs) for the same harness. The harness **fails** on any of these:

- ET, trap or split drift beyond 1e-9 s;
- a different sample count, loop step count, final `dt` or `finished` flag;
- a fixture / engine schema mismatch.

Results:

* ET, trap speed, **every split**, `finished`, sample count, loop step count
  and final `dt` are **identical** on all 53 fixture cases, and on all 1,082
  catalog runs (re-checked 2026-10-24 with the schema-2 wasm; mean 15 ms/sim
  with channels on the busy host).
* The integrated state channels (t, x, v, rpm, gear, T_tire, T_clutch,
  P_boost, r_eff) are bit-identical everywhere.
* The force-type channels (F_drag, F_rr, N_front/N_rear, slip, traction %,
  a, F_drive, power) differ by **1 ULP at a small fraction of steps** (for
  example, 27 of 9,935 F_drag samples on the K5).
  - **Cause.** wasm has no glibc, so Rust's pure-Rust libm (musl/FreeBSD-msun
    lineage) supplies `pow` and `sin`. Its `pow(x, 2.0)` rounds differently
    from glibc's in rare cases.
  - **Why the times don't move.** The integrator absorbs these 1-ULP force
    differences. They enter `v` through `dt/6·(k1 + 2k2 + 2k3 + k4)`, scaled
    by ~1.7e-4 relative to `v` itself — far below one ULP of `v`. The
    trajectory, and every reported time, is unchanged.
  - **Residual risk.** A discrete event (a gear-shift threshold, clutch lock)
    could in principle amplify a 1-ULP state difference. None occurred on the
    catalog, and the step-count / dt checks would catch one.
* The SVML `exp` emulation is pure Rust (`f64::mul_add` → correctly rounded
  software FMA on wasm), so it is bit-exact in the browser too.

## Performance

Serial, single core, best-of-3. These come from the `bench` section of the
2026-10-24 sweep, over 23 bikes (the 3 references + 20 catalog picks). The
shared host was busy that day; the 2026-10-23 numbers (quieter host) are in
brackets.

| Mode | Python | native end to end (resolve + run + numpy) | native loop only | speed-up |
|---|---|---|---|---|
| fixed dt (≈12.6k steps) | 652 ms [429] | 13.6 ms [8.9] | 8.5 ms [5.1] | 48× / 77× [48× / 83×] |
| adaptive dt (≈8.0k steps) | 463 ms [324] | 10.1 ms [6.2] | 6.0 ms [3.6] | 46× / 77× [52× / 91×] |
| resolve only | — | 1.9 ms [0.8] | — | — |

wasm32 under node 22 (V8): 5.2 ms/sim summary-only and 6.5 ms with all 18
channels decoded on the quiet host; 16 ms with channels on the busy one.

Opt-level sweep for the wasm profile (2026-10-23):

| Opt level | Raw | gzip | Time/sim |
|---|---|---|---|
| `z` | 246 KB | 89 KB | 11.4 ms |
| **`s` (chosen)** | 270 KB (now 274 KB with the fingerprint exports) | 93 KB | 5.2 ms |
| `3` | 291 KB | 108 KB | 10.5 ms |

About 40 % of the wasm per-step cost is the SVML-exact `exp` (13 software
FMAs). `exp_impl: "libm"` runs ~2× faster, but it no longer matches an
AVX-512 NumPy host bit for bit.

## Build & use

```bash
make native               # maturin build --release --locked (abi3 wheel) + pip install
make native-test          # cargo test + pytest gate; FAILS if the build is missing/stale
make native-parity        # FULL sweep (1,894 cases, ~10 min on 4 cores) → reports/native_parity_<date>.json
make native-parity-quick  # CI slice (refs + 40 bikes + stress slice), no report
make wasm                 # cargo build wasm32 + copy + manifest + fixtures + node parity
```

```python
from motoquant import engine_select, native

eng = engine_select.make_engine(cfg)   # NativeEngine or MotoQuantEngine (MOTOQUANT_ENGINE)
r = eng.run()                          # SimResult — identical either way
engine_select.engine_info()            # what /api/health reports

if native.available():
    r = native.run_native(cfg)          # SimResult, identical to MotoQuantEngine(cfg).run()
    ts = native.run_top_speed_native(cfg)  # TopSpeedResult via Python's own post-processing
    s = native.summary_native(cfg)      # splits only, no channel arrays (fastest)
    native.native_info()                # version, schema, fingerprint, stale, exp_impl, exact
```

```js
import { loadEngine, simulate } from '@/lib/engine';
await loadEngine();                            // fetches /engine/motoquant_core.wasm once (cached per URL)
const r = await simulate(resolvedConfig, { adaptive: false });
r.et; r.trapKmh; r.splits; r.channels.v; r.gear;
// errors: err.kind ∈ 'value' | 'memory' | 'overflow' | 'zero_division'
```

**Docker.** The `Dockerfile` builds the wheel in a `python:3.11-slim-bookworm`
builder: rustup minimal, toolchain 1.97.0, `maturin build --locked`. The
runtime image installs it. Both stages run bookworm, so the manylinux tag
always installs, and the image never uses alpine/musl (parity needs glibc
libm).

- A build-time self-check fails the image if the wheel was requested but
  does not load.
- `--build-arg MOTOQUANT_NATIVE=0` produces a pure-Python image.
- Verified 2026-10-24 by building and booting both variants. `/api/health`
  reports `engine: native` and `engine: python`
  (`fallback_reason: unavailable`) respectively, and K5 = 9.9331 s from both.

The browser needs a *resolved* config. Today the fixtures carry them. The
production path is a server route that returns
`native.resolved_json(native.resolve_config(cfg))` for a bike/venue/parts
selection (≈ 5–9 KB of JSON, cacheable per selection). That route is not
wired yet (see "Next steps").

## The regen contract

The Rust core is a cache of `run()`'s *code*, in the same way the surrogate
is a cache of its *outputs*. It must be kept in lock-step:

| You changed… | You must… | Gate that catches it |
|---|---|---|
| `physics.py` `run()` or any sub-model method it calls | port the same change to `engine.rs` in the same PR, `make native wasm`, `make native-parity` | `test_engine_fixtures_are_fresh` (Python ET vs committed fixture), `tests/test_native_engine.py` bit-identity, `cargo test` fixtures, `native.yml` |
| what `resolve_engine` must serialise (new knob read in the loop, renamed field) | bump `SCHEMA_VERSION` in **both** `native.py` and `config.rs` (and `ENGINE_SCHEMA` in `engine.js`), `make native wasm` | `deny_unknown_fields`, schema check on both sides, the wasm's own `schema_version()` export read by `test_wasm_manifest_matches_binary`, `test_engine_fixtures_are_fresh` (resolve drift) |
| any Rust source, `Cargo.toml` or `Cargo.lock` | `make native-test native-parity wasm` (rebuilds both artefacts) | source fingerprint: `native.is_stale()` (auto refuses a stale extension; `make native-test` / CI fail), `test_wasm_manifest_matches_binary` (committed wasm built from other sources) |
| catalog data, category-profile values, defaults, parts | nothing for parity (resolved at run time); regenerate fixtures with `make wasm` only if a *fixture* bike's ET moved | `test_engine_fixtures_are_fresh` |

A schema mismatch never produces a silently wrong number. The extension
refuses it (`available()` is False on a mismatch), and so does the wasm
loader. A stale extension is refused by `auto`.

Schema history: **1** was the initial schema (2026-10-23). **2** added
`mass.m_total_cfg` (2026-10-24).

## Limitations (honest list)

* **Bit-parity is host-relative.**
  - Python's own results depend on the host's libm and NumPy dispatch
    (glibc `pow`, SVML vs libm `exp`). The native engine calls the same libm
    and probes the NumPy `exp` path, so it matches the *local* Python bit for
    bit. Two different machines can still disagree with *each other* at the
    ULP level.
  - `native_info()["exact"]` reports whether the probe reproduced the host.
    If `exact` is False, `auto` uses Python.
  - One known case: a NumPy build that dispatches `np.exp` to something else
    (e.g. NumPy's AVX512F Tang kernel on a non-SVML build). That path is not
    ported yet; the probe makes it visible.
* **wasm uses Rust's libm**, not glibc. This gives 1-ULP force-channel noise;
  the reported times are identical on the catalog (see above).
* **Output size is capped.** `MAX_SAMPLES` = 4,194,304 stored samples per
  run, about 70 simulated minutes at 1 ms and about 600 MB of channels.
  - Python pre-allocates `np.zeros(int(max_time / dt) + 1)` and raises
    `MemoryError` when that cannot be allocated, which depends on the host.
  - Native allocates lazily (`try_reserve`) and raises `MemoryError` only
    once a run would actually exceed the cap.
  - So `max_time = 1e13` on a bike that finishes in 10 s works natively,
    where Python fails up front.
  - An allocator failure below the cap is also a `MemoryError`, never a
    process abort. Before the cap, a runaway run aborted the interpreter
    (reproduced 2026-10-24).
  - The longest legitimate request (API top speed: 120 s adaptive, ≤ 240 k
    samples) is about 17× below the cap.
* **Non-finite inputs are refused.**
  - The JSON contract is finite doubles. A NaN/inf *config* raises
    `ValueError` on the native path, where Python would propagate it into
    garbage.
  - The NaN/inf *guard* (break + trim) is ported and pinned by a Rust unit
    test, but finite inputs cannot reach it.
  - Non-finite `max_time` / `distance` *arguments* behave like Python (see
    the error table).
* **`progress_cb`** is honoured coarsely: 0.0 at the start, 1.0 at the end.
  A native sim takes milliseconds, so there is nothing to report in between.
  Cooperative job cancellation (`jobs.JobCancelled`) therefore takes effect
  at the end of the sim.
* **Python-float exceptions in degenerate configs** (`OverflowError` from
  `float ** 2`, `ZeroDivisionError` mid-loop) become IEEE inf/NaN in Rust.
  Only the two divisors that are config constants (wheelbase, CoG height)
  are pre-checked.
* **Not ported:** `pacejka_force`, `BrakingModel`, `ClutchModel.torque` and
  `StagingModel.total_dead_time_s`. `run()` does not call them.

## Decision record

[ADR-0007](adr/0007-rust-physics-core.md) (accepted 2026-10-24). It
supersedes ADR-0003 in part and replaces CLIENT_COMPUTE's Pyodide plan. It
also records the evidence and the dual-implementation discipline (the CI
gate, the schema version, the source fingerprint, fixture freshness and the
exception-class mirroring).

## Next steps (not done here)

1. **Remaining Python-only call sites.** Any code that still constructs
   `MotoQuantEngine(...)` directly bypasses the selector and always runs the
   slow Python loop. `grep -rn "MotoQuantEngine(" motoquant/` lists them; the
   only intended ones are `physics.py`, `native.py` and `engine_select.py`.
   On 2026-10-24 the analysis layer and `nlp.py` were being switched over;
   the CLI (`run.py`), `calibration/calibrator.py`, `llm/estimator.py` and the
   `motoquant/__init__.py` quick-run helper were not yet. Switching them is
   mechanical (`engine_select.make_engine(cfg)`).
2. **Resolved-config route** (`GET /api/resolve?bike_id=&venue_id=&parts=`),
   so the simulator page can run exact full sims client-side with
   `web/lib/engine.js`, labelled "exact — computed on your device". Keep
   leaderboard saves server-authoritative (recompute on save).
3. **Sweeps and surrogate data generation** through `summary_native` +
   `multiprocessing`: ~50–80× fewer CPU-seconds for `phys_weighted_sweep`,
   `tune_cluster_knobs` and surrogate regeneration. The accuracy epoch
   depends on this.
4. Optional: port NumPy's AVX512F Tang `exp` as a third `exp_impl` for
   non-SVML NumPy builds.
