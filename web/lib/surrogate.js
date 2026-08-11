/**
 * MotoQuant in-browser surrogate — instant client-side quick-sim estimates.
 * =========================================================================
 * Runs the SAME ReLU MLP the backend serves from /api (26 → 128 → 64 → 2,
 * see motoquant/analysis/surrogate_numpy.py), against per-bike feature
 * bundles exported by scripts/gen_surrogate_web.py. Every slider drag is
 * answered locally in ~0.01 ms with zero server involvement; the server's
 * full RK4 sim remains the authoritative number (and the only source of
 * splits/timeseries), one explicit click away.
 *
 * EXACTNESS CONTRACT (mirrors the Python inference pipeline exactly):
 *   1. compute base features in float64  (surrogate_data._extract_nominal_features)
 *   2. derive the 7 gear/power features  (_compute_derived_features — ported below)
 *   3. cast the assembled 26-vector to float32  (config_to_feature_vector) → Math.fround
 *   4. run the MLP in float64            (NumpySurrogate.predict)
 * Parity with the Python path is pinned to <1e-9 s by
 * web/scripts/surrogate-parity.mjs + tests/test_surrogate_web_export.py.
 *
 * HONESTY CONTRACT: this is the surrogate, not the physics. It is a cache of
 * the RK4 engine (~0.11 s catalog ET MAE, see artifacts/surrogate/README.md);
 * it is blind to parts, tire swaps, and weather (only altitude). Callers MUST
 * label results as estimates and fall back to the server when
 * `predictQuick` returns { ok: false } — it refuses rather than guessing:
 *   - parts or tire overrides selected        → reason 'unsupported-overrides'
 *   - any feature outside the training envelope → reason 'envelope'
 *   - assets unavailable / bike unknown        → reason 'unavailable'
 */

const ASSET_BASE = '/surrogate';

// Features surrogate.js recomputes from slider state; everything else comes
// verbatim from the per-bike bundle. Keep in sync with gen_surrogate_web.py.
const DERIVED = [
  'power_to_weight_hp_kg', 'effective_1st_ratio', 'effective_top_ratio',
  'gear_ratio_2nd', 'gear_ratio_3rd', 'gear_ratio_4th', 'gear_ratio_5th',
];

function decodeF32(b64) {
  const raw = atob(b64);
  const buf = new ArrayBuffer(raw.length);
  const view = new Uint8Array(buf);
  for (let i = 0; i < raw.length; i++) view[i] = raw.charCodeAt(i);
  return new Float32Array(buf); // little-endian, matching the export
}

let _assets = null; // resolved {model, bikes} or null after a failed load
let _loading = null; // in-flight promise so concurrent callers share one fetch

async function loadAssets() {
  if (_assets) return _assets;
  if (_loading) return _loading;
  _loading = (async () => {
    try {
      const [mRes, bRes] = await Promise.all([
        fetch(`${ASSET_BASE}/model.json`),
        fetch(`${ASSET_BASE}/bikes.json`),
      ]);
      if (!mRes.ok || !bRes.ok) return null;
      const [model, bikes] = await Promise.all([mRes.json(), bRes.json()]);
      if (model.format !== 'motoquant-surrogate-web/1') return null;
      // A mismatched pair (one file regenerated without the other) would
      // silently misapply features — refuse instead.
      if (model.npz_sha256 !== bikes.npz_sha256) {
        console.warn('surrogate: model/bikes fingerprint mismatch — falling back to server');
        return null;
      }
      const layers = model.layers.map((l) => ({
        shape: l.shape,
        W: decodeF32(l.W),
        b: decodeF32(l.b),
      }));
      _assets = {
        featureNames: model.feature_names,
        featMean: decodeF32(model.feat_mean),
        featStd: decodeF32(model.feat_std),
        tgtMean: decodeF32(model.tgt_mean),
        tgtStd: decodeF32(model.tgt_std),
        envMin: decodeF32(model.env_min),
        envMax: decodeF32(model.env_max),
        layers,
        meta: model.meta_json ? JSON.parse(model.meta_json) : null,
        bikes: bikes.bikes,
        venues: bikes.venues,
      };
      return _assets;
    } catch (e) {
      console.warn('surrogate: asset load failed — falling back to server', e);
      return null;
    } finally {
      _loading = null;
    }
  })();
  return _loading;
}

/** Warm the asset cache (call on mount; safe to call repeatedly). */
export function preloadSurrogate() {
  loadAssets();
}

