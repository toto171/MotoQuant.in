/**
 * Shared constants + pure helpers for the /simulator page (CLARITY v6).
 * No React in here — everything is trivially testable and tree-shakeable.
 */

// ── Defaults (the values the sliders start at; also the "not custom" test) ──
export const DEFAULTS = {
  riderKg: 75,
  powerBoost: 0,
  massChange: 0,
  ambientTemp: 25,
  trackTemp: 30,
  humidity: 40,
  headwind: 0,
};

// The server simulates at Aamby Valley's altitude whenever no venue is sent.
export const DEFAULT_PLACE = { name: 'Aamby Valley', altitudeM: 679 };

export const MODE_KEY = 'mq-sim-mode';

// ── GROWTH_EXP_003: default-bike A/B test (kept verbatim) ───────────────────
// A (control / SEO-stable) = Hayabusa. B (variant) = Pulsar NS 200.
const EXP003_DEFAULT_BIKE_PATTERNS = {
  A: [/hayabusa/i],
  B: [/pulsar\s*ns\s*200/i, /pulsar ns 200/i],
};

export function pickDefaultBikeForVariant(bikes, variant) {
  if (!bikes || bikes.length === 0) return null;
  const patterns = EXP003_DEFAULT_BIKE_PATTERNS[variant] || EXP003_DEFAULT_BIKE_PATTERNS.A;
  for (const re of patterns) {
    const match = bikes.find((b) => re.test(`${b.manufacturer || ''} ${b.model || b.model_name || ''}`));
    if (match) return match;
  }
  return bikes[0];
}

// One-tap starting points — the bikes the Indian drag scene actually asks for.
export const POPULAR_BIKE_PATTERNS = [
  { label: 'Hayabusa', re: /hayabusa/i },
  { label: 'R15 V4', re: /yzf[- ]?r15 v4/i },
  { label: 'Duke 390', re: /\bduke 390/i },
  { label: 'Classic 350', re: /classic 350/i },
  { label: 'ZX-10R', re: /zx[- ]?10r/i },
  { label: 'GSX-R1000', re: /gsx[- ]?r ?1000/i },
];

// ── Part exclusivity: one part per slot (mirrors analysis/roi.py) ───────────
const EXCLUSIVE_CATEGORIES = new Set([
  'exhaust', 'ecu', 'clutch_kit', 'air_filter', 'quickshifter', 'battery', 'chain',
  'boost_kit', 'nitrous', 'wheelie_bar', 'swingarm_ext', 'lowering_kit', 'air_shifter',
  'lockup_clutch',
]);
const EXCLUSIVE_ALIASES = { lockup_clutch: 'clutch_kit', air_shifter: 'quickshifter' };

/** Exclusivity group for a category name, or null when parts can be stacked. */
export function exclusiveGroup(categoryName) {
  const n = (categoryName || '').toLowerCase();
  if (!EXCLUSIVE_CATEGORIES.has(n)) return null;
  return EXCLUSIVE_ALIASES[n] || n;
}

// ── Formatting ──────────────────────────────────────────────────────────────
export const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
export const fmt = (v, d = 2) => (isNum(v) ? v.toFixed(d) : null);
export const inr = (n) => `₹${Math.round(n).toLocaleString('en-IN')}`;

export function bikeName(b) {
  if (!b) return '';
  return `${b.manufacturer || ''} ${b.model || b.model_name || ''}`.trim();
}

/** "0.38 s quicker" / "0.12 s slower" — never a bare minus sign. */
export function quickerSlower(deltaS) {
  if (!isNum(deltaS) || Math.abs(deltaS) < 0.0005) return 'no change';
  return `${Math.abs(deltaS).toFixed(2)} s ${deltaS < 0 ? 'quicker' : 'slower'}`;
}

/**
 * Plain-words description of the conditions a result was computed under.
 * `snap` is the snapshot captured when the run started (see makeSnap).
 */
