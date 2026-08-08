'use client';

/**
 * SimulatorWidget — the landing-page live simulator (IGNITION v5 skin).
 *
 * v5 re-voice ONLY: surfaces are .card / .input-base tokens, the run
 * buttons use the sitewide .btn-* vocabulary, and results render as the
 * signature mini .timeslip. ALL logic is preserved verbatim from v3:
 * BIKE_CATEGORIES + the bikeIdMap catalog-ID self-heal, quick sim via
 * /api/simulate/quick, the job-backed top-speed run with Stop, the
 * bike_preset vs bike_id split, telemetry, and the Sim/Chat mode toggle.
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, AlertCircle, MapPin, MessageSquare, Gauge } from 'lucide-react';
import LocationPicker, { environmentOverridesFromLocation } from './LocationPicker';
import ChatPanel from './ChatPanel';
import { API_URL, runJob } from '../lib/api';
import SimProgress from './SimProgress';
import ScoreboardDigits from './ScoreboardDigits';
import { track, trackSimRun, installErrorHandlers } from '../lib/telemetry';

// Curated bike list — popular India-market machines first, then global
// dream bikes. Each entry uses bike_id (catalog primary key) so we can
// hit the full physics catalog rather than the legacy bike_preset path
// that only knows three reference bikes. IDs validated against
// motoquant.db on April 24, 2026; if a re-seed renumbers the catalog
// these IDs need re-verification (see scripts/validation_sweep.py for
// model-name lookup by manufacturer + substring).
const BIKE_CATEGORIES = [
  {
    name: 'Indian Sport',
    bikes: [
      { id: 178, label: 'KTM RC 390',           cc: '373cc', hp: 43 },
      { id: 177, label: 'KTM Duke 390',         cc: '373cc', hp: 43 },
      { id: 192, label: 'Yamaha YZF-R15 V4',    cc: '155cc', hp: 18 },
      { id: 186, label: 'TVS Apache RR 310',    cc: '312cc', hp: 34 },
      { id: 303, label: 'Aprilia RS 457',       cc: '457cc', hp: 48 },
      { id: 268, label: 'Suzuki Gixxer SF 250', cc: '249cc', hp: 27 },
    ],
  },
  {
    name: 'Indian Naked',
    bikes: [
      { id: 251, label: 'Bajaj Pulsar NS200',     cc: '200cc', hp: 24 },
      { id: 254, label: 'Bajaj Pulsar N250',      cc: '249cc', hp: 25 },
      { id: 256, label: 'Bajaj Pulsar NS400Z',    cc: '373cc', hp: 40 },
      { id: 187, label: 'TVS Apache RTR 200 4V',  cc: '197cc', hp: 20 },
      { id: 193, label: 'Yamaha MT-15 V2',        cc: '155cc', hp: 18 },
      { id: 201, label: 'Triumph Speed 400',      cc: '398cc', hp: 40 },
      { id: 203, label: 'Husqvarna Svartpilen 401', cc: '373cc', hp: 43 },
      { id: 275, label: 'Hero Karizma XMR 210',   cc: '210cc', hp: 25 },
    ],
  },
  {
    name: 'Royal Enfield',
    bikes: [
      { id: 211, label: 'Continental GT 650', cc: '648cc', hp: 47 },
      { id: 210, label: 'Interceptor 650',    cc: '648cc', hp: 47 },
      { id: 277, label: 'Classic 350',        cc: '349cc', hp: 20 },
      { id: 279, label: 'Hunter 350',         cc: '349cc', hp: 20 },
    ],
  },
  {
    name: 'Dream Bikes',
    bikes: [
      // Reference bikes — exact-validated against magazine timeslips
      { id: null, presetId: 'gsxr1000_k5',   label: 'Suzuki GSX-R 1000 K5', cc: '999cc', hp: 178 },
      { id: null, presetId: 'hayabusa_gen1', label: 'Suzuki Hayabusa Gen1', cc: '1299cc', hp: 175 },
      { id: null, presetId: 'yzfr1_4c8',     label: 'Yamaha YZF-R1 (4C8)',  cc: '998cc', hp: 180 },
      // Catalog dream bikes
      { id: 123, label: 'Suzuki Hayabusa (2021)',  cc: '1340cc', hp: 190 },
      { id: 161, label: 'BMW S 1000 RR',           cc: '999cc',  hp: 210 },
      { id: 156, label: 'Kawasaki Ninja H2',       cc: '998cc',  hp: 310 },
      { id: 233, label: 'Ducati Panigale V4R',     cc: '998cc',  hp: 221 },
      { id: 228, label: 'Kawasaki Z H2',           cc: '998cc',  hp: 197 },
    ],
  },
];

// Animated counter component
function AnimatedCounter({ target, decimals = 3 }) {
  const [count, setCount] = useState(0);
  const intervalRef = useRef(null);

  useEffect(() => {
    const duration = 1200;
    const frameRate = 60;
    const frames = duration / (1000 / frameRate);
    const increment = target / frames;
    let current = 0;

    intervalRef.current = setInterval(() => {
      current += increment;
      if (current >= target) {
        setCount(target);
        clearInterval(intervalRef.current);
      } else {
        setCount(current);
      }
    }, 1000 / frameRate);

    return () => clearInterval(intervalRef.current);
  }, [target]);

  return count.toFixed(decimals);
}

// ─── Main widget ──────────────────────────────────────────────────────────────

// ── SegEt — the user's own ET on the strip timing board ──────────────
// The sim result is the user's personal timeslip, so the ET counts up on
// the timing-board numerals (ScoreboardDigits — seven-segment again in
// v5, default signal orange: the live number is the moving part).
function SegEt({ target }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let raf;
    const t0 = performance.now();
    const dur = 900;
    const tick = (now) => {
      const t = Math.min(1, (now - t0) / dur);
      const e = 1 - Math.pow(1 - t, 3);
      setVal(target * e);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target]);
  return (
    <span className="inline-flex items-baseline gap-1.5 justify-center">
      <span className="flex sm:hidden"><ScoreboardDigits value={val.toFixed(3)} h={26} label={`${target}s`} /></span>
      <span className="hidden sm:flex"><ScoreboardDigits value={val.toFixed(3)} h={34} label={`${target}s`} /></span>
      <span className="font-mono text-white/40 text-sm sm:text-base">s</span>
    </span>
  );
}

export default function SimulatorWidget() {
  // Default to "Indian Sport" tab + KTM RC 390 (one of the most-recognized
  // Indian-market sport bikes; mid-pack performance so it's a good demo
  // bike that doesn't oversell or undersell the simulator).
  const [widgetMode, setWidgetMode] = useState('sim'); // 'sim' | 'chat'
  const [activeTab, setActiveTab] = useState(0);
  const [selectedBike, setSelectedBike] = useState(BIKE_CATEGORIES[0].bikes[0]);
  const [riderKg, setRiderKg] = useState(75);
  const [powerBoost, setPowerBoost] = useState(0);
  const [massChange, setMassChange] = useState(0);
  const [location, setLocation] = useState(null);
  const [locationOpen, setLocationOpen] = useState(false);
  // Sim mode — 'quarter' (¼-mile ET + trap + splits) or 'topspeed' (terminal
  // velocity + time-to-terminal + gear + RPM). Each mode hits a different
  // FastAPI endpoint and renders a different result panel below.
  const [simMode, setSimMode] = useState('quarter');
  const [result, setResult] = useState(null);          // quarter-mile result
  const [topSpeedResult, setTopSpeedResult] = useState(null);  // top-speed result
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [prog, setProg] = useState(null); // {progress, stage} from the jobs poller
  const abortRef = useRef(null);

  function stopSim() {
    abortRef.current?.abort(); // runJob also cancels the job server-side
    setLoading(false);
    setProg(null);
  }
  // CRITICAL: production DB IDs drift over time as the catalog is reseeded.
  // Hardcoded IDs in BIKE_CATEGORIES were stale — id 192 was 'YZF-R15 V4'
  // when the list was authored but is now 'Aprilia ...' on prod (verified
  // via /api/bikes/{id}). To stay robust we fetch the catalog on mount and
  // resolve each labelled bike to its CURRENT id by manufacturer + model
  // name match. Keys are the .label string from BIKE_CATEGORIES, values
  // are catalog ids. While this map is empty (initial render OR if the
  // fetch fails) we fall back to the hardcoded id, which at worst sims
  // the wrong bike instead of erroring out.
  const [bikeIdMap, setBikeIdMap] = useState({});

  useEffect(() => {
    installErrorHandlers();
    track('widget_view', { surface: 'landing_widget' });
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_URL}/api/bikes?limit=500`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(data => {
        if (cancelled) return;
        const bikes = data.bikes || [];
        const map = {};
        BIKE_CATEGORIES.forEach(cat => {
          cat.bikes.forEach(entry => {
            if (entry.presetId) return; // reference bikes use preset, no id lookup
            // Match strategy: case-insensitive substring match on
            //   "{manufacturer} {model_name}"  vs  entry.label
            // Tolerates the API returning slight name variations
            // (e.g. "YZF-R15 V4 (2021-)" vs label "Yamaha YZF-R15 V4").
            const labelLower = entry.label.toLowerCase();
            // The /api/bikes endpoint returns each row with `manufacturer`
            // and `model` (NOT `model_name` — that's the DB column name,
            // not the API field). Verified Apr 29 via /api/bikes?limit=5
            // — the prod API exposes: id, manufacturer, model, year,
            // category, displacement_cc, peak_power_hp, dry_mass_kg.
            const found = bikes.find(b => {
              const full = `${b.manufacturer ?? ''} ${b.model ?? ''}`.toLowerCase();
              if (full.includes(labelLower)) return true;
              // Fallback: drop the manufacturer prefix from the label
              // and try matching just the model fragment.
              const tokens = labelLower.split(/\s+/);
              const modelOnly = tokens.slice(1).join(' ');
              return modelOnly && full.includes(modelOnly);
            });
            if (found) map[entry.label] = found.id;
          });
        });
        setBikeIdMap(map);
      })
      .catch(() => { /* keep map empty; fall back to hardcoded ids */ });
    return () => { cancelled = true; };
  }, []);

  async function runSim(mode = simMode) {
    setSimMode(mode);
    setLoading(true);
    setError(null);
    // Clear BOTH results when starting a new sim. Without this, the
    // previous mode's panel was still mounted briefly during the loading
    // state — and on slow networks the user could see the stale panel
    // sitting next to the loading dots of the new mode for seconds.
    setResult(null);
    setTopSpeedResult(null);
    const controller = new AbortController();
    abortRef.current = controller;
    // One handle → guaranteed start/end pair on the same surface + mode.
    const runEvent = trackSimRun('landing_widget', mode, {
      bike_label: selectedBike?.label ?? 'unknown',
      bike_id: selectedBike?.id ?? null,
      bike_preset: selectedBike?.presetId ?? null,
      power_boost_pct: powerBoost,
      mass_delta_kg: massChange,
      rider_kg: riderKg,
    });
    try {
      const envOverrides = environmentOverridesFromLocation(location);
      const body = {
        rider_mass_kg: riderKg,
        power_boost_pct: powerBoost,
        mass_delta_kg: massChange,
        ...envOverrides,
      };
      // Reference bikes use bike_preset (legacy path that hits hand-built
      // BikeConfig from defaults.py); catalog bikes use bike_id resolved
      // from the API at mount time (bikeIdMap). If the resolution map
      // hasn't loaded yet OR the label couldn't be matched, fall back
      // to the hardcoded id from BIKE_CATEGORIES.
      if (selectedBike.presetId) {
        body.bike_preset = selectedBike.presetId;
      } else {
        body.bike_id = bikeIdMap[selectedBike.label] ?? selectedBike.id;
      }
      // Different endpoint per mode:
      //   quarter  → /api/simulate/quick (ET + trap + 60ft / ⅛-mile splits)
      //   topspeed → /api/simulate/top-speed (terminal velocity + plateau
      //              detection + gear + RPM at terminal)
      let data;
      if (mode === 'topspeed') {
        // Background job — the bar tracks real engine progress through the
        // terminal-velocity run (falls back to the sync route on old backends).
        data = await runJob('topspeed', body, {
          onProgress: setProg,
          signal: controller.signal,
          fallbackPath: '/api/simulate/top-speed',
        });
      } else {
        // Quick sim is ~50 ms server-side — a single synchronous request;
        // the staged bar covers network / cold-start waits.
        const res = await fetch(`${API_URL}/api/simulate/quick`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
          signal: controller.signal,
        });
        if (!res.ok) {
          const msg = await res.text();
          throw new Error(`API error ${res.status}: ${msg}`);
        }
        data = await res.json();
      }
      if (mode === 'quarter') setResult(data);
      else setTopSpeedResult(data);
      runEvent.success({
        et_quarter_s: data?.et_quarter_s ?? null,
        trap_speed_kmh: data?.trap_speed_kmh ?? null,
        terminal_velocity_kmh: data?.terminal_velocity_kmh ?? null,
        reached_plateau: data?.reached_plateau ?? null,
      });
    } catch (e) {
      if (e?.name === 'AbortError') {
        runEvent.cancelled(); // user pressed Stop — neither success nor error
        return;
      }
      setError(e.message);
      runEvent.error(e);
    } finally {
      setLoading(false);
      setProg(null);
    }
  }

  return (
    <div className="card relative mx-auto w-full max-w-2xl overflow-hidden rounded-2xl p-5 sm:p-6">
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute top-0 left-1 right-1 z-20"
          >
            <SimProgress active edge progress={prog?.progress ?? null} />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative z-10 mb-6 flex items-center justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-display font-semibold text-lg md:text-xl text-white">
            Live simulator
          </h3>
          <p className="label-mono mt-1">Real physics · runs in seconds</p>
        </div>

        {/* Mode toggle — Simulate / Chat */}
        <div className="flex shrink-0 items-center gap-0.5 rounded-lg border border-white/[0.12] bg-asphalt-3 p-0.5">
          {[
            { id: 'sim', icon: Gauge, label: 'Sim' },
            { id: 'chat', icon: MessageSquare, label: 'Chat' },
          ].map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setWidgetMode(id)}
              className={`flex h-9 items-center gap-1.5 rounded-md px-3 font-mono text-[11px] uppercase tracking-[0.15em] transition-colors ${
                widgetMode === id
                  ? 'bg-asphalt-4 text-white'
                  : 'text-white/50 hover:text-white/80'
              }`}
            >
              <Icon size={12} aria-hidden="true" />
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Chat mode ────────────────────────────────────────────────────── */}
      {widgetMode === 'chat' && (
        <div className="relative z-10 mb-6">
          <ChatPanel apiUrl={API_URL} />
        </div>
      )}

      {/* ── Sim mode ─────────────────────────────────────────────────────── */}
      {widgetMode === 'sim' && (
      <>

      {/* Bike selector — category tabs + chip grid */}
      <div className="relative z-10 mb-6">
        <div className="mb-3 flex items-center justify-between gap-2">
          <label className="label-mono">Select bike</label>
          <span className="truncate font-mono text-[10px] tabular-nums text-white/30">
            {selectedBike.label} · {selectedBike.cc} · {selectedBike.hp} hp
          </span>
        </div>

        {/* Category tabs */}
        <div className="scrollbar-thin mb-3 flex gap-1.5 overflow-x-auto">
          {BIKE_CATEGORIES.map((cat, idx) => (
            <button
              key={cat.name}
              onClick={() => setActiveTab(idx)}
              className={`h-10 shrink-0 whitespace-nowrap rounded border px-3 font-mono text-[11px] uppercase tracking-[0.15em] transition-colors ${
                activeTab === idx
                  ? 'border-white/30 bg-asphalt-4 text-white'
                  : 'border-white/[0.08] bg-asphalt-3/60 text-white/50 hover:border-white/20 hover:text-white/80'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Bike chip grid for active tab */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-2.5">
          {BIKE_CATEGORIES[activeTab].bikes.map((b) => {
            const key = b.presetId || `id${b.id}`;
            const isSelected =
              (b.presetId && selectedBike.presetId === b.presetId) ||
              (b.id != null && selectedBike.id === b.id);
            return (
              <button
                key={key}
                onClick={() => setSelectedBike(b)}
                className={`min-h-[52px] rounded-lg border p-2.5 text-left transition-colors sm:p-3 ${
                  isSelected
                    ? 'border-white/45 bg-white/[0.07]'
                    : 'border-white/[0.08] bg-asphalt-3/50 hover:border-white/20 hover:bg-asphalt-3'
                }`}
              >
                <div className="text-xs font-semibold leading-tight text-white sm:text-sm">
                  {b.label}
                </div>
                <div className="mt-1.5 font-mono text-[10px] tabular-nums text-white/40">
                  {b.cc} · {b.hp} hp
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Sliders */}
      <div className="relative z-10 mb-8 grid grid-cols-1 gap-5 sm:grid-cols-3 sm:gap-4">
        {[
          {
            label: 'Rider weight',
            value: riderKg,
            onChange: setRiderKg,
            min: 50,
            max: 130,
            format: v => `${v} kg`,
          },
          {
            // Range matches the full simulator page (-20..+50%) so the
            // landing widget and /simulator agree on what a "build" can do.
            label: 'Power boost',
            value: powerBoost,
            onChange: setPowerBoost,
            min: -20,
            max: 50,
            format: v => `${v > 0 ? '+' : ''}${v}%`,
            // Semantic colour: positive boost = green (faster ET),
            // negative = red (slower), zero = neutral white.
            valueColor:
              powerBoost > 0 ? 'text-signal-go'
              : powerBoost < 0 ? 'text-signal-foul'
              : 'text-white',
          },
          {
            // Range matches the full simulator page (-30..+30 kg).
            label: 'Mass change',
            value: massChange,
            onChange: setMassChange,
            min: -30,
            max: 30,
            format: v => `${v > 0 ? '+' : ''}${v} kg`,
            // Mass added = red (slower), mass reduced = green (faster),
            // zero = neutral. Inverse of power-boost direction (since
            // adding kg hurts ET while adding hp helps it).
            valueColor:
              massChange > 0 ? 'text-signal-foul'
              : massChange < 0 ? 'text-signal-go'
              : 'text-white',
          },
        ].map((slider, idx) => (
          <div key={idx} className="space-y-2">
            <label className="label-mono block">
              {slider.label}
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={slider.min}
                max={slider.max}
                value={slider.value}
                onChange={e => slider.onChange(Number(e.target.value))}
                className="h-6 flex-1 cursor-pointer accent-white"
              />
            </div>
            <div className={`text-right font-mono text-sm tabular-nums transition-colors ${slider.valueColor ?? 'text-white'}`}>
              {slider.format(slider.value)}
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        .scrollbar-thin::-webkit-scrollbar { height: 4px; }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
        }
      `}</style>

      {/* Location picker */}
      <div className="relative z-10 mb-6">
        <button
          type="button"
          onClick={() => setLocationOpen(v => !v)}
          className="flex min-h-[44px] w-full items-center justify-between rounded-lg border border-white/[0.08] bg-asphalt-3/60 px-3 py-2.5 text-left transition-colors hover:border-white/25"
        >
          <div className="flex min-w-0 flex-1 items-center gap-2 text-sm">
            <MapPin size={14} className="shrink-0 text-white/45" aria-hidden="true" />
            {location ? (
              <span className="truncate font-mono text-white/80">
                {location.venue_name || location.location_name || location._label}
                {location.density_altitude_m != null && (
                  <span className="ml-2 text-xs tabular-nums text-white/50">
                    DA {Math.round(location.density_altitude_m)} m
                  </span>
                )}
              </span>
            ) : (
              <span className="font-mono text-white/50">Race location (optional)</span>
            )}
          </div>
          <span className="label-mono ml-2 shrink-0">
            {locationOpen ? 'CLOSE' : location ? 'CHANGE' : 'ADD'}
          </span>
        </button>

        <AnimatePresence>
          {locationOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2 }}
              className="mt-2 overflow-hidden"
            >
              <LocationPicker
                value={location}
                onResolved={(env) => { setLocation(env); setLocationOpen(false); }}
                onCleared={() => { setLocation(null); setLocationOpen(false); }}
                compact
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="relative z-10 grid grid-cols-1 gap-3 sm:grid-cols-2">
        <button
          onClick={() => (loading && simMode === 'quarter' ? stopSim() : runSim('quarter'))}
          disabled={loading && simMode !== 'quarter'}
          className={[
            'w-full',
            loading && simMode === 'quarter'
              ? 'btn-running'
              : simMode === 'quarter' ? 'btn-primary' : 'btn-ghost',
          ].join(' ')}
        >
          {loading && simMode === 'quarter' ? (
            <span className="font-mono tabular-nums">■ Stop</span>
          ) : (
            <>
              <Zap size={15} aria-hidden="true" />
              <span>Quarter-mile ET</span>
            </>
          )}
        </button>

        <button
          onClick={() => (loading && simMode === 'topspeed' ? stopSim() : runSim('topspeed'))}
          disabled={loading && simMode !== 'topspeed'}
          className={[
            'w-full',
            loading && simMode === 'topspeed'
              ? 'btn-running'
              : simMode === 'topspeed' ? 'btn-primary' : 'btn-ghost',
          ].join(' ')}
        >
          {loading && simMode === 'topspeed' ? (
            <span className="font-mono tabular-nums">
              ■ Stop{prog?.progress != null ? ` — ${Math.round(prog.progress * 100)}%` : ''}
            </span>
          ) : (
            <>
              <Gauge size={15} aria-hidden="true" />
              <span>Top speed stats</span>
            </>
          )}
        </button>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="relative z-10 mt-4 flex items-center gap-2 rounded-lg border border-signal-foul/30 bg-signal-foul/10 p-3 text-sm text-signal-foul"
          >
            <AlertCircle size={16} aria-hidden="true" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Quarter-mile result — the mini timeslip ─────────────────── */}
      <AnimatePresence>
        {simMode === 'quarter' && result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.4 }}
            className="relative z-10 mt-8"
          >
            <div className="timeslip">
              <div className="flex items-center justify-between gap-2 pb-2">
                <span className="label-mono">Quarter-mile · Official slip</span>
                <span className="label-mono">402 m · 1320 ft</span>
              </div>

              <div className="border-b border-dashed border-white/10 py-4 text-center">
                <p className="label-mono mb-2">Elapsed time</p>
                <SegEt target={result.et_quarter_s} />
              </div>

              <div className="timeslip-row">
                <span className="text-white/45">60 FT</span>
                <span className="text-white">{(result.et_60ft_s ?? 0).toFixed(3)} s</span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">⅛ MILE</span>
                <span className="text-white">{(result.et_eighth_s ?? 0).toFixed(3)} s</span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">¼ MILE</span>
                <span className="font-bold text-white">{(result.et_quarter_s ?? 0).toFixed(3)} s</span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">TRAP SPEED</span>
                <span className="text-white">
                  <AnimatedCounter target={result.trap_speed_kmh} decimals={1} /> km/h
                </span>
              </div>
              <div className="timeslip-row">
                <span className="shrink-0 text-white/45">BIKE</span>
                {/* Full catalog name — CSS-truncated, never string-mangled
                    (the old slice(-2) turned "Suzuki GSX-R 1000 K5" into
                    "1000 K5"). */}
                <span className="min-w-0 truncate text-right text-white/85" title={result.bike_name}>
                  {result.bike_name}
                </span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">PEAK POWER</span>
                <span className="text-white">{result.peak_power_hp.toFixed(0)} hp</span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Top-Speed result panel ──────────────────────────────────
          Different KPIs for top-speed mode: terminal velocity, time +
          distance to plateau, terminal gear/RPM/power. Renders only
          when simMode === 'topspeed' and topSpeedResult is in state. */}
      <AnimatePresence>
        {simMode === 'topspeed' && topSpeedResult && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.4 }}
            className="relative z-10 mt-8"
          >
            <div className="timeslip">
              <div className="flex items-center justify-between gap-2 pb-2">
                <span className="label-mono">Top speed · Official slip</span>
                {topSpeedResult.reached_plateau ? (
                  <span className="chip chip-go">Plateau reached</span>
                ) : (
                  <span className="chip chip-stage">Limited</span>
                )}
              </div>

              <div className="border-b border-dashed border-white/10 py-4 text-center">
                <p className="label-mono mb-2">Terminal velocity</p>
                <p className="font-mono text-4xl font-bold tabular-nums text-white sm:text-5xl">
                  <AnimatedCounter target={topSpeedResult.terminal_velocity_kmh ?? 0} decimals={1} />
                  <span className="ml-1.5 text-sm font-medium text-white/40">km/h</span>
                </p>
                {!topSpeedResult.reached_plateau && (
                  <p className="mt-2 font-mono text-[11px] text-white/45">
                    gearing or wind limited
                  </p>
                )}
              </div>

              <div className="timeslip-row">
                <span className="text-white/45">TIME</span>
                <span className="text-white">
                  {topSpeedResult.time_to_terminal_s?.toFixed(1) ?? '—'} s
                </span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">DISTANCE</span>
                <span className="text-white">
                  {topSpeedResult.distance_to_terminal_m == null
                    ? '—'
                    : topSpeedResult.distance_to_terminal_m >= 1000
                      ? (topSpeedResult.distance_to_terminal_m / 1000).toFixed(2)
                      : Math.round(topSpeedResult.distance_to_terminal_m)}
                  {' '}{topSpeedResult.distance_to_terminal_m >= 1000 ? 'km' : 'm'}
                </span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">MPH</span>
                <span className="text-white">
                  {topSpeedResult.terminal_velocity_mph?.toFixed(1) ?? '—'}
                </span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">GEAR</span>
                <span className="text-white">{topSpeedResult.terminal_gear ?? '—'}</span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">RPM</span>
                <span className="text-white">
                  {topSpeedResult.terminal_rpm?.toLocaleString('en-US') ?? '—'}
                </span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">POWER</span>
                <span className="text-white">
                  {topSpeedResult.terminal_power_hp?.toFixed(0) ?? '—'} hp
                </span>
              </div>
              <div className="timeslip-row">
                <span className="shrink-0 text-white/45">BIKE</span>
                <span className="min-w-0 truncate text-right text-white/85" title={topSpeedResult.bike_name}>
                  {topSpeedResult.bike_name}
                </span>
              </div>
              <div className="timeslip-row">
                <span className="text-white/45">PEAK POWER</span>
                <span className="text-white">
                  {topSpeedResult.peak_power_hp?.toFixed(0) ?? '—'} hp
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* end sim mode */}
      </>
      )}

      <p className="relative z-10 mt-6 text-center text-xs text-white/30">
        First-principles RK4 physics · 15 sub-models · 1 ms timestep
      </p>
    </div>
  );
}
