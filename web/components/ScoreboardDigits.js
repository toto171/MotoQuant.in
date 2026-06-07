'use client';

/**
 * ScoreboardDigits — drag-strip timing-board numerals.
 *
 * Seven-segment SVG digits modelled on strip scoreboard / ET display
 * boards (the BITKRAFT "bit font" idea translated to drag racing —
 * timing boards are OUR pixel font). Hand-rolled polygons, zero font
 * assets, zero network cost, perfectly tabular.
 *
 *   <ScoreboardDigits value="10.0334" h={36} />
 *   <ScoreboardCounter value={501} h={34} />   // counts up on first view
 *
 * Unlit "ghost" segments render at low opacity behind the lit ones,
 * like a real LED board. Pure static SVG — no rAF unless counting.
 */

import { useEffect, useRef, useState } from 'react';
import { useInView } from 'framer-motion';

// Segment polygons on a 0..56 × 0..80 grid, thickness ~8 with bevels.
const SEGS = {
  A: '6,2 50,2 42,10 14,10',
  F: '2,6 10,14 10,34 2,40',
  B: '54,6 54,40 46,34 46,14',
  G: '8,40 14,36 42,36 48,40 42,44 14,44',
  E: '2,40 10,46 10,66 2,74',
  C: '54,40 54,74 46,66 46,46',
  D: '6,78 14,70 42,70 50,78',
};
const ALL = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];

const DIGIT_MAP = {
  0: 'ABCDEF',
  1: 'BC',
  2: 'ABGED',
  3: 'ABGCD',
  4: 'FGBC',
  5: 'AFGCD',
  6: 'AFGECD',
  7: 'ABC',
  8: 'ABCDEFG',
  9: 'ABCDFG',
  '-': 'G',
};

const GHOST_FILL = 'rgba(255,255,255,0.055)';

function Digit({ char, h, color, ghost }) {
  const lit = DIGIT_MAP[char] || '';
  const w = (h * 56) / 80;
  return (
    <svg
      viewBox="0 0 56 80"
      width={w}
      height={h}
      className="block flex-shrink-0"
      aria-hidden="true"
    >
      {ALL.map((s) => {
        const on = lit.includes(s);
        if (!on && !ghost) return null;
        return (
          <polygon
            key={s}
            points={SEGS[s]}
            fill={on ? color : GHOST_FILL}
          />
        );
      })}
    </svg>
  );
}

function Dot({ h, color }) {
  const w = (h * 16) / 80;
  return (
    <svg viewBox="0 0 16 80" width={w} height={h} className="block flex-shrink-0" aria-hidden="true">
      <rect x="3" y="68" width="10" height="10" rx="1.5" fill={color} />
    </svg>
  );
}

function Colon({ h, color }) {
  const w = (h * 16) / 80;
  return (
    <svg viewBox="0 0 16 80" width={w} height={h} className="block flex-shrink-0" aria-hidden="true">
      <rect x="3" y="22" width="10" height="10" rx="1.5" fill={color} />
      <rect x="3" y="50" width="10" height="10" rx="1.5" fill={color} />
    </svg>
  );
}

export default function ScoreboardDigits({
  value,
  h = 36,
  color = '#FF5E1F',
  ghost = true,
  className = '',
  label,
}) {
  const chars = String(value).split('');
  const gap = Math.max(2, Math.round(h * 0.09));
  return (
    <span
      className={['inline-flex items-end select-none', className].join(' ')}
      style={{ gap }}
      role={label ? 'img' : undefined}
      aria-label={label || String(value)}
    >
      {chars.map((c, i) => {
        if (c === '.') return <Dot key={i} h={h} color={color} />;
        if (c === ':') return <Colon key={i} h={h} color={color} />;
        if (c === ' ') return <span key={i} style={{ width: h * 0.2 }} />;
        return <Digit key={i} char={c} h={h} color={color} ghost={ghost} />;
      })}
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
