'use client';

/**
 * EcuAutotune — environment-aware ECU / setup recommendation tool (IGNITION v5).
 *
 * Pick a bike, set a race location (via the shared LocationPicker, which
 * resolves text / GPS / a seeded venue into a full environment) and
 * optionally override conditions manually, then call the job-backed
 * POST /api/jobs/autotune (with sync fallback) and render:
 *   - environment summary (temp, humidity, density altitude, air density,
 *     power-correction %)
 *   - gearing recommendation (front/rear sprocket + final drive + ΔET +
 *     rationale; "fixed (shaft/belt)" when not adjustable)
 *   - launch-RPM recommendation (recommended vs stock + ΔET)
 *   - tyre-pressure guideline (rear/front + rationale)
 *   - fuel / timing guideline (trim % + timing° + rationale)
 *   - combined net ET improvement + overall rationale
 *
 * FUNCTION IS FROZEN (v5 is a re-skin): shared BikePicker + LocationPicker,
 * useAsyncTask + ActionButton run/stop pattern (real % in the button),
 * validated manual condition inputs (min/max/step + clamped before request —
 * non-numeric input never enters the body). v4 layout: input card stack
 * left, results card stack right (lg:grid-cols-[0.9fr_1.1fr]).
 */

import { useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Sliders, AlertCircle, MapPin, Thermometer, Wind,
  Droplets, Mountain, Cog, Flag, CircleDot, Flame,
} from 'lucide-react';
import { autotuneEcuJob } from '../lib/api';
import useAsyncTask from '../lib/useAsyncTask';
import ActionButton from './ActionButton';
import SimProgress from './SimProgress';
import BikePicker from './BikePicker';
import ScoreboardDigits from './ScoreboardDigits';
import LocationPicker, { environmentOverridesFromLocation } from './LocationPicker';
import UpgradeNotice from './UpgradeNotice';

// ─── helpers ────────────────────────────────────────────────────────────────
const fmtNum = (n, d = 1) => (n == null ? '—' : Number(n).toFixed(d));
const fmtDelta = (n, d = 3) =>
  n == null ? '—' : `${n > 0 ? '+' : ''}${Number(n).toFixed(d)}`;
// Sign-aware tone for ET deltas. Convention unified July 6, 2026:
// delta_et_s = tuned − stock ⇒ NEGATIVE = faster (time dropped) = good
// = signal-go.
const deltaTone = (n) =>
  n == null || Number(n) === 0
    ? 'font-mono tabular-nums text-white/50'
    : Number(n) < 0
      ? 'delta-down'
      : 'delta-up';
const deltaChip = (n) =>
  n == null || Number(n) === 0 ? 'chip' : Number(n) < 0 ? 'chip chip-go' : 'chip chip-foul';
const fmtInt = (n) => (n == null ? '—' : Math.round(Number(n)).toLocaleString('en-US'));

// One-tap starts for first-time users (shared BikePicker `popular` prop).
const POPULAR_BIKES = [
  { label: 'Hayabusa', search: 'hayabusa' },
  { label: 'R15 V4', search: 'r15 v4' },
  { label: 'Duke 390', search: 'duke 390' },
  { label: 'Classic 350', search: 'classic 350' },
  { label: 'ZX-10R', search: 'zx-10r' },
  { label: 'GSX-R1000', search: 'gsx-r1000' },
];

// ─── validated manual conditions ─────────────────────────────────────────────
// Physical envelopes for the manual overrides. Values are clamped into range
// before entering the request body; non-numeric input shows an inline hint
// and NEVER enters the body.
const MANUAL_FIELDS = [
  { key: 'temp', label: 'Temp °C', icon: Thermometer, min: -20, max: 55, step: 0.5, ph: 'e.g. 32', hint: '−20 to 55 °C' },
  { key: 'humidity', label: 'Humidity %', icon: Droplets, min: 0, max: 100, step: 1, ph: 'e.g. 55', hint: '0 to 100 %' },
  { key: 'altitude', label: 'Altitude m', icon: Mountain, min: -100, max: 5000, step: 10, ph: 'e.g. 600', hint: '−100 to 5000 m' },
];

const clamp = (n, min, max) => Math.min(max, Math.max(min, n));

/**
 * Parse + validate a manual field. Returns:
 *  - { value: null, invalid: false }  — empty, field unused
 *  - { value: null, invalid: true }   — non-numeric, excluded from request
 *  - { value: n, invalid: false, clamped } — numeric, clamped into [min,max]
 */
