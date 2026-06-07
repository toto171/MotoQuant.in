'use client';

/**
 * BootSequence — first-visit terminal boot overlay.
 *
 * BITKRAFT-inspired (their ASCII/`var pagesToLoad` boot screen), with
 * the discipline they skipped: HARD-CAPPED at ~1.6s, purely cosmetic
 * (never gates on real asset loads), shown once per session, skipped
 * entirely for prefers-reduced-motion, dismissible by any input.
 *
 * Renders nothing during SSR (client decides after mount), so SEO,
 * hydration and LCP HTML are untouched.
 *
 * Stats arrive via props from page.js so headline numbers keep a
 * single source of truth (audit_headline_stats.py hygiene).
 */

import { useEffect, useRef, useState } from 'react';
import ScoreboardDigits from './ScoreboardDigits';

const BOOT_MS = 1550;
const FADE_MS = 320;
const KEY = 'mq-boot-seen';

export default function BootSequence({ bikes, parts, venues, tires }) {
  const [phase, setPhase] = useState('idle'); // idle | run | fade | done
  const [pct, setPct] = useState(0);
  const [lineCount, setLineCount] = useState(0);
  const doneRef = useRef(false);

  const LINES = [
    '> MOTOQUANT PRO — ENGINE OS',
    `// loading catalog: ${bikes} bikes · ${parts} parts · ${venues} venues`,
    `// pacejka coefficients: ${tires} tires ✓`,
    '// submodels online [15/15] · rk4 @ 1ms',
    '// baselines: K5 10.0334 · R1 10.2859 · BUSA 10.4712 ✓',
    '> staging ready_',
  ];

  // Decide on mount only — never during SSR.
  useEffect(() => {
    try {
      const reduced =
        window.matchMedia &&
        window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (reduced || sessionStorage.getItem(KEY)) return;
      sessionStorage.setItem(KEY, '1');
    } catch {
      return; // storage blocked → skip the theatre, never risk a stuck overlay
    }
    setPhase('run');
  }, []);

  // Drive percentage + line reveal off one rAF clock.
  useEffect(() => {
    if (phase !== 'run') return;
    let raf;
    const t0 = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - t0) / BOOT_MS);
      setPct(Math.floor(t * 100));
      setLineCount(Math.min(LINES.length, Math.floor(t * (LINES.length + 1))));
      if (t < 1) {
        raf = requestAnimationFrame(tick);
      } else if (!doneRef.current) {
        doneRef.current = true;
        setPhase('fade');
      }
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  // Fade out, then unmount.
  useEffect(() => {
    if (phase !== 'fade') return;
    const t = setTimeout(() => setPhase('done'), FADE_MS);
    return () => clearTimeout(t);
  }, [phase]);

  // Any input skips.
  useEffect(() => {
    if (phase !== 'run') return;
    const skip = () => {
      doneRef.current = true;
      setPhase('fade');
    };
    window.addEventListener('pointerdown', skip);
    window.addEventListener('keydown', skip);
    return () => {
      window.removeEventListener('pointerdown', skip);
      window.removeEventListener('keydown', skip);
    };
  }, [phase]);

  if (phase === 'idle' || phase === 'done') return null;

  return (
    <div
      className="fixed inset-0 z-[100] bg-black flex flex-col justify-between transition-opacity"
      style={{
        opacity: phase === 'fade' ? 0 : 1,
        transitionDuration: `${FADE_MS}ms`,
      }}
      aria-hidden="true"
    >
      {/* progress hairline */}
      <div className="absolute top-0 left-0 h-[2px] bg-brand-orange" style={{ width: `${pct}%` }} />

      {/* corner brackets */}
      <span className="absolute top-3 left-3 w-5 h-5 border-l border-t border-white/25" />
      <span className="absolute top-3 right-3 w-5 h-5 border-r border-t border-white/25" />
      <span className="absolute bottom-3 left-3 w-5 h-5 border-l border-b border-white/25" />
      <span className="absolute bottom-3 right-3 w-5 h-5 border-r border-b border-white/25" />

      {/* boot log */}
      <div className="px-6 sm:px-10 pt-10 font-mono text-[11px] sm:text-xs leading-relaxed text-white/70 whitespace-pre-wrap">
        {LINES.slice(0, lineCount).map((l, i) => (
          <div key={i} className={l.startsWith('>') ? 'text-brand-orange' : ''}>
            {l}
          </div>
        ))}
        <span className="inline-block w-2 h-3.5 bg-brand-orange/80 align-middle animate-pulse" />
      </div>

      {/* timing-board percentage */}
      <div className="px-6 sm:px-10 pb-10 flex items-end justify-between">
        <div className="font-mono text-[10px] tracking-[0.3em] uppercase text-white/35">
          The physics of faster
        </div>
        <div className="flex items-end gap-3">
          <ScoreboardDigits
            value={String(pct).padStart(2, '0')}
            h={72}
            color="#FF5E1F"
          />
          <span className="font-mono text-white/40 text-sm pb-1">%</span>
        </div>
      </div>
    </div>
  );
}
