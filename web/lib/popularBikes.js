/**
 * ONE popular-bikes list for the whole site (simulator, landing widget,
 * Upgrades, Race-day setup). Each entry names a model FAMILY by its model name
 * (years suffix removed) — "Hayabusa (2021-2024)" is in the
 * Hayabusa family, "Hayabusa 25th Anniversary (2024)" and "ZX-10RR" are not —
 * and resolves to that family's newest generation. An entry that matches
 * nothing in the loaded catalogue is not offered at all.
 */
export const POPULAR_BIKES = [
  { label: 'Hayabusa', family: 'hayabusa' },
  { label: 'R15 V4', family: 'yzfr15v4' },
  { label: 'Duke 390', family: 'duke390' },
  { label: 'Classic 350', family: 'classic350' },
  { label: 'ZX-10R', family: 'ninjazx10r' },
  { label: 'GSX-R1000', family: 'gsxr1000' },
];

// Model name without its "(years)" suffix, lower-case, spaces and hyphens removed.
const familyOf = (b) => String(b.model || b.model_name || '').split('(')[0].toLowerCase().replace(/[\s-]+/g, '');

// "(2017-2023)" / "(2024)"; built with RegExp() to keep the build's bracket checker simple.
const YEAR_RANGE = new RegExp('[(]\\s*((?:19|20)\\d\\d)\\s*(?:-\\s*((?:19|20)\\d\\d))?');

/** Last year of a "(2017-2023)" / "(2021-2026)" / "(2024)" name suffix, else year. */
function lastYear(b) {
  const m = YEAR_RANGE.exec(b.model || b.model_name || '');
  if (m) return parseInt(m[2] || m[1], 10);
  return b.year || 0;
}

/** Newest-generation catalogue bike for one popular entry, or null. */
export function resolvePopular(bikes, entry) {
  let best = null;
  for (const b of bikes || []) {
    if (familyOf(b) !== entry.family) continue;
    if (!best || lastYear(b) > lastYear(best) || (lastYear(b) === lastYear(best) && (b.year || 0) > (best.year || 0))) best = b;
  }
  return best;
}

/** [{label, bike}] for every popular entry that exists in `bikes`. */
export function popularChips(bikes) {
  return POPULAR_BIKES.map((p) => ({ label: p.label, bike: resolvePopular(bikes, p) })).filter((c) => c.bike);
}
