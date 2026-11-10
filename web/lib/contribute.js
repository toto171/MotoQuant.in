/**
 * Links that open a prefilled GitHub issue for a rider's contribution.
 *
 * Contributions go to the public issue tracker, where anyone can see them and
 * a maintainer reviews them before anything changes in the catalog. The site
 * stores nothing. Field ids match .github/ISSUE_TEMPLATE/submit-timeslip.yml.
 * This module imports nothing (web/scripts/lib.test.mjs loads it directly).
 */

export const REPO_URL = 'https://github.com/toto171/MotoQuant.in';

function fixed(v, digits) {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(digits) : '';
}

/**
 * A prefilled "Submit a timeslip" issue.
 * @param {object} run  bikeName, bikeId, et, trap, sixty, eighth (any may be missing)
 */
export function timeslipIssueUrl(run = {}) {
  const p = new URLSearchParams({ template: 'submit-timeslip.yml' });
  const et = fixed(run.et, 3);
  p.set('title', `Timeslip: ${run.bikeName || 'bike'}${et ? ` ${et} s` : ''}`);
  if (run.bikeName) p.set('bike', run.bikeName);
  if (run.bikeId != null) p.set('catalog', `https://www.motoquant.in/bikes/${run.bikeId}`);
  if (et) p.set('et', et);
  const trap = fixed(run.trap, 1);
  if (trap) p.set('trap', trap);
  const sixty = fixed(run.sixty, 3);
  if (sixty) p.set('sixty', sixty);
  const eighth = fixed(run.eighth, 3);
  if (eighth) p.set('eighth', eighth);
  return `${REPO_URL}/issues/new?${p.toString()}`;
}