function manualFieldValue(raw, { min, max }) {
  if (raw === '' || raw == null) return { value: null, invalid: false, clamped: false };
  const n = Number(raw);
  if (!Number.isFinite(n)) return { value: null, invalid: true, clamped: false };
  return { value: clamp(n, min, max), invalid: false, clamped: n < min || n > max };
}

// ─── env stat ────────────────────────────────────────────────────────────────
function EnvStat({ icon: Icon, label, value, accent }) {
  return (
    <div className="text-left">
      <p className="label-mono flex items-center gap-1">
        {Icon && <Icon size={10} className="text-white/40" aria-hidden="true" />} {label}
      </p>
      <p className={`text-sm font-mono tabular-nums mt-0.5 ${accent || 'text-white/90'}`}>{value}</p>
    </div>
  );
}

// ─── recommendation card shell ──────────────────────────────────────────────
function RecCard({ icon: Icon, title, children, delta, badge }) {
  return (
    <div className="card p-5 md:p-6">
      <div className="flex items-center justify-between mb-3">
        <p className="label-mono flex items-center gap-1.5">
          {Icon && <Icon size={13} className="text-white/40" aria-hidden="true" />} {title}
        </p>
        <div className="flex items-center gap-2">
          {badge && <span className="chip">{badge}</span>}
          {delta != null && (
            <span className={`text-xs ${deltaTone(delta)}`}>{fmtDelta(delta, 3)}s</span>
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
  const reduce = useReducedMotion();

  // Optional manual conditions (override / supplement the resolved location)
  const [showManual, setShowManual] = useState(false);
  const [manual, setManual] = useState({ temp: '', humidity: '', altitude: '' });

  // Per-field parse/validate state (drives inline hints + the request body)
  const fieldStates = Object.fromEntries(
    MANUAL_FIELDS.map((f) => [f.key, manualFieldValue(manual[f.key], f)]),
  );

  // Job-backed run — useAsyncTask owns AbortController + progress + error;
  // autotuneEcuJob polls /api/jobs with the real sweep % and cancels the
  // job server-side when the signal aborts (Stop).
  const task = useAsyncTask(async (signal, onProgress) => {
    if (!bike) throw new Error('Pick a bike first.');
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
    // Manual overrides win when supplied. Values are validated + clamped —
    // invalid (non-numeric) input never enters the body.
    const temp = fieldStates.temp;
    const humidity = fieldStates.humidity;
    const altitude = fieldStates.altitude;
    if (temp.value != null) body.ambient_temp_c = temp.value;
    else if (env.ambient_temp_c != null) body.ambient_temp_c = env.ambient_temp_c;
    if (humidity.value != null) body.humidity_pct = humidity.value;
    else if (env.humidity_pct != null) body.humidity_pct = env.humidity_pct;
    if (altitude.value != null) body.altitude_m = altitude.value;

    return autotuneEcuJob(body, onProgress, signal);
  });

  const run = () => {
    task.reset(); // clear the previous result + error before a fresh run
    task.run();
  };

  const result = task.result;
  const env = result?.environment;
  const gearing = result?.gearing;
  const launch = result?.launch_rpm;
  const tyre = result?.tyre_pressure;
  const fuel = result?.fuel_timing;
  const combined = result?.combined;

  return (
    <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:items-start">
      {/* ── Inputs (left column) ─────────────────────────────────────── */}
      <div className="relative space-y-4">
        <AnimatePresence>
          {task.active && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute -top-1 left-1 right-1 z-20"
            >
              <SimProgress active edge progress={task.progress} />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="card p-5 md:p-6">
          <BikePicker value={bike} onSelect={setBike} popular={POPULAR_BIKES} />
        </div>

        {/* Location + conditions */}
        <div className="card p-5 md:p-6 space-y-5">
          <div>
            <span className="label-mono block mb-1.5">Race location</span>
            <button
              type="button"
              onClick={() => setLocationOpen((v) => !v)}
              className="w-full flex items-center justify-between rounded-lg border border-white/10 hover:border-white/25 bg-asphalt-3 px-3.5 py-2.5 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
            >
              <div className="flex items-center gap-2 text-sm min-w-0 flex-1">
                <MapPin size={14} className="text-white/40 shrink-0" aria-hidden="true" />
                {location ? (
                  <span className="font-mono text-white/80 truncate">
                    {location.venue_name || location.location_name || location._label}
                    {location.density_altitude_m != null && (
                      <span className="ml-2 text-accent text-xs tabular-nums">
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

          {/* Manual conditions (optional, validated) */}
          <div>
            <button
              type="button"
              onClick={() => setShowManual((v) => !v)}
              className="label-mono hover:text-white transition-colors"
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
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                    {MANUAL_FIELDS.map((f) => {
                      const st = fieldStates[f.key];
                      const flagged = st.invalid || st.clamped;
                      return (
                        <div key={f.key}>
                          <label
                            htmlFor={`mq-manual-${f.key}`}
                            className="label-mono flex items-center gap-1 mb-1"
                          >
                            <f.icon size={10} aria-hidden="true" /> {f.label}
                          </label>
                          <input
                            id={`mq-manual-${f.key}`}
                            type="number"
                            inputMode="decimal"
                            min={f.min}
                            max={f.max}
                            step={f.step}
                            value={manual[f.key]}
                            onChange={(e) =>
                              setManual((m) => ({ ...m, [f.key]: e.target.value }))
                            }
                            placeholder={f.ph}
                            aria-invalid={st.invalid || undefined}
                            className={`input-base font-mono ${
                              flagged ? 'border-signal-stage/60 focus:border-signal-stage/70' : ''
                            }`}
                          />
                          {flagged && (
                            <p className="text-[10px] font-mono text-signal-stage mt-1">
                              {st.invalid ? `Enter a number (${f.hint})` : `Clamped to ${f.hint}`}
                            </p>
                          )}
                        </div>
                      );
                    })}
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
              <span className="label-mono block">Rider weight</span>
              <span className="text-sm font-mono text-white/80 tabular-nums">{riderKg} kg</span>
            </div>
            <input
              type="range"
              min={50}
              max={130}
              value={riderKg}
              onChange={(e) => setRiderKg(Number(e.target.value))}
              aria-label="Rider weight in kilograms"
              className="w-full h-1.5 bg-asphalt-4 rounded-full appearance-none cursor-pointer accent-accent"
            />
          </div>
        </div>

        {task.active && (
          <SimProgress
            active
            progress={task.progress}
            stage={task.stage}
            label="Computing setup"
          />
        )}

        <ActionButton
          task={task}
          onRun={run}
          label={
            <>
              <Sliders size={16} aria-hidden="true" /> Get setup
            </>
          }
          runningLabel="Computing setup"
          disabled={!bike}
          className="w-full"
        />
        {!bike && (
          <p className="text-[11px] text-white/40 font-mono text-center">
            Pick a bike to arm the setup sweep.
          </p>
        )}
      </div>

      {/* ── Results (right column) ───────────────────────────────────── */}
      <div className="space-y-4">
        {/* Error — 401/402 (sign-in / upgrade / quota) get the shared
            UpgradeNotice with CTA; everything else keeps the foul tile. */}
        <AnimatePresence>
          {task.error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
            >
              {task.errorObj?.status === 401 || task.errorObj?.status === 402 ? (
                <UpgradeNotice error={task.errorObj} onRetry={run} />
              ) : (
                <div className="card border-signal-foul/30 bg-signal-foul/10 p-3 text-signal-foul text-sm flex items-center gap-2">
                  <AlertCircle size={16} aria-hidden="true" /> {task.error}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Idle / running placeholder */}
        {!result && !task.error && (
          <div className="card p-8 md:p-10 text-center">
            <Sliders size={22} className="mx-auto text-white/30 mb-3" aria-hidden="true" />
            <p className="label-mono mb-2">
              {task.active ? 'Setup sweep running' : 'Setup sheet standing by'}
            </p>
            <p className="text-sm text-white/45 max-w-sm mx-auto">
              {task.active
                ? 'Sweeping gearing and launch RPM against the density altitude — your setup sheet lands here.'
                : 'Pick a bike and where you’re running. Gearing, launch RPM, tyre pressure and fuel/timing come back with predicted ET deltas.'}
            </p>
            {task.active && (
              <div className="max-w-xs mx-auto mt-5">
                <SimProgress active progress={task.progress} stage={task.stage} label="Computing setup" />
              </div>
            )}
          </div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: reduce ? 0 : 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: reduce ? 0 : 12 }}
              transition={{ duration: 0.35 }}
              className="space-y-4"
            >
              {/* Header */}
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="font-display font-semibold text-lg md:text-xl tracking-tight text-white">
                  {result.bike_name}
                  <span className="label-mono ml-2">setup</span>
                </h3>
                {result.scoring_method && <span className="chip">{result.scoring_method}</span>}
              </div>

              {/* Combined net result — the setup slip headline */}
              {combined && (
                <div className="card p-5 md:p-6">
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div className="min-w-0">
                      <p className="label-mono">Tuned ET</p>
                      {combined.et_s != null ? (
                        /* The setup sheet's one hero number — seven-seg
                           timing board, brand orange (live data). */
                        <div className="flex items-end gap-2 mt-2">
                          <ScoreboardDigits
                            value={Number(combined.et_s).toFixed(3)}
                            h={32}
                            label={`Tuned ET ${Number(combined.et_s).toFixed(3)} seconds`}
                          />
                          <span className="font-mono text-sm text-white/40 pb-0.5">s</span>
                        </div>
                      ) : (
                        <p className="font-mono text-3xl md:text-4xl font-bold text-white tabular-nums mt-1.5">
                          {fmtNum(combined.et_s, 3)}
                          <span className="text-base text-white/40 ml-1">s</span>
                        </p>
                      )}
                      <p className="text-xs font-mono text-white/40 tabular-nums mt-1.5">
                        trap {fmtNum(combined.trap_kmh, 1)} km/h
                      </p>
                    </div>
                    <span className={`${deltaChip(combined.delta_et_s)} h-7 px-2.5 text-xs shrink-0`}>
                      {fmtDelta(combined.delta_et_s, 3)}s net
                    </span>
                  </div>
                </div>
              )}

              {/* Environment summary */}
              {env && (
                <div className="card p-5 md:p-6">
                  <div className="flex items-center justify-between mb-3">
                    <p className="label-mono flex items-center gap-1.5">
                      <MapPin size={13} className="text-white/40" aria-hidden="true" />
                      {env.location || 'Conditions'}
                    </p>
                    {result.environment_source && (
                      <span className="text-[10px] font-mono text-white/35 uppercase tracking-wide">
                        {result.environment_source}
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-3">
                    <EnvStat icon={Thermometer} label="Temp" value={`${fmtNum(env.temperature_c, 1)}°C`} />
                    <EnvStat icon={Droplets} label="Humidity" value={`${fmtNum(env.humidity_pct, 0)}%`} />
                    <EnvStat icon={Mountain} label="Density alt" value={`${fmtInt(env.density_altitude_ft)} ft`} accent="text-accent" />
                    <EnvStat icon={Wind} label="Air density" value={`${fmtNum(env.air_density_kgm3, 3)}`} />
                    <EnvStat label="Pressure" value={`${fmtNum(env.pressure_hpa, 0)} hPa`} />
                    <EnvStat
                      label="Power corr"
                      value={`${fmtDelta(env.power_correction_pct, 1)}%`}
                      accent={env.power_correction_pct < 0 ? 'text-signal-foul' : 'text-signal-go'}
                    />
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
                          <p className="label-mono">Front</p>
                          <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                            {fmtInt(gearing.recommended_front)}
                            {gearing.stock_front != null && (
                              <span className="text-white/40 text-xs ml-1.5">from {fmtInt(gearing.stock_front)}</span>
                            )}
                          </p>
                        </div>
                        <div>
                          <p className="label-mono">Rear</p>
                          <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                            {fmtInt(gearing.recommended_rear)}
                            {gearing.stock_rear != null && (
                              <span className="text-white/40 text-xs ml-1.5">from {fmtInt(gearing.stock_rear)}</span>
                            )}
                          </p>
                        </div>
                        <div>
                          <p className="label-mono">Final drive</p>
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
                      <p className="label-mono">Rear</p>
                      <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                        {fmtNum(tyre.rear_psi, 1)} <span className="text-white/40 text-xs">psi</span>
                        {tyre.stock_rear_psi != null && (
                          <span className="text-white/40 text-xs ml-1.5">from {fmtNum(tyre.stock_rear_psi, 0)}</span>
                        )}
                      </p>
                    </div>
                    <div>
                      <p className="label-mono">Front</p>
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
                          <p className="label-mono">Fuel trim</p>
                          <p className="text-base font-mono font-bold text-white tabular-nums mt-0.5">
                            {fmtDelta(fuel.fuel_trim_pct, 1)}%
                          </p>
                        </div>
                        <div>
                          <p className="label-mono">Timing</p>
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
                <div className="card p-4 md:p-5">
                  <p className="label-mono mb-2">Summary</p>
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
    </div>
  );
}
