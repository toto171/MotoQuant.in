/**
 * When may the in-browser instant estimate (lib/surrogate.js) answer?
 *
 * The model's inputs are: the bike, rider weight, power change, weight change
 * and — only as altitude — a known venue. It has NO input for anything else, so
 * every other condition must send the request to the exact server simulation.
 * This is the one place that list lives:
 *
 *   reason          why the estimate is refused                 enforced by
 *   ─────────────────────────────────────────────────────────────────────────
 *   no-catalog-bike  hand-built reference bike, no feature row  bikeId == null
 *   parts            any selected part                          hasParts
 *   tyres            a front/rear tyre override                 hasTyres
 *   weather          air/track temp, humidity or wind changed   !weatherDefault
 *   place            a resolved place (its altitude + weather)  hasPlace
 *   surface          venue surface is not asphalt, or unknown   predictQuick (venueSurface)
 *   venue-altitude   venue missing from the exported altitudes  predictQuick
 *   envelope         inputs outside the training range          predictQuick
 *
 * (There is no track-preparation control in the UI; if one is added it must
 * be added here as a blocker.)
 */

/** Surface of a venue record from /api/venues (`surface_type`; `track_surface` accepted too). */
export function venueSurface(venue) {
  if (!venue) return null;
  return venue.surface_type ?? venue.track_surface ?? null;
}

/** First blocker that forces the exact server path, or null when the estimate may answer. */
export function instantBlocker({ bikeId, hasParts, hasTyres, weatherDefault, hasPlace }) {
  if (bikeId == null) return 'no-catalog-bike';
  if (hasParts) return 'parts';
  if (hasTyres) return 'tyres';
  if (!weatherDefault) return 'weather';
  if (hasPlace) return 'place';
  return null;
}

/** Hint under every "Where are you racing?" picker on the sim routes (they send altitude + weather). */
export const LOCATION_HINT = 'Adjusts for altitude and weather.';
