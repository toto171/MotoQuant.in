'use client';

/**
 * HudFrame — persistent race-instrumentation chrome.
 *
 * BITKRAFT wraps their viewport in a sci-fi HUD (notched corners,
 * SOUND ON, live X/Y mouse coords). Our translation is strip-side
 * instrumentation:
 *
 *   corners      — four thin timing-gate brackets
 *   bottom-left  — engine status: RK4 · 1MS · 15 SUBMODELS + live dot
 *   bottom-right — scroll position rendered as DISTANCE down a
 *                  quarter-mile: `D 0142.6M / 0402M` (the page IS the run)
 *
 * Costs: one passive scroll listener, rAF-throttled, writes a single
 * text node via ref (zero React re-renders). Desktop-only (hidden
 * below sm) — phones get clean edges and zero extra work.
 */

import { useEffect, useRef } from 'react';

const QUARTER_MILE_M = 402.336;

export default function HudFrame() {
  const distRef = useRef(null);

  useEffect(() => {
    let raf = 0;
    const update = () => {
      raf = 0;
      const el = distRef.current;
      if (!el) return;
      const doc = document.documentElement;
      const max = Math.max(1, doc.scrollHeight - window.innerHeight);
      const d = (window.scrollY / max) * QUARTER_MILE_M;
      el.textContent = `D ${d.toFixed(1).padStart(6, '0')}M / 0402M`;
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className="hidden sm:block pointer-events-none fixed inset-0 z-40" aria-hidden="true">
      {/* timing-gate corner brackets */}
      <span className="absolute top-2.5 left-2.5 w-5 h-5 border-l border-t border-white/20" />
      <span className="absolute top-2.5 right-2.5 w-5 h-5 border-r border-t border-white/20" />
      <span className="absolute bottom-2.5 left-2.5 w-5 h-5 border-l border-b border-white/20" />
      <span className="absolute bottom-2.5 right-2.5 w-5 h-5 border-r border-b border-white/20" />

      {/* engine status — bottom left */}
      <div className="absolute bottom-3.5 left-9 flex items-center gap-2 font-mono text-[10px] tracking-[0.22em] text-white/40 bg-black/65 rounded-sm px-2 py-1">
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-green opacity-60" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-brand-green" />
        </span>
        RK4 · 1MS · 15 SUBMODELS
      </div>

      {/* distance readout — bottom right */}
      <div
        ref={distRef}
        className="absolute bottom-3.5 right-9 font-mono text-[10px] tracking-[0.22em] text-white/40 tabular-nums bg-black/65 rounded-sm px-2 py-1"
      >
        D 0000.0M / 0402M
      </div>
    </div>
  );
}
