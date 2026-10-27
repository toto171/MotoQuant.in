/**
 * In-browser MotoQuant physics engine — the Rust core compiled to wasm32.
 *
 * This runs the FULL quarter-mile simulation (the same RK4 loop as
 * motoquant/physics.py, transliterated float-op for float-op in
 * rust/motoquant-core) entirely client-side. It consumes a *resolved* config:
 * the plain-JSON dict produced by motoquant/native.py::resolve_config, where
 * Python has already applied category profiles, environment corrections,
 * tire grip scaling, gear ratios, shift points, etc. ("Python resolves,
 * Rust integrates" — see docs/RUST_CORE.md).
 *
 * Parity: web/scripts/engine-parity.mjs runs THIS module under node against
 * Python-reference fixtures (rust/fixtures/engine_parity.json). The wasm build
 * uses Rust's pure-Rust libm for pow/sin/exp instead of glibc, so results may
 * carry ULP-level drift from the server's numbers; the harness measures it.
 *
 * ABI (raw C, no wasm-bindgen): alloc(len)->ptr, dealloc(ptr,len),
 * simulate(ptr,len)->resultPtr, schema_version(), source_fingerprint_hi/lo().
 * The result buffer is
 *   u32 total | u32 headerLen | u32 n | u32 nFloat | header JSON | pad8 |
 *   nFloat×n f64 (channel-major) | n f64 gear
 *
 * Usage:
 *   import { simulate } from '@/lib/engine';
 *   const r = await simulate(resolvedConfig, { adaptive: false });
 *   r.et, r.trap, r.splits, r.channels.v, r.gear
 *
 * Timing (schema 3, 2026-10 physics epoch): channels are integrated from rest
 * (t = 0, x = 0); splits/ET/trap are timed from the start beam after
 * `rolloutM` (default 1 ft) of travel, exactly like MotoQuantEngine.run().
 *
 * Errors: a failed simulation throws an Error whose `.kind` mirrors the
 * Python exception class the reference engine raises ('value' | 'memory' |
 * 'overflow' | 'zero_division').
 */

export const ENGINE_SCHEMA = 3;
/** 1 ft — the drag-strip rollout every published ET uses (2026-10 epoch). */
export const ROLLOUT_M = 0.3048;
const DEFAULT_URL = '/engine/motoquant_core.wasm';

// One cache entry per wasm URL: url -> Promise<{ exports, url }>. Keyed by
// URL so two different engines (e.g. a preview build next to the default)
// never share an instance; a failed load is evicted so the next call retries.
const _engines = new Map();
const _loaded = new Map(); // url -> resolved { exports, url } (for simulateLoaded)

async function instantiate(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`engine: fetch ${url} failed (${resp.status})`);
  let result;
  const ct = resp.headers && typeof resp.headers.get === 'function' ? resp.headers.get('content-type') : null;
  if (typeof WebAssembly.instantiateStreaming === 'function' && ct && ct.includes('application/wasm')) {
    result = await WebAssembly.instantiateStreaming(resp, {});
  } else {
    const bytes = await resp.arrayBuffer();
    result = await WebAssembly.instantiate(bytes, {});
  }
  const exports = result.instance.exports;
  const schema = exports.schema_version();
  if (schema !== ENGINE_SCHEMA) {
    throw new Error(`engine: wasm schema ${schema} != engine.js schema ${ENGINE_SCHEMA} — rebuild with \`make wasm\``);
  }
  return { exports, url };
}

/**
 * Fetch + instantiate the wasm at `url` once. Concurrent callers for the SAME
 * url share one promise; different urls get different engines.
 */
export function loadEngine(url = DEFAULT_URL) {
  let p = _engines.get(url);
  if (!p) {
    p = instantiate(url).then(
      (e) => {
        _loaded.set(url, e);
        return e;
      },
      (err) => {
        _engines.delete(url);
        throw err;
      },
    );
    _engines.set(url, p);
  }
  return p;
}

/** Warm the engine without running anything (e.g. on simulator mount). */
export function preloadEngine(url) {
  return loadEngine(url).then(
    () => true,
    () => false,
  );
}

const CHANNEL_KEYS = {
  t: 't', x: 'x', v: 'v', a: 'a', rpm: 'rpm', slip: 'slip', traction_pct: 'tractionPct',
  N_front: 'nFront', N_rear: 'nRear', F_drive: 'fDrive', F_drag: 'fDrag', F_rr: 'fRr',
  T_tire: 'tTire', T_clutch: 'tClutch', P_boost: 'pBoost', power_kw: 'powerKw', r_eff: 'rEff',
};

