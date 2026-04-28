'use client';

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, AlertCircle, MapPin, MessageSquare, Gauge } from 'lucide-react';
import LocationPicker, { environmentOverridesFromLocation } from './LocationPicker';
import ChatPanel from './ChatPanel';
import { API_URL } from '../lib/api';

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
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runSim() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const envOverrides = environmentOverridesFromLocation(location);
      const body = {
        rider_mass_kg: riderKg,
        power_boost_pct: powerBoost,
        mass_delta_kg: massChange,
        ...envOverrides,
      };
      // Reference bikes use bike_preset (legacy path that hits hand-built
      // BikeConfig from defaults.py); catalog bikes use bike_id (resolves
      // to the importer-built BikeConfig from the seeded SQLite catalog).
      if (selectedBike.presetId) {
        body.bike_preset = selectedBike.presetId;
      } else {
        body.bike_id = selectedBike.id;
      }
      const res = await fetch(`${API_URL}/api/simulate/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`API error ${res.status}: ${msg}`);
      }
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
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
            className="absolute inset-0 rounded-2xl pointer-events-none"
            style={{
              background: 'conic-gradient(from 0deg, transparent, #FF5E1F, transparent)',
              opacity: 0.3,
            }}
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
        )}
      </AnimatePresence>

      <div className="flex items-center justify-between mb-6 relative z-10">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <motion.div whileHover={{ scale: 1.1 }} transition={{ type: 'spring', stiffness: 400 }}>
            <Zap className="text-[#FF5E1F]" size={20} />
          </motion.div>
          <span className="bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">
            Live Quarter-Mile Simulator
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
          <label className="text-xs font-semibold text-white/60 uppercase tracking-wide">
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
            highlight: powerBoost > 0,
          },
          {
            label: 'Mass change',
            value: massChange,
            onChange: setMassChange,
            min: -15,
            max: 15,
            format: v => `${v > 0 ? '+' : ''}${v} kg`,
            highlight: massChange !== 0,
          },
        ].map((slider, idx) => (
          <div key={idx} className="space-y-2">
            <label className="block text-xs font-semibold text-white/60 uppercase tracking-wide">
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
            <div className={`text-sm font-mono text-right transition-colors ${
              slider.highlight ? 'text-[#00FFB2]' : 'text-white'
            }`}>
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

      <motion.button
        onClick={runSim}
        disabled={loading}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="relative w-full py-3 bg-gradient-to-r from-[#FF5E1F] to-[#FF7A00] hover:shadow-[0_0_40px_rgba(255,94,31,0.4)] disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-semibold text-white transition-all flex items-center justify-center gap-2 group overflow-hidden z-10"
      >
        <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors" />
        <div className="relative flex items-center gap-2">
          {loading ? (
            <>
              <motion.div
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 1.2, repeat: Infinity }}
                className="flex gap-1"
              >
                <span className="w-1.5 h-1.5 bg-white rounded-full" />
                <span className="w-1.5 h-1.5 bg-white rounded-full" />
                <span className="w-1.5 h-1.5 bg-white rounded-full" />
              </motion.div>
              <span>Simulating…</span>
            </>
          ) : (
            <>
              <Zap size={16} />
              <span>Run Simulation</span>
            </>
          )}
        </div>
      </motion.button>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center gap-2 relative z-10"
          >
            <AlertCircle size={16} />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {result && (
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
                <p className="text-[10px] sm:text-xs font-semibold text-white/50 mb-2 uppercase tracking-wide">
                  Quarter-Mile ET
                </p>
                <p className="text-3xl sm:text-5xl font-mono font-bold text-[#FF5E1F]">
                  <AnimatedCounter target={result.et_quarter_s} decimals={3} />
                  <span className="text-xl sm:text-3xl ml-1">s</span>
                </p>
              </motion.div>

              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-6 text-center backdrop-blur"
              >
                <p className="text-[10px] sm:text-xs font-semibold text-white/50 mb-2 uppercase tracking-wide">
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
              <p className="text-xs font-semibold text-white/50 mb-4 uppercase tracking-wide">Split Timeline</p>
              <div className="relative">
                <div className="absolute top-8 left-0 right-0 h-0.5 bg-gradient-to-r from-[#FF5E1F] via-[#FF7A00] to-transparent opacity-40" />

                <div className="grid grid-cols-4 gap-1 sm:gap-2 relative">
                  {[
                    { label: '0 ft', val: 0 },
                    { label: '60 ft', val: result.et_60ft_s },
                    { label: '⅛ mile', val: result.et_eighth_s },
                    { label: '¼ mile', val: result.et_quarter_s },
                  ].map((split, idx) => (
                    <div key={idx} className="text-center">
                      <div className="w-3 h-3 sm:w-4 sm:h-4 rounded-full bg-[#FF5E1F] shadow-[0_0_15px_rgba(255,94,31,0.5)] mx-auto mb-3" />
                      <p className="text-[10px] sm:text-xs text-white/40 mb-1">{split.label}</p>
                      <p className="text-xs sm:text-sm font-mono font-semibold text-white">
                        {split.val === 0 ? '0.000s' : `${split.val.toFixed(3)}s`}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
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

      {/* end sim mode */}
      </>
      )}

      <p className="text-xs text-white/30 text-center mt-6 relative z-10">
        First-principles RK4 physics · 15 sub-models · 1 ms timestep · 327 bikes
      </p>
    </motion.div>
  );
}
