/**
 * Shared constants + pure helpers for the /simulator page (CLARITY v6).
 * No React in here — everything is trivially testable and tree-shakeable.
 */

// ── Defaults (the values the sliders start at; also the "not custom" test) ──
// The weather values mirror the SERVER's default conditions (22 °C / 30 °C
// track / 40 % / no wind). While all four are at these values the weather
// fields are simply not sent, so the server runs — and echoes — its defaults.
export const DEFAULTS = {
  riderKg: 75,
  powerBoost: 0,
  massChange: 0,
  ambientTemp: 22,
  trackTemp: 30,
  humidity: 40,
  headwind: 0,
};

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

// ── Part exclusivity: one part per physical slot ────────────────────────────
// SINGLE TABLE, ported from the backend so the picker can never build a setup
// the optimizer would not: motoquant/analysis/roi.py (EXCLUSIVE_CATEGORIES,
// _EXCLUSIVE_CATEGORY_ALIASES, _sprocket_positions, _brake_susp_slot and the
// group-key function that uses them). Keep the two in step. The rule there:
// a part whose slot cannot be confidently determined is NON-exclusive.
const EXCLUSIVE_CATEGORIES = new Set([
  'exhaust', 'ecu', 'clutch_kit', 'air_filter', 'quickshifter', 'battery', 'chain',
  'boost_kit', 'nitrous', 'wheelie_bar', 'swingarm_ext', 'lowering_kit', 'air_shifter',
  'lockup_clutch',
]);
const EXCLUSIVE_ALIASES = { lockup_clutch: 'clutch_kit', air_shifter: 'quickshifter' };

const SPROCKET_POS_RE = /\b(front|rear)\s+sprocket\b/i;
const BRAKE_SUBTYPE = {
  brake_pads: 'pad', pads: 'pad', pad: 'pad', rotor: 'rotor', brake_rotor: 'rotor', disc: 'rotor',
  rotor_and_pads: 'rotor_and_pads', caliper: 'caliper', radial_caliper: 'caliper',
  master_cylinder: 'master_cylinder', line: 'line', brake_hose: 'line', hose: 'line',
};
const SUSP_SLOT = {
  fork: 'fork', fork_internals: 'fork', fork_cartridge: 'fork', fork_springs: 'fork', cartridge: 'fork',
  rear_shock: 'shock', shock: 'shock', monoshock: 'shock',
};
const BRAKE_NAME_RE = /\b(pad|rotor|disc|line|hose|caliper|master)s?\b/i;
const BRAKE_NAME_SUBTYPE = {
  pad: 'pad', rotor: 'rotor', disc: 'rotor', line: 'line', hose: 'line', caliper: 'caliper', master: 'master_cylinder',
};
const FORK_NAME_RE = /\b(fork|cartridge)s?\b/i;
const SHOCK_NAME_RE = /\b(shock|monoshock)s?\b/i;

function specsOf(part) {
  let sp = part?.specifications;
  if (typeof sp === 'string') {
    try { sp = JSON.parse(sp); } catch { sp = null; }
  }
  return sp && typeof sp === 'object' ? sp : {};
}

/**
 * Exclusivity slot for a part, or null when it can be stacked freely.
 * Two selected parts with the same non-null slot cannot both be in a build.
 */
