/**
 * Saved runs and timeslip links.
 *
 * MotoQuant has no accounts. A saved run is kept in this browser only
 * (localStorage), and a timeslip link carries the whole setup in its query
 * string: bike, upgrades, tyres and the exact conditions as numbers. The
 * timeslip page sends that setup to the simulator and shows what comes back,
 * so a shared time is always one the physics produced, never a number someone
 * typed, and opening an old link re-runs it with the current version.
 */

const STORE_KEY = 'mq.runs.v1';
const CHANGE_EVENT = 'mq-runs-changed';
export const MAX_SAVED_RUNS = 100;

// Query-string keys of a timeslip link, the API field each one feeds, and the
// range the API accepts. Anything outside a range is dropped, not clamped.
const NUMBER_FIELDS = [
  ['rider', 'rider_mass_kg', 20, 250],
  ['boost', 'power_boost_pct', -50, 200],
  ['mass', 'mass_delta_kg', -100, 200],
  ['alt', 'altitude_m', -500, 8000],
  ['temp', 'ambient_temp_c', -30, 60],
  ['track', 'track_temp_c', -30, 80],
  ['hum', 'humidity_pct', 0, 100],
  ['pres', 'pressure_hpa', 800, 1100],
  ['wind', 'headwind_kmh', -200, 200],
];
const ID_FIELDS = [
  ['bike', 'bike_id'],
  ['venue', 'venue_id'],
  ['ft', 'front_tire_id'],
  ['rt', 'rear_tire_id'],
];
const MAX_PARTS = 30;

function positiveInt(raw) {
  if (raw == null || !/^\d{1,9}$/.test(String(raw))) return null;
  const n = Number(raw);
  return n >= 1 ? n : null;
}

function finiteNumber(raw) {
  if (raw == null || raw === '') return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

/**
 * Build a timeslip query string from a finished result.
 *
 * @param {object} setup
 *   bikeId, venueId?, riderKg, powerBoost, massChange, partIds[],
 *   frontTireId?, rearTireId?, environment (the API's echo of the conditions
 *   it simulated: altitude_m, ambient_temp_c, track_temp_c, humidity_pct,
 *   pressure_hpa, headwind_kmh).
 */
export function timeslipQuery(setup) {
  const p = new URLSearchParams();
  if (setup.bikeId != null) p.set('bike', String(setup.bikeId));
  if (setup.venueId != null) p.set('venue', String(setup.venueId));
  if (setup.riderKg != null) p.set('rider', String(setup.riderKg));
  if (setup.powerBoost) p.set('boost', String(setup.powerBoost));
  if (setup.massChange) p.set('mass', String(setup.massChange));
  const parts = (setup.partIds || []).filter((id) => positiveInt(id) != null);
  if (parts.length) p.set('parts', parts.join(','));
  if (setup.frontTireId != null) p.set('ft', String(setup.frontTireId));
  if (setup.rearTireId != null) p.set('rt', String(setup.rearTireId));
  const env = setup.environment || {};
  // Full precision: String(number) round-trips exactly, so the re-run sees
  // the very conditions the saved run used (rounding moved times by 0.1 ms).
  if (Number.isFinite(env.altitude_m)) p.set('alt', String(env.altitude_m));
  if (Number.isFinite(env.ambient_temp_c)) p.set('temp', String(env.ambient_temp_c));
  if (Number.isFinite(env.track_temp_c)) p.set('track', String(env.track_temp_c));
  if (Number.isFinite(env.humidity_pct)) p.set('hum', String(env.humidity_pct));
  if (Number.isFinite(env.pressure_hpa)) p.set('pres', String(env.pressure_hpa));
  if (Number.isFinite(env.headwind_kmh) && env.headwind_kmh !== 0) {
    p.set('wind', String(env.headwind_kmh));
  }
  return p.toString();
}

/**
 * Turn a timeslip query into a /api/simulate/quick request body.
 * Returns null when the link names no valid bike.
 */
export function timeslipRequest(searchParams) {
  const get = (k) => searchParams.get(k);
  const body = {};
  for (const [key, field] of ID_FIELDS) {
    const v = positiveInt(get(key));
    if (v != null) body[field] = v;
  }
  if (body.bike_id == null) return null;
  for (const [key, field, lo, hi] of NUMBER_FIELDS) {
    const v = finiteNumber(get(key));
    if (v != null && v >= lo && v <= hi) body[field] = v;
  }
  const parts = (get('parts') || '')
    .split(',')
    .map(positiveInt)
    .filter((v) => v != null);
  if (parts.length) body.part_ids = [...new Set(parts)].slice(0, MAX_PARTS);
  return body;
}

// ── Saved runs (this browser only) ──────────────────────────────────────────

function readStore() {
  try {
    const raw = window.localStorage.getItem(STORE_KEY);
    const list = raw ? JSON.parse(raw) : [];
    return Array.isArray(list) ? list.filter((r) => r && typeof r.query === 'string') : [];
  } catch {
    return [];
  }
}

function writeStore(list) {
  try {
    window.localStorage.setItem(STORE_KEY, JSON.stringify(list));
    window.dispatchEvent(new Event(CHANGE_EVENT));
    return true;
  } catch {
    return false; // private mode or storage full: saving is best-effort
  }
}

/** Saved runs, newest first. */
export function listRuns() {
  if (typeof window === 'undefined') return [];
  return readStore();
}

/**
 * Save a run. ``run`` holds what the list shows (bikeName, et, trap, et60,
 * eighth, conditions, changes) plus the timeslip ``query``. Saving the same
 * setup again replaces the older entry. Returns the stored run, or null when
 * the browser refused to store it.
 */
export function saveRun(run) {
  const id =
    typeof crypto !== 'undefined' && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const entry = { ...run, id, savedAt: new Date().toISOString() };
  const list = [entry, ...readStore().filter((r) => r.query !== run.query)];
  return writeStore(list.slice(0, MAX_SAVED_RUNS)) ? entry : null;
}

export function deleteRun(id) {
  writeStore(readStore().filter((r) => r.id !== id));
}

export function clearRuns() {
  writeStore([]);
}

/** Call ``fn`` whenever saved runs change (in this tab or another). */
export function onRunsChange(fn) {
  const onStorage = (e) => {
    if (e.key === STORE_KEY) fn();
  };
  window.addEventListener(CHANGE_EVENT, fn);
  window.addEventListener('storage', onStorage);
  return () => {
    window.removeEventListener(CHANGE_EVENT, fn);
    window.removeEventListener('storage', onStorage);
  };
}
