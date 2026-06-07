'use client';

/**
 * CodeComment — section-transition microcopy in engine-log voice.
 *
 * BITKRAFT decorates section breaks with fake code comments
 * (`// ENTERING 3RD DIMENSION...`). Ours are real engine vocabulary:
 *
 *   <CodeComment>staging: two-step armed</CodeComment>
 *   → // STAGING: TWO-STEP ARMED_
 *
 * Static text + CSS-blinking cursor. Zero JS work after mount.
 */

export default function CodeComment({ children, className = '', center = false }) {
  return (
    <div
      className={[
        'font-mono text-[11px] tracking-[0.22em] uppercase text-white/35 select-none',
        center ? 'text-center' : '',
        className,
      ].join(' ')}
      aria-hidden="true"
    >
      <span className="text-brand-orange/70">//&nbsp;</span>
      {children}
      <span className="cc-cursor text-brand-orange/70">_</span>
    </div>
  );
}
