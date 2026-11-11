'use client';

/**
 * Small shared building blocks for the two "tool" pages (/optimize and
 * /autotune). Kept in one file so the pages stay visually identical.
 *
 *   <Step n={1} title="Choose your bike">…</Step>
 *   <MoreOptions id="opt" label="More options">…</MoreOptions>
 *   <RangeField id label valueText min max step value onChange hint />
 *   <ErrorCard message onRetry />
 *   friendlyError(message)
 *   fmtINR(n) / fmtSecs(n) / fmtGain(deltaSeconds)
 */

import { useEffect, useState } from 'react';
import { AlertCircle, ChevronDown, Wind } from 'lucide-react';
import { environmentOverridesFromLocation } from '../LocationPicker';

// ─── formatting ──────────────────────────────────────────────────────────────
export const fmtINR = (n) =>
  n == null || !Number.isFinite(Number(n)) ? '' : `₹${Math.round(Number(n)).toLocaleString('en-IN')}`;

/** Seconds with 2 decimals (3 for tiny values so a gain never reads "0.00"). */
export function fmtSecs(n, d = 2) {
  if (n == null || !Number.isFinite(Number(n))) return '';
  return Number(n).toFixed(d);
}

/**
 * Plain-language time change. delta_et_s is after − before, so NEGATIVE means
 * quicker. Returns { text, tone } where tone is 'go' | 'foul' | 'flat'.
 */
export function describeTimeChange(delta, d = 2) {
  if (delta == null || !Number.isFinite(Number(delta))) return null;
  const v = Number(delta);
  const abs = Math.abs(v);
  if (abs < 0.0005) return { text: 'no change', tone: 'flat', abs: 0 };
  const digits = abs < 0.005 ? 3 : d;
  return v < 0
    ? { text: `${abs.toFixed(digits)} s quicker`, tone: 'go', abs }
    : { text: `${abs.toFixed(digits)} s slower`, tone: 'foul', abs };
}

export const TONE_TEXT = {
  go: 'text-signal-go',
  foul: 'text-signal-foul',
  flat: 'text-white/60',
};

// ─── errors ──────────────────────────────────────────────────────────────────
export function friendlyError(message) {
  const m = String(message || '');
  if (/failed to fetch|networkerror|load failed|network request failed|connection lost/i.test(m)) {
    return "We couldn't reach the simulation server. Check your connection and try again.";
  }
  if (/429|too many|rate/i.test(m)) {
    return "You're going a little fast. Wait a few seconds and try again.";
  }
  return m || 'Something went wrong. Please try again.';
}

export function ErrorCard({ message, onRetry }) {
  return (
    <div
      role="alert"
      className="card flex flex-col gap-3 border-signal-foul/40 bg-signal-foul/[0.08] p-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <p className="flex items-start gap-2 text-sm text-signal-foul">
        <AlertCircle size={18} className="mt-0.5 shrink-0" aria-hidden="true" />
        <span>{friendlyError(message)}</span>
      </p>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-ghost btn-sm shrink-0">
          Try again
        </button>
      )}
    </div>
  );
}

// ─── layout pieces ───────────────────────────────────────────────────────────
export function Step({ n, title, children, hint = null, id }) {
  return (
    <section id={id} className="card card-pad scroll-mt-24" aria-labelledby={`step-${n}-title`}>
      <div className="mb-4 flex items-center gap-3">
        <span className="step-badge" aria-hidden="true">
          {n}
        </span>
        <h2 id={`step-${n}-title`} className="font-display text-lg font-semibold text-white">
          {title}
        </h2>
      </div>
      {hint && <p className="-mt-2 mb-4 text-sm text-white/65">{hint}</p>}
      {children}
    </section>
  );
}

/** Disclosure that remembers its state in localStorage (never required). */
export function MoreOptions({ storageKey, label = 'More options', children, forceOpen = false }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    try {
      if (window.localStorage.getItem(storageKey) === '1') setOpen(true);
    } catch {
      /* storage unavailable — stay collapsed */
    }
  }, [storageKey]);

  const shown = open || forceOpen;
  const toggle = () => {
    const next = !open;
    setOpen(next);
    try {
      window.localStorage.setItem(storageKey, next ? '1' : '0');
    } catch {
      /* ignore */
    }
  };

  return (
    <div>
      <button
        type="button"
        onClick={toggle}
        aria-expanded={shown}
        aria-controls={`${storageKey}-panel`}
        className="inline-flex min-h-[44px] items-center gap-1.5 text-sm font-semibold text-accent transition-colors hover:text-accent-bright focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 rounded-md"
      >
        <ChevronDown
          size={16}
          aria-hidden="true"
          className={`transition-transform ${shown ? 'rotate-180' : ''}`}
        />
        {label}
      </button>
      <div id={`${storageKey}-panel`} hidden={!shown} className="mt-3 space-y-5">
        {children}
      </div>
    </div>
  );
}

export function RangeField({ id, label, valueText, min, max, step = 1, value, onChange, hint }) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="text-sm font-medium text-white/80">
          {label}
        </label>
        <output htmlFor={id} className="font-mono text-sm font-medium tabular-nums text-white">
          {valueText}
        </output>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="h-11 w-full cursor-pointer accent-accent"
      />
      {hint && <p className="field-hint">{hint}</p>}
    </div>
  );
}

