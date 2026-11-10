'use client';

/**
 * SimulatorWidget — the landing-page calculator (CLARITY v6).
 *
 * A 10-second version of the simulator's Simple mode:
 *   choose a bike -> (optional) rider weight / location -> "Calculate my time".
 * An instant estimate appears as soon as a bike is chosen (computed in the
 * browser by lib/surrogate.js); "Calculate my time" runs the exact server
 * simulation; "Top speed" runs the job-backed top-speed run (Stop-able).
 *
 * Bike chips are resolved to CURRENT catalog ids at runtime by name (ids drift
 * whenever the catalog is reseeded). Nothing is estimated or runnable for a
 * catalog bike until that map has resolved, and a chip that cannot be found is
 * hidden rather than pointing at the wrong bike.
 */

import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { AlertCircle, MapPin, ChevronDown, ArrowRight } from 'lucide-react';
import { environmentOverridesFromLocation } from './LocationPicker';
import { predictQuick, preloadSurrogate } from '../lib/surrogate';
import { instantBlocker, LOCATION_HINT } from '../lib/instantEstimate';
import { API_URL, runJob, getBikeCatalog } from '../lib/api';
import ConditionsLine from './ConditionsLine';
import SimProgress from './SimProgress';
import ResultSentence from './ResultSentence';
import Term from './Term';
import { track, trackSimRun, installErrorHandlers } from '../lib/telemetry';

// Heavy / optional pieces load only when the visitor actually uses them.
const ChatPanel = dynamic(() => import('./ChatPanel'), {
  ssr: false,
  loading: () => <div className="skeleton h-40 w-full rounded-xl" aria-hidden="true" />,
});
const LocationPicker = dynamic(() => import('./LocationPicker'), {
  ssr: false,
  loading: () => <div className="skeleton h-28 w-full rounded-xl" aria-hidden="true" />,
});

// Curated bikes. `match` is the catalog name (year range stripped) used to
// find the CURRENT id at runtime; when several rows share a name the newest
// model year wins. `catalogId` names a row directly (the three hand-validated
// reference bikes are pinned at ids 1-3).
const BIKE_GROUPS = [
  {
    name: 'Indian sport bikes',
    bikes: [
      { label: 'KTM RC 390', match: 'KTM RC 390' },
      { label: 'KTM Duke 390', match: 'KTM Duke 390' },
      { label: 'Yamaha YZF-R15 V4', match: 'Yamaha YZF-R15 V4' },
      { label: 'TVS Apache RR 310', match: 'TVS Apache RR 310' },
      { label: 'Aprilia RS 457', match: 'Aprilia RS 457' },
      { label: 'Suzuki Gixxer SF 250', match: 'Suzuki Gixxer SF 250' },
    ],
  },
  {
    name: 'Indian naked bikes',
    bikes: [
      { label: 'Bajaj Pulsar NS200', match: 'Bajaj Pulsar NS200 BS6' },
      { label: 'Bajaj Pulsar N250', match: 'Bajaj Pulsar N250' },
      { label: 'Bajaj Pulsar NS400Z', match: 'Bajaj Pulsar NS400Z' },
      { label: 'TVS Apache RTR 200 4V', match: 'TVS Apache RTR 200 4V' },
      { label: 'Yamaha MT-15 V2', match: 'Yamaha MT-15 V2' },
      { label: 'Triumph Speed 400', match: 'Triumph Speed 400' },
      { label: 'Husqvarna Svartpilen 401', match: 'Husqvarna Svartpilen 401' },
      { label: 'Hero Karizma XMR 210', match: 'Hero Karizma XMR 210' },
    ],
  },
  {
    name: 'Royal Enfield',
    bikes: [
      { label: 'Continental GT 650', match: 'Royal Enfield Continental GT 650' },
      { label: 'Interceptor 650', match: 'Royal Enfield Interceptor 650' },
      { label: 'Classic 350', match: 'Royal Enfield Classic 350' },
      { label: 'Hunter 350', match: 'Royal Enfield Hunter 350' },
    ],
  },
  {
    name: 'Dream bikes',
    bikes: [
      // The three reference bikes, by catalog id, so they run in the same
      // default conditions as every other bike on the site.
      { label: 'Suzuki GSX-R 1000 K5', catalogId: 1 },
      { label: 'Suzuki Hayabusa Gen1', catalogId: 3 },
      { label: 'Yamaha YZF-R1 (4C8)', catalogId: 2 },
      { label: 'Suzuki Hayabusa (2021)', match: 'Suzuki Hayabusa' },
      { label: 'BMW S 1000 RR', match: 'BMW S 1000 RR' },
      { label: 'Kawasaki Ninja H2', match: 'Kawasaki Ninja H2' },
      { label: 'Ducati Panigale V4R', match: 'Ducati Panigale V4R' },
      { label: 'Kawasaki Z H2', match: 'Kawasaki Z H2' },
    ],
  },
];

