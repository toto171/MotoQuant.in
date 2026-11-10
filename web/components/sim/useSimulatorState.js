'use client';

/**
 * useSimulatorState — every piece of state, data fetching and async task for
 * the /simulator page, in one hook so the UI components stay presentational.
 *
 * Correctness rules this hook enforces (audit F1/F2/F6/F8/F12):
 *  - Every result is TAGGED with a snapshot of the inputs it was computed for
 *    (`meta.key`, `meta.bikeId`, …). The UI only shows / saves a result whose
 *    bike matches the current bike, and only saves one whose key matches the
 *    current inputs. Changing bike stops + resets every task.
 *  - Late responses never land: useAsyncTask drops results of aborted runs and
 *    the tasks below re-check the signal after every await.
 *  - ?bike / ?bike_id / ?venue / … are applied on mount AND whenever the query
 *    string changes while the page stays mounted (command-palette navigation).
 *  - Bikes/venues are usable as soon as they arrive; the heavy parts catalogue,
 *    tyres and categories load lazily (Advanced only), abortable, with retry.
 *  - Live quick-sim ticks emit telemetry only for the first run per bike; a
 *    429 shows the server's message and pauses Live updates briefly.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  API_URL as API, simulateJob, topspeedJob, compareJob,
  getBikeCatalog, getPartsCatalog, getCompatiblePartIds,
} from '../../lib/api';
import useAsyncTask from '../../lib/useAsyncTask';
import { predictQuick, preloadSurrogate } from '../../lib/surrogate';
import { instantBlocker, venueSurface } from '../../lib/instantEstimate';
import { saveRun as storeRun, timeslipQuery, timeslipRequest } from '../../lib/runs';
import { track, trackSimRun, installErrorHandlers } from '../../lib/telemetry';
import {
  DEFAULTS, MODE_KEY, bikeName, partSlot, makeKey, normalizeFull,
  pickDefaultBikeForVariant, resolveBikeSlug, resolveVenueSlug, tyreFitsWheel,
} from './format';

const isNumber = (v) => typeof v === 'number' && Number.isFinite(v);
const abortError = () => new DOMException('Aborted', 'AbortError');
const throwIfAborted = (signal) => { if (signal?.aborted) throw abortError(); };

const ENV_KEYS = ['temp', 'track', 'hum', 'wind'];
const ADVANCED_KEYS = ['parts', 'ft', 'rt', ...ENV_KEYS];

function linkWantsAdvanced(sp) {
  return ADVANCED_KEYS.some((k) => sp?.has?.(k));
}

async function readDetail(res) {
  try {
    const j = await res.json();
    if (typeof j?.detail === 'string') return j.detail;
  } catch { /* not JSON */ }
  return '';
}

