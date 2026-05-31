'use client';

/**
 * EcuAutotune — environment-aware ECU / setup recommendation tool.
 *
 * Pick a bike, set a race location (via the shared LocationPicker, which
 * resolves text / GPS / a seeded venue into a full environment) and
 * optionally override conditions manually, then call POST /api/autotune/ecu
 * and render:
 *   - environment summary (temp, humidity, density altitude, air density,
 *     power-correction %)
 *   - gearing recommendation (front/rear sprocket + final drive + ΔET +
 *     rationale; "fixed (shaft/belt)" when not adjustable)
 *   - launch-RPM recommendation (recommended vs stock + ΔET)
 *   - tyre-pressure guideline (rear/front + rationale)
 *   - fuel / timing guideline (trim % + timing° + rationale)
 *   - combined net ET improvement + overall rationale
 *
 * Mirrors SimulatorWidget styling (glass cards, brand-orange / brand-accent
 * palette, framer-motion) and reuses LocationPicker +
 * environmentOverridesFromLocation from the simulator widget.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sliders, Search, ChevronDown, AlertCircle, MapPin, Thermometer, Wind,
  Droplets, Mountain, Cog, Flag, CircleDot, Flame, Sparkles,
} from 'lucide-react';
import { API_URL, autotuneEcu } from '../lib/api';
import LocationPicker, { environmentOverridesFromLocation } from './LocationPicker';

// ─── helpers ────────────────────────────────────────────────────────────────
const fmtNum = (n, d = 1) => (n == null ? '—' : Number(n).toFixed(d));
const fmtDelta = (n, d = 3) =>
  n == null ? '—' : `${n > 0 ? '+' : ''}${Number(n).toFixed(d)}`;
const fmtInt = (n) => (n == null ? '—' : Math.round(Number(n)).toLocaleString('en-US'));

// ─── Bike picker (self-contained, debounced /api/bikes search) ───────────────
function BikePicker({ value, onSelect }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [bikes, setBikes] = useState([]);
  const [loading, setLoading] = useState(false);
  const ref = useRef(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    const h = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      let cancelled = false;
      setLoading(true);
      const params = new URLSearchParams();
      if (q.trim()) params.set('search', q.trim());
      params.set('limit', '60');
      fetch(`${API_URL}/api/bikes?${params.toString()}`)
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((data) => {
          if (!cancelled) setBikes(data.bikes || []);
        })
        .catch(() => {
          if (!cancelled) setBikes([]);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
      return () => {
        cancelled = true;
      };
    }, 220);
    return () => clearTimeout(debounceRef.current);
  }, [q]);

  const label = value
    ? `${value.manufacturer || ''} ${value.model || ''}`.trim()
    : 'Select a bike';

  return (
    <div className="relative" ref={ref}>
      <label className="flex items-center gap-1.5 text-[10px] text-white/40 mb-1.5 uppercase tracking-widest font-medium">
        <Sliders size={11} className="text-brand-orange" /> Bike
      </label>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg border border-white/10 bg-black/30 hover:border-brand-orange/40 text-left transition-colors"
      >
        <span className={`text-sm truncate ${value ? 'text-white' : 'text-white/40'}`}>
          {label}
          {value?.displacement_cc != null && (
            <span className="ml-2 text-[11px] font-mono text-white/40">
              {Math.round(value.displacement_cc)}cc
              {value.peak_power_hp != null && ` · ${Math.round(value.peak_power_hp)} hp`}
            </span>
          )}
        </span>
        <ChevronDown size={15} className={`text-white/40 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            className="absolute z-30 mt-1.5 w-full rounded-lg border border-white/10 bg-ink-2 shadow-2xl overflow-hidden"
          >
            <div className="p-2 border-b border-white/5">
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-white/40" />
                <input
                  autoFocus
                  type="text"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Search bikes…"
                  className="w-full pl-8 pr-3 py-2 bg-black/40 border border-white/10 rounded-md text-sm text-white placeholder:text-white/30 focus:border-brand-orange focus:outline-none font-mono"
                />
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto">
              {loading ? (
                <p className="px-3 py-4 text-xs text-white/40 font-mono">Loading…</p>
              ) : bikes.length === 0 ? (
                <p className="px-3 py-4 text-xs text-white/40 font-mono">No bikes found.</p>
              ) : (
                bikes.map((b) => (
                  <button
                    key={b.id}
                    type="button"
                    onClick={() => {
                      onSelect(b);
                      setOpen(false);
                    }}
                    className="w-full px-3 py-2 text-left hover:bg-brand-orange/10 transition-colors flex items-center justify-between gap-2"
                  >
                    <span className="text-sm text-white/90 truncate">
                      {b.manufacturer} {b.model}
                    </span>
                    <span className="text-[10px] font-mono text-white/40 shrink-0">
                      {b.displacement_cc ? `${Math.round(b.displacement_cc)}cc` : ''}
                    </span>
                  </button>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─── env stat ────────────────────────────────────────────────────────────────
function EnvStat({ icon: Icon, label, value, accent }) {
  return (
    <div className="text-left">
      <p className="flex items-center gap-1 text-[9px] font-mono uppercase tracking-wider text-white/40">
        {Icon && <Icon size={10} className="text-white/40" />} {label}
      </p>
      <p className={`text-sm font-mono tabular-nums mt-0.5 ${accent || 'text-white/90'}`}>{value}</p>
    </div>
  );
}

// ─── recommendation card shell ──────────────────────────────────────────────
function RecCard({ icon: Icon, title, children, delta, badge }) {
  return (
    <div className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-5 backdrop-blur">
      <div className="flex items-center justify-between mb-3">
        <p className="flex items-center gap-1.5 text-xs font-semibold text-white/55 uppercase tracking-wider">
          {Icon && <Icon size={13} className="text-brand-orange" />} {title}
        </p>
        <div className="flex items-center gap-2">
          {badge && (
            <span className="px-2 py-0.5 rounded-full bg-white/[0.06] border border-white/10 text-[9px] font-mono uppercase tracking-wide text-white/50">
              {badge}
            </span>
          )}
          {delta != null && (
            <span className="text-xs font-mono text-brand-accent tabular-nums">{fmtDelta(delta, 3)}s</span>
          )}
        </div>
      </div>
      {children}
    </div>
  );
}

// ─── main ─────────────────────────────────────────────────────────────────────
export default function EcuAutotune() {
  const [bike, setBike] = useState(null);
  const [location, setLocation] = useState(null);
  const [locationOpen, setLocationOpen] = useState(false);
  const [riderKg, setRiderKg] = useState(75);

  // Optional manual conditions (override / supplement the resolved location)
  const [showManual, setShowManual] = useState(false);
  const [tempC, setTempC] = useState('');
  const [humidity, setHumidity] = useState('');
  const [altitude, setAltitude] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const run = useCallback(async () => {
    if (!bike) {
      setError('Pick a bike first.');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const env = environmentOverridesFromLocation(location);
      const body = {
        bike_id: bike.id,
        rider_weight_kg: riderKg,
      };
      // Prefer a resolved venue id; otherwise pass the location label so the
      // backend resolves it (same path /api/venues/resolve uses).
      if (env.venue_id != null) body.venue_id = env.venue_id;
      else if (location) {
        const label =
          location.venue_name || location.location_name || location._label || location.resolved_name;
        if (label) body.location = label;
      }
      // Manual overrides win when supplied.
      if (tempC !== '') body.ambient_temp_c = Number(tempC);
      else if (env.ambient_temp_c != null) body.ambient_temp_c = env.ambient_temp_c;
      if (humidity !== '') body.humidity_pct = Number(humidity);
      else if (env.humidity_pct != null) body.humidity_pct = env.humidity_pct;
      if (altitude !== '') body.altitude_m = Number(altitude);

      const data = await autotuneEcu(body);
      setResult(data);
    } catch (e) {
      setError(e.message || 'Autotune failed.');
    } finally {
      setLoading(false);
    }
  }, [bike, location, riderKg, tempC, humidity, altitude]);

  const env = result?.environment;
  const gearing = result?.gearing;
  const launch = result?.launch_rpm;
  const tyre = result?.tyre_pressure;
  const fuel = result?.fuel_timing;
  const combined = result?.combined;

  return (
    <div className="space-y-6">
      {/* ── Controls card ───────────────────────────────────────────── */}
      <div className="relative bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-2xl p-5 sm:p-7">
        <AnimatePresence>
          {loading && (
            <motion.div
              className="absolute inset-0 rounded-2xl pointer-events-none"
              style={{ background: 'conic-gradient(from 0deg, transparent, #FF5E1F, transparent)', opacity: 0.25 }}
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
            />
          )}
        </AnimatePresence>

        <div className="relative z-10 space-y-5">
          <BikePicker value={bike} onSelect={setBike} />

          {/* Location */}
          <div>
            <label className="block text-[10px] text-white/40 mb-1.5 uppercase tracking-widest font-medium">
              Race location
            </label>
            <button
              type="button"
              onClick={() => setLocationOpen((v) => !v)}
              className="w-full flex items-center justify-between px-3 py-2.5 rounded-lg border border-white/10 hover:border-brand-orange/40 bg-black/30 text-left transition-colors"
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
                  <span className="font-mono text-white/50">Pick a venue or city (optional)</span>
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
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Manual conditions (optional) */}
          <div>
            <button
              type="button"
              onClick={() => setShowManual((v) => !v)}
              className="text-[11px] font-mono text-white/50 hover:text-brand-orange transition-colors uppercase tracking-wide"
            >
              {showManual ? '− Hide manual conditions' : '+ Set conditions manually'}
            </button>
            <AnimatePresence>
              {showManual && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="grid grid-cols-3 gap-3 mt-3">
                    {[
                      { label: 'Temp °C', v: tempC, set: setTempC, ph: 'e.g. 32', icon: Thermometer },
                      { label: 'Humidity %', v: humidity, set: setHumidity, ph: 'e.g. 55', icon: Droplets },
                      { label: 'Altitude m', v: altitude, set: setAltitude, ph: 'e.g. 600', icon: Mountain },
                    ].map((f) => (
                      <div key={f.label}>
                        <label className="flex items-center gap-1 text-[9px] font-mono uppercase tracking-wider text-white/40 mb-1">
                          <f.icon size={10} /> {f.label}
                        </label>
                        <input
                          type="number"
                          inputMode="decimal"
                          value={f.v}
                          onChange={(e) => f.set(e.target.value)}
                          placeholder={f.ph}
                          className="w-full px-2.5 py-2 bg-black/40 border border-white/10 rounded-lg text-sm text-white placeholder:text-white/25 focus:border-brand-orange focus:outline-none font-mono"
                        />
                      </div>
                    ))}
                  </div>
                  <p className="text-[10px] text-white/30 mt-2 font-mono">
                    Manual values override the resolved location.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Rider weight */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-[10px] text-white/40 uppercase tracking-widest font-medium">Rider weight</label>
              <span className="text-sm font-mono text-white/80 tabular-nums">{riderKg} kg</span>
            </div>
            <input
              type="range"
              min={50}
              max={130}
              value={riderKg}
              onChange={(e) => setRiderKg(Number(e.target.value))}
              className="w-full h-1.5 bg-white/10 rounded-full appearance-none cursor-pointer accent-brand-orange"
            />
          </div>

          <motion.button
            onClick={run}
            disabled={loading || !bike}
            whileHover={{ scale: loading || !bike ? 1 : 1.01 }}
            whileTap={{ scale: loading || !bike ? 1 : 0.99 }}
            className="w-full py-3.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 bg-gradient-to-r from-brand-orange to-brand-orangeLight text-black shadow-orange-soft hover:brightness-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:saturate-50"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                Computing setup…
              </>
            ) : (
              <>
                <Sliders size={16} /> Get setup
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* ── Error ───────────────────────────────────────────────────── */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-sm flex items-center gap-2"
          >
            <AlertCircle size={16} /> {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Results ─────────────────────────────────────────────────── */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.35 }}
            className="space-y-5"
          >
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h3 className="text-lg font-bold text-white">
                {result.bike_name}
                <span className="ml-2 text-xs font-mono text-white/40 uppercase tracking-wide">setup</span>
              </h3>
              {result.scoring_method && (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-brand-accent/10 border border-brand-accent/30 text-[11px] font-mono text-brand-accent">
                  {result.scoring_method}
                </span>
              )}
            </div>

            {/* Environment summary */}
            {env && (
              <div className="bg-white/[0.04] border border-white/10 rounded-xl p-4 sm:p-5 backdrop-blur">
                <div className="flex items-center justify-between mb-3">
                  <p className="flex items-center gap-1.5 text-xs font-semibold text-white/55 uppercase tracking-wider">
                    <MapPin size={13} className="text-brand-orange" />
                    {env.location || 'Conditions'}
                  </p>
                  {result.environment_source && (
                    <span className="text-[10px] font-mono text-white/35 uppercase tracking-wide">
                      {result.environment_source}
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
                  <EnvStat icon={Thermometer} label="Temp" value={`${fmtNum(env.temperature_c, 1)}°C`} />
                  <EnvStat icon={Droplets} label="Humidity" value={`${fmtNum(env.humidity_pct, 0)}%`} />
                  <EnvStat icon={Mountain} label="Density alt" value={`${fmtInt(env.density_altitude_ft)} ft`} accent="text-brand-orange" />
                  <EnvStat icon={Wind} label="Air density" value={`${fmtNum(env.air_density_kgm3, 3)}`} />
                  <EnvStat label="Pressure" value={`${fmtNum(env.pressure_hpa, 0)} hPa`} />
                  <EnvStat
                    label="Power corr"
                    value={`${fmtDelta(env.power_correction_pct, 1)}%`}
                    accent={env.power_correction_pct < 0 ? 'text-brand-red' : 'text-brand-accent'}
                  />
                </div>
              </div>
            )}

            {/* Combined net result */}
            {combined && (
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-white/[0.04] border border-white/10 rounded-xl p-4 text-center backdrop-blur">
                  <p className="text-[10px] font-semibold text-white/50 mb-1.5 uppercase tracking-wide">Tuned ET</p>
                  <p className="text-2xl sm:text-3xl font-mono font-bold text-brand-orange">
                    {fmtNum(combined.et_s, 3)}<span className="text-base ml-1">s</span>
                  </p>
                </div>
                <div className="bg-white/[0.04] border border-white/10 rounded-xl p-4 text-center backdrop-blur">
                  <p className="text-[10px] font-semibold text-white/50 mb-1.5 uppercase tracking-wide">Trap</p>
                  <p className="text-2xl sm:text-3xl font-mono font-bold text-white">{fmtNum(combined.trap_kmh, 1)}</p>
                  <p className="text-[11px] text-white/40 mt-1 font-mono">km/h</p>
                </div>
                <div className="bg-white/[0.04] border border-white/10 rounded-xl p-4 text-center backdrop-blur">
                  <p className="text-[10px] font-semibold text-white/50 mb-1.5 uppercase tracking-wide">Net gain</p>
                  <p className="text-2xl sm:text-3xl font-mono font-bold text-brand-accent">{fmtDelta(combined.delta_et_s, 3)}</p>
                  <p className="text-[11px] text-white/40 mt-1 font-mono">seconds</p>
                </div>
              </div>
            )}

            {/* Gearing */}
            {gearing && (
              <RecCard
                icon={Cog}
                title="Gearing"
                delta={gearing.adjustable ? gearing.delta_et_s : null}
                badge={gearing.adjustable ? undefined : `fixed (${gearing.drive || 'shaft/belt'})`}
              >
                {gearing.adjustable ? (
                  <>
                    <div className="grid grid-cols-3 gap-3 mb-3">
                      <div>
                        <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Front</p>
                        <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                          {fmtInt(gearing.recommended_front)}
                          {gearing.stock_front != null && (
                            <span className="text-white/40 text-xs ml-1.5">from {fmtInt(gearing.stock_front)}</span>
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Rear</p>
                        <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                          {fmtInt(gearing.recommended_rear)}
                          {gearing.stock_rear != null && (
                            <span className="text-white/40 text-xs ml-1.5">from {fmtInt(gearing.stock_rear)}</span>
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Final drive</p>
                        <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                          {fmtNum(gearing.recommended_final_drive, 2)}
                        </p>
                      </div>
                    </div>
                    {gearing.recommendation && (
                      <p className="text-sm text-white/70">{gearing.recommendation}</p>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-white/70">
                    {gearing.recommendation ||
                      `Final drive is fixed on this ${gearing.drive || 'shaft/belt'}-drive bike — no sprocket swap available.`}
                  </p>
                )}
              </RecCard>
            )}

            {/* Launch RPM */}
            {launch && (
              <RecCard icon={Flag} title="Launch RPM" delta={launch.delta_et_s}>
                <div className="flex items-baseline gap-3 mb-2">
                  <p className="text-2xl font-mono font-bold text-white tabular-nums">{fmtInt(launch.recommended_rpm)}</p>
                  {launch.stock_rpm != null && (
                    <p className="text-xs font-mono text-white/40">from {fmtInt(launch.stock_rpm)} stock</p>
                  )}
                  <span className="text-xs font-mono text-white/40">rpm</span>
                </div>
                {launch.rationale && <p className="text-sm text-white/70">{launch.rationale}</p>}
              </RecCard>
            )}

            {/* Tyre pressure */}
            {tyre && (
              <RecCard
                icon={CircleDot}
                title="Tyre pressure"
                badge={tyre.is_guideline ? 'guideline' : undefined}
              >
                <div className="grid grid-cols-2 gap-3 mb-2 max-w-xs">
                  <div>
                    <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Rear</p>
                    <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                      {fmtNum(tyre.rear_psi, 1)} <span className="text-white/40 text-xs">psi</span>
                      {tyre.stock_rear_psi != null && (
                        <span className="text-white/40 text-xs ml-1.5">from {fmtNum(tyre.stock_rear_psi, 0)}</span>
                      )}
                    </p>
                  </div>
                  <div>
                    <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Front</p>
                    <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                      {fmtNum(tyre.front_psi, 1)} <span className="text-white/40 text-xs">psi</span>
                      {tyre.stock_front_psi != null && (
                        <span className="text-white/40 text-xs ml-1.5">from {fmtNum(tyre.stock_front_psi, 0)}</span>
                      )}
                    </p>
                  </div>
                </div>
                {tyre.rationale && <p className="text-sm text-white/70">{tyre.rationale}</p>}
              </RecCard>
            )}

            {/* Fuel / timing */}
            {fuel && (
              <RecCard
                icon={Flame}
                title="Fuel & timing"
                badge={fuel.is_guideline ? 'guideline' : undefined}
              >
                {fuel.applicable === false ? (
                  <p className="text-sm text-white/70">
                    {fuel.rationale || 'No fuel / timing change recommended for these conditions.'}
                  </p>
                ) : (
                  <>
                    <div className="grid grid-cols-2 gap-3 mb-2 max-w-xs">
                      <div>
                        <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Fuel trim</p>
                        <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                          {fmtDelta(fuel.fuel_trim_pct, 1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">Timing</p>
                        <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                          {fmtDelta(fuel.timing_advance_deg, 1)}°
                        </p>
                      </div>
                    </div>
                    {fuel.rationale && <p className="text-sm text-white/70">{fuel.rationale}</p>}
                  </>
                )}
              </RecCard>
            )}

            {/* Overall rationale */}
            {result.rationale && (
              <div className="bg-brand-accent/[0.06] border border-brand-accent/25 rounded-xl p-4">
                <p className="flex items-center gap-1.5 text-xs font-semibold text-brand-accent uppercase tracking-wider mb-2">
                  <Sparkles size={13} /> Summary
                </p>
                <p className="text-sm text-white/80">{result.rationale}</p>
              </div>
            )}

            <p className="text-[11px] text-white/30 text-center pt-1">
              Density-altitude-aware setup from first-principles RK4 physics. Pressure & fuel/timing are guidelines —
              dyno-verify before a competitive run.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
