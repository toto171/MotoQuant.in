/**
 * CodeComment — small section label (kept API: children, className, center).
 * v6: a quiet sentence-case line; no tri-dot lamps, no mono all-caps.
 * Prefer PageHeader / .eyebrow in new code. Server-component safe.
 */

export default function CodeComment({ children, className = '', center = false }) {
  return (
    <div
      className={[
        'flex items-center text-xs font-medium text-white/55 select-none',
        center ? 'justify-center text-center' : '',
        className,
      ].join(' ')}
    >
      <span>{children}</span>
    </div>
  );
}
