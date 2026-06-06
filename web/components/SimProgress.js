'use client';

/**
 * SimProgress — real progress bar for simulation work.
 *
 * Replaces the old rotating spinners across the site. Two data modes:
 *
 *  - determinate: `progress` is a 0..1 float (from the /api/jobs poller) —
 *    the fill tracks real backend progress (RK4 distance covered, sweep
 *    counts, candidate scoring…) and the percentage is shown.
 *  - staged: `progress` is null (quick sim / cold start / legacy fallback) —
 *    an animated sweep runs and the caption escalates to an honest
 *    "waking the engine" message when the wait smells like a free-tier
 *    cold start.
 *
 * Variants: default (caption row + bar), `compact` (inline pill for nav
 * chips), `edge` (bare 3px strip pinned to a card's top edge).
 */

import { useEffect, useState } from 'react';

const SWEEP_CSS = `
@keyframes mq-progress-sweep {
  0%   { transform: translateX(-110%); }
  100% { transform: translateX(420%); }
}
.mq-progress-sweep { animation: mq-progress-sweep 1.4s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) {
  .mq-progress-sweep { animation: none; width: 100% !important; opacity: 0.5; }
}
`;

const COLD_START_AFTER_S = 4;
const COLD_START_MSG =
  'Waking the simulation engine — a cold start can take up to a minute';

export default function SimProgress({
  active = false,
  progress = null,
  stage = '',
  label = 'Running simulation',
  compact = false,
  edge = false,
  onStop = null,
  className = '',
}) {
  const [elapsedS, setElapsedS] = useState(0);

  useEffect(() => {
    if (!active) {
      setElapsedS(0);
      return undefined;
    }
    const t0 = Date.now();
    const id = setInterval(() => setElapsedS((Date.now() - t0) / 1000), 500);
    return () => clearInterval(id);
  }, [active]);

  if (!active) return null;

  const determinate = typeof progress === 'number' && progress > 0;
  const pct = determinate ? Math.min(100, Math.round(progress * 100)) : null;
  const caption =
    stage ||
    (!determinate && elapsedS >= COLD_START_AFTER_S ? COLD_START_MSG : label);

  const aria = {
    role: 'progressbar',
    'aria-valuemin': 0,
    'aria-valuemax': 100,
    ...(pct != null ? { 'aria-valuenow': pct } : {}),
    'aria-label': caption,
  };

  const fill = determinate ? (
    <div
      className="h-full rounded-full bg-gradient-to-r from-[#FF5E1F] to-[#FF7A00] transition-[width] duration-300 ease-linear"
      style={{ width: `${Math.max(pct, 2)}%` }}
    />
  ) : (
    <div className="mq-progress-sweep h-full w-1/3 rounded-full bg-gradient-to-r from-transparent via-[#FF5E1F] to-transparent" />
  );

  if (edge) {
    return (
      <div className={`h-[3px] overflow-hidden ${className}`} {...aria}>
        <style>{SWEEP_CSS}</style>
        {fill}
      </div>
    );
  }

  if (compact) {
    return (
      <div className={`flex items-center gap-2 ${className}`} {...aria}>
        <style>{SWEEP_CSS}</style>
        <div className="w-24 h-1 rounded-full bg-white/[0.08] overflow-hidden">{fill}</div>
        <span className="text-[10px] text-orange-400 tabular-nums whitespace-nowrap">
          {pct != null ? `${pct}%` : `${label}…`}
        </span>
        {onStop && (
          <button
            type="button"
            onClick={onStop}
            className="text-[10px] text-gray-500 hover:text-red-400 transition-colors whitespace-nowrap"
          >
            ■ Stop
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={className} {...aria}>
      <style>{SWEEP_CSS}</style>
      <div className="flex items-baseline justify-between mb-1.5 gap-3">
        <span className="text-[10px] text-gray-500 uppercase tracking-widest font-medium truncate">
          {caption}
        </span>
        {pct != null && (
          <span className="text-xs font-mono font-bold text-orange-400 tabular-nums shrink-0">
            {pct}%
          </span>
        )}
        {onStop && (
          <button
            type="button"
            onClick={onStop}
            className="text-[10px] uppercase tracking-widest text-gray-500 hover:text-red-400 transition-colors shrink-0"
          >
            ■ Stop
          </button>
        )}
      </div>
      <div className="h-1.5 rounded-full bg-white/[0.08] overflow-hidden">{fill}</div>
    </div>
  );
}