const YEAR_SUFFIX = /\s*\(\d{4}(?:\s*-\s*\d{0,4})?\)\s*$/;
const normName = (b) =>
  `${b.manufacturer ?? ''} ${b.model ?? ''}`.replace(YEAR_SUFFIX, '').trim().toLowerCase();

// label -> {id, cc, hp} using the live catalog. Exact (year-stripped) name
// match; newest model year wins on ties. Unmatched entries are simply absent.
function resolveCatalog(bikes) {
  const byName = new Map();
  for (const b of bikes) {
    const k = normName(b);
    const prev = byName.get(k);
    if (!prev || (b.year ?? 0) > (prev.year ?? 0)) byName.set(k, b);
  }
  const byId = new Map(bikes.map((b) => [b.id, b]));
  const out = {};
  for (const g of BIKE_GROUPS) {
    for (const e of g.bikes) {
      const hit = e.catalogId != null ? byId.get(e.catalogId) : byName.get(e.match.toLowerCase());
      if (hit) {
        out[e.label] = {
          id: hit.id,
          cc: hit.displacement_cc != null ? Math.round(hit.displacement_cc) : null,
          hp: hit.peak_power_hp != null ? Math.round(hit.peak_power_hp) : null,
        };
      }
    }
  }
  return out;
}

const cleanName = (n) => (n ? String(n).replace(YEAR_SUFFIX, '') : n);

function friendlyError(e) {
  const msg = String(e?.message || '');
  if (e instanceof TypeError || /failed to fetch|networkerror|load failed/i.test(msg)) {
    return "We couldn't reach the simulator. Check your connection and try again.";
  }
  if (/lost|restart|connection/i.test(msg)) return msg;
  return 'Something went wrong while calculating. Please try again in a moment.';
}

function locationName(loc) {
  return loc?.venue_name || loc?.location_name || loc?._label || 'Your location';
}

function Slider({ id, label, hint, value, min, max, onChange, format, tone }) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="field-label !mb-0">
          {label}
        </label>
        <output
          htmlFor={id}
          className={`font-mono text-sm tabular-nums ${tone ?? 'text-white'}`}
        >
          {format(value)}
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuetext={format(value)}
        className="mt-2 block h-11 w-full cursor-pointer accent-accent"
      />
      {hint && <p className="field-hint !mt-0">{hint}</p>}
    </div>
  );
}