export default function useSimulatorState(searchParams) {
  const qs = searchParams?.toString() ?? '';
  const defaultBikeVariant = searchParams?.get('variant') === 'B' ? 'B' : 'A';

  // ─── Catalogue data ────────────────────────────────────────────────────────
  const [bikes, setBikes] = useState([]);
  const [venues, setVenues] = useState([]);
  const [categories, setCategories] = useState([]);
  const [catalogParts, setCatalogParts] = useState([]); // whole catalogue, fetched once
  const [compatIds, setCompatIds] = useState(null); // Set of part ids that fit `partsBikeId`
  const [allTires, setAllTires] = useState([]);
  const [bikesStatus, setBikesStatus] = useState('loading'); // loading | ready | error
  const [venuesStatus, setVenuesStatus] = useState('loading');
  const [bootError, setBootError] = useState(null);
  const [bootProgress, setBootProgress] = useState(0);
  const [partsStatus, setPartsStatus] = useState('idle'); // idle | loading | ready | error
  const [partsError, setPartsError] = useState(null);
  const [partsBikeId, setPartsBikeId] = useState(null); // bike the parts list is annotated for
  const [tiresStatus, setTiresStatus] = useState('idle');

  // ─── Selections ────────────────────────────────────────────────────────────
  const [bike, setBike] = useState(null);
  const [selectedParts, setSelectedParts] = useState([]);
  const [frontTire, setFrontTire] = useState(null);
  const [rearTire, setRearTire] = useState(null);
  const [venue, setVenue] = useState(null);
  const [location, setLocation] = useState(null); // resolved env payload (LocationPicker)
  const [riderKg, setRiderKg] = useState(DEFAULTS.riderKg);
  const [powerBoost, setPowerBoost] = useState(DEFAULTS.powerBoost);
  const [massChange, setMassChange] = useState(DEFAULTS.massChange);
  const [ambientTemp, setAmbientTemp] = useState(DEFAULTS.ambientTemp);
  const [trackTemp, setTrackTemp] = useState(DEFAULTS.trackTemp);
  const [humidity, setHumidity] = useState(DEFAULTS.humidity);
  const [headwind, setHeadwind] = useState(DEFAULTS.headwind);
  const [envTouched, setEnvTouched] = useState(false);
  const [showEnv, setShowEnv] = useState(false);

  // ─── View state ────────────────────────────────────────────────────────────
  const [mode, setModeState] = useState('simple');
  const [modeReady, setModeReady] = useState(false);
  const [activeTab, setActiveTab] = useState('quarter');
  const [liveSim, setLiveSim] = useState(true);
  const [livePausedUntil, setLivePausedUntil] = useState(0);
  const [focusRequest, setFocusRequest] = useState(null);
  const [linkReady, setLinkReady] = useState(false);
  const [linkPending, setLinkPending] = useState(false);
  const [bikeNotice, setBikeNotice] = useState(false);
  const [notices, setNotices] = useState([]); // plain-words notes about a shared link / stale ids

  // ─── Compare config ────────────────────────────────────────────────────────
  const [compareBike, setCompareBike] = useState(null);
  const [comparePower, setComparePower] = useState(0);
  const [compareMass, setCompareMass] = useState(0);

  // ─── Uploads / save / share ────────────────────────────────────────────────
  const [uploadResult, setUploadResult] = useState(null);
  const [savedRun, setSavedRun] = useState(null);
  const [shareCopied, setShareCopied] = useState(false);
  const lastDragyFileRef = useRef(null);
  const lastDynoFileRef = useRef(null);

  // ─── Refs ──────────────────────────────────────────────────────────────────
  const bikeRef = useRef(null);
  bikeRef.current = bike;
  const linkAppliedRef = useRef(false);
  const lastQsRef = useRef(null);
  const pendingLinkRef = useRef(null); // { parts: number[]|null, ft, rt }
  const partsAbortRef = useRef(null);
  const coreAbortRef = useRef(null);
  const lastTrackedBikeRef = useRef(null);
  const saveSourceRef = useRef(null);
  const catNameRef = useRef({});
  const allTiresRef = useRef([]);
  allTiresRef.current = allTires;

  // ─── Derived ───────────────────────────────────────────────────────────────
  const categoryNameById = useMemo(() => {
    const m = {};
    for (const c of categories) m[c.id] = c.name;
    return m;
  }, [categories]);
  catNameRef.current = categoryNameById;

  // The catalogue with each part annotated for the CURRENT bike. Fit comes from
  // the ids-only compatibility request, so a bike change never re-downloads the
  // catalogue; while a bike's ids are still loading nothing is annotated.
  const allParts = useMemo(() => {
    if (!compatIds) return catalogParts;
    return catalogParts.map((p) => {
      const fits = compatIds.has(p.id);
      return fits ? { ...p, compatible: true } : {
        ...p,
        compatible: false,
        fitment_reason: 'it is not listed as fitting this bike',
      };
    });
  }, [catalogParts, compatIds]);

  const buildCost = useMemo(
    () => selectedParts.reduce((s, p) => s + (p.price_inr || 0), 0),
    [selectedParts],
  );
  const weatherDefault =
    ambientTemp === DEFAULTS.ambientTemp && trackTemp === DEFAULTS.trackTemp &&
    humidity === DEFAULTS.humidity && headwind === DEFAULTS.headwind;
  const envCustom = location ? envTouched : !weatherDefault;

  const vals = { bike, selectedParts, frontTire, rearTire, venue, location, riderKg, powerBoost,
    massChange, ambientTemp, trackTemp, humidity, headwind };
  const keyFull = makeKey(vals, true);
  const keyNoParts = makeKey(vals, false);

  // Snapshot of the inputs a run is about to use — attached to its result.
  function makeSnap(withParts = true) {
    return {
      key: withParts ? keyFull : keyNoParts,
      bikeId: bike?.id ?? null,
      bikeName: bikeName(bike),
      riderKg,
      venueId: venue?.id ?? null,
      venueName: venue?.name ?? null,
      venueAltM: venue?.altitude_m ?? location?.altitude_m ?? null,
      placeLabel: !venue && location ? (location._label || location.location_name || 'your location') : null,
      tempC: ambientTemp,
      humidity,
      envCustom,
      partCount: selectedParts.length,
      powerBoost,
      massChange,
      frontTireId: frontTire?.id ?? null,
      rearTireId: rearTire?.id ?? null,
    };
  }

  // Weather is only sent once the user (or a chosen place) has changed it. At
  // the defaults it is left out, so the server runs its own default conditions
  // and says so in the `environment` block it echoes.
  function weatherFields() {
    if (weatherDefault) return {};
    return {
      ambient_temp_c: ambientTemp,
      track_temp_c: trackTemp,
      humidity_pct: humidity,
      headwind_kmh: headwind,
    };
  }

  // The chosen place, in the fields every sim route accepts. A known venue is
  // sent by id (the server then uses its altitude and surface); any other
  // resolved place (a hill town, a city) is sent by name with its coordinates
  // and altitude, so the altitude it was resolved at is the altitude simulated.
  function placeFields() {
    if (venue?.id != null) return { venue_id: venue.id };
    if (!location) return {};
    // Conditions restored from a timeslip link: a place with no name to look
    // up, so send its altitude and pressure, never a label (a label would be
    // sent to the weather lookup).
    if (location._saved) {
      const saved = {};
      if (isNumber(location.altitude_m)) saved.altitude_m = location.altitude_m;
      if (isNumber(location.pressure_hpa)) saved.pressure_hpa = location.pressure_hpa;
      return saved;
    }
    const out = {};
    const label = location.venue_name || location.location_name || location._label || location.resolved_name;
    if (label) out.location = label;
    if (isNumber(location.latitude)) out.lat = location.latitude;
    if (isNumber(location.longitude)) out.lon = location.longitude;
    if (isNumber(location.altitude_m)) out.altitude_m = location.altitude_m;
    return out;
  }

  // A shared link can carry a venue or tyre id that no longer exists; the API
  // answers 404 "Venue 9 not found" / "Tire 9 not found". Drop that one id from
  // the setup, say so, and retry the request once without it.
  const addNotice = useCallback((msg) => {
    setNotices((prev) => (prev.includes(msg) ? prev : [...prev, msg]));
  }, []);
  const dismissNotice = useCallback((msg) => {
    setNotices((prev) => prev.filter((m) => m !== msg));
  }, []);
  async function withRefRecovery(body, call) {
    try {
      return await call(body);
    } catch (e) {
      const m = e?.status === 404 ? /^(Venue|Tire) (\d+) not found/i.exec(e?.message || '') : null;
      if (!m) throw e;
      const kind = m[1].toLowerCase();
      const id = Number(m[2]);
      const next = { ...body };
      for (const k of Object.keys(next)) {
        if (kind === 'venue' ? k === 'venue_id' : /tire_id$/.test(k) && next[k] === id) delete next[k];
      }
      if (kind === 'venue') {
        setVenue(null);
        setLocation(null);
        addNotice('The venue in this link is no longer available, so the default conditions are used.');
      } else {
        setFrontTire((t) => (t?.id === id ? null : t));
        setRearTire((t) => (t?.id === id ? null : t));
        addNotice('A tyre in this link is no longer in the catalog, so the original tyre is used.');
      }
      return call(next);
    }
  }

  // Shared sim request body (read fresh at call time — useAsyncTask keeps fn current).
  function baseSimBody(extra = {}) {
    const body = {
      rider_mass_kg: riderKg,
      power_boost_pct: powerBoost,
      mass_delta_kg: massChange,
      ...weatherFields(),
      ...extra,
    };
    if (bike?.id != null) body.bike_id = bike.id;
    else if (bike?.preset) body.bike_preset = bike.preset;
    if (frontTire?.id != null) body.front_tire_id = frontTire.id;
    if (rearTire?.id != null) body.rear_tire_id = rearTire.id;
    Object.assign(body, placeFields());
    return body;
  }

  /* ═══════════════ Async tasks ═══════════════ */

  // Quick sim. Live mode answers locally from the in-browser surrogate when it
  // can (default weather, no parts/tyres); everything else — and every explicit
  // Calculate press — goes to the exact server sim. Request shapes unchanged.
  const quickTask = useAsyncTask(async (signal, _onProgress, trigger = 'auto') => {
    if (!bike) return null;
    const emit = trigger !== 'auto' || lastTrackedBikeRef.current !== bike.id;
    if (trigger === 'auto') lastTrackedBikeRef.current = bike.id;

    // Anything the in-browser model has no input for goes to the server (see
    // lib/instantEstimate.js for the full list and what enforces each item).
    const blocker = instantBlocker({
      bikeId: bike?.id ?? null,
      hasParts: selectedParts.length > 0,
      hasTyres: frontTire?.id != null || rearTire?.id != null,
      weatherDefault,
      hasPlace: !!location,
    });
    if (trigger === 'auto' && !blocker) {
      const est = await predictQuick({
        bikeId: bike.id,
        riderMassKg: riderKg,
        powerBoostPct: powerBoost,
        massDeltaKg: massChange,
        venueId: venue?.id ?? null,
        venueSurface: venueSurface(venue),
      });
      throwIfAborted(signal);
      if (est.ok) {
        const runEvent = emit
          ? trackSimRun('simulator_page', 'quarter', {
              trigger, engine: 'client-surrogate', bike_id: bike.id, part_count: 0,
            })
          : null;
        const data = {
          et_quarter_s: est.etS,
          trap_speed_kmh: est.trapKmh,
          peak_power_hp: est.peakPowerHp,
          total_mass_kg: est.totalMassKg,
          estimated: true,
          // What the in-browser model assumed (no server block exists for it).
          estimateAssumes: { venueName: venue?.name ?? null, altitudeM: venue?.altitude_m ?? null },
          meta: { ...makeSnap(true), estimated: true },
        };
        runEvent?.success({ et_quarter_s: data.et_quarter_s, trap_speed_kmh: data.trap_speed_kmh });
        return data;
      }
      // est.ok === false → fall through to the server path.
    }

    const runEvent = emit
      ? trackSimRun('simulator_page', 'quarter', {
          trigger, engine: 'server', bike_id: bike?.id ?? null, part_count: selectedParts.length,
        })
      : null;
    try {
      const snap = makeSnap(true);
      const body = baseSimBody({ part_ids: selectedParts.map((p) => p.id) });
      const data = await withRefRecovery(body, async (b) => {
        const res = await fetch(`${API}/api/simulate/quick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(b),
          signal,
        });
        if (!res.ok) {
          const detail = await readDetail(res);
          const err = new Error(
            res.status === 429
              ? detail || 'You are calculating very quickly. Live updates are paused for a few seconds.'
              : detail || `The simulator returned an error (${res.status}). Please try again.`,
          );
          err.status = res.status;
          err.retryAfter = Number(res.headers.get('retry-after')) || null;
          throw err;
        }
        return res.json();
      });
      throwIfAborted(signal);
      runEvent?.success({
        et_quarter_s: data?.et_quarter_s ?? null,
        trap_speed_kmh: data?.trap_speed_kmh ?? null,
      });
      return { ...data, estimated: false, meta: { ...snap, estimated: false } };
    } catch (e) {
      if (e?.name === 'AbortError') runEvent?.cancelled();
      else runEvent?.error(e);
      if (e?.status === 429) {
        setLivePausedUntil(Date.now() + (e.retryAfter || 15) * 1000);
      }
      throw e;
    }
  });

  // Full simulation — job-backed with real RK4 progress. Honours the selected
  // parts exactly like the quick sim (same part_ids, same engine), so the two
  // agree to the millisecond.
  const fullSimTask = useAsyncTask(async (signal, onProgress) => {
    const runEvent = trackSimRun('simulator_page', 'full', {
      bike_id: bike?.id ?? null, part_count: selectedParts.length,
    });
    try {
      const snap = makeSnap(true);
      const body = baseSimBody({ part_ids: selectedParts.map((p) => p.id) });
      const data = await withRefRecovery(body, (b) => simulateJob(b, onProgress, signal));
      throwIfAborted(signal);
      runEvent.success({
        et_quarter_s: data?.et_quarter_s ?? null,
        trap_speed_kmh: data?.trap_speed_kmh ?? null,
      });
      return { ...data, meta: snap };
    } catch (e) {
      if (e?.name === 'AbortError') runEvent.cancelled();
      else runEvent.error(e);
      throw e;
    }
  });

  const topSpeedTask = useAsyncTask(async (signal, onProgress) => {
    const runEvent = trackSimRun('simulator_page', 'topspeed', {
      bike_label: bike?.model_name ?? bike?.model ?? 'unknown',
      bike_id: bike?.id ?? null,
    });
    try {
      const snap = makeSnap(true);
      const body = baseSimBody({ part_ids: selectedParts.map((p) => p.id), include_timeseries: true });
      const data = await withRefRecovery(body, (b) => topspeedJob(b, onProgress, signal));
      throwIfAborted(signal);
      runEvent.success({
        terminal_velocity_kmh: data?.terminal_velocity_kmh ?? null,
        reached_plateau: data?.reached_plateau ?? null,
      });
      return { ...data, meta: snap };
    } catch (e) {
      if (e?.name === 'AbortError') runEvent.cancelled();
      else runEvent.error(e);
      throw e;
    }
  });

  const compareKey = JSON.stringify([keyFull, compareBike?.id ?? null, comparePower, compareMass]);

  const compareTask = useAsyncTask(async (signal, onProgress) => {
    const bBike = compareBike || bike;
    const body = {
      a_bike_id: bike.id != null ? bike.id : undefined,
      a_bike_preset: bike.preset || undefined,
      a_power_boost_pct: powerBoost,
      a_mass_delta_kg: massChange,
      a_rider_mass_kg: riderKg,
      a_part_ids: selectedParts.map((p) => p.id),
      a_front_tire_id: frontTire?.id ?? undefined,
      a_rear_tire_id: rearTire?.id ?? undefined,
      b_bike_id: bBike.id != null ? bBike.id : undefined,
      b_bike_preset: bBike.preset || undefined,
      b_power_boost_pct: comparePower,
      b_mass_delta_kg: compareMass,
      b_rider_mass_kg: riderKg,
      b_part_ids: [],
      ...placeFields(),
      ...weatherFields(),
    };
    const runEvent = trackSimRun('simulator_page', 'compare', {
      bike_id: bike?.id ?? null,
      compare_bike_id: bBike?.id ?? null,
    });
    try {
      const snap = { ...makeSnap(true), compareKey, bBikeName: bikeName(bBike) };
      const data = await withRefRecovery(body, (b) => compareJob(b, onProgress, signal));
      throwIfAborted(signal);
      runEvent.success({
        delta_et_s: data?.delta?.et_s ?? null,
        faster: data?.delta?.faster ?? null,
      });
      return { ...data, meta: snap };
    } catch (e) {
      if (e?.name === 'AbortError') runEvent.cancelled();
      else runEvent.error(e);
      throw e;
    }
  });

  const dragyTask = useAsyncTask(async (signal, _p, file) => {
    const formData = new FormData();
    formData.append('file', file);
    if (bike?.id != null) formData.append('bike_id', bike.id.toString());
    else if (bike?.preset) formData.append('bike_preset', bike.preset);
    const forBike = bike?.id ?? null;
    const res = await fetch(`${API}/api/calibrate/dragy`, { method: 'POST', body: formData, signal });
    if (!res.ok) throw new Error((await readDetail(res)) || `Upload failed (${res.status})`);
    const data = await res.json();
    throwIfAborted(signal);
    if (forBike !== (bikeRef.current?.id ?? null)) throw abortError();
    setUploadResult({ type: 'dragy', bikeId: forBike, ...data });
    return data;
  });

  const dynoTask = useAsyncTask(async (signal, _p, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API}/api/calibrate/dyno`, { method: 'POST', body: formData, signal });
    if (!res.ok) throw new Error((await readDetail(res)) || `Upload failed (${res.status})`);
    const data = await res.json();
    throwIfAborted(signal);
    setUploadResult({ type: 'dyno', ...data });
    return data;
  });

  // Save: always the result's OWN setup, never whatever is selected now. The
  // run is kept in this browser; its timeslip link carries the setup and the
  // conditions the server simulated, so opening it re-runs the same race.
  const saveTask = useAsyncTask(async (_signal, _p, override) => {
    const src = override || saveSourceRef.current;
    if (!src || src.estimated || src.et_quarter_s == null || src.meta?.bikeId == null) return null;
    const m = src.meta;
    const query = timeslipQuery({
      bikeId: m.bikeId,
      venueId: m.venueId,
      riderKg: m.riderKg,
      powerBoost: m.powerBoost,
      massChange: m.massChange,
      partIds: (src.parts_applied || []).map((p) => p.id),
      frontTireId: m.frontTireId,
      rearTireId: m.rearTireId,
      environment: src.environment,
    });
    const stored = storeRun({
      query,
      bikeName: m.bikeName,
      et: src.et_quarter_s,
      trap: src.trap_speed_kmh,
      et60: src.et_60ft_s ?? null,
      eighth: src.et_eighth_s ?? null,
      environment: src.environment || null,
      riderKg: m.riderKg,
      powerBoost: m.powerBoost,
      massChange: m.massChange,
      parts: (src.parts_applied || []).map((p) => [p.brand, p.name].filter(Boolean).join(' ')),
      tyresChanged: m.frontTireId != null || m.rearTireId != null,
    });
    // The timeslip link needs no storage, so a browser that refuses the write
    // (private browsing, storage full) still gets the link; the card says the
    // run was not kept.
    setSavedRun({ query, forKey: m.key, notStored: !stored });
    track('save_run', { bike_id: m.bikeId, surface: 'simulator_page', stored: !!stored });
    return { query };
  });

  // Stable handles (the task objects themselves are new every render).
  const { run: runQuick, stop: stopQuick, reset: resetQuick } = quickTask;
  const { run: runFull, stop: stopFull, reset: resetFull } = fullSimTask;
  const { stop: stopTop, reset: resetTop } = topSpeedTask;
  const { stop: stopCompare, reset: resetCompare } = compareTask;
  const { stop: stopDragy, reset: resetDragy } = dragyTask;
  const { stop: stopSave, reset: resetSave } = saveTask;

  /* ═══════════════ Result derivation ═══════════════ */

  const quickRes =
    quickTask.result && quickTask.result.meta?.bikeId === bike?.id ? quickTask.result : null;
  const fullRes =
    fullSimTask.result && fullSimTask.result.meta?.bikeId === bike?.id ? fullSimTask.result : null;
  const topRes =
    topSpeedTask.result && topSpeedTask.result.meta?.bikeId === bike?.id ? topSpeedTask.result : null;
  const compareRes =
    compareTask.result && compareTask.result.meta?.bikeId === bike?.id ? compareTask.result : null;

  const quickFresh = !!quickRes && quickRes.meta.key === keyFull;
  const fullFresh = !!fullRes && fullRes.meta.key === keyFull;
  const topFresh = !!topRes && topRes.meta.key === keyFull;
  const compareFresh = !!compareRes && compareRes.meta.compareKey === compareKey;

  const exactFull = fullFresh ? normalizeFull(fullRes) : null;
  const headline = exactFull || quickRes;
  const headlineFresh = exactFull ? true : quickFresh;
  const saveable = headline && !headline.estimated && headlineFresh ? headline : null;
  saveSourceRef.current = saveable;
  const savedForHeadline = savedRun && saveable && savedRun.forKey === saveable.meta.key ? savedRun : null;

  /* ═══════════════ Actions ═══════════════ */

  const setMode = useCallback((m) => {
    setModeState(m);
    try { localStorage.setItem(MODE_KEY, m); } catch { /* private mode */ }
  }, []);

  // Stop every in-flight task and drop every result tied to the old bike (F1).
  const changeBike = useCallback((b) => {
    stopQuick(); resetQuick();
    stopFull(); resetFull();
    stopTop(); resetTop();
    stopCompare(); resetCompare();
    stopSave(); resetSave();
    stopDragy(); resetDragy();
    setSavedRun(null);
    setBikeNotice(false);
    setUploadResult((prev) => (prev?.type === 'dragy' ? null : prev));
    setSelectedParts([]);
    setFrontTire(null);
    setRearTire(null);
    setBike(b);
  }, [stopQuick, resetQuick, stopFull, resetFull, stopTop, resetTop, stopCompare, resetCompare,
    stopSave, resetSave, stopDragy, resetDragy]);

  const togglePart = useCallback((part) => {
    setSelectedParts((prev) => {
      if (prev.some((p) => p.id === part.id)) return prev.filter((p) => p.id !== part.id);
      const grp = partSlot(part, catNameRef.current[part.category_id]);
      const kept = grp
        ? prev.filter((p) => partSlot(p, catNameRef.current[p.category_id]) !== grp)
        : prev;
      return [...kept, part];
    });
  }, []);
  const removePart = useCallback((id) => {
    setSelectedParts((prev) => prev.filter((p) => p.id !== id));
  }, []);

  // Slider setters that remember "the user changed the weather by hand".
  const setAmbientTempUser = useCallback((v) => { setEnvTouched(true); setAmbientTemp(v); }, []);
  const setTrackTempUser = useCallback((v) => { setEnvTouched(true); setTrackTemp(v); }, []);
  const setHumidityUser = useCallback((v) => { setEnvTouched(true); setHumidity(v); }, []);
  const setHeadwindUser = useCallback((v) => { setEnvTouched(true); setHeadwind(v); }, []);

  const resetEnv = useCallback(() => {
    setLocation(null);
    setVenue(null);
    setEnvTouched(false);
    setAmbientTemp(DEFAULTS.ambientTemp);
    setTrackTemp(DEFAULTS.trackTemp);
    setHumidity(DEFAULTS.humidity);
    setHeadwind(DEFAULTS.headwind);
  }, []);

  // LocationPicker resolved a place: venue (if it matched one), temperature, humidity.
  const applyLocation = useCallback((env) => {
    setLocation(env);
    setEnvTouched(false);
    if (env?.matched_venue_id != null) {
      const v = venues.find((x) => x.id === env.matched_venue_id);
      setVenue(v || {
        id: env.matched_venue_id,
        name: env.venue_name || env.location_name || 'Venue',
        altitude_m: env.altitude_m ?? null,
      });
    } else {
      setVenue(null);
    }
    // Same bounds as the slider, the share-link parser and the API (-30..60 °C).
    if (env?.temperature_c != null) setAmbientTemp(Math.max(-30, Math.min(60, Math.round(env.temperature_c))));
    if (env?.humidity_pct != null) setHumidity(Math.round(env.humidity_pct));
  }, [venues]);

  // Venue chosen from the plain list in Advanced (not via the location picker).
  const pickVenue = useCallback((v) => {
    setLocation(null);
    setVenue(v && v.id != null ? v : null);
  }, []);

  const resetAll = useCallback(() => {
    setSelectedParts([]);
    setFrontTire(null);
    setRearTire(null);
    setPowerBoost(DEFAULTS.powerBoost);
    setMassChange(DEFAULTS.massChange);
    setRiderKg(DEFAULTS.riderKg);
    resetEnv();
    setCompareBike(null);
    setComparePower(0);
    setCompareMass(0);
    stopFull(); resetFull();
    stopTop(); resetTop();
    stopCompare(); resetCompare();
    setUploadResult(null);
    setSavedRun(null);
  }, [resetEnv, stopFull, resetFull, stopTop, resetTop, stopCompare, resetCompare]);

  const startFullSim = useCallback((opts = {}) => {
    if (!bikeRef.current || fullSimTask.active) return Promise.resolve(undefined);
    if (opts.goTo) setActiveTab(opts.goTo);
    return runFull();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fullSimTask.active, runFull]);

  const startTopSpeed = useCallback(() => {
    if (!bikeRef.current || topSpeedTask.active) return;
    setActiveTab('topspeed');
    topSpeedTask.run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topSpeedTask.active, topSpeedTask.run]);

  const startCompare = useCallback(() => {
    if (!bikeRef.current || compareTask.active) return;
    setActiveTab('compare');
    compareTask.run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [compareTask.active, compareTask.run]);

  const calculateNow = useCallback(() => runQuick('manual'), [runQuick]);

  const goAdvanced = useCallback((tab = null, focus = null) => {
    setMode('advanced');
    if (tab) setActiveTab(tab);
    if (focus) setFocusRequest(focus);
  }, [setMode]);

  const onDragyFile = useCallback((e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    lastDragyFileRef.current = file;
    setUploadResult(null);
    dragyTask.run(file);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dragyTask.run]);
  const onDynoFile = useCallback((e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    lastDynoFileRef.current = file;
    setUploadResult(null);
    dynoTask.run(file);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dynoTask.run]);

  // Share the exact setup (every query key old links used still works).
  const buildShareUrl = useCallback(() => {
    const params = new URLSearchParams();
    if (bike?.id) params.set('bike', String(bike.id));
    if (venue?.id) params.set('venue', String(venue.id));
    if (riderKg !== DEFAULTS.riderKg) params.set('rider', String(riderKg));
    if (powerBoost !== 0) params.set('boost', String(powerBoost));
    if (massChange !== 0) params.set('mass', String(massChange));
    if (selectedParts.length > 0) params.set('parts', selectedParts.map((p) => p.id).join(','));
    if (frontTire?.id != null) params.set('ft', String(frontTire.id));
    if (rearTire?.id != null) params.set('rt', String(rearTire.id));
    if (ambientTemp !== DEFAULTS.ambientTemp) params.set('temp', String(ambientTemp));
    if (trackTemp !== DEFAULTS.trackTemp) params.set('track', String(trackTemp));
    if (humidity !== DEFAULTS.humidity) params.set('hum', String(humidity));
    if (headwind !== DEFAULTS.headwind) params.set('wind', String(headwind));
    return `${window.location.origin}/simulator?${params.toString()}`;
  }, [bike, venue, riderKg, powerBoost, massChange, selectedParts, frontTire, rearTire,
    ambientTemp, trackTemp, humidity, headwind]);

  const copyOrShare = useCallback(async (url, title) => {
    try {
      if (navigator.share) {
        await navigator.share({ title, url });
        return true;
      }
    } catch { /* dismissed — fall through to copy */ }
    try {
      await navigator.clipboard.writeText(url);
      setShareCopied(true);
      setTimeout(() => setShareCopied(false), 2200);
      return true;
    } catch { return false; }
  }, []);

  const shareBuild = useCallback(async () => {
    const ok = await copyOrShare(buildShareUrl(), `MotoQuant | ${bikeName(bike)}`);
    if (ok) track('share_build', { bike_id: bike?.id });
  }, [buildShareUrl, copyOrShare, bike]);

  // "Save and share this run": make the result exact if needed, save it in
  // this browser, then share its timeslip link.
  const saveAndShare = useCallback(async () => {
    let src = saveSourceRef.current;
    if (!src) {
      const full = await startFullSim();
      if (!full) return;
      src = normalizeFull(full);
    }
    const resp = await saveTask.run(src);
    if (resp?.query) {
      await copyOrShare(`${window.location.origin}/timeslip?${resp.query}`, `MotoQuant | ${bikeName(bike)}`);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startFullSim, saveTask.run, copyOrShare, bike]);

  /* ═══════════════ Data loading ═══════════════ */

  // Clear the "waiting for the share link's parts/tyres" gate once nothing is pending.
  const settlePending = useCallback(() => {
    const p = pendingLinkRef.current;
    if (!p || (!p.parts && p.ft == null && p.rt == null)) setLinkPending(false);
  }, []);

  const loadCore = useCallback(async () => {
    coreAbortRef.current?.abort();
    const ctl = new AbortController();
    coreAbortRef.current = ctl;
    setBikesStatus('loading');
    setVenuesStatus('loading');
    setBootError(null);
    setBootProgress(0);
    const tick = () => setBootProgress((v) => Math.min(1, v + 0.5));
    const getJson = async (url) => {
      const res = await fetch(url, { signal: ctl.signal });
      if (!res.ok) throw new Error(`API ${res.status}`);
      return res.json();
    };
    // The bike list is the shared, memoised catalogue (one request per page
    // load, reused by the landing widget and anything else that needs it).
    getBikeCatalog()
      .then((list) => {
        if (ctl.signal.aborted) return;
        setBikes(list);
        if (list.length) setBikesStatus('ready');
        else {
          setBikesStatus('error');
          setBootError('The simulator is running but has no bikes loaded yet. Please try again in a moment.');
        }
      })
      .catch((e) => {
        if (e?.name === 'AbortError') return;
        console.error('bikes load failed', e);
        setBikesStatus('error');
        setBootError('We could not load the bike list. The server may be waking up, which can take up to a minute.');
      })
      .finally(() => { if (!ctl.signal.aborted) tick(); });
    getJson(`${API}/api/venues`)
      .then((d) => { if (!ctl.signal.aborted) { setVenues(d.venues || []); setVenuesStatus('ready'); } })
      .catch((e) => { if (e?.name !== 'AbortError') setVenuesStatus('error'); })
      .finally(() => { if (!ctl.signal.aborted) tick(); });
  }, []);

  // Tyres + part categories: only needed by the Advanced workbench.
  const applyPendingTires = useCallback((list) => {
    const p = pendingLinkRef.current;
    if (!p || (p.ft == null && p.rt == null)) return;
    // A shared link may carry a tyre for the wrong wheel; ignore it.
    const ft = list.find((x) => x.id === p.ft && tyreFitsWheel(x, 'front'));
    const rt = list.find((x) => x.id === p.rt && tyreFitsWheel(x, 'rear'));
    if (ft) setFrontTire(ft);
    if (rt) setRearTire(rt);
    p.ft = null;
    p.rt = null;
  }, []);

  const loadAdvanced = useCallback(async () => {
    setTiresStatus('loading');
    try {
      const [tires, cats] = await Promise.all([
        fetch(`${API}/api/tires?limit=2000`).then((r) => (r.ok ? r.json() : Promise.reject(r.status))),
        fetch(`${API}/api/parts/categories`).then((r) => (r.ok ? r.json() : Promise.reject(r.status))),
      ]);
      const list = tires.tires || [];
      setAllTires(list);
      setCategories(cats.categories || []);
      setTiresStatus('ready');
      applyPendingTires(list);
    } catch (e) {
      console.warn('advanced data load failed', e);
      setTiresStatus('error');
      if (pendingLinkRef.current) { pendingLinkRef.current.ft = null; pendingLinkRef.current.rt = null; }
    } finally {
      settlePending();
    }
  }, [applyPendingTires, settlePending]);

  // Parts: the whole catalogue is fetched ONCE (shared, memoised); which parts
  // fit the current bike is a separate ids-only request, so switching bike
  // costs a few KB. Abortable, with one automatic retry before showing Retry.
  const loadParts = useCallback(async (bikeId) => {
    partsAbortRef.current?.abort();
    const ctl = new AbortController();
    partsAbortRef.current = ctl;
    setPartsStatus('loading');
    setPartsError(null);
    const attempt = () => Promise.all([getPartsCatalog(), getCompatiblePartIds(bikeId, ctl.signal)]);
    try {
      let out;
      try {
        out = await attempt();
      } catch (e) {
        if (e?.name === 'AbortError') throw e;
        await new Promise((r) => setTimeout(r, 1200));
        if (ctl.signal.aborted) return;
        out = await attempt();
      }
      if (ctl.signal.aborted) return;
      const [catalog, ids] = out;
      const fits = new Set(ids);
      setCatalogParts(catalog);
      setCompatIds(fits);
      setPartsBikeId(bikeId);
      setPartsStatus('ready');
      const pending = pendingLinkRef.current;
      if (pending?.parts) {
        const found = [];
        let missing = 0;
        let notFit = 0;
        for (const id of pending.parts) {
          const part = catalog.find((p) => p.id === id);
          if (!part) missing += 1;
          else if (!fits.has(id)) notFit += 1;
          else found.push({ ...part, compatible: true });
        }
        if (found.length) setSelectedParts(found);
        if (missing) addNotice('Some parts in this link are no longer in the catalog and were skipped.');
        if (notFit) addNotice('Some parts in this link do not fit the selected bike and were left out.');
        pending.parts = null;
      }
      setSelectedParts((prev) => prev.filter((p) => fits.has(p.id) || !catalog.some((x) => x.id === p.id)));
    } catch (e) {
      if (e?.name === 'AbortError') return;
      console.warn('parts load failed', e);
      setPartsStatus('error');
      setPartsError('We could not load the parts list.');
      if (pendingLinkRef.current) pendingLinkRef.current.parts = null;
    } finally {
      if (!ctl.signal.aborted) settlePending();
    }
  }, [settlePending, addNotice]);

  /* ═══════════════ Effects ═══════════════ */

  // Mount: mode preference, error handlers, surrogate preload, core data.
  useEffect(() => {
    installErrorHandlers();
    track('page_view', { surface: 'simulator_page' });
    preloadSurrogate();
    let m = 'simple';
    try { if (localStorage.getItem(MODE_KEY) === 'advanced') m = 'advanced'; } catch { /* ignore */ }
    if (linkWantsAdvanced(searchParams)) m = 'advanced';
    setModeState(m);
    setModeReady(true);
    loadCore();
    return () => { coreAbortRef.current?.abort(); partsAbortRef.current?.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Apply a share link / deep link to the state (initial AND on query changes — F2).
  const applyLink = useCallback((sp, initial) => {
    const qsNum = (key, set, min, max) => {
      if (!sp.has(key)) return false;
      const v = parseFloat(sp.get(key) ?? '');
      if (Number.isFinite(v) && v >= min && v <= max) { set(v); return true; }
      return false;
    };
    const hasBikeParam = sp.has('bike') || sp.has('bike_id');
    let target = null;
    let slugMissed = false;
    if (hasBikeParam) {
      const raw = (sp.get('bike') ?? sp.get('bike_id') ?? '').trim();
      if (/^\d+$/.test(raw)) target = bikes.find((b) => b.id === parseInt(raw, 10)) || null;
      else target = resolveBikeSlug(raw, bikes);
      slugMissed = !target;
    }
    if (!target && initial) target = pickDefaultBikeForVariant(bikes, defaultBikeVariant);
    if (target && target.id !== bikeRef.current?.id) changeBike(target);
    if (hasBikeParam) setBikeNotice(slugMissed);

    let venueApplied = false;
    if (sp.has('venue')) {
      const rawVenue = (sp.get('venue') ?? '').trim();
      const v = /^\d+$/.test(rawVenue)
        ? venues.find((x) => x.id === parseInt(rawVenue, 10))
        : resolveVenueSlug(rawVenue, venues); // blog links use names like "mmrt"

      if (v) { setVenue(v); setLocation(null); venueApplied = true; }
      else addNotice('The venue in this link is not available, so the conditions saved in the link are used.');
    }
    qsNum('rider', setRiderKg, 50, 130);
    qsNum('boost', setPowerBoost, -20, 50);
    qsNum('mass', setMassChange, -30, 30);
    const envSet = [
      qsNum('temp', setAmbientTemp, -30, 60),
      qsNum('track', setTrackTemp, 10, 65),
      qsNum('hum', setHumidity, 0, 100),
      qsNum('wind', setHeadwind, -30, 30),
    ].some(Boolean);
    if (envSet) { setShowEnv(true); setEnvTouched(true); setLocation(null); }
    // A timeslip of a run at a place (not a catalog venue) carries that
    // place's altitude and pressure; keep them, or the simulator would re-run
    // at the default venue's altitude and show a different time.
    // Parsed exactly as the timeslip page parses them (lib/runs.js), so the
    // simulator and the slip send the same request.
    const saved = !venueApplied ? timeslipRequest(sp) : null;
    if (saved && saved.altitude_m != null) {
      setVenue(null);
      setLocation({
        _saved: true,
        _label: 'Conditions from the timeslip',
        altitude_m: saved.altitude_m,
        ...(saved.pressure_hpa != null ? { pressure_hpa: saved.pressure_hpa } : {}),
      });
    }

    const partIds = (sp.get('parts') || '').split(',').map((s) => parseInt(s, 10)).filter(Number.isFinite);
    const ft = parseInt(sp.get('ft') ?? '', 10);
    const rt = parseInt(sp.get('rt') ?? '', 10);
    if (partIds.length || Number.isFinite(ft) || Number.isFinite(rt)) {
      pendingLinkRef.current = {
        parts: partIds.length ? partIds : null,
        ft: Number.isFinite(ft) ? ft : null,
        rt: Number.isFinite(rt) ? rt : null,
      };
      setLinkPending(true);
      if (allTiresRef.current.length) applyPendingTires(allTiresRef.current);
      settlePending();
    }
    if (linkWantsAdvanced(sp)) setModeState('advanced');
  }, [bikes, venues, defaultBikeVariant, changeBike, applyPendingTires, settlePending, addNotice]);

  useEffect(() => {
    if (linkAppliedRef.current) return;
    if (bikesStatus !== 'ready' || venuesStatus === 'loading') return;
    linkAppliedRef.current = true;
    lastQsRef.current = qs;
    applyLink(searchParams, true);
    setLinkReady(true);
  }, [bikesStatus, venuesStatus, qs, searchParams, applyLink]);

  useEffect(() => {
    if (!linkAppliedRef.current || qs === lastQsRef.current) return;
    lastQsRef.current = qs;
    applyLink(searchParams, false);
  }, [qs, searchParams, applyLink]);

  // Advanced-only data.
  useEffect(() => {
    if (mode === 'advanced' && modeReady && (tiresStatus === 'idle')) loadAdvanced();
  }, [mode, modeReady, tiresStatus, loadAdvanced]);

  useEffect(() => {
    if (mode !== 'advanced' || !bike?.id) return;
    if (partsBikeId === bike.id && partsStatus === 'ready') return;
    loadParts(bike.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, bike?.id]);

  // Live quick-sim (400 ms debounce). Simple mode is always live.
  const liveActive = mode === 'simple' || liveSim;
  useEffect(() => {
    if (!bike || !linkReady || linkPending || !liveActive) return undefined;
    const wait = livePausedUntil - Date.now();
    if (wait > 0) {
      const t = setTimeout(() => setLivePausedUntil(0), wait + 50);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => runQuick('auto'), 400);
    return () => clearTimeout(t);
  }, [bike, selectedParts, frontTire, rearTire, venue, location, riderKg, powerBoost, massChange,
    ambientTemp, trackTemp, humidity, headwind, liveActive, livePausedUntil, linkReady,
    linkPending, runQuick]);

  // A new run invalidates the previous "Saved" state.
  useEffect(() => { setSavedRun(null); resetSave(); }, [keyFull, resetSave]);

  const clearFocusRequest = useCallback(() => setFocusRequest(null), []);

  // Which op feeds the header progress chip (jobs first, quick last).
  const activeOp = fullSimTask.active
    ? { task: fullSimTask, label: 'Full simulation' }
    : topSpeedTask.active
      ? { task: topSpeedTask, label: 'Top speed' }
      : compareTask.active
        ? { task: compareTask, label: 'Comparing' }
        : quickTask.active && !liveActive
          ? { task: quickTask, label: 'Calculating' }
          : null;

  return {
    // data
    bikes, venues, categories, allParts, allTires, categoryNameById,
    bikesStatus, venuesStatus, bootError, bootProgress, partsStatus, partsError, partsBikeId, tiresStatus,
    reloadCore: loadCore,
    retryParts: () => bike?.id && loadParts(bike.id),
    retryAdvanced: () => { setTiresStatus('idle'); },
    // selections
    bike, selectedParts, frontTire, rearTire, venue, location,
    riderKg, powerBoost, massChange, ambientTemp, trackTemp, humidity, headwind,
    envCustom, showEnv, buildCost,
    setRiderKg, setPowerBoost, setMassChange, setFrontTire, setRearTire, setShowEnv,
    setAmbientTemp: setAmbientTempUser, setTrackTemp: setTrackTempUser,
    setHumidity: setHumidityUser, setHeadwind: setHeadwindUser,
    changeBike, togglePart, removePart, applyLocation, pickVenue, resetEnv, resetAll,
    // view
    mode, modeReady, setMode, activeTab, setActiveTab, liveSim, setLiveSim, liveActive,
    bikeNotice, dismissBikeNotice: () => setBikeNotice(false), notices, dismissNotice,
    focusRequest, clearFocusRequest, goAdvanced, defaultBikeVariant,
    // compare config
    compareBike, setCompareBike, comparePower, setComparePower, compareMass, setCompareMass,
    // tasks + results
    quickTask, fullSimTask, topSpeedTask, compareTask, dragyTask, dynoTask, saveTask,
    quickRes, fullRes, topRes, compareRes,
    quickFresh, fullFresh, topFresh, compareFresh,
    headline, headlineFresh, saveable, savedRun: savedForHeadline, exactFull,
    activeOp, livePausedUntil,
    // actions
    startFullSim, startTopSpeed, startCompare, calculateNow, saveAndShare,
    shareBuild, shareCopied,
    uploadResult, onDragyFile, onDynoFile, lastDragyFileRef, lastDynoFileRef,
    keyFull, keyNoParts,
  };
}
