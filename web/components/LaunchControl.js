'use client';

/**
 * LaunchControl — BITKRAFT's "DRAG & HOLD TO ENTER" translated to
 * launch control, v2.
 *
 * v2 (premium pass): the control carries its own miniature staging
 * lights — a horizontal strip of lamps INSIDE the button that mirrors
 * the big NHRA tree using the exact same SEQUENCE timing table. The
 * countdown is therefore always in the user's sightline (the v1 flaw:
 * tree above the fold, button below — you could never watch both).
 * Label typography now matches the primary CTA (display bold), the
 * launch run plays on the dial for ~1.5s BEFORE the page glides to
 * telemetry, and focus-visible rings make it keyboard-premium.
 *
 * Hold: tree + mini-lamps restart their sequence, revs build on the
 * H2R dial (shared MotionValue, max(scroll, hold) in page.js).
 * Release on green: run plays, then glide to #telemetry.
 * Release early: red light on BOTH trees — a real foul.
 */

import { useEffect, useRef, useState } from 'react';
import { animate } from 'framer-motion';
import { SEQUENCE } from './ChristmasTree';

const GREEN_AT_MS = 1100;   // must match ChristmasTree SEQUENCE green timing
const LAUNCH_RPM_P = 0.36;  // dial progress at the two-step limiter (~13k rpm)
const RUN_VIEW_MS = 1500;   // let the ET run play on the dial before gliding
const RESET_MS = 5200;