export default function SimulatorWidget() {
  const [widgetMode, setWidgetMode] = useState('sim'); // 'sim' | 'chat'
  const [activeTab, setActiveTab] = useState(0);
  const [selectedBike, setSelectedBike] = useState(BIKE_GROUPS[0].bikes[0]);
  const [riderKg, setRiderKg] = useState(75);
  const [powerBoost, setPowerBoost] = useState(0);
  const [massChange, setMassChange] = useState(0);
  const [moreOpen, setMoreOpen] = useState(false);
  const [location, setLocation] = useState(null);
  const [locationOpen, setLocationOpen] = useState(false);

  // Last exact run: { kind: 'quarter'|'topspeed', data, sig }. Shown only
  // while the inputs still match `sig`, so a stale number is never presented.
  const [run, setRun] = useState(null);
  const [runningKind, setRunningKind] = useState(null);
  const [error, setError] = useState(null);
  const [prog, setProg] = useState(null);
  const abortRef = useRef(null);
  const rootRef = useRef(null);

  // Catalog resolution state: 'loading' | 'ready' | 'error'
  const [catalog, setCatalog] = useState({ state: 'loading', map: {} });
  const [armed, setArmed] = useState(false); // user has reached/used the widget
  const [estimate, setEstimate] = useState(null);
  const [estimatePending, setEstimatePending] = useState(false);

  const loading = runningKind != null;

  // ── Catalog -> current ids (limit=2000 covers the full 534-bike catalog) ──
  const loadCatalog = useCallback(() => {
    let cancelled = false;
    setCatalog({ state: 'loading', map: {} });
    getBikeCatalog()
      .then((bikes) => {
        if (!cancelled) setCatalog({ state: 'ready', map: resolveCatalog(bikes || []) });
      })
      .catch(() => {
        if (!cancelled) setCatalog({ state: 'error', map: {} });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    installErrorHandlers();
    track('widget_view', { surface: 'landing_widget' });
    return loadCatalog();
  }, [loadCatalog]);

  // Warm the in-browser surrogate only once the widget is on screen or used —
  // not on every page load.
  useEffect(() => {
    const el = rootRef.current;
    if (!el || armed) return undefined;
    if (typeof IntersectionObserver === 'undefined') {
      setArmed(true);
      return undefined;
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((en) => en.isIntersecting)) {
          setArmed(true);
          io.disconnect();
        }
      },
      { rootMargin: '200px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [armed]);

  useEffect(() => {
    if (armed) preloadSurrogate();
  }, [armed]);

  // Chips appear once the catalog resolves their ids.
  const groups = useMemo(
    () =>
      BIKE_GROUPS.map((g) => ({
        name: g.name,
        bikes: g.bikes
          .map((e) => {
            const r = catalog.map[e.label];
            return r ? { ...e, ...r } : null;
          })
          .filter(Boolean),
      })).filter((g) => g.bikes.length > 0),
    [catalog.map],
  );

  // Keep the selected bike pointing at its resolved record (id for catalog).
  const bike = useMemo(() => {
    const r = catalog.map[selectedBike.label];
    return r ? { ...selectedBike, ...r } : null;
  }, [selectedBike, catalog.map]);

  const bikeReady = bike != null && bike.id != null;
  const bikeId = bike ? bike.id : null;
  const env = useMemo(() => environmentOverridesFromLocation(location), [location]);

  const sig = JSON.stringify([bike?.id ?? null, riderKg, powerBoost, massChange, env]);

  // ── Live in-browser estimate ───────────────────────────────────────────
  // Only for catalog bikes, only after the id map resolved, and only while NO
  // place is chosen: the in-browser model has no input for a place's weather
  // or surface, so a chosen place always goes to the exact server simulation
  // (see lib/instantEstimate.js for the full list of what forces that).
  useEffect(() => {
    let cancelled = false;
    const canEstimate =
      armed &&
      catalog.state === 'ready' &&
      bike &&
      bike.id != null &&
      !instantBlocker({ bikeId: bike.id, hasParts: false, hasTyres: false, weatherDefault: true, hasPlace: !!location });
    if (!canEstimate) {
      setEstimate(null);
      setEstimatePending(false);
      return undefined;
    }
    setEstimatePending(true);
    predictQuick({
      bikeId: bike.id,
      riderMassKg: riderKg,
      powerBoostPct: powerBoost,
      massDeltaKg: massChange,
      venueId: null,
    }).then((r) => {
      if (cancelled) return;
      setEstimate(r.ok ? r : null);
      setEstimatePending(false);
    });
    return () => {
      cancelled = true;
    };
  }, [armed, catalog.state, bike, riderKg, powerBoost, massChange, location, env]);

  function stopSim() {
    abortRef.current?.abort(); // runJob also cancels the job server-side
    setRunningKind(null);
    setProg(null);
  }

  async function runSim(kind) {
    if (!bikeReady) return;
    setRunningKind(kind);
    setError(null);
    setRun(null);
    const controller = new AbortController();
    abortRef.current = controller;
    const mode = kind === 'topspeed' ? 'topspeed' : 'quarter';
    const runEvent = trackSimRun('landing_widget', mode, {
      bike_label: bike.label,
      bike_id: bike.id ?? null,
      power_boost_pct: powerBoost,
      mass_delta_kg: massChange,
      rider_kg: riderKg,
    });
    try {
      const body = {
        rider_mass_kg: riderKg,
        power_boost_pct: powerBoost,
        mass_delta_kg: massChange,
        ...env,
      };
      body.bike_id = bike.id;

      let data;
      if (kind === 'topspeed') {
        data = await runJob('topspeed', body, {
          onProgress: setProg,
          signal: controller.signal,
          fallbackPath: '/api/simulate/top-speed',
        });
      } else {
        const res = await fetch(`${API_URL}/api/simulate/quick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`API error ${res.status}`);
        data = await res.json();
      }
      setRun({ kind, data, sig });
      runEvent.success({
        engine: 'server',
        et_quarter_s: data?.et_quarter_s ?? null,
        trap_speed_kmh: data?.trap_speed_kmh ?? null,
        terminal_velocity_kmh: data?.terminal_velocity_kmh ?? null,
        reached_plateau: data?.reached_plateau ?? null,
      });
    } catch (e) {
      if (e?.name === 'AbortError') {
        runEvent.cancelled();
        return;
      }
      setError(friendlyError(e));
      runEvent.error(e);
    } finally {
      setRunningKind(null);
      setProg(null);
    }
  }

  const exact = run && run.sig === sig ? run : null;
  const placeName = location ? locationName(location) : null;
  const catalogBlocked = catalog.state !== 'ready';

  // With a place chosen there is no instant estimate (see above), so work the
  // exact time out for it straight away — once per distinct setup, after the
  // sliders have settled — instead of leaving the card empty.
  const autoSigRef = useRef(null);
  useEffect(() => {
    if (!location || !bikeReady || catalogBlocked || loading || exact) return undefined;
    if (autoSigRef.current === sig) return undefined;
    const t = setTimeout(() => {
      autoSigRef.current = sig;
      runSim('quarter');
    }, 600);
    return () => clearTimeout(t);
    // runSim is recreated each render; `sig` captures every input it reads.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sig, location, bikeReady, loading, exact]);

  // Conditions are worded from the server's echoed `environment` block (exact
  // results) or from what the in-browser estimate assumes — never restated
  // from what this page sent (see ConditionsLine).
  const changeLocation = () => {
    setLocationOpen(true);
    document.getElementById('widget-location')?.scrollIntoView?.({ block: 'center', behavior: 'smooth' });
  };

  const simulatorHref = (() => {
    const p = new URLSearchParams();
    if (bikeId != null) p.set('bike_id', String(bikeId));
    if (riderKg !== 75) p.set('rider', String(riderKg));
    if (powerBoost) p.set('boost', String(powerBoost));
    if (massChange) p.set('mass', String(massChange));
    if (env.venue_id != null) p.set('venue', String(env.venue_id));
    const q = p.toString();
    return q ? `/simulator?${q}` : '/simulator';
  })();

    return (
    <div
      ref={rootRef}
      onPointerDownCapture={() => setArmed(true)}
      onFocusCapture={() => setArmed(true)}
      className="card relative mx-auto w-full max-w-2xl overflow-hidden p-5 sm:p-6"
    >
      {loading && (
        <div className="absolute inset-x-0 top-0 z-20">
          <SimProgress active edge progress={prog?.progress ?? null} />
        </div>
      )}

      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <h2 className="font-display text-lg font-semibold text-white md:text-xl">
            Try it now
          </h2>
          <p className="text-sm text-white/60">Choose a bike and get its quarter-mile time.</p>
        </div>

        <div className="seg-control shrink-0" role="tablist" aria-label="Widget mode">
          {[
            { id: 'sim', label: 'Calculator' },
            { id: 'chat', label: 'Ask in plain English' },
          ].map(({ id, label }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={widgetMode === id}
              onClick={() => setWidgetMode(id)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Ask mode ─────────────────────────────────────────────────── */}
      {widgetMode === 'chat' && (
        <div className="mb-2">
          <ChatPanel apiUrl={API_URL} />
        </div>
      )}

      {/* ── Calculator mode ──────────────────────────────────────────── */}
      {widgetMode === 'sim' && (
        <>
          <div className="mb-6">
            <div className="mb-2 flex items-center gap-2">
              <span className="step-badge" aria-hidden="true">1</span>
              <h3 className="field-label !mb-0" id="widget-bike-heading">Choose a bike</h3>
            </div>

            {catalog.state === 'error' && (
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-signal-stage/30 bg-signal-stage/10 p-3 text-sm text-signal-stage">
                <span>We couldn&rsquo;t load the bike list.</span>
                <button type="button" onClick={loadCatalog} className="btn-ghost btn-sm">
                  Try again
                </button>
              </div>
            )}

            {catalog.state === 'loading' && groups.length === 0 && (
              <div className="skeleton h-28 w-full rounded-xl" aria-hidden="true" />
            )}

            {groups.length > 0 && (
              <>
                <div
                  className="mb-3 flex gap-1.5 overflow-x-auto pb-1"
                  role="tablist"
                  aria-label="Bike groups"
                >
                  {groups.map((g, idx) => (
                    <button
                      key={g.name}
                      type="button"
                      role="tab"
                      aria-selected={activeTab === idx}
                      onClick={() => setActiveTab(idx)}
                      className={`h-11 shrink-0 whitespace-nowrap rounded-lg border px-3.5 text-sm font-medium transition-colors ${
                        activeTab === idx
                          ? 'border-accent bg-accent/10 text-white'
                          : 'border-white/10 bg-asphalt-3 text-white/70 hover:border-white/25 hover:text-white'
                      }`}
                    >
                      {g.name}
                    </button>
                  ))}
                </div>

                <div
                  className="grid grid-cols-2 gap-2 sm:grid-cols-3"
                  role="group"
                  aria-labelledby="widget-bike-heading"
                >
                  {(groups[Math.min(activeTab, groups.length - 1)]?.bikes ?? []).map((b) => {
                    const isSelected = b.label === selectedBike.label;
                    return (
                      <button
                        key={b.label}
                        type="button"
                        aria-pressed={isSelected}
                        onClick={() => setSelectedBike(b)}
                        className={`min-h-[56px] rounded-lg border p-2.5 text-left transition-colors ${
                          isSelected
                            ? 'border-accent bg-accent/10'
                            : 'border-white/10 bg-asphalt-3 hover:border-white/25'
                        }`}
                      >
                        <span className="block text-sm font-semibold leading-tight text-white">
                          {b.label}
                        </span>
                        {(b.cc != null || b.hp != null) && (
                          <span className="mt-1 block text-xs text-white/60">
                            {[b.cc != null ? `${b.cc} cc` : null, b.hp != null ? `${b.hp} hp` : null]
                              .filter(Boolean)
                              .join(' · ')}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
                <p className="mt-2 text-sm text-white/60">
                  Don&rsquo;t see yours?{' '}
                  <Link
                    href="/simulator"
                    className="text-accent underline underline-offset-2 hover:text-accent-bright"
                  >
                    Search all 534 bikes
                  </Link>
                </p>
              </>
            )}
          </div>

          <div className="mb-5">
            <div className="mb-2 flex items-center gap-2">
              <span className="step-badge" aria-hidden="true">2</span>
              <h3 className="field-label !mb-0">You and the conditions</h3>
            </div>
            <Slider
              id="widget-rider"
              label="Rider weight with gear"
              value={riderKg}
              min={50}
              max={130}
              onChange={setRiderKg}
              format={(v) => `${v} kg`}
            />
          </div>

          {/* More options */}
          <div className="mb-5">
            <button
              type="button"
              onClick={() => setMoreOpen((v) => !v)}
              aria-expanded={moreOpen}
              aria-controls="widget-more"
              className="flex min-h-[44px] items-center gap-1.5 text-sm font-medium text-white/75 hover:text-white"
            >
              <ChevronDown
                size={16}
                aria-hidden="true"
                className={`transition-transform ${moreOpen ? 'rotate-180' : ''}`}
              />
              More options
            </button>
            {moreOpen && (
              <div id="widget-more" className="mt-2 grid gap-5 sm:grid-cols-2">
                <Slider
                  id="widget-power"
                  label="Engine power change"
                  hint="More or less power than stock."
                  value={powerBoost}
                  min={-20}
                  max={50}
                  onChange={setPowerBoost}
                  format={(v) => `${v > 0 ? '+' : ''}${v}%`}
                  tone={powerBoost > 0 ? 'text-signal-go' : powerBoost < 0 ? 'text-signal-foul' : undefined}
                />
                <Slider
                  id="widget-mass"
                  label="Weight added or removed"
                  hint="Parts, luggage, a lighter battery."
                  value={massChange}
                  min={-30}
                  max={30}
                  onChange={setMassChange}
                  format={(v) => `${v > 0 ? '+' : ''}${v} kg`}
                  tone={massChange > 0 ? 'text-signal-foul' : massChange < 0 ? 'text-signal-go' : undefined}
                />
              </div>
            )}
          </div>

          {/* Location */}
          <div className="mb-6" id="widget-location">
            <button
              type="button"
              onClick={() => setLocationOpen((v) => !v)}
              aria-expanded={locationOpen}
              className="flex min-h-[48px] w-full items-center justify-between gap-3 rounded-lg border border-white/10 bg-asphalt-3 px-3 py-2.5 text-left transition-colors hover:border-white/25"
            >
              <span className="flex min-w-0 items-center gap-2 text-sm">
                <MapPin size={16} className="shrink-0 text-white/60" aria-hidden="true" />
                <span className="truncate text-white/85">
                  {location ? placeName : 'Where are you racing? (optional)'}
                </span>
              </span>
              <span className="shrink-0 text-sm font-medium text-accent">
                {locationOpen ? 'Close' : location ? 'Change' : 'Add'}
              </span>
            </button>
            <p className="field-hint">{LOCATION_HINT}</p>
            {locationOpen && (
              <div className="mt-2">
                <LocationPicker
                  value={location}
                  onResolved={(e) => {
                    setLocation(e);
                    setLocationOpen(false);
                  }}
                  onCleared={() => {
                    setLocation(null);
                    setLocationOpen(false);
                  }}
                  compact
                />
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => (runningKind === 'quarter' ? stopSim() : runSim('quarter'))}
              disabled={(loading && runningKind !== 'quarter') || !bikeReady || catalogBlocked}
              className={`w-full ${runningKind === 'quarter' ? 'btn-running' : 'btn-primary'}`}
            >
              {runningKind === 'quarter' ? 'Stop' : 'Calculate my time'}
            </button>
            <button
              type="button"
              onClick={() => (runningKind === 'topspeed' ? stopSim() : runSim('topspeed'))}
              disabled={(loading && runningKind !== 'topspeed') || !bikeReady || catalogBlocked}
              className={`w-full ${runningKind === 'topspeed' ? 'btn-running' : 'btn-ghost'}`}
            >
              {runningKind === 'topspeed'
                ? `Stop${prog?.progress != null ? ` (${Math.round(prog.progress * 100)}%)` : ''}`
                : 'Top speed'}
            </button>
          </div>

          {error && (
            <div
              role="alert"
              className="mt-4 flex items-start gap-2 rounded-lg border border-signal-foul/30 bg-signal-foul/10 p-3 text-sm text-signal-foul"
            >
              <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
              {error}
            </div>
          )}

          {/* ── Result ─────────────────────────────────────────────── */}
          <div className="mt-6" aria-live="polite">
            {exact?.kind === 'quarter' && (
              <QuarterResult data={exact.data} riderKg={riderKg} placeName={placeName} placeLabel={placeName} onChange={changeLocation} />
            )}
            {exact?.kind === 'topspeed' && (
              <TopSpeedResult data={exact.data} riderKg={riderKg} placeName={placeName} placeLabel={placeName} onChange={changeLocation} />
            )}
            {!exact && loading && runningKind === 'quarter' && (
              <p role="status" className="text-sm text-white/70">Calculating exact time…</p>
            )}
            {!exact && !loading && estimate && (
              <EstimateResult
                estimate={estimate}
                bikeName={bike.label}
                riderKg={riderKg}
                placeName={placeName}
                estimateVenue={env.venue_id != null ? placeName : null}
                                onChange={changeLocation}
              />
            )}
            {!exact && !loading && !estimate && estimatePending && (
              <div className="skeleton h-28 w-full rounded-xl" aria-hidden="true" />
            )}
            {!exact && !loading && !estimate && !estimatePending && bikeReady && !catalogBlocked && (
              <p className="text-sm text-white/60">
                Press <strong className="font-semibold text-white/80">Calculate my time</strong> to see
                the result for {bike.label}.
              </p>
            )}
          </div>

          <div className="mt-4">
            <Link
              href={simulatorHref}
              className="inline-flex min-h-[44px] items-center gap-1.5 text-sm font-medium text-accent hover:text-accent-bright"
            >
              Open in the full simulator <ArrowRight size={16} aria-hidden="true" />
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Result blocks ──────────────────────────────────────────────────────────

function BigNumber({ value, unit }) {
  return (
    <p className="font-display font-bold tabular-nums text-accent">
      <span className="text-6xl md:text-7xl">{value}</span>
      <span className="ml-2 text-xl font-medium text-white/60">{unit}</span>
    </p>
  );
}

function EstimateResult({ estimate, bikeName, riderKg, placeName, estimateVenue, estimateAltitudeM, onChange }) {
  return (
    <div className="rounded-xl border border-white/10 bg-asphalt-3 p-4 sm:p-5">
      <BigNumber value={estimate.etS.toFixed(2)} unit="s" />
      <ResultSentence
        className="mt-2"
        bikeName={bikeName}
        riderKg={riderKg}
        et={estimate.etS}
        trapKmh={estimate.trapKmh}
        venueName={placeName}
        estimated
      />
      <ConditionsLine
        className="mt-3 text-sm text-white/60"
        estimate={{ venueName: estimateVenue, altitudeM: estimateAltitudeM }}
        onChange={onChange}
      />
      <p className="mt-2 text-sm text-white/60">
        Press <strong className="font-semibold text-white/80">Calculate my time</strong> for the
        exact result with launch and halfway splits.
      </p>
    </div>
  );
}

function QuarterResult({ data, riderKg, placeName, placeLabel, onChange }) {
  const has = (v) => typeof v === 'number' && Number.isFinite(v);
  return (
    <div className="rounded-xl border border-white/10 bg-asphalt-3 p-4 sm:p-5">
      <BigNumber value={data.et_quarter_s.toFixed(2)} unit="s" />
      <ResultSentence
        className="mt-2"
        bikeName={cleanName(data.bike_name)}
        riderKg={riderKg}
        et={data.et_quarter_s}
        trapKmh={data.trap_speed_kmh}
        venueName={placeName}
      />
      <ConditionsLine className="mt-3 text-sm text-white/60" env={data.environment} placeLabel={placeLabel} onChange={onChange} />
      <div className="mt-3">
        {has(data.et_60ft_s) && (
          <div className="stat-row">
            <span><Term k="sixty">First 60 ft (launch)</Term></span>
            <span>{data.et_60ft_s.toFixed(2)} s</span>
          </div>
        )}
        {has(data.et_eighth_s) && (
          <div className="stat-row">
            <span><Term k="eighth">Halfway (⅛ mile)</Term></span>
            <span>{data.et_eighth_s.toFixed(2)} s</span>
          </div>
        )}
        {has(data.trap_speed_kmh) && (
          <div className="stat-row">
            <span><Term k="trap">Finish-line speed</Term></span>
            <span>{data.trap_speed_kmh.toFixed(0)} km/h</span>
          </div>
        )}
        {has(data.peak_power_hp) && (
          <div className="stat-row">
            <span>Power</span>
            <span>{data.peak_power_hp.toFixed(0)} hp</span>
          </div>
        )}
        {has(data.total_mass_kg) && (
          <div className="stat-row">
            <span>Total weight with rider</span>
            <span>{data.total_mass_kg.toFixed(0)} kg</span>
          </div>
        )}
      </div>
    </div>
  );
}

function TopSpeedResult({ data, riderKg, placeName, placeLabel, onChange }) {
  const has = (v) => typeof v === 'number' && Number.isFinite(v);
  if (!has(data.terminal_velocity_kmh)) return null;
  return (
    <div className="rounded-xl border border-white/10 bg-asphalt-3 p-4 sm:p-5">
      <BigNumber value={data.terminal_velocity_kmh.toFixed(0)} unit="km/h" />
      <p className="mt-2 text-base leading-relaxed text-white/80">
        {data.bike_name ? `${cleanName(data.bike_name)} with a ${Math.round(riderKg)} kg rider` : 'This bike'}{' '}
        tops out at about{' '}
        <strong className="font-semibold text-white">
          {data.terminal_velocity_kmh.toFixed(0)} km/h
        </strong>
        {has(data.terminal_velocity_mph) ? ` (${data.terminal_velocity_mph.toFixed(0)} mph)` : ''}
        {placeName ? ` at ${placeName}` : ''}.
        {data.reached_plateau === false
          ? ' It was still gaining speed slowly when the run ended, so the true top speed may be a little higher.'
          : ''}
      </p>
      <ConditionsLine className="mt-3 text-sm text-white/60" env={data.environment} placeLabel={placeLabel} onChange={onChange} />
      <div className="mt-3">
        {has(data.time_to_terminal_s) && (
          <div className="stat-row">
            <span>Time to get there</span>
            <span>{data.time_to_terminal_s.toFixed(0)} s</span>
          </div>
        )}
        {has(data.distance_to_terminal_m) && (
          <div className="stat-row">
            <span>Distance needed</span>
            <span>
              {data.distance_to_terminal_m >= 1000
                ? `${(data.distance_to_terminal_m / 1000).toFixed(1)} km`
                : `${Math.round(data.distance_to_terminal_m)} m`}
            </span>
          </div>
        )}
        {data.terminal_gear != null && (
          <div className="stat-row">
            <span>Gear at top speed</span>
            <span>{data.terminal_gear}</span>
          </div>
        )}
        {has(data.terminal_rpm) && (
          <div className="stat-row">
            <span>Engine speed</span>
            <span>{Math.round(data.terminal_rpm).toLocaleString('en-IN')} rpm</span>
          </div>
        )}
      </div>
    </div>
  );
}
