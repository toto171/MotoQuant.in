'use client';

/**
 * ChristmasTree — NHRA-accurate drag-strip pro tree.
 *
 * Layout (top → bottom), matching real-world signage:
 *
 *      ┌───────────────────┐
 *      │    PRE-STAGE      │
 *      │  (•)         (•)  │   2 small amber bulbs (paired)
 *      ├───────────────────┤
 *      │      STAGE        │
 *      │  (•)         (•)  │   2 small amber bulbs (paired)
 *      └───────────────────┘
 *              ●               large amber  (countdown 3)
 *              ●               large amber  (countdown 2)
 *              ●               large amber  (countdown 1)
 *              ●               GREEN — go
 *              ●               red — foul (intentionally never lit
 *                                          on the marketing landing)
 *
 * Sequencing on hero scroll progress 0..1:
 *
 *   0.00 → bike approaches:   pre-stage pair on
 *   0.10 → bike fully staged: stage pair on (pre-stage stays on)
 *   0.30 → amber #1 (top)     on
 *   0.45 → amber #2 (mid)     on
 *   0.60 → amber #3 (bottom)  on
 *   0.78 → GREEN — go          on
 *
 * The red lamp is rendered to keep the geometry honest but is never
 * activated by the scroll progression — there's no false start on a
 * marketing site.
 */

import { useEffect, useState } from 'react';
import { motion, useMotionValueEvent } from 'framer-motion';

// Threshold list mapping scroll progress → which logical lamps light.
// The order in this array IS the lighting order; index N lights when
// progress ≥ THRESHOLDS[N].
const THRESHOLDS = [
  { id: 'pre-stage', at: 0.00 },
  { id: 'stage',     at: 0.10 },
  { id: 'amber-1',   at: 0.30 },
  { id: 'amber-2',   at: 0.45 },
  { id: 'amber-3',   at: 0.60 },
  { id: 'green',     at: 0.78 },
];

function smallBulbClass(on, color = 'amber') {
  if (!on) {
    return 'bg-ink-3 border-ink-4 shadow-[inset_0_2px_4px_rgba(0,0,0,0.6)]';
  }
  if (color === 'amber') {
    return 'bg-brand-amber border-yellow-300 shadow-lamp-amber animate-lamp-pulse';
  }
  return 'bg-brand-red border-red-300 shadow-lamp-red';
}

function largeBulbClass(on, color) {
  if (!on) {
    return 'bg-ink-3 border-ink-4 shadow-[inset_0_4px_8px_rgba(0,0,0,0.7)]';
  }
  switch (color) {
    case 'amber':
      return 'bg-brand-amber border-yellow-300 shadow-lamp-amber animate-lamp-pulse';
    case 'green':
      return 'bg-brand-green border-green-400 shadow-lamp-green animate-lamp-pulse';
    case 'red':
      return 'bg-brand-red border-red-300 shadow-lamp-red';
    default:
      return '';
  }
}

function StageRow({ label, on }) {
  return (
    <div className="w-full flex flex-col items-stretch">
      <div
        className={[
          'mx-auto px-3 py-1 rounded-sm border font-mono text-[9px] sm:text-[10px] tracking-[0.18em] uppercase',
          on
            ? 'border-brand-amber/70 text-brand-amber bg-black/40'
            : 'border-white/10 text-white/40 bg-black/30',
        ].join(' ')}
      >
        {label}
      </div>
      <div className="mt-2 flex items-center justify-center gap-3 sm:gap-4">
        <span
          className={[
            'w-4 h-4 sm:w-5 sm:h-5 rounded-full border transition-all duration-300',
            smallBulbClass(on),
          ].join(' ')}
        />
        <span
          className={[
            'w-4 h-4 sm:w-5 sm:h-5 rounded-full border transition-all duration-300',
            smallBulbClass(on),
          ].join(' ')}
        />
      </div>
    </div>
  );
}

export default function ChristmasTree({ progress, className = '' }) {
  const [lit, setLit] = useState(() => new Set());

  useMotionValueEvent(progress, 'change', (v) => {
    const p = Math.min(1, Math.max(0, v));
    const next = new Set();
    for (const t of THRESHOLDS) {
      if (p >= t.at) next.add(t.id);
    }
    setLit((prev) => {
      // Only update if changed (string-compare set contents)
      if (prev.size !== next.size) return next;
      for (const x of prev) if (!next.has(x)) return next;
      return prev;
    });
  });

  // Initial paint from current progress value
  useEffect(() => {
    const p = progress.get?.() ?? 0;
    const init = new Set();
    for (const t of THRESHOLDS) if (p >= t.at) init.add(t.id);
    setLit(init);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const greenOn = lit.has('green');

  return (
    <div className={['relative select-none', className].join(' ')} aria-hidden="true">
      {/* Soft green halo when GO lights up */}
      <motion.div
        className="absolute -inset-6 rounded-3xl bg-tree-glow blur-2xl pointer-events-none"
        animate={{ opacity: greenOn ? 1 : 0 }}
        transition={{ duration: 0.5 }}
      />

      <div className="relative w-[180px] sm:w-[220px] rounded-2xl bg-ink-1/90 border border-white/10 backdrop-blur-sm p-4 sm:p-5">
        {/* Crown rail — small detail to evoke the real boxed sign */}
        <div className="mx-auto mb-3 h-1 w-12 rounded-full bg-white/10" />

        {/* Pre-stage panel */}
        <StageRow label="Pre-Stage" on={lit.has('pre-stage')} />

        {/* Stage panel */}
        <div className="mt-3">
          <StageRow label="Stage" on={lit.has('stage')} />
        </div>

        {/* Vertical mast — the staff that holds the big bulbs */}
        <div className="mt-4 mx-auto w-[3px] h-3 bg-white/10 rounded-full" />

        {/* The 3 amber + green + red — the actual countdown column */}
        <div className="mt-2 flex flex-col items-center gap-3 sm:gap-3.5">
          {/* Amber 1 */}
          <span
            className={[
              'w-[54px] sm:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(lit.has('amber-1'), 'amber'),
            ].join(' ')}
          />
          {/* Amber 2 */}
          <span
            className={[
              'w-[54px] sm:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(lit.has('amber-2'), 'amber'),
            ].join(' ')}
          />
          {/* Amber 3 */}
          <span
            className={[
              'w-[54px] sm:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(lit.has('amber-3'), 'amber'),
            ].join(' ')}
          />
          {/* Green — GO */}
          <span
            className={[
              'w-[54px] sm:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(greenOn, 'green'),
            ].join(' ')}
          />
          {/* Red — foul. Never lit by scroll, but rendered for accuracy. */}
          <span
            className={[
              'w-[54px] sm:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(false, 'red'),
            ].join(' ')}
          />
        </div>

        <div className="mt-3 text-center text-[9px] sm:text-[10px] font-mono tracking-[0.22em] text-white/45">
          NHRA · PRO TREE
        </div>
      </div>
    </div>
  );
}
