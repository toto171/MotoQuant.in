// Single source of truth for the API base URL.
//
// Every place in web/ that needs to reach the backend derives its base URL
// from ONE of the three exports below — do not re-derive
// `process.env.NEXT_PUBLIC_API_URL || ...` chains inline in components.
//
// 1) API_URL — the default for browser fetches. In production it is
//    deliberately the *empty string* so every fetch becomes same-origin
//    (`/api/bikes`, `/api/simulate/quick`, etc.) and gets routed via the
//    `/api/:path*` rewrite (declared in `next.config.js`, mirrored in the
//    root `vercel.json`) to the Render backend. Two advantages over hitting
//    Render directly from the browser:
//
//      a. DNS filters on corporate / college / hostel WiFi routinely block
//         PaaS wildcard domains wholesale (they host unmoderated user
//         projects, so they are common filter targets). We hit exactly this
//         with the previous Railway host — the user's Windows resolver
//         returned REFUSED for the API subdomain, which surfaced as
//         "Failed to fetch" / NXDOMAIN in the browser despite the backend
//         being perfectly healthy. Routing via motoquant.in means only
//         Vercel's edge needs to resolve the backend host, which it
//         always can.
//      b. No more CORS -- it's all same-origin. We can drop
//         `allow_origins=['*']` from the FastAPI side later.
//
//    For local dev, put `NEXT_PUBLIC_API_URL=http://localhost:8000` in
//    `web/.env.local` so the fetches go to your local uvicorn.
export const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

// 2) serverApiBase(fallback) — for server-side code (sitemap.js, metadata
//    layouts) that runs at build/ISR time where a relative URL cannot work.
//    Resolution order: public env override, then the server-only
//    MOTOQUANT_INTERNAL_API_URL, then the caller-supplied absolute fallback
//    (typically SITE_URL, i.e. same-origin via the production rewrite).
export function serverApiBase(fallback) {
  return (
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.MOTOQUANT_INTERNAL_API_URL ||
    fallback
  );
}

