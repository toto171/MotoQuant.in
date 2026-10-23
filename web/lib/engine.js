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
 * simulate(ptr,len)->resultPtr, schema_version(). The result buffer is
 *   u32 total | u32 headerLen | u32 n | u32 nFloat | header JSON | pad8 |
 *   nFloat×n f64 (channel-major) | n f64 gear
 *
 * Usage:
 *   import { simulate } from '@/lib/engine';
 *   const r = await simulate(resolvedConfig, { adaptive: false });
 *   r.et, r.trap, r.splits, r.channels.v, r.gear
 */

export const ENGINE_SCHEMA = 1;
const DEFAULT_URL = '/engine/motoquant_core.wasm';

let _engine = null; // { exports, url }
let _loading = null;

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

/** Fetch + instantiate the wasm once (concurrent callers share the promise). */
export function loadEngine(url = DEFAULT_URL) {
  if (_engine && _engine.url === url) return Promise.resolve(_engine);
  if (!_loading) {
    _loading = instantiate(url)
      .then((e) => {
        _engine = e;
        return e;
      })
      .finally(() => {
        _loading = null;
      });
  }
  return _loading;
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
 * @param {object} resolvedConfig  motoquant/native.py resolve_config() output (schema 1)
 * @param {object} [opts]
 * @param {number} [opts.distance=402.336]  metres
 * @param {number} [opts.maxTime=26]        seconds
 * @param {boolean} [opts.adaptive=false]   adaptive-dt integration
 * @param {boolean} [opts.channels=true]    return per-step channels (else splits only)
 * @returns {Promise<{et:number, trap:number, trapKmh:number, finished:boolean,
 *   splits:object, dt:number, steps:number, n:number, nanBreak:boolean,
 *   channels:object|null, gear:Float64Array|null, elapsedMs:number}>}
 */
export async function simulate(resolvedConfig, opts = {}) {
  const { exports } = await loadEngine(opts.url);
  return simulateSync(exports, resolvedConfig, opts);
}

function simulateSync(exports, resolvedConfig, opts) {
  const req = JSON.stringify({
    config: resolvedConfig,
    distance: opts.distance ?? 402.336,
    max_time: opts.maxTime ?? 26.0,
    adaptive: !!opts.adaptive,
    channels: opts.channels ?? true,
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
  if (!header.ok) throw new Error(`engine: ${header.error}`);
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

/** Synchronous variant for callers that already awaited loadEngine(). */
export function simulateLoaded(resolvedConfig, opts = {}) {
  if (!_engine) throw new Error('engine: call loadEngine() first');
  return simulateSync(_engine.exports, resolvedConfig, opts);
}