function decodeResult(exports, ptr) {
  const mem = exports.memory.buffer;
  const dv = new DataView(mem, ptr, 16);
  const total = dv.getUint32(0, true);
  const headerLen = dv.getUint32(4, true);
  const n = dv.getUint32(8, true);
  const nFloat = dv.getUint32(12, true);
  const header = JSON.parse(new TextDecoder().decode(new Uint8Array(mem, ptr + 16, headerLen)));
  let channels = null;
  let gear = null;
  if (header.ok && nFloat > 0) {
    const pre = 16 + headerLen;
    const start = ptr + pre + ((8 - (pre % 8)) % 8);
    // slice() copies into a fresh, 8-aligned ArrayBuffer that survives dealloc
    // and memory growth.
    const body = new Float64Array(mem.slice(start, start + 8 * n * (nFloat + (header.gear ? 1 : 0))));
    channels = {};
    header.channels.forEach((name, i) => {
      channels[CHANNEL_KEYS[name] || name] = body.subarray(i * n, (i + 1) * n);
    });
    if (header.gear) gear = body.subarray(nFloat * n, (nFloat + 1) * n);
  }
  return { total, header, channels, gear, n };
}

/**
 * Run one simulation.
 *
 * @param {object} resolvedConfig  motoquant/native.py resolve_config() output (schema 3)
 * @param {object} [opts]
 * @param {number} [opts.distance=402.336]  metres
 * @param {number} [opts.maxTime=26]        seconds
 * @param {boolean} [opts.adaptive=false]   adaptive-dt integration
 * @param {boolean} [opts.channels=true]    return per-step channels (else splits only)
 * @param {number}  [opts.rolloutM=0.3048]  drag-strip rollout (m): splits are timed from the
 *                                          start beam, t(x = rollout + d) - t(x = rollout);
 *                                          0 = from first motion (motoquant/constants.py ROLLOUT_M)
 * @param {string}  [opts.url]              wasm URL (default /engine/motoquant_core.wasm)
 * @returns {Promise<{et:number, trap:number, trapKmh:number, finished:boolean,
 *   splits:object, dt:number, steps:number, n:number, nanBreak:boolean,
 *   channels:object|null, gear:Float64Array|null, elapsedMs:number}>}
 */
export async function simulate(resolvedConfig, opts = {}) {
  const { exports } = await loadEngine(opts.url ?? DEFAULT_URL);
  return simulateSync(exports, resolvedConfig, opts);
}

function simulateSync(exports, resolvedConfig, opts) {
  const req = JSON.stringify({
    config: resolvedConfig,
    distance: opts.distance ?? 402.336,
    max_time: opts.maxTime ?? 26.0,
    adaptive: !!opts.adaptive,
    channels: opts.channels ?? true,
    rollout_m: opts.rolloutM ?? ROLLOUT_M,
  });
  const bytes = new TextEncoder().encode(req);
  const t0 = typeof performance !== 'undefined' ? performance.now() : Date.now();
  const inPtr = exports.alloc(bytes.length);
  new Uint8Array(exports.memory.buffer, inPtr, bytes.length).set(bytes);
  let resPtr = 0;
  try {
    resPtr = exports.simulate(inPtr, bytes.length);
  } finally {
    exports.dealloc(inPtr, bytes.length);
  }
  const { total, header, channels, gear, n } = decodeResult(exports, resPtr);
  exports.dealloc(resPtr, total);
  const t1 = typeof performance !== 'undefined' ? performance.now() : Date.now();
  if (!header.ok) {
    const err = new Error(`engine: ${header.error}`);
    err.kind = header.kind || 'value';
    throw err;
  }
  const s = header.splits;
  return {
    et: s.time_quarter,
    trap: s.speed_quarter,
    trapKmh: s.speed_quarter * 3.6,
    finished: s.finished_quarter,
    splits: s,
    dt: header.dt,
    steps: header.steps,
    n,
    nanBreak: header.nan_break,
    channels,
    gear,
    elapsedMs: t1 - t0,
  };
}

/** Synchronous variant for callers that already awaited loadEngine(opts.url). */
export function simulateLoaded(resolvedConfig, opts = {}) {
  const e = _loaded.get(opts.url ?? DEFAULT_URL);
  if (!e) throw new Error('engine: call loadEngine() first');
  return simulateSync(e.exports, resolvedConfig, opts);
}
