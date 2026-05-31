// Single source of truth for the API base URL.
//
// In production we deliberately default to the *empty string* so every
// fetch becomes same-origin (`/api/bikes`, `/api/simulate/quick`, etc.)
// and gets routed via a Vercel rewrite in `vercel.json` to the Railway
// backend. This has two advantages over hitting Railway directly from
// the browser:
//
//   1. DNS filters on corporate / college / hostel WiFi routinely block
//      `*.up.railway.app` wholesale (Railway hosts unmoderated user
//      projects so it's a common target). The user's Windows resolver
//      was returning REFUSED for our Railway subdomain, which surfaced
//      as "Failed to fetch" / NXDOMAIN in the browser despite the
//      backend being perfectly healthy. Routing via motoquant.in means
//      only Vercel's edge needs to resolve Railway, which it always can.
//   2. No more CORS -- it's all same-origin. We can drop
//      `allow_origins=['*']` from the FastAPI side later.
//
// For local dev, put `NEXT_PUBLIC_API_URL=http://localhost:8000` in
// `web/.env.local` so the fetches go to your local uvicorn.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

// --- Shared POST helper -----------------------------------------------------
// Mirrors the fetch + error-extraction pattern used inline in
// LocationPicker.resolve / SimulatorWidget.runSim: POST JSON, and on a
// non-2xx response try to surface the FastAPI `detail` field (string or
// JSON) before falling back to the raw body text. Throws Error on failure
// so callers can `try/catch` and render the message in an error tile.
async function postJson(path, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let msg = `API error ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail) {
        msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
      }
    } catch {
      try {
        const t = await res.text();
        if (t) msg = `${msg}: ${t}`;
      } catch {
        /* keep the status-only message */
      }
    }
    throw new Error(msg);
  }
  return res.json();
}

/**
 * Budget-constrained build optimiser. POSTs to /api/optimize/build and
 * returns the full optimisation result (base vs optimised ET/trap, the
 * selected parts list, synergies, warnings, next-upgrade suggestion,
 * category priority, and the scoring-method metadata).
 *
 * @param {object}  opts
 * @param {number}  opts.bike_id          Catalog bike id (required).
 * @param {number}  opts.budget_inr       Budget ceiling in INR (required).
 * @param {string} [opts.goal]            "min_et" | "max_trap" (default "min_et").
 * @param {string} [opts.profile]         "all" | "street_legal" | "drag_prep" | "full_race".
 * @param {number} [opts.rider_weight_kg] Rider mass in kg.
 * @param {number} [opts.venue_id]        Venue id for environment.
 * @param {number} [opts.max_candidates]  Cap on parts evaluated.
 */
export async function optimizeBuild({
  bike_id,
  budget_inr,
  goal,
  profile,
  rider_weight_kg,
  venue_id,
  max_candidates,
}) {
  const body = { bike_id, budget_inr };
  if (goal != null) body.goal = goal;
  if (profile != null) body.profile = profile;
  if (rider_weight_kg != null) body.rider_weight_kg = rider_weight_kg;
  if (venue_id != null) body.venue_id = venue_id;
  if (max_candidates != null) body.max_candidates = max_candidates;
  return postJson('/api/optimize/build', body);
}

/**
 * ECU / setup autotune. POSTs to /api/autotune/ecu and returns the
 * environment summary plus gearing, launch-RPM, tyre-pressure, and
 * fuel/timing recommendations and the combined net ET improvement.
 *
 * Location can be supplied either as a free-text `location` string (the
 * backend resolves it the same way /api/venues/resolve does) or as
 * explicit manual conditions (altitude / temp / humidity / pressure).
 *
 * @param {object}  opts
 * @param {number}  opts.bike_id          Catalog bike id (required).
 * @param {string} [opts.location]        Free-text venue / city name.
 * @param {number} [opts.venue_id]        Seeded venue id.
 * @param {number} [opts.altitude_m]      Manual altitude override (m).
 * @param {number} [opts.ambient_temp_c]  Manual ambient temperature (C).
 * @param {number} [opts.humidity_pct]    Manual relative humidity (%).
 * @param {number} [opts.pressure_hpa]    Manual barometric pressure (hPa).
 * @param {number} [opts.rider_weight_kg] Rider mass in kg.
 * @param {number} [opts.gear_span]       Sprocket search span (default 3).
 * @param {number} [opts.launch_steps]    Launch-RPM candidate count (default 6).
 */
export async function autotuneEcu({
  bike_id,
  location,
  venue_id,
  altitude_m,
  ambient_temp_c,
  humidity_pct,
  pressure_hpa,
  rider_weight_kg,
  gear_span,
  launch_steps,
}) {
  const body = { bike_id };
  if (location != null && location !== '') body.location = location;
  if (venue_id != null) body.venue_id = venue_id;
  if (altitude_m != null) body.altitude_m = altitude_m;
  if (ambient_temp_c != null) body.ambient_temp_c = ambient_temp_c;
  if (humidity_pct != null) body.humidity_pct = humidity_pct;
  if (pressure_hpa != null) body.pressure_hpa = pressure_hpa;
  if (rider_weight_kg != null) body.rider_weight_kg = rider_weight_kg;
  if (gear_span != null) body.gear_span = gear_span;
  if (launch_steps != null) body.launch_steps = launch_steps;
  return postJson('/api/autotune/ecu', body);
}
