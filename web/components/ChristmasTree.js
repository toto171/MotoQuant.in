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
 *              ●               red — foul (intentionally never lit)
 *
 * Sequence — TIMER-DRIVEN, fires once on first user scroll.
 *
 * The first version drove every lamp off scroll progress and only fully
 * lit the green when the user had scrolled through 78% of the hero.
 * Real visitors don't scroll that precisely, so most never saw the
 * green. New design: pre-stage starts lit (the bike has rolled up to
 * the lights), then any scroll movement triggers a real Pro-Tree
 * sequence: stage at +200ms, ambers at +400/600/800ms, GREEN at
 * +1200ms. After GREEN it stays lit. Total ~1.2s — the same timing
 * a real Pro Tree would run.
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

// id, color, ms-after-trigger
const SEQUENCE = [
  { id: 'pre-stage', color: 'amber', at:    0 },
  { id: 'stage',     color: 'amber', at:  150 },
  { id: 'amber-1',   color: 'amber', at:  350 },
  { id: 'amber-2',   color: 'amber', at:  550 },
  { id: 'amber-3',   color: 'amber', at:  750 },
  { id: 'green',     color: 'green', at: 1100 },
];

function smallBulbClass(on) {
  return on
    ? 'bg-brand-amber border-yellow-300 shadow-lamp-amber animate-lamp-pulse'
    : 'bg-ink-3 border-ink-4 shadow-[inset_0_2px_4px_rgba(0,0,0,0.6)]';
}

function largeBulbClass(on, color) {
  if (!on) return 'bg-ink-3 border-ink-4 shadow-[inset_0_4px_8px_rgba(0,0,0,0.7)]';
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
      <div className="mt-1.5 sm:mt-2 flex items-center justify-center gap-2 sm:gap-3 lg:gap-4">
        <span
          className={[
            'w-3 h-3 sm:w-4 sm:h-4 lg:w-5 lg:h-5 rounded-full border transition-all duration-300',
            smallBulbClass(on),
          ].join(' ')}
        />
        <span
          className={[
            'w-3 h-3 sm:w-4 sm:h-4 lg:w-5 lg:h-5 rounded-full border transition-all duration-300',
            smallBulbClass(on),
          ].join(' ')}
        />
      </div>
    </div>
  );
}

export default function ChristmasTree({ className = '', runSignal = 0, foul = false }) {
  // Pre-stage starts lit immediately (bike has rolled up to the lights).
  const [lit, setLit] = useState(() => new Set(['pre-stage']));
  // Number of sequence runs so far. 0 = not yet fired; each increment
  // restarts the full pro-tree sequence (LaunchControl re-arms via
  // runSignal; the first run also auto-fires on scroll/dwell as before).
  const [runCount, setRunCount] = useState(0);

  // First user scroll OR first 800 ms of dwell → fire the sequence.
  // Either signal is sufficient — whichever comes first wins.
  useEffect(() => {
    if (runCount > 0) return;

    function fire() {
      setRunCount((c) => (c === 0 ? 1 : c));
    }

    const onScroll = () => {
      if (window.scrollY > 4) fire();
    };
    window.addEventListener('scroll', onScroll, { passive: true });

    // Fallback: if the user is reading without scrolling, fire after
    // a short dwell so the green-light moment isn't gated entirely on
    // scroll behaviour.
    const dwell = setTimeout(fire, 1200);

    return () => {
      window.removeEventListener('scroll', onScroll);
      clearTimeout(dwell);
    };
  }, [runCount]);

  // External restart — LaunchControl increments runSignal on every hold.
  useEffect(() => {
    if (runSignal > 0) setRunCount((c) => c + 1);
  }, [runSignal]);

  // Each run: reset to pre-stage, then schedule lamps per SEQUENCE.
  useEffect(() => {
    if (!runCount) return;
    setLit(new Set(['pre-stage']));
    const timeouts = SEQUENCE.map(({ id, at }) =>
      setTimeout(() => {
        setLit((prev) => {
          if (prev.has(id)) return prev;
          const next = new Set(prev);
          next.add(id);
          return next;
        });
      }, at)
    );
    return () => timeouts.forEach(clearTimeout);
  }, [runCount]);

  const greenOn = lit.has('green') && !foul;

  return (
    <div className={['relative select-none', className].join(' ')} aria-hidden="true">
      {/* Soft green halo when GO lights up */}
      <motion.div
        className="absolute -inset-6 rounded-3xl bg-tree-glow blur-2xl pointer-events-none"
        animate={{ opacity: greenOn ? 1 : 0 }}
        transition={{ duration: 0.5 }}
      />

      <div className="relative w-[150px] sm:w-[200px] lg:w-[220px] rounded-2xl bg-ink-1/90 border border-white/10 backdrop-blur-sm p-3 sm:p-4 lg:p-5">
        {/* Crown rail */}
        <div className="mx-auto mb-3 h-1 w-12 rounded-full bg-white/10" />

        {/* Pre-stage panel */}
        <StageRow label="Pre-Stage" on={lit.has('pre-stage')} />

        {/* Stage panel */}
        <div className="mt-3">
          <StageRow label="Stage" on={lit.has('stage')} />
        </div>

        {/* Vertical mast */}
        <div className="mt-4 mx-auto w-[3px] h-3 bg-white/10 rounded-full" />

        {/* The 3 amber + green + red column */}
        <div className="mt-2 flex flex-col items-center gap-1.5 sm:gap-2.5 lg:gap-3.5">
          <span
            className={[
              'w-[40px] sm:w-[52px] lg:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(lit.has('amber-1'), 'amber'),
            ].join(' ')}
          />
          <span
            className={[
              'w-[40px] sm:w-[52px] lg:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(lit.has('amber-2'), 'amber'),
            ].join(' ')}
          />
          <span
            className={[
              'w-[40px] sm:w-[52px] lg:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(lit.has('amber-3'), 'amber'),
            ].join(' ')}
          />
          <span
            className={[
              'w-[40px] sm:w-[52px] lg:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(greenOn, 'green'),
            ].join(' ')}
          />
          <span
            className={[
              'w-[40px] sm:w-[52px] lg:w-[64px] aspect-square rounded-full border-2 transition-all duration-300',
              largeBulbClass(foul, 'red'),
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
