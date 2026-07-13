'use client';

/**
 * ScoreboardDigits — timing-board numerals (STAGED v4).
 *
 * v3 rendered hand-rolled seven-segment SVG polygons. v4 renders clean
 * JetBrains Mono tabular digits — the timeslip voice — while keeping the
 * exact component API so every call site (blog posts, features, whitepaper,
 * /r/[id], simulator) re-skins without churn:
 *
 *   <ScoreboardDigits value="10.0334" h={36} />
 *   <ScoreboardCounter value={541} h={34} />   // counts up on first view
 *
 * `h` is the legacy digit-height prop — mapped to font-size. Legacy brand
 * hexes passed as `color` are remapped onto the v4 palette so untouched
 * callers land on-system.
 */

import { useEffect, useRef, useState } from 'react';
import { useInView } from 'framer-motion';

// Legacy → v4 palette remap. Old orange was the seven-seg default and is
// deliberately mapped to white (numbers are neutral; volt is reserved for
// emphasis — pass '#C9F231' explicitly where the design calls for it).
const COLOR_REMAP = {
  '#FF5E1F': '#FFFFFF',
  '#FF8F57': '#FFFFFF',
  '#CC4000': '#FFFFFF',
  '#22C55E': '#34D97B',
  '#F59E0B': '#FFB224',
  '#EF4444': '#FF5A48',
  '#00FFB2': '#6FE3B2',
};

function resolveColor(color) {
  if (!color) return '#FFFFFF';
  const key = String(color).toUpperCase();
  return COLOR_REMAP[key] || color;
}

export default function ScoreboardDigits({
  value,
  h = 36,
  color = '#FF5E1F',
  ghost = true, // kept for API compatibility; no ghost segments in v4
  className = '',
  label,
}) {
  void ghost;
  return (
    <span
      className={['inline-flex select-none items-baseline font-mono font-bold tabular-nums', className].join(' ')}
      style={{ fontSize: h, lineHeight: 1, color: resolveColor(color), letterSpacing: '0.01em' }}
      role={label ? 'img' : undefined}
      aria-label={label || String(value)}
    >
      {String(value)}
    </span>
  );
}

/**
 * ScoreboardCounter — integer count-up on first viewport entry.
 * rAF + ease-out cubic; respects prefers-reduced-motion (snaps).
 */
export function ScoreboardCounter({
  value,
  h = 34,
  color = '#FF5E1F',
  ghost = true,
  duration = 1100,
  className = '',
}) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: '0px 0px -10% 0px' });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const reduced =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) {
      setDisplay(value);
      return;
    }
    let raf;
    const t0 = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - t0) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(Math.round(value * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, value, duration]);

  return (
    <span ref={ref} className={className}>
      <ScoreboardDigits value={display} h={h} color={color} ghost={ghost} label={String(value)} />
    </span>
  );
}