export function partSlot(part, categoryName) {
  const cat = (categoryName || '').toLowerCase();
  const name = String(part?.model_name || '');
  const specs = specsOf(part);

  if (cat === 'sprocket') {
    if (specs.position === 'front' || specs.position === 'rear') return `sprocket:${specs.position}`;
    const m = SPROCKET_POS_RE.exec(name);
    return m ? `sprocket:${m[1].toLowerCase()}` : null;
  }

  if (cat === 'suspension') {
    let slot = SUSP_SLOT[String(specs.type || '').toLowerCase()];
    if (!slot) {
      const fork = FORK_NAME_RE.test(name);
      const shock = SHOCK_NAME_RE.test(name);
      if (fork && !shock) slot = 'fork';
      else if (shock && !fork) slot = 'shock';
    }
    return slot ? `suspension:${slot}` : null;
  }

  if (cat === 'brakes') {
    let subtype = BRAKE_SUBTYPE[String(specs.type || '').toLowerCase()];
    if (!subtype) {
      const m = BRAKE_NAME_RE.exec(name);
      if (m) subtype = BRAKE_NAME_SUBTYPE[m[1].toLowerCase()];
    }
    if (!subtype) return null;
    let pos = String(specs.position || '').toLowerCase();
    if (!['front', 'rear', 'front_rear'].includes(pos)) {
      const f = /\bfront\b/i.test(name);
      const r = /\brear\b/i.test(name);
      pos = f && r ? 'front_rear' : f ? 'front' : r ? 'rear' : '';
    }
    return pos ? `brakes:${subtype}:${pos}` : null;
  }

  if (!EXCLUSIVE_CATEGORIES.has(cat)) return null;
  return EXCLUSIVE_ALIASES[cat] || cat;
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

/** Pure key of the inputs that determine a result (for staleness checks). */
export function makeKey(v, withParts = true) {
  return JSON.stringify([
    v.bike?.id ?? v.bike?.preset ?? null,
    withParts ? (v.selectedParts || []).map((p) => p.id) : null,
    v.frontTire?.id ?? null,
    v.rearTire?.id ?? null,
    v.venue?.id ?? null,
    // A resolved place that is not a known venue changes the altitude that is simulated.
    v.venue?.id == null && v.location ? [v.location.latitude ?? null, v.location.longitude ?? null, v.location.altitude_m ?? null] : null,
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
    environment: f.environment || null,
    parts_applied: f.parts_applied || [],
    parts_skipped: f.parts_skipped || [],
    build_cost_inr: f.build_cost_inr ?? 0,
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
 * Resolve a slug like "ktm-duke-390" against the catalogue. A wrong bike is
 * worse than no bike, so every step is strict and an ambiguous slug resolves
 * to NOTHING (the caller then shows the default bike plus a visible notice):
 *   1. exact normalised manufacturer+model match;
 *   2. every slug token equals a WHOLE token of the name (so "r1" never
 *      matches "r15", "300" never "3000", "r600" never "r750");
 *   3. squeezed spelling ("gsx-r600" vs "GSX-R 600"): the squeezed slug must
 *      equal a contiguous run of whole name tokens joined together — never an
 *      arbitrary substring ("cbr250r" is not inside "cbr250rr").
 * Hits are grouped into model families (name with the year range stripped).
 * Exactly one family must remain — the one with the fewest name tokens when
 * the match is a loose one, so "classic 350" is the Classic, not a Halcyon
 * variant — and within it the generation covering the slug's year, else the
 * newest. Returns a bike or null.
 */
export function resolveBikeSlug(slug, bikes) {
  const tokens = normTokens(slug);
  if (!tokens.length || !bikes?.length) return null;
  const slugYear = (tokens.find((x) => /^(19|20)\d\d$/.test(x)) || null);
  const y = slugYear ? parseInt(slugYear, 10) : null;
  const index = bikes.map((b) => {
    const label = `${b.manufacturer || ''} ${b.model || b.model_name || ''}`;
    const toks = normTokens(label);
    const rng = /\(\s*((?:19|20)\d\d)\s*-\s*((?:19|20)\d\d)?/.exec(label);
    const from = rng ? parseInt(rng[1], 10) : b.year || null;
    const to = rng ? (rng[2] ? parseInt(rng[2], 10) : 9999) : from;
    return { b, toks, set: new Set(toks), joined: toks.join(' '), family: toks.join(' '), from, to };
  });
  // One family, one generation — or null when the hits span several families.
  const pick = (hits, slugToks = tokens) => {
    const fams = new Map();
    for (const e of hits) {
      if (!fams.has(e.family)) fams.set(e.family, []);
      fams.get(e.family).push(e);
    }
    let chosen = [...fams.values()];
    if (y != null && chosen.length > 1) {
      // Prefer the family that actually has a generation covering the slug's year.
      const covering = chosen.filter((g) => g.some((e) => e.from != null && y >= e.from && y <= e.to));
      if (covering.length) chosen = covering;
    }
    if (chosen.length > 1) {
      const min = Math.min(...chosen.map((g) => g[0].toks.length));
      chosen = chosen.filter((g) => g[0].toks.length === min);
    }
    if (chosen.length > 1) {
      // Still several: acceptable only when they are successive versions of
      // ONE model ("MT-15 V1" / "MT-15 V2"), i.e. the words that differ
      // between them are all version codes. Then the newest version wins.
      const own = new Set(slugToks);
      const extras = chosen.map((g) => new Set(g[0].toks.filter((t) => !own.has(t))));
      const common = [...extras[0]].filter((t) => extras.every((x) => x.has(t)));
      const differing = extras.flatMap((x) => [...x].filter((t) => !common.includes(t)));
      if (differing.length && differing.every((t) => /^(v\d+|[kl]\d|mk\d+|gen\d)$/.test(t))) {
        chosen.sort((a, c) => Math.max(...c.map((e) => e.b.year || 0)) - Math.max(...a.map((e) => e.b.year || 0)));
        chosen = [chosen[0]];
      }
    }
    if (chosen.length !== 1) return null;
    const gens = chosen[0];
    gens.sort((a, c) => {
      if (y != null) {
        const ai = a.from != null && y >= a.from && y <= a.to ? 1 : 0;
        const ci = c.from != null && y >= c.from && y <= c.to ? 1 : 0;
        if (ai !== ci) return ci - ai; // the generation that covers the slug's year
      }
      return (c.b.year || 0) - (a.b.year || 0);
    });
    return gens[0].b;
  };
  const attempt = (t) => {
    const joined = t.join(' ');
    const exact = index.filter((e) => e.joined === joined);
    if (exact.length) return pick(exact, t);
    const loose = index.filter((e) => t.every((x) => e.set.has(x)));
    return loose.length ? pick(loose, t) : null;
  };
  const digitRuns = (str) => str.match(/\d+/g) || [];
  const squeezed = (t) => {
    // Years and Suzuki-style generation codes ("k8") carry no model identity.
    const core = t.filter((x) => x.length > 1 && !/^(19|20)\d\d$/.test(x) && !/^[kl]\d$/.test(x));
    if (!core.length) return null;
    const want = core.join('');
    const hits = index.filter((e) => {
      for (let i = 0; i < e.toks.length; i++) {
        let acc = '';
        for (let j = i; j < e.toks.length && acc.length < want.length; j++) {
          acc += e.toks[j];
          if (acc === want) {
            // Every number in the slug must be a whole number in the name.
            const nameRuns = new Set(e.toks.flatMap(digitRuns));
            return digitRuns(want).every((r) => nameRuns.has(r) || e.toks.slice(i, j + 1).some((tk) => digitRuns(tk).includes(r)));
          }
        }
      }
      return false;
    });
    return hits.length ? pick(hits, core) : null;
  };
  const expanded = tokens.flatMap((x) => (x === 're' ? ['royal', 'enfield'] : [x]));
  const noYear = expanded.filter((x) => !/^(19|20)\d\d$/.test(x));
  return attempt(tokens) || attempt(expanded) || attempt(noYear) || squeezed(expanded);
}

/**
 * Resolve a venue slug like "mmrt" or "aamby-valley" (blog links) against the
 * venue list: every slug token must appear among the venue name's tokens.
 * Several hits -> the shortest name. Returns a venue or null.
 */
export function resolveVenueSlug(slug, venues) {
  const tokens = normTokens(slug);
  if (!tokens.length || !venues?.length) return null;
  const hits = venues
    .map((v) => ({ v, set: new Set(normTokens(v.name)), n: normTokens(v.name).length }))
    .filter((e) => tokens.every((t) => e.set.has(t)));
  if (!hits.length) return null;
  hits.sort((a, b) => a.n - b.n);
  return hits[0].v;
}

// True when a catalog tyre can be fitted at ``wheel`` ('front' | 'rear').
// Tyres marked 'both' (or with no position) fit either wheel.
export function tyreFitsWheel(tyre, wheel) {
  const pos = String(tyre?.position || '').toLowerCase();
  return pos !== 'front' && pos !== 'rear' ? true : pos === wheel;
}