export function conditionsText(snap) {
  if (!snap) return '';
  const temp = isNum(snap.tempC) ? `${Math.round(snap.tempC)} °C` : null;
  if (snap.venueName) {
    const alt = isNum(snap.venueAltM) ? `${Math.round(snap.venueAltM)} m` : null;
    if (snap.envCustom) {
      return `${snap.venueName}${alt ? ` (${alt})` : ''} altitude with your custom conditions`;
    }
    return `${snap.venueName}${alt ? ` — ${alt}` : ''}${temp && !snap.estimated ? `, ${temp}` : ''}`;
  }
  if (snap.placeLabel) {
    return `${snap.placeLabel} weather${temp ? ` — ${temp}` : ''}${
      isNum(snap.humidity) ? `, ${Math.round(snap.humidity)} % humidity` : ''
    }; altitude stays at the ${DEFAULT_PLACE.name} default (${DEFAULT_PLACE.altitudeM} m)`;
  }
  if (snap.envCustom) {
    return `your custom conditions (${DEFAULT_PLACE.altitudeM} m altitude${temp ? `, ${temp}` : ''}${
      isNum(snap.humidity) ? `, ${Math.round(snap.humidity)} % humidity` : ''
    })`;
  }
  return `${DEFAULT_PLACE.name} default — ${DEFAULT_PLACE.altitudeM} m altitude${
    temp && !snap.estimated ? `, ${temp}` : ''
  }`;
}

/** Pure key of the inputs that determine a result (for staleness checks). */
export function makeKey(v, withParts = true) {
  return JSON.stringify([
    v.bike?.id ?? v.bike?.preset ?? null,
    withParts ? (v.selectedParts || []).map((p) => p.id) : null,
    v.frontTire?.id ?? null,
    v.rearTire?.id ?? null,
    v.venue?.id ?? null,
    v.riderKg, v.powerBoost, v.massChange,
    v.ambientTemp, v.trackTemp, v.humidity, v.headwind,
  ]);
}

/** Normalise a full-simulation response to the quick-sim result shape. */
export function normalizeFull(f) {
  if (!f) return null;
  return {
    et_quarter_s: f.et_quarter_s,
    trap_speed_kmh: f.trap_speed_kmh,
    et_60ft_s: f.splits?.['60ft_s'] ?? null,
    et_eighth_s: f.splits?.['660ft_s'] ?? null,
    peak_power_hp: f.config?.peak_power_hp ?? null,
    total_mass_kg: f.config?.total_mass_kg ?? null,
    estimated: false,
    exact: true,
    meta: f.meta,
  };
}

/** Plain words for an error thrown by a sim request. */
export function friendlyError(e) {
  const m = (e?.message || '').toString();
  if (e?.status === 429 || /\b429\b/.test(m)) return null; // handled separately
  if (!m || /failed to fetch|networkerror|load failed/i.test(m)) {
    return 'Could not reach the simulator. Check your connection and try again.';
  }
  return m;
}

// ── ?bike=<slug> deep links (blog calls-to-action) ───────────────────────────
function normTokens(str) {
  return (str || '')
    .toLowerCase()
    .replace(/\(\s*(?:19|20)\d\d[^)]*\)/g, ' ') // "(2017-2023)" year ranges only
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .split(' ')
    .filter(Boolean);
}

/**
 * Resolve a slug like "ktm-duke-390" against the catalogue: exact normalised
 * manufacturer+model match first, then "every slug token appears in the name";
 * several hits -> newest model year, then the shortest name. Returns a bike or null.
 */
export function resolveBikeSlug(slug, bikes) {
  let tokens = normTokens(slug);
  if (!tokens.length || !bikes?.length) return null;
  const index = bikes.map((b) => {
    const toks = normTokens(`${b.manufacturer || ''} ${b.model || b.model_name || ''}`);
    return { b, toks, set: new Set(toks), joined: toks.join(' ') };
  });
  const attempt = (t) => {
    const joined = t.join(' ');
    let hits = index.filter((e) => e.joined === joined);
    if (!hits.length) hits = index.filter((e) => t.every((x) => e.set.has(x)));
    if (!hits.length) return null;
    hits.sort((a, c) => (c.b.year || 0) - (a.b.year || 0) || a.toks.length - c.toks.length);
    return hits[0].b;
  };
  const expanded = tokens.flatMap((x) => (x === 're' ? ['royal', 'enfield'] : [x]));
  const noYear = expanded.filter((x) => !/^(19|20)\d\d$/.test(x));
  return attempt(tokens) || attempt(expanded) || attempt(noYear);
}
