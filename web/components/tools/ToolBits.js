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
import { AlertCircle, ChevronDown } from 'lucide-react';

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
    return "You're going a little fast — wait a few seconds and try again.";
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
export function Step({ n, title, children, hint = null }) {
  return (
    <section className="card card-pad" aria-labelledby={`step-${n}-title`}>
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
