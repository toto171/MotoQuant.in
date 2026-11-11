/**
 * stockCatalog — the bike catalog as it ships in the build, for server code.
 *
 * Two committed files, both generated from motoquant.db:
 *   - app/leaderboard/stock_times.json (scripts/gen_stock_leaderboard.py):
 *     every bike with its simulated stock quarter-mile time and finish-line
 *     speed, all under one rider weight and one set of conditions;
 *   - data/bike-ids.json (web/scripts/gen_bike_ids.py): the live catalog ids.
 *
 * Bike pages, the /bikes index and the sitemap read these instead of the
 * backend API, so their metadata and crawlable text never depend on the API
 * being awake. Only ids present in BOTH files are served; anything else is a
 * 404. Import this from server components only: the full JSON stays on the
 * server, and a client component receives just the one entry it needs.
 */

import STOCK from '../app/leaderboard/stock_times.json';
import BIKE_ID_MANIFEST from '../data/bike-ids.json';

const MANIFEST_IDS = new Set(BIKE_ID_MANIFEST.ids);

const BY_ID = new Map(
  STOCK.bikes.filter((b) => MANIFEST_IDS.has(b.id)).map((b) => [b.id, b]),
);

/** Rider weight (kg) every stock time was simulated with. */
export const STOCK_RIDER_KG = STOCK.rider_kg;

/** The conditions every stock time was simulated in (name, altitude_m, ...). */
export const STOCK_CONDITIONS = STOCK.conditions;

/** The bike ids that have a page, in catalog-manifest order. */
export const BIKE_PAGE_IDS = BIKE_ID_MANIFEST.ids.filter((id) => BY_ID.has(id));

/**
 * The stock entry for a route param, or null when the id is not a plain
 * positive integer or is not in the catalog.
 */
export function getStockBike(id) {
  const s = String(id ?? '');
  if (!/^[1-9]\d{0,6}$/.test(s)) return null;
  return BY_ID.get(Number(s)) || null;
}

/** Every bike that has a page. */
export function stockBikes() {
  return [...BY_ID.values()];
}

/** "Suzuki Hayabusa GSX1300R Gen1" */
export function stockBikeName(bike) {
  return [bike.manufacturer, bike.model].filter(Boolean).join(' ');
}
