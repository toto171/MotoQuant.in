'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, AlertCircle, MapPin, MessageSquare, Gauge } from 'lucide-react';
import LocationPicker, { environmentOverridesFromLocation } from './LocationPicker';
import ChatPanel from './ChatPanel';
import { API_URL, runJob } from '../lib/api';
import SimProgress from './SimProgress';
import ScoreboardDigits from './ScoreboardDigits';
import { track, installErrorHandlers } from '../lib/telemetry';

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
// ETs render on ScoreboardDigits everywhere (stats strip, telemetry
// ELAPSED, reference baselines); the sim result is the user's personal
// timeslip, so it counts up on the same seven-segment board.
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
    <span className="inline-flex items-end gap-1.5 justify-center">
      <span className="flex sm:hidden"><ScoreboardDigits value={val.toFixed(3)} h={30} label={`${target}s`} /></span>
      <span className="hidden sm:flex"><ScoreboardDigits value={val.toFixed(3)} h={42} label={`${target}s`} /></span>
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
    track('sim_run_start', {
      surface: 'landing_widget',
      mode,
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
      track('sim_run_success', {
        surface: 'landing_widget',
        mode,
        bike_label: selectedBike?.label ?? 'unknown',
        et_quarter_s: data?.et_quarter_s ?? null,
        trap_speed_kmh: data?.trap_speed_kmh ?? null,
        terminal_velocity_kmh: data?.terminal_velocity_kmh ?? null,
        reached_plateau: data?.reached_plateau ?? null,
      });
    } catch (e) {
      if (e?.name === 'AbortError') return; // user pressed Stop
      setError(e.message);
      track('sim_run_error', {
        surface: 'landing_widget',
        mode,
        bike_label: selectedBike?.label ?? 'unknown',
        error: String(e?.message ?? e).slice(0, 200),
      });
    } finally {
      setLoading(false);
      setProg(null);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="relative bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-2xl p-5 sm:p-8 max-w-2xl mx-auto overflow-hidden"
    >
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

      <div className="flex items-center justify-between mb-6 relative z-10">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <motion.div whileHover={{ scale: 1.1 }} transition={{ type: 'spring', stiffness: 400 }}>
            <Zap className="text-[#FF5E1F]" size={20} />
          </motion.div>
          <span className="bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
            Live Simulator
          </span>
        </h3>

        {/* Mode toggle — Simulate / Chat */}
        <div className="flex items-center gap-0.5 bg-white/[0.04] rounded-lg p-0.5 border border-white/10">
          {[
            { id: 'sim', icon: Gauge, label: 'Sim' },
            { id: 'chat', icon: MessageSquare, label: 'Chat' },
          ].map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setWidgetMode(id)}
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
                widgetMode === id
                  ? 'bg-[#FF5E1F] text-white shadow-sm'
                  : 'text-white/50 hover:text-white/80'
              }`}
            >
              <Icon size={12} />
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
      <div className="mb-6 relative z-10">
        <div className="flex items-center justify-between mb-3">
          <label className="text-[10px] font-mono text-white/45 uppercase tracking-[0.25em]">
            Select Bike
          </label>
          <span className="text-[10px] font-mono text-white/30">
            {selectedBike.label} · {selectedBike.cc} · {selectedBike.hp} hp
          </span>
        </div>

        {/* Category tabs */}
        <div className="flex gap-1 sm:gap-2 mb-3 overflow-x-auto scrollbar-thin">
          {BIKE_CATEGORIES.map((cat, idx) => (
            <button
              key={cat.name}
              onClick={() => setActiveTab(idx)}
              className={`shrink-0 px-3 py-1.5 rounded-md text-xs font-semibold transition-all whitespace-nowrap ${
                activeTab === idx
                  ? 'bg-[#FF5E1F] text-white shadow-[0_0_15px_rgba(255,94,31,0.3)]'
                  : 'bg-white/[0.04] text-white/60 hover:bg-white/[0.08] hover:text-white/90'
              }`}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Bike chip grid for active tab */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 sm:gap-2.5">
          {BIKE_CATEGORIES[activeTab].bikes.map((b) => {
            const key = b.presetId || `id${b.id}`;
            const isSelected =
              (b.presetId && selectedBike.presetId === b.presetId) ||
              (b.id != null && selectedBike.id === b.id);
            return (
              <motion.button
                key={key}
                onClick={() => setSelectedBike(b)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`relative p-2.5 sm:p-3 rounded-xl border transition-all duration-300 text-left group ${
                  isSelected
                    ? 'bg-white/[0.08] border-[#FF5E1F] shadow-[0_0_20px_rgba(255,94,31,0.2)]'
                    : 'bg-white/[0.02] border-white/5 hover:bg-white/[0.05] hover:border-white/10'
                }`}
              >
                <div className="font-semibold text-xs sm:text-sm leading-tight text-white">
                  {/* Strip the manufacturer prefix on small chips for tighter layout */}
                  {b.label}
                </div>
                <div className="text-[10px] text-white/40 mt-1.5 group-hover:text-white/60 transition-colors">
                  {b.cc} · {b.hp} hp
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Sliders */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 sm:gap-4 mb-8 relative z-10">
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
            label: 'Power boost',
            value: powerBoost,
            onChange: setPowerBoost,
            min: -10,
            max: 30,
            format: v => `${v > 0 ? '+' : ''}${v}%`,
            // Semantic colour: positive boost = green (faster ET),
            // negative = red (slower), zero = neutral white.
            valueColor:
              powerBoost > 0 ? 'text-[#00FFB2]'
              : powerBoost < 0 ? 'text-[#FF6B6B]'
              : 'text-white',
          },
          {
            label: 'Mass change',
            value: massChange,
            onChange: setMassChange,
            min: -15,
            max: 15,
            format: v => `${v > 0 ? '+' : ''}${v} kg`,
            // Mass added = red (slower), mass reduced = green (faster),
            // zero = neutral. Inverse of power-boost direction (since
            // adding kg hurts ET while adding hp helps it).
            valueColor:
              massChange > 0 ? 'text-[#FF6B6B]'
              : massChange < 0 ? 'text-[#00FFB2]'
              : 'text-white',
          },
        ].map((slider, idx) => (
          <div key={idx} className="space-y-2">
            <label className="block text-[10px] font-mono text-white/45 uppercase tracking-[0.25em]">
              {slider.label}
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={slider.min}
                max={slider.max}
                value={slider.value}
                onChange={e => slider.onChange(Number(e.target.value))}
                className="flex-1 h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-[#FF5E1F] slider-thumb"
              />
            </div>
            <div className={`text-sm font-mono text-right transition-colors ${slider.valueColor ?? 'text-white'}`}>
              {slider.format(slider.value)}
            </div>
          </div>
        ))}
      </div>

      <style jsx>{`
        input[type='range']::-webkit-slider-thumb {
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: linear-gradient(135deg, #FF5E1F, #FF7A00);
          cursor: pointer;
          box-shadow: 0 0 20px rgba(255, 94, 31, 0.5);
          transition: box-shadow 0.2s;
        }
        input[type='range']::-webkit-slider-thumb:hover {
          box-shadow: 0 0 30px rgba(255, 94, 31, 0.8);
        }
        input[type='range']::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: linear-gradient(135deg, #FF5E1F, #FF7A00);
          cursor: pointer;
          border: none;
          box-shadow: 0 0 20px rgba(255, 94, 31, 0.5);
        }
        input[type='range']::-moz-range-thumb:hover {
          box-shadow: 0 0 30px rgba(255, 94, 31, 0.8);
        }
        .scrollbar-thin::-webkit-scrollbar { height: 4px; }
        .scrollbar-thin::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
        }
      `}</style>

      {/* Location picker */}
      <div className="mb-6 relative z-10">
        <button
          type="button"
          onClick={() => setLocationOpen(v => !v)}
          className="w-full flex items-center justify-between px-3 py-2 rounded-lg border border-white/10 hover:border-brand-orange/40 bg-black/20 text-left transition-colors"
        >
          <div className="flex items-center gap-2 text-sm min-w-0 flex-1">
            <MapPin size={14} className="text-brand-orange shrink-0" />
            {location ? (
              <span className="font-mono text-white/80 truncate">
                {location.venue_name || location.location_name || location._label}
                {location.density_altitude_m != null && (
                  <span className="ml-2 text-brand-accent text-xs tabular-nums">
                    DA {Math.round(location.density_altitude_m)} m
                  </span>
                )}
              </span>
            ) : (
              <span className="font-mono text-white/50">Race location (optional)</span>
            )}
          </div>
          <span className="text-[10px] font-mono text-white/40 ml-2 shrink-0">
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

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 relative z-10">
        <motion.button
          onClick={() => (loading && simMode === 'quarter' ? stopSim() : runSim('quarter'))}
          disabled={loading && simMode !== 'quarter'}
          whileHover={{ scale: loading ? 1 : 1.02 }}
          whileTap={{ scale: loading ? 1 : 0.98 }}
          className={[
            'relative py-3.5 rounded-xl font-semibold text-sm sm:text-[0.95rem] transition-all flex items-center justify-center gap-2 group overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed',
            simMode === 'quarter'
              ? 'bg-gradient-to-r from-[#FF5E1F] to-[#FF7A00] text-white shadow-[0_0_30px_rgba(255,94,31,0.35)] hover:shadow-[0_0_45px_rgba(255,94,31,0.5)]'
              : 'bg-white/[0.04] border border-white/10 text-white/85 hover:bg-white/[0.08] hover:border-[#FF5E1F]/40',
          ].join(' ')}
        >
          {loading && simMode === 'quarter' ? (
            <span className="tabular-nums">■ Stop</span>
          ) : (
            <>
              <Zap size={15} />
              <span>Quarter-Mile ET</span>
            </>
          )}
        </motion.button>

        <motion.button
          onClick={() => (loading && simMode === 'topspeed' ? stopSim() : runSim('topspeed'))}
          disabled={loading && simMode !== 'topspeed'}
          whileHover={{ scale: loading ? 1 : 1.02 }}
          whileTap={{ scale: loading ? 1 : 0.98 }}
          className={[
            'relative py-3.5 rounded-xl font-semibold text-sm sm:text-[0.95rem] transition-all flex items-center justify-center gap-2 group overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed',
            simMode === 'topspeed'
              ? 'bg-gradient-to-r from-[#FF5E1F] to-[#FF7A00] text-white shadow-[0_0_30px_rgba(255,94,31,0.35)] hover:shadow-[0_0_45px_rgba(255,94,31,0.5)]'
              : 'bg-white/[0.04] border border-white/10 text-white/85 hover:bg-white/[0.08] hover:border-[#FF5E1F]/40',
          ].join(' ')}
        >
          {loading && simMode === 'topspeed' ? (
            <span className="tabular-nums">
              ■ Stop{prog?.progress != null ? ` — ${Math.round(prog.progress * 100)}%` : ''}
            </span>
          ) : (
            <>
              <Gauge size={15} />
              <span>Top Speed Stats</span>
            </>
          )}
        </motion.button>
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 p-3 bg-brand-red/10 border border-brand-red/30 rounded-lg text-brand-red text-sm flex items-center gap-2 relative z-10"
          >
            <AlertCircle size={16} />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {simMode === 'quarter' && result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.4 }}
            className="mt-8 space-y-4 relative z-10"
          >
            <div className="grid grid-cols-2 gap-4">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-6 text-center backdrop-blur"
              >
                <p className="text-[10px] font-mono text-white/45 mb-2 uppercase tracking-[0.25em]">
                  Quarter-Mile ET
                </p>
                <div className="flex justify-center">
                  <SegEt target={result.et_quarter_s} />
                </div>
              </motion.div>

              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-6 text-center backdrop-blur"
              >
                <p className="text-[10px] font-mono text-white/45 mb-2 uppercase tracking-[0.25em]">
                  Trap Speed
                </p>
                <p className="text-3xl sm:text-5xl font-mono font-bold text-white">
                  <AnimatedCounter target={result.trap_speed_kmh} decimals={1} />
                </p>
                <p className="text-xs text-white/40 mt-2">km/h</p>
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-6 backdrop-blur"
            >
              <div className="flex items-center justify-between mb-4">
                <p className="text-[10px] font-mono text-white/45 uppercase tracking-[0.25em]">Split Timeline</p>
                <p className="text-[10px] font-mono text-white/30 tabular-nums">
                  402 m · 1320 ft
                </p>
              </div>
              {(() => {
                const splits = [
                  { label: '0 ft',    val: 0,                       distM: 0 },
                  { label: '60 ft',   val: result.et_60ft_s ?? 0,   distM: 18.3 },
                  { label: '⅛ mile',  val: result.et_eighth_s ?? 0, distM: 201 },
                  { label: '¼ mile',  val: result.et_quarter_s ?? 0,distM: 402 },
                ];
                const totalT = splits[3].val || 1;
                return (
                  <div className="relative">
                    {/* Progress track: full width, rendered behind the
                        4 milestone cards. The orange fill width is
                        always 100 % at the end (the last marker IS the
                        finish line), but the gradient stops are
                        positioned by relative time so the eye reads the
                        pacing — narrow gaps = quick splits, wide gaps
                        = slow splits. */}
                    <div className="absolute left-3 right-3 top-[18px] h-[3px] rounded-full bg-white/10 overflow-hidden">
                      <motion.div
                        initial={{ scaleX: 0 }}
                        animate={{ scaleX: 1 }}
                        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
                        style={{ transformOrigin: 'left' }}
                        className="h-full bg-gradient-to-r from-[#FF5E1F] via-[#FF8F57] to-[#FFD089]"
                      />
                    </div>

                    <div className="grid grid-cols-4 gap-1 sm:gap-2 relative">
                      {splits.map((s, idx) => {
                        const pct = totalT > 0 ? Math.round((s.val / totalT) * 100) : 0;
                        return (
                          <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 + idx * 0.08, duration: 0.4 }}
                            className="flex flex-col items-center text-center"
                          >
                            {/* Milestone dot — sits ON the progress track */}
                            <div className="w-[14px] h-[14px] sm:w-[18px] sm:h-[18px] rounded-full bg-[#FF5E1F] border-2 border-black shadow-[0_0_18px_rgba(255,94,31,0.6)] mb-2.5" />
                            {/* Distance label */}
                            <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-white/45 mb-0.5">
                              {s.label}
                            </p>
                            {/* Big time value */}
                            <p className="text-sm sm:text-base font-mono font-bold text-white tabular-nums leading-none">
                              {s.val === 0 ? '0.000' : s.val.toFixed(3)}
                              <span className="text-white/40 text-[10px] sm:text-xs ml-0.5">s</span>
                            </p>
                            {/* Pace tick (% of total ET) */}
                            <p className="text-[9px] sm:text-[10px] font-mono text-[#FF8F57]/70 tabular-nums mt-1">
                              {pct}%
                            </p>
                          </motion.div>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}
            </motion.div>

            <div className="grid grid-cols-2 gap-4 text-center">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="text-sm"
              >
                <p className="text-white/40 text-xs mb-1">Bike</p>
                <p className="font-semibold text-white">{result.bike_name?.split(' ').slice(-2).join(' ')}</p>
              </motion.div>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
                className="text-sm"
              >
                <p className="text-white/40 text-xs mb-1">Peak Power</p>
                <p className="font-semibold text-[#00FFB2]">{result.peak_power_hp.toFixed(0)} hp</p>
              </motion.div>
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
            className="mt-8 space-y-4 relative z-10"
          >
            <div className="grid grid-cols-2 gap-4">
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.1 }}
                className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-6 text-center backdrop-blur"
              >
                <p className="text-[10px] font-mono text-white/45 mb-2 uppercase tracking-[0.25em]">
                  Top Speed
                </p>
                <p className="text-3xl sm:text-5xl font-mono font-bold text-[#FF5E1F]">
                  <AnimatedCounter target={topSpeedResult.terminal_velocity_kmh ?? 0} decimals={1} />
                </p>
                <p className="text-xs text-white/40 mt-2">km/h</p>
              </motion.div>

              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-6 text-center backdrop-blur flex flex-col justify-center"
              >
                <p className="text-[10px] font-mono text-white/45 mb-2 uppercase tracking-[0.25em]">
                  Plateau
                </p>
                {topSpeedResult.reached_plateau ? (
                  <>
                    <p className="text-2xl sm:text-3xl font-mono font-bold text-[#00FFB2]">Reached</p>
                    <p className="text-[11px] text-white/45 mt-1.5 font-mono tabular-nums">
                      in {topSpeedResult.time_to_terminal_s?.toFixed(1) ?? '—'}s
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-2xl sm:text-3xl font-mono font-bold text-brand-amber/85">Limited</p>
                    <p className="text-[11px] text-white/45 mt-1.5 font-mono tabular-nums">
                      gearing or wind
                    </p>
                  </>
                )}
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-6 backdrop-blur"
            >
              <p className="text-xs font-semibold text-white/55 mb-4 uppercase tracking-wider">Run Detail</p>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4">
                <div>
                  <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-white/40 mb-1">Time</p>
                  <p className="text-base sm:text-lg font-mono font-bold text-white tabular-nums">
                    {topSpeedResult.time_to_terminal_s?.toFixed(1) ?? '—'}<span className="text-white/40 text-xs ml-0.5">s</span>
                  </p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-white/40 mb-1">Distance</p>
                  <p className="text-base sm:text-lg font-mono font-bold text-white tabular-nums">
                    {topSpeedResult.distance_to_terminal_m == null
                      ? '—'
                      : topSpeedResult.distance_to_terminal_m >= 1000
                        ? (topSpeedResult.distance_to_terminal_m / 1000).toFixed(2)
                        : Math.round(topSpeedResult.distance_to_terminal_m)}
                    <span className="text-white/40 text-xs ml-0.5">{topSpeedResult.distance_to_terminal_m >= 1000 ? 'km' : 'm'}</span>
                  </p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-white/40 mb-1">mph</p>
                  <p className="text-base sm:text-lg font-mono font-bold text-white tabular-nums">
                    {topSpeedResult.terminal_velocity_mph?.toFixed(1) ?? '—'}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-white/40 mb-1">Gear</p>
                  <p className="text-base sm:text-lg font-mono font-bold text-white tabular-nums">
                    {topSpeedResult.terminal_gear ?? '—'}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-white/40 mb-1">RPM</p>
                  <p className="text-base sm:text-lg font-mono font-bold text-white tabular-nums">
                    {topSpeedResult.terminal_rpm?.toLocaleString('en-US') ?? '—'}
                  </p>
                </div>
                <div>
                  <p className="text-[10px] sm:text-[11px] font-mono uppercase tracking-wider text-white/40 mb-1">Power</p>
                  <p className="text-base sm:text-lg font-mono font-bold text-[#00FFB2] tabular-nums">
                    {topSpeedResult.terminal_power_hp?.toFixed(0) ?? '—'}<span className="text-white/40 text-xs ml-0.5">hp</span>
                  </p>
                </div>
              </div>
            </motion.div>

            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="text-sm">
                <p className="text-white/40 text-xs mb-1">Bike</p>
                <p className="font-semibold text-white">{topSpeedResult.bike_name?.split(' ').slice(-2).join(' ')}</p>
              </div>
              <div className="text-sm">
                <p className="text-white/40 text-xs mb-1">Peak Power</p>
                <p className="font-semibold text-[#00FFB2]">{topSpeedResult.peak_power_hp?.toFixed(0) ?? '—'} hp</p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* end sim mode */}
      </>
      )}

      <p className="text-xs text-white/30 text-center mt-6 relative z-10">
        First-principles RK4 physics · 15 sub-models · 1 ms timestep
      </p>
    </motion.div>
  );
}