// Exact port of surrogate_data._compute_derived_features (float64 throughout).
function computeDerived(base) {
  const pw = base.peak_power_hp / Math.max(base.total_mass_kg, 1.0);
  const g1 = base.gear_ratio_1st;
  let gt = base.gear_ratio_top;
  if (gt >= g1) gt = g1 * 0.70;
  const eff1 = base.primary_ratio * base.final_drive_ratio * g1;
  const efft = base.primary_ratio * base.final_drive_ratio * gt;
  const n = 6;
  const gears = [];
  for (let k = 1; k <= n; k++) gears.push(gt + (g1 - gt) * (n - k) / (n - 1));
  return {
    power_to_weight_hp_kg: pw,
    effective_1st_ratio: eff1,
    effective_top_ratio: efft,
    gear_ratio_2nd: gears[1],
    gear_ratio_3rd: gears[2],
    gear_ratio_4th: gears[3],
    gear_ratio_5th: gears[4],
  };
}

// MLP forward pass in float64 — mirrors NumpySurrogate.predict for one row.
function forward(assets, x26) {
  const { featMean, featStd, tgtMean, tgtStd, layers } = assets;
  let a = new Float64Array(x26.length);
  for (let i = 0; i < a.length; i++) a[i] = (x26[i] - featMean[i]) / featStd[i];
  for (let li = 0; li < layers.length; li++) {
    const { shape, W, b } = layers[li];
    const [nin, nout] = shape;
    const out = new Float64Array(nout);
    for (let j = 0; j < nout; j++) {
      let s = 0.0;
      for (let k = 0; k < nin; k++) s += a[k] * W[k * nout + j];
      s += b[j];
      out[j] = li < layers.length - 1 ? Math.max(0.0, s) : s;
    }
    a = out;
  }
  return {
    etS: a[0] * tgtStd[0] + tgtMean[0],
    trapMps: a[1] * tgtStd[1] + tgtMean[1],
  };
}

/**
 * Instant client-side quick-sim estimate.
 *
 * @param {object} opts
 * @param {number} opts.bikeId          bike_models.id (catalog bikes only)
 * @param {number} [opts.riderMassKg=75]
 * @param {number} [opts.powerBoostPct=0]
 * @param {number} [opts.massDeltaKg=0]
 * @param {number|null} [opts.venueId]  overrides altitude when set
 * @param {boolean} [opts.hasParts]     any part/tire override selected → refuse
 * @returns {Promise<{ok:true, etS:number, trapKmh:number, source:'surrogate'}
 *                  |{ok:false, reason:'unsupported-overrides'|'envelope'|'unavailable'}>}
 */
export async function predictQuick({
  bikeId,
  riderMassKg = 75,
  powerBoostPct = 0,
  massDeltaKg = 0,
  venueId = null,
  hasParts = false,
}) {
  if (hasParts) return { ok: false, reason: 'unsupported-overrides' };
  const assets = await loadAssets();
  if (!assets) return { ok: false, reason: 'unavailable' };
  const bike = assets.bikes[String(bikeId)];
  if (!bike) return { ok: false, reason: 'unavailable' };

  // Slider transforms — same order and arithmetic as api._build_config.
  const scale = 1.0 + powerBoostPct / 100.0;
  const base = { ...bike.f };
  base.peak_power_hp = bike.f.peak_power_hp * scale;
  base.peak_torque_nm = bike.f.peak_torque_nm * scale;
  base.total_mass_kg = bike.dry_mass_kg + massDeltaKg + riderMassKg;
  if (venueId != null && assets.venues[String(venueId)] != null) {
    base.altitude_m = assets.venues[String(venueId)];
  }

  const feat = { ...base, ...computeDerived(base) };
  const x = new Float64Array(assets.featureNames.length);
  const violations = [];
  for (let i = 0; i < assets.featureNames.length; i++) {
    const name = assets.featureNames[i];
    if (!(name in feat)) return { ok: false, reason: 'unavailable' };
    x[i] = Math.fround(feat[name]); // the float32 cast in config_to_feature_vector
    if (x[i] < assets.envMin[i] || x[i] > assets.envMax[i]) violations.push(name);
  }
  if (violations.length) return { ok: false, reason: 'envelope', violations };

  const { etS, trapMps } = forward(assets, x);
  return {
    ok: true,
    etS,
    trapKmh: trapMps * 3.6,
    // Echo the derived scalars the UI tiles show, so an estimate renders the
    // same power/mass the exact run would (both are inputs, not predictions).
    peakPowerHp: base.peak_power_hp,
    totalMassKg: base.total_mass_kg,
    source: 'surrogate',
  };
}

/** Model metadata (holdout MAE etc.) for honest UI labeling; null until loaded. */
export function surrogateMeta() {
  return _assets ? _assets.meta : null;
}
