/**
 * Overlay two (or more) time series that were sampled on DIFFERENT time grids.
 *
 * Each series carries its own `t_s` array; plotting series B against series
 * A's index would draw B at the wrong times. `mergeOnTime` builds one row per
 * distinct time in any series and fills every series by linear interpolation
 * over ITS OWN time axis. Outside a series' own time range the value is null
 * (a gap), never 0 and never held, so a run that ends earlier simply stops.
 *
 *   series: [{ prefix: 'a', t: [...], channels: { speed: [...], rpm: [...] } }]
 *   rows:   [{ t, a_speed, a_rpm, b_speed, ... }]  — sorted by t, de-duplicated.
 * At a series' own sample times the value is exactly the sample.
 */
function lerpAt(ts, vs, x) {
  const n = Math.min(ts.length, vs.length);
  if (!n || x < ts[0] || x > ts[n - 1]) return null;
  let lo = 0;
  let hi = n - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (ts[mid] <= x) lo = mid; else hi = mid;
  }
  const t0 = ts[lo];
  const t1 = ts[hi];
  const v0 = vs[lo];
  const v1 = vs[hi];
  if (typeof v0 !== 'number' || typeof v1 !== 'number') return null;
  if (x === t0 || t1 === t0) return v0;
  if (x === t1) return v1;
  return v0 + ((v1 - v0) * (x - t0)) / (t1 - t0);
}

export function mergeOnTime(series, { round = 6 } = {}) {
  const all = new Set();
  for (const s of series) for (const t of s.t || []) if (typeof t === 'number' && Number.isFinite(t)) all.add(+t.toFixed(round));
  const grid = [...all].sort((x, y) => x - y);
  return grid.map((t) => {
    const row = { t };
    for (const s of series) {
      for (const [name, vs] of Object.entries(s.channels)) {
        const v = lerpAt(s.t, vs || [], t);
        row[`${s.prefix}_${name}`] = v == null ? null : v;
      }
    }
    return row;
  });
}