/** Segmented two-option switch with proper pressed state. */
export function Segmented({ label, options, value, onChange, idPrefix }) {
  return (
    <div>
      <span id={`${idPrefix}-label`} className="field-label">
        {label}
      </span>
      <div className="seg-control w-full" role="group" aria-labelledby={`${idPrefix}-label`}>
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            aria-pressed={value === o.id}
            onClick={() => onChange(o.id)}
            className="flex-1"
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── manual race conditions (shared by Upgrades + Race-day setup) ───────────
// Physical envelopes for the manual overrides. Values are clamped into range
// before entering a request body; non-numeric input shows an inline hint and
// NEVER enters the body.
export const MANUAL_FIELDS = [
  { key: 'temp', label: 'Air temperature (°C)', min: -20, max: 55, step: 0.5, ph: 'e.g. 32', hint: '−20 to 55 °C' },
  { key: 'humidity', label: 'Humidity (%)', min: 0, max: 100, step: 1, ph: 'e.g. 55', hint: '0 to 100 %' },
  { key: 'altitude', label: 'Altitude above sea level (m)', min: -100, max: 5000, step: 10, ph: 'e.g. 600', hint: '−100 to 5000 m' },
];

const clampNum = (n, min, max) => Math.min(max, Math.max(min, n));

/**
 * Parse + validate a manual field. Returns:
 *  - { value: null, invalid: false }  — empty, field unused
 *  - { value: null, invalid: true }   — non-numeric, excluded from request
 *  - { value: n, invalid: false, clamped } — numeric, clamped into [min,max]
 */
export function manualFieldValue(raw, { min, max }) {
  if (raw === '' || raw == null) return { value: null, invalid: false, clamped: false };
  const n = Number(raw);
  if (!Number.isFinite(n)) return { value: null, invalid: true, clamped: false };
  return { value: clampNum(n, min, max), invalid: false, clamped: n < min || n > max };
}

export const EMPTY_MANUAL = { temp: '', humidity: '', altitude: '' };

/** Parse every manual field at once: { temp: {...}, humidity: {...}, altitude: {...} }. */
export function manualStates(manual) {
  return Object.fromEntries(MANUAL_FIELDS.map((f) => [f.key, manualFieldValue(manual[f.key], f)]));
}

/**
 * Race-condition fields for a request body — the SAME mapping for every tool:
 * a matched venue id, else the place's name with the altitude and pressure it
 * was resolved at, then the hand-set values on top (they win over the place).
 * A searched place therefore arrives with all four of altitude, temperature,
 * humidity and pressure, and the server makes no weather lookup for the run.
 */
export function conditionsBody(location, states) {
  const body = {};
  const env = environmentOverridesFromLocation(location);
  if (env.venue_id != null) body.venue_id = env.venue_id;
  else if (location) {
    const label =
      location.venue_name || location.location_name || location._label || location.resolved_name;
    if (label) body.location = label;
  }
  if (states.temp.value != null) body.ambient_temp_c = states.temp.value;
  else if (env.ambient_temp_c != null) body.ambient_temp_c = env.ambient_temp_c;
  if (states.humidity.value != null) body.humidity_pct = states.humidity.value;
  else if (env.humidity_pct != null) body.humidity_pct = env.humidity_pct;
  if (states.altitude.value != null) body.altitude_m = states.altitude.value;
  else if (env.altitude_m != null) body.altitude_m = env.altitude_m;
  if (env.pressure_hpa != null) body.pressure_hpa = env.pressure_hpa;
  return body;
}

/** The "Set conditions by hand" disclosure body. */
export function ManualConditions({ idPrefix = 'mq-manual', storageKey, manual, setManual }) {
  const states = manualStates(manual);
  const anyManual = Object.values(manual).some((v) => v !== '');
  return (
    <MoreOptions storageKey={storageKey} label="Set conditions by hand">
      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => setManual({ temp: '25', humidity: '', altitude: '0' })}
          className="btn-ghost btn-sm"
        >
          <Wind size={16} aria-hidden="true" /> Standard conditions (sea level, 25 °C)
        </button>
        {anyManual && (
          <button
            type="button"
            onClick={() => setManual(EMPTY_MANUAL)}
            className="min-h-[44px] text-sm font-medium text-white/70 underline-offset-2 hover:text-white hover:underline"
          >
            Clear
          </button>
        )}
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {MANUAL_FIELDS.map((f) => {
          const st = states[f.key];
          const flagged = st.invalid || st.clamped;
          return (
            <div key={f.key}>
              <label htmlFor={`${idPrefix}-${f.key}`} className="field-label">
                {f.label}
              </label>
              <input
                id={`${idPrefix}-${f.key}`}
                type="number"
                inputMode="decimal"
                min={f.min}
                max={f.max}
                step={f.step}
                value={manual[f.key]}
                onChange={(e) => setManual((m) => ({ ...m, [f.key]: e.target.value }))}
                placeholder={f.ph}
                aria-invalid={st.invalid || undefined}
                aria-describedby={flagged ? `${idPrefix}-${f.key}-msg` : undefined}
                className={`input-base font-mono ${
                  flagged ? 'border-signal-stage/70 focus:border-signal-stage' : ''
                }`}
              />
              {flagged && (
                <p id={`${idPrefix}-${f.key}-msg`} className="field-hint text-signal-stage">
                  {st.invalid ? `Enter a number (${f.hint})` : `Adjusted to fit ${f.hint}`}
                </p>
              )}
            </div>
          );
        })}
      </div>
      <p className="field-hint">Values you type here replace the ones from the place above.</p>
    </MoreOptions>
  );
}
