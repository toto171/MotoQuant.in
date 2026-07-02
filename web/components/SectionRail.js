'use client';

/**
 * SectionRail — scrollspy dot rail for long storytelling pages (landing).
 * Fixed right-center, lg+ only (phones get the bottom tool bar instead).
 * Labels slide out on hover/focus; the active section's dot burns orange.
 *
 * Pure IntersectionObserver — no scroll listeners, no re-render storms.
 * Reduced motion: jump-scroll instead of smooth, no transitions needed
 * (opacity/width only anyway).
 *
 * Props: sections = [{ id, label }] — ids must exist on the page.
 */

import { useEffect, useState } from 'react';

export default function SectionRail({ sections = [], className = '' }) {
  const [active, setActive] = useState(sections[0]?.id ?? null);

  useEffect(() => {
    if (!sections.length) return undefined;
    const io = new IntersectionObserver(
      (entries) => {
        // pick the most-visible intersecting section
        let best = null;
        for (const e of entries) {
          if (e.isIntersecting && (!best || e.intersectionRatio > best.intersectionRatio)) {
            best = e;
          }
        }
        if (best) setActive(best.target.id);
      },
      { rootMargin: '-35% 0px -45% 0px', threshold: [0, 0.25, 0.5] }
    );
    const els = sections
      .map((s) => document.getElementById(s.id))
      .filter(Boolean);
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [sections]);

  const jump = (id) => {
    const el = document.getElementById(id);
    if (!el) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
  };

  if (!sections.length) return null;

  return (
    <nav
      aria-label="Page sections"
      className={`fixed right-5 top-1/2 z-40 hidden -translate-y-1/2 lg:block ${className}`}
    >
      <ul className="flex flex-col items-end gap-3">
        {sections.map((s) => {
          const isActive = active === s.id;
          return (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => jump(s.id)}
                aria-current={isActive ? 'true' : undefined}
                className="group flex items-center gap-2 focus-visible:outline-none"
              >
                <span
                  className={`max-w-0 overflow-hidden whitespace-nowrap font-mono text-[9px] uppercase tracking-[0.22em] transition-all duration-200 group-hover:max-w-[140px] group-focus-visible:max-w-[140px] ${
                    isActive ? 'text-brand-orange' : 'text-white/50'
                  }`}
                >
                  {s.label}
                </span>
                <span
                  aria-hidden="true"
                  className={`block h-1.5 rounded-full transition-all duration-200 ${
                    isActive
                      ? 'w-5 bg-brand-orange shadow-orange-soft'
                      : 'w-1.5 bg-white/25 group-hover:bg-white/60'
                  }`}
                />
                <span className="sr-only">{s.label}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
