'use client';

/**
 * LaunchControl — BITKRAFT's "DRAG & HOLD TO ENTER" translated to
 * launch control.
 *
 * Hold the button: the pro tree restarts its real NHRA sequence and
 * the H2R dial builds revs to the two-step limiter. Release on green:
 * the run plays out (dial sweeps through ET + trap scenes) and the
 * page glides to the telemetry section. Release before green: red
 * light — a real foul, on the tree's never-otherwise-lit red bulb.
 *
 * Drives the SAME MotionValue the hero dial already reads (combined
 * with scroll progress via max() in page.js), so there's one needle
 * and zero new render loops. Pointer + keyboard operable.
 */

import { useEffect, useRef, useState } from 'react';
import { animate } from 'framer-motion';

const GREEN_AT_MS = 1100;   // must match ChristmasTree SEQUENCE green timing
const LAUNCH_RPM_P = 0.36;  // dial progress at the two-step limiter (~13k rpm)

export default function LaunchControl({ holdMV, onTreeRun, onFoul, className = '' }) {
  const [status, setStatus] = useState('idle'); // idle | staging | launched | foul
  const animRef = useRef(null);
  const downAtRef = useRef(0);
  const resetTimerRef = useRef(null);
  const statusRef = useRef(status);
  statusRef.current = status;

  const stopAnim = () => {
    if (animRef.current) {
      animRef.current.stop();
      animRef.current = null;
    }
  };

  const press = () => {
    if (statusRef.current === 'staging') return;
    clearTimeout(resetTimerRef.current);
    stopAnim();
    setStatus('staging');
    onFoul?.(false);
    onTreeRun?.();          // restart the pro-tree sequence
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

    if (held < GREEN_AT_MS) {
      // ─ red light ─ left before green
      setStatus('foul');
      onFoul?.(true);
      animRef.current = animate(holdMV, 0, { duration: 0.55, ease: 'easeInOut' });
      resetTimerRef.current = setTimeout(() => {
        onFoul?.(false);
        setStatus('idle');
      }, 1900);
      return;
    }

    // ─ clean launch ─ play the run: revs → ET clock → trap speed
    setStatus('launched');
    animRef.current = animate(holdMV, 1, {
      duration: 2.4,
      ease: [0.16, 1, 0.3, 1],
    });
    const reduced =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setTimeout(() => {
      document.getElementById('telemetry')?.scrollIntoView({
        behavior: reduced ? 'auto' : 'smooth',
        block: 'start',
      });
    }, 550);
    resetTimerRef.current = setTimeout(() => {
      holdMV.set(0); // hand the needle back to scroll-driving, quietly
      setStatus('idle');
    }, 4200);
  };

  useEffect(() => {
    return () => {
      stopAnim();
      clearTimeout(resetTimerRef.current);
    };
  }, []);

  const LABELS = {
    idle: '■ HOLD TO LAUNCH',
    staging: 'REVS BUILDING — RELEASE ON GREEN',
    launched: 'LAUNCHED · ET 9.62 ✓',
    foul: 'RED LIGHT — TOO EARLY',
  };

  const tone = {
    idle: 'border-brand-orange/40 hover:border-brand-orange text-brand-orange',
    staging: 'border-brand-amber text-brand-amber',
    launched: 'border-brand-green text-brand-green',
    foul: 'border-brand-red text-brand-red',
  }[status];

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
        'relative inline-flex items-center justify-center px-7 py-4 rounded-md border-2',
        'font-display font-bold transition-colors select-none touch-none overflow-hidden',
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
      <span className="relative font-mono text-sm tracking-[0.12em]">{LABELS[status]}</span>
    </button>
  );
}
