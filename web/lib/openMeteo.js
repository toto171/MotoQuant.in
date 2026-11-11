/**
 * Live weather from Open-Meteo, fetched by the visitor's own browser.
 *
 * Why here and not on the API: Open-Meteo's free tier limits calls per IP
 * address, and a free Render service shares its outbound address with many
 * other apps, so lookups made by the API kept failing with HTTP 429
 * (2026-11-11). From the browser every visitor uses their own allowance.
 *
 * The API still does the atmosphere maths: LocationPicker sends this reading
 * to /api/venues/resolve as `observed`, and the server returns air density,
 * effective altitude and power correction from its environment model.
 *
 * This mirrors motoquant/api.py::_fetch_open_meteo_uncached (the server's own
 * lookup, still used as a fallback): the same "City, CC" parsing, the same
 * geocoder query, elevation from the geocoder and then the forecast, and
 * sea-level pressure (pressure_msl). Keep the two in step.
 *
 * Data: Open-Meteo.com, CC BY 4.0 (credited where the reading is shown).
 */

/**
 * A self-hosted copy that must not send visitors to a third party, or that
 * relies on the API's own provider (OPENWEATHERMAP_API_KEY, or
 * MOTOQUANT_OPEN_METEO=0), builds the site with
 * NEXT_PUBLIC_MOTOQUANT_BROWSER_WEATHER=0: the picker then asks the API only,
 * as before. Next.js inlines the value at build time.
 */
export const BROWSER_WEATHER_ENABLED = process.env.NEXT_PUBLIC_MOTOQUANT_BROWSER_WEATHER !== '0';

const GEOCODE_URL = 'https://geocoding-api.open-meteo.com/v1/search';
const FORECAST_URL = 'https://api.open-meteo.com/v1/forecast';
const TIMEOUT_MS = 10000;

// The API's bounds for a reading and a place (VenueResolveRequest,
// ObservedWeather): never send what it would reject.
const ALTITUDE_MIN_M = -500;
const ALTITUDE_MAX_M = 8000;

export const UNAVAILABLE_MESSAGE =
  "Live weather isn't available right now. Pick a track or set the conditions by hand.";

export class PlaceNotFoundError extends Error {
  constructor() {
    super("We couldn't find that place. Try a nearby city or pick a track.");
    this.name = 'PlaceNotFoundError';
  }
}

/**
 * Two decimals is about 1 km: enough for the weather, without sending a
 * visitor's exact GPS position to a third party.
 */
export function roundCoord(v) {
  return Math.round(v * 100) / 100;
}

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/** "Pune, IN" -> { name: 'Pune', countryCode: 'IN' }; a trailing two-letter part narrows the search. */
export function parsePlaceQuery(text) {
  const raw = String(text || '').trim();
  const parts = raw.split(',').map((p) => p.trim()).filter(Boolean);
  const name = parts.length ? parts[0] : raw;
  const last = parts.length > 1 ? parts[parts.length - 1] : '';
  return { name, countryCode: last.length === 2 ? last.toUpperCase() : null };
}

async function getJson(url, params) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${url}?${new URLSearchParams(params)}`, { signal: ctrl.signal });
    if (!res.ok) {
      throw new Error(
        `Live weather isn't available right now (HTTP ${res.status}). Pick a track or set the conditions by hand.`,
      );
    }
    return await res.json();
  } catch (e) {
    if (e instanceof Error && e.message.startsWith("Live weather isn't")) throw e;
    // Timeout, offline, or a blocker that stops the request.
    throw new Error(UNAVAILABLE_MESSAGE);
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Current conditions for a place name or for coordinates.
 *
 * @param {object}  where
 * @param {string} [where.query]       Place name, optionally "City, CC".
 * @param {number} [where.lat]         Latitude (rounded before it is sent).
 * @param {number} [where.lon]         Longitude (rounded before it is sent).
 * @param {number} [where.altitude_m]  Known altitude (e.g. from GPS); wins over Open-Meteo's.
 * @returns {Promise<{name: string|null, latitude: number, longitude: number,
 *   altitude_m: number, observed: object}>}  `observed` is the API's ObservedWeather shape.
 * @throws {PlaceNotFoundError} when the geocoder has no match.
 */
export async function fetchOpenMeteoConditions({ query, lat, lon, altitude_m } = {}) {
  let latitude = num(lat);
  let longitude = num(lon);
  let altitude = num(altitude_m);
  let name = null;
  let country = null;

  if (latitude == null || longitude == null) {
    const { name: q, countryCode } = parsePlaceQuery(query);
    if (!q) throw new PlaceNotFoundError();
    const geo = await getJson(GEOCODE_URL, { name: q, count: '10', language: 'en', format: 'json' });
    let results = Array.isArray(geo?.results) ? geo.results : [];
    if (countryCode) results = results.filter((r) => r?.country_code === countryCode);
    const top = results[0];
    if (!top || num(top.latitude) == null || num(top.longitude) == null) throw new PlaceNotFoundError();
    latitude = top.latitude;
    longitude = top.longitude;
    name = top.name || null;
    country = top.country_code || null;
    if (altitude == null && num(top.elevation) != null) altitude = top.elevation;
  } else {
    latitude = roundCoord(latitude);
    longitude = roundCoord(longitude);
  }

  const data = await getJson(FORECAST_URL, {
    latitude: String(latitude),
    longitude: String(longitude),
    current: 'temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m',
    wind_speed_unit: 'ms',
  });
  const current = data?.current || {};
  if (altitude == null && num(data?.elevation) != null) altitude = data.elevation;

  // Same defaults as the server when a field is missing.
  const observed = {
    temperature_c: clamp(num(current.temperature_2m) ?? 25, -90, 60),
    humidity_pct: clamp(num(current.relative_humidity_2m) ?? 50, 0, 100),
    pressure_msl_hpa: clamp(num(current.pressure_msl) ?? 1013.25, 800, 1100),
    wind_speed_ms: clamp(num(current.wind_speed_10m) ?? 0, 0, 120),
    wind_direction_deg: clamp(num(current.wind_direction_10m) ?? 0, 0, 360),
  };
  if (typeof country === 'string' && /^[A-Z]{2}$/.test(country)) observed.country = country;

  return {
    name,
    latitude,
    longitude,
    altitude_m: clamp(altitude ?? 0, ALTITUDE_MIN_M, ALTITUDE_MAX_M),
    observed,
  };
}
