'use client';

/**
 * CodeComment — section-transition microcopy (STAGED v4 skin).
 *
 * Legacy API kept (children, className, center) so blog posts, simulator,
 * account and whitepaper call sites re-skin without churn. v4 renders the
 * label voice with the StageDots motif instead of the engine-log `//` +
 * blinking cursor.
 *
 *   <CodeComment>staging: two-step armed</CodeComment>
 */

import StageDots from './StageDots';

export default function CodeComment({ children, className = '', center = false }) {
  return (
    <div
      className={[
        'flex items-center gap-2.5 font-mono text-[10px] font-medium tracking-[0.25em] uppercase text-white/40 select-none',
        center ? 'justify-center text-center' : '',
        className,
      ].join(' ')}
      aria-hidden="true"
    >
      <StageDots size={5} />
      <span>{children}</span>
    </div>
  );
}