export default function LaunchControl({ holdMV, onTreeRun, onFoul, onLaunch, className = '' }) {
  const [status, setStatus] = useState('idle'); // idle | staging | launched | foul
  const [lit, setLit] = useState(() => new Set(['pre-stage']));
  const animRef = useRef(null);
  const downAtRef = useRef(0);
  const timersRef = useRef([]);
  const resetTimerRef = useRef(null);
  const statusRef = useRef(status);
  statusRef.current = status;

  const clearTimers = () => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  };

  const stopAnim = () => {
    if (animRef.current) {
      animRef.current.stop();
      animRef.current = null;
    }
  };

  const press = () => {
    if (statusRef.current === 'staging') return;
    clearTimeout(resetTimerRef.current);
    clearTimers();
    stopAnim();
    setStatus('staging');
    onFoul?.(false);
    onTreeRun?.();          // restart the big pro tree
    // …and run the same sequence on the in-button mini lamps.
    setLit(new Set(['pre-stage']));
    timersRef.current = SEQUENCE.map(({ id, at }) =>
      setTimeout(() => {
        setLit((prev) => {
          if (prev.has(id)) return prev;
          const next = new Set(prev);
          next.add(id);
          return next;
        });
      }, at)
    );
    downAtRef.current = performance.now();
    holdMV.set(0);
    animRef.current = animate(holdMV, LAUNCH_RPM_P, {
      duration: 1.05,
      ease: 'easeOut',
    });
  };

  const release = () => {
    if (statusRef.current !== 'staging') return;
    const held = performance.now() - downAtRef.current;
    stopAnim();
    clearTimers();

    if (held < GREEN_AT_MS) {
      // ─ red light ─ left before green
      setStatus('foul');
      onFoul?.(true);
      animRef.current = animate(holdMV, 0, { duration: 0.55, ease: 'easeInOut' });
      resetTimerRef.current = setTimeout(() => {
        onFoul?.(false);
        setLit(new Set(['pre-stage']));
        setStatus('idle');
      }, 2100);
      return;
    }

    // ─ clean launch ─ play the run on the dial first, then glide down
    setStatus('launched');
    onLaunch?.(); // e.g. the TronGrid fires a light-cycle burst
    animRef.current = animate(holdMV, 1, {
      duration: 2.4,
      ease: [0.16, 1, 0.3, 1],
    });
    const reduced =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    timersRef.current.push(
      setTimeout(() => {
        document.getElementById('telemetry')?.scrollIntoView({
          behavior: reduced ? 'auto' : 'smooth',
          block: 'start',
        });
      }, RUN_VIEW_MS)
    );
    resetTimerRef.current = setTimeout(() => {
      holdMV.set(0); // hand the needle back to scroll-driving, quietly
      setLit(new Set(['pre-stage']));
      setStatus('idle');
    }, RESET_MS);
  };

  useEffect(() => {
    return () => {
      stopAnim();
      clearTimers();
      clearTimeout(resetTimerRef.current);
    };
  }, []);

  const LABELS = {
    idle: 'Hold to launch',
    staging: 'Release on green…',
    launched: 'ET 9.62 — clean run',
    foul: 'Red light — too soon',
  };

  const tone = {
    idle: 'border-brand-orange/40 hover:border-brand-orange text-brand-orange',
    staging: 'border-brand-amber text-brand-amber',
    launched: 'border-brand-green text-brand-green',
    foul: 'border-brand-red text-brand-red',
  }[status];

  const lampClass = (id) => {
    if (id === 'red') {
      return status === 'foul'
        ? 'bg-brand-red shadow-[0_0_8px_rgba(239,68,68,0.9)]'
        : 'bg-white/10';
    }
    const on = lit.has(id) && status !== 'foul';
    if (id === 'pre-stage' && on && status === 'idle') {
      // invite affordance: pre-stage breathes while the control is idle
      return 'bg-brand-amber/90 animate-pulse shadow-[0_0_6px_rgba(245,158,11,0.7)]';
    }
    if (!on) return 'bg-white/10';
    if (id === 'green') return 'bg-brand-green shadow-[0_0_8px_rgba(34,197,94,0.9)]';
    return 'bg-brand-amber shadow-[0_0_6px_rgba(245,158,11,0.8)]';
  };

  return (
    <button
      type="button"
      onPointerDown={(e) => {
        e.preventDefault();
        e.currentTarget.setPointerCapture?.(e.pointerId);
        press();
      }}
      onPointerUp={release}
      onPointerCancel={release}
      onContextMenu={(e) => e.preventDefault()}
      onKeyDown={(e) => {
        if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) {
          e.preventDefault();
          press();
        }
      }}
      onKeyUp={(e) => {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          release();
        }
      }}
      aria-label="Launch control: press and hold, release when the tree goes green"
      className={[
        'relative inline-flex flex-col items-center justify-center gap-2 px-7 py-3 rounded-md border-2',
        'font-display font-bold transition-colors select-none touch-none overflow-hidden',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-orange/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black',
        tone,
        className,
      ].join(' ')}
      style={{ WebkitTapHighlightColor: 'transparent' }}
    >
      {/* staging fill — grows with revs while held */}
      <span
        className={[
          'absolute inset-0 origin-left bg-current opacity-10 transition-transform',
          status === 'staging' ? 'scale-x-100 duration-[1100ms] ease-out' : 'scale-x-0 duration-300',
        ].join(' ')}
        aria-hidden="true"
      />

      {/* miniature pro tree — same SEQUENCE as the big one */}
      <span className="relative flex items-center gap-[5px]" aria-hidden="true">
        <span className={`w-1.5 h-1.5 rounded-full transition-colors duration-200 ${lampClass('pre-stage')}`} />
        <span className={`w-1.5 h-1.5 rounded-full transition-colors duration-200 ${lampClass('stage')}`} />
        <span className="w-1 h-px bg-white/15" />
        <span className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${lampClass('amber-1')}`} />
        <span className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${lampClass('amber-2')}`} />
        <span className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${lampClass('amber-3')}`} />
        <span className="w-1 h-px bg-white/15" />
        <span className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${lampClass('green')}`} />
        <span className={`w-2.5 h-2.5 rounded-full transition-colors duration-200 ${lampClass('red')}`} />
      </span>

      <span className="relative leading-none">{LABELS[status]}</span>
    </button>
  );
}
