'use client';

/**
 * StageDots — the STAGED v4 signature motif (see web/DESIGN.md §4).
 *
 * Three 6px dots: pre-stage · stage · GO (amber, amber, green). Used as
 * section eyebrows, list bullets and loading accents — the ONLY decorative
 * ornament in the system.
 *
 *   <StageDots />                    // static
 *   <StageDots animate />           // ONE amber→amber→green light-up on view
 *   <StageDots foul />              // third dot red — errors/404 only
 *   <StageDots size={8} />
 *
 * `animate` is opacity-only keyframes with per-dot delay; reduced-motion
 * renders the static state (the animation is `both`-filled from a dimmed
 * start, so we simply skip the class).
 */

import { useEffect, useState } from 'react';

export default function StageDots({
  animate = false,
  foul = false,
  size = 6,
  className = '',
}) {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    if (!animate) return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReduced(mq.matches);
  }, [animate]);

  const run = animate && !reduced;
  const dot = (color, delayMs) => (
    <span
      aria-hidden="true"
      className={[
        'rounded-full',
        color,
        run ? 'animate-stage-light' : '',
      ].join(' ')}
      style={{
        width: size,
        height: size,
        ...(run ? { animationDelay: `${delayMs}ms` } : null),
      }}
    />
  );

  return (
    <span className={['inline-flex items-center gap-[5px]', className].join(' ')}>
      {dot('bg-signal-stage', 0)}
      {dot('bg-signal-stage', 220)}
      {dot(foul ? 'bg-signal-foul' : 'bg-signal-go', 440)}
    </span>
  );
}