// --- Shared POST helper -----------------------------------------------------
// Mirrors the fetch + error-extraction pattern used inline in
// LocationPicker.resolve / SimulatorWidget.runSim: POST JSON, and on a
// non-2xx response try to surface the FastAPI `detail` field (string or
// JSON) before falling back to the raw body text. Throws Error on failure
// so callers can `try/catch` and render the message in an error tile.
async function postJson(path, body, signal) {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
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
    const err = new Error(msg);
    err.status = res.status;
    throw err;
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
function optimizeBuildBody({
  bike_id,
  budget_inr,
  goal,
  profile,
  rider_weight_kg,
  venue_id,
  max_candidates,
  location,
  lat,
  lon,
  altitude_m,
  ambient_temp_c,
  track_temp_c,
  humidity_pct,
  pressure_hpa,
}) {
  const body = { bike_id, budget_inr };
  // Optional race conditions — same fields (and meaning) as the autotune route.
  if (location != null && location !== '') body.location = location;
  if (lat != null && lon != null) {
    body.lat = lat;
    body.lon = lon;
  }
  if (altitude_m != null) body.altitude_m = altitude_m;
  if (ambient_temp_c != null) body.ambient_temp_c = ambient_temp_c;
  if (track_temp_c != null) body.track_temp_c = track_temp_c;
  if (humidity_pct != null) body.humidity_pct = humidity_pct;
  if (pressure_hpa != null) body.pressure_hpa = pressure_hpa;
  if (goal != null) body.goal = goal;
  if (profile != null) body.profile = profile;
  if (rider_weight_kg != null) body.rider_weight_kg = rider_weight_kg;
  if (venue_id != null) body.venue_id = venue_id;
  if (max_candidates != null) body.max_candidates = max_candidates;
  return body;
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
function autotuneEcuBody({
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
  return body;
}

// --- Background jobs (real progress) ----------------------------------------
// POST /api/jobs/{kind} starts the work server-side and returns a job_id;
// GET /api/jobs/{id} reports {status, progress 0..1, stage, result|error}.
// runJob() drives the SimProgress bars. Every wrapper takes a `fallbackPath`:
// when the backend predates /api/jobs/* (deploy skew, self-hosted, the desktop
// sidecar) we degrade gracefully to the synchronous route — same result, just
// without the live percentage.

export async function startJob(kind, body, signal) {
  return postJson(`/api/jobs/${kind}`, body, signal);
}

export async function cancelJob(jobId) {
  // Cooperative server-side cancel — the worker stops at its next progress
  // tick and frees its concurrency slot. No-op on finished jobs.
  return postJson(`/api/jobs/${jobId}/cancel`);
}

// Sleep for `ms`, but resolve early when the tab becomes visible again or the
// network comes back, so a resumed job is re-polled immediately.
function sleepOrWake(ms) {
  return new Promise((resolve) => {
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      if (typeof document !== 'undefined') document.removeEventListener('visibilitychange', onVis);
      if (typeof window !== 'undefined') window.removeEventListener('online', finish);
      resolve();
    };
    const onVis = () => {
      if (document.visibilityState === 'visible') finish();
    };
    const timer = setTimeout(finish, ms);
    if (typeof document !== 'undefined') document.addEventListener('visibilitychange', onVis);
    if (typeof window !== 'undefined') window.addEventListener('online', finish);
  });
}

export async function runJob(kind, body, { onProgress, fallbackPath, pollMs = 350, signal } = {}) {
  onProgress?.({ status: 'connecting', progress: null, stage: '' });
  let started;
  try {
    started = await startJob(kind, body, signal);
  } catch (e) {
    if (e?.name === 'AbortError') throw e;
    if (
      fallbackPath &&
      (e?.status === 404 || e?.status === 405 || /API error (404|405)/.test(e?.message || ''))
    ) {
      onProgress?.({ status: 'running', progress: null, stage: '' });
      return postJson(fallbackPath, body, signal);
    }
    throw e;
  }
  const aborted = () => {
    // Stop button: free the server slot, then unwind like a fetch abort.
    cancelJob(started.job_id).catch(() => {});
    return new DOMException('Aborted', 'AbortError');
  };
  if (signal?.aborted) throw aborted();

  // Polling is failure-tolerant: long jobs (the optimiser full-sim fallback
  // runs for minutes) see hundreds of polls, and one VoWiFi blip / proxy
  // hiccup must NOT kill a run that is still healthy server-side.
  //  - transient errors (network, 5xx): keep polling for up to 150 s
//    (the optimiser verification stage saturates the 0.5-CPU free
//     tier for ~60-90 s, starving job-status polls; the job still
//     completes server-side, so the client must outwait it)
  //  - 404: in-memory registry lost the job (restart) — confirm 3× in a row
  //  - interval backs off 350 ms → 800 ms → 1.5 s as the job ages
  let t0 = Date.now();
  // Tolerance window runs from the FIRST failure of the current streak (reset
  // on any successful poll) so a laptop sleep / backgrounded tab does not
  // cancel a healthy job on the first failed poll after waking.
  let firstFailAt = null;
  let lostCount = 0;
  let restarts = 0;
  for (;;) {
    let j = null;
    let lost = false;
    try {
      const res = await fetch(`${API_URL}/api/jobs/${started.job_id}`, {
        cache: 'no-store',
        signal,
      });
      if (res.status === 404) {
        lost = true;
      } else if (res.ok) {
        j = await res.json();
      }
      // other statuses (502/504 proxy, 5xx) → treated as transient
    } catch (e) {
      if (e?.name === 'AbortError') throw aborted();
      // transient network failure — tolerated below
    }

    if (j != null) {
      firstFailAt = null;
      lostCount = 0;
      if (signal?.aborted) throw aborted();
      if (j.status === 'cancelled') throw new DOMException('Aborted', 'AbortError');
      if (j.status === 'error') throw new Error(j.error || 'Simulation failed');
      onProgress?.({ status: j.status, progress: j.progress, stage: j.stage });
      if (j.status === 'done') return j.result;
    } else if (lost) {
      lostCount += 1;
      if (lostCount >= 3) {
        // The registry is in-memory — a backend restart (deploy / crash)
        // loses the job. Self-heal: the sims are pure compute, so re-submit
        // the same work once instead of surfacing an error.
        if (restarts >= 1) {
          throw new Error('Progress lost (the engine restarted mid-run) — please run again');
        }
        restarts += 1;
        lostCount = 0;
        onProgress?.({
          status: 'connecting',
          progress: null,
          stage: 'Engine restarted — running again from the start',
        });
        try {
          started = await startJob(kind, body, signal);
        } catch (e) {
          if (e?.name === 'AbortError') throw aborted();
          throw new Error(
            'Progress lost and the engine is not reachable — please run again'
          );
        }
        firstFailAt = null;
        t0 = Date.now(); // restart the poll-interval backoff for the new job
        continue;
      }
    } else if (firstFailAt == null) {
      firstFailAt = Date.now();
    } else if (Date.now() - firstFailAt > 150_000) {
      cancelJob(started.job_id).catch(() => {}); // don't leave a zombie burning CPU
      throw new Error(
        'Connection lost while the simulation was running — check your network and run again'
      );
    }

    const age = Date.now() - t0;
    const interval = age > 60_000 ? 1500 : age > 10_000 ? 800 : pollMs;
    await sleepOrWake(interval);
    if (signal?.aborted) throw aborted();
  }
}

export function optimizeBuildJob(opts, onProgress, signal) {
  return runJob('optimize', optimizeBuildBody(opts), {
    onProgress,
    signal,
    fallbackPath: '/api/optimize/build',
  });
}

export function autotuneEcuJob(opts, onProgress, signal) {
  return runJob('autotune', autotuneEcuBody(opts), {
    onProgress,
    signal,
    fallbackPath: '/api/autotune/ecu',
  });
}

export function simulateJob(body, onProgress, signal) {
  return runJob('simulate', body, {
    onProgress,
    signal,
    fallbackPath: '/api/simulate',
  });
}

export function topspeedJob(body, onProgress, signal) {
  return runJob('topspeed', body, {
    onProgress,
    signal,
    fallbackPath: '/api/simulate/top-speed',
  });
}

// A-vs-B comparison as a background job (added July 2026 alongside
// POST /api/jobs/compare) — real progress across both sims + Stop. Falls
// back to the synchronous compare route on older backends.
export function compareJob(body, onProgress, signal) {
  return runJob('compare', body, {
    onProgress,
    signal,
    fallbackPath: '/api/simulate/compare',
  });
}

/**
 * One agent-mode chat turn as a background job (POST /api/jobs/chat) —
 * agent turns can run multiple sims / an optimizer pass, so they stream
 * live stage text ("Simulating Hayabusa…", "Optimizing stage_4…") through
 * onProgress and are cancellable via the AbortSignal (runJob cancels the
 * job server-side on abort). Falls back to the synchronous /api/chat route
 * with the SAME body on older backends (404/405 on /api/jobs/chat).
 *
 * The server is stateless — the client holds the transcript and sends the
 * prior turns back with every request.
 *
 * @param {string} query      The user's new message.
 * @param {Array} [messages]  Prior turns [{role:'user'|'assistant', content}],
 *                            oldest first (server caps at 24).
 * @param {object} [opts]     {signal, onProgress}
 * @returns {Promise<object>} ChatResponse dict ({summary, blocks, error, …}).
 */
export function chatJob(query, messages, { signal, onProgress } = {}) {
  const body = { query };
  if (Array.isArray(messages) && messages.length > 0) body.messages = messages;
  return runJob('chat', body, {
    onProgress,
    signal,
    fallbackPath: '/api/chat',
  });
}

// ── Bike catalog (shared, memoised) ─────────────────────────────────────
// One in-flight promise for the full catalog (limit=2000). Cached for the
// page lifetime; a failure clears the cache so the next call retries.
let _catalogPromise = null;
export function getBikeCatalog() {
  if (_catalogPromise) return _catalogPromise;
  _catalogPromise = (async () => {
    const res = await fetch(`${API_URL}/api/bikes?limit=2000`);
    if (!res.ok) {
      const err = new Error(`API error ${res.status}`);
      err.status = res.status;
      throw err;
    }
    const data = await res.json();
    return Array.isArray(data) ? data : data.bikes || data.items || [];
  })();
  _catalogPromise.catch(() => {
    _catalogPromise = null;
  });
  return _catalogPromise;
}

// ── Parts catalog + per-bike compatibility (two cheap requests) ─────────
// The full catalog is fetched ONCE per page load (no bike id → no per-bike
// annotation, and the list omits fitment_rules/specifications by default).
// Which parts fit a given bike is a separate ids-only request, so changing
// bike costs a few KB instead of re-downloading the whole catalog.
let _partsPromise = null;
export function getPartsCatalog() {
  if (_partsPromise) return _partsPromise;
  _partsPromise = (async () => {
    // include_rules adds each part's `specifications` (slot position/type for the
    // picker's one-per-slot rule); the response is gzipped (~55 KB).
    const res = await fetch(`${API_URL}/api/parts?limit=5000&include_rules=true`);
    if (!res.ok) {
      const err = new Error(`API error ${res.status}`);
      err.status = res.status;
      throw err;
    }
    const data = await res.json();
    return Array.isArray(data?.parts) ? data.parts : [];
  })();
  _partsPromise.catch(() => {
    _partsPromise = null;
  });
  return _partsPromise;
}

/** Ids of the parts that fit `bikeId` (abortable). Resolves to a number[]. */
export async function getCompatiblePartIds(bikeId, signal) {
  const res = await fetch(
    `${API_URL}/api/parts?bike_id=${encodeURIComponent(bikeId)}&compatible_only=true&limit=5000&fields=id`,
    { signal },
  );
  if (!res.ok) {
    const err = new Error(`API error ${res.status}`);
    err.status = res.status;
    throw err;
  }
  const data = await res.json();
  return Array.isArray(data?.part_ids) ? data.part_ids : [];
}

// ── Part display label ──────────────────────────────────────────────────
// Defensive: render a part's display name without double-printing the brand.
// The data layer (parts_repo.normalize_model_name) already strips a leading
// brand from model_name, but this guard means a future data regression can't
// reintroduce "Akrapovic Akrapovic Slip-On". Accepts model_name or name.
export function partLabel(brand, name) {
  const b = (brand || '').trim();
  const m = (name || '').trim();
  if (!b) return m;
  if (!m) return b;
  if (m.toLowerCase().startsWith(b.toLowerCase())) return m;
  return `${b} ${m}`;
}
