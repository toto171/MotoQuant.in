/**
 * Reveal / Stagger / StaggerItem / Counter — layout primitives (CLARITY v6).
 *
 * Rule 7: content is visible in the server HTML and never waits for a scroll
 * animation. These components keep their v5 names and props so existing pages
 * keep compiling, but they now render their children immediately and
 * statically. Motion is an optional enhancement only; the old
 * delay / y / duration / margin / stagger props are accepted and ignored.
 *
 *   <Reveal className="...">…</Reveal>
 *   <Stagger className="grid…"><StaggerItem>…</StaggerItem></Stagger>
 *   <Counter value={541} />          // final value, no count-up from zero
 *
 * Server-component safe (no hooks, no client-only imports).
 */

export function Reveal({
  children,
  className = '',
  as: Tag = 'div',
  // accepted for backward compatibility, intentionally unused:
  // eslint-disable-next-line no-unused-vars
  delay, y, duration, margin,
  ...rest
}) {
  return (
    <Tag className={className} {...rest}>
      {children}
    </Tag>
  );
}

export function Stagger({
  children,
  className = '',
  // eslint-disable-next-line no-unused-vars
  stagger,
  ...rest
}) {
  return (
    <div className={className} {...rest}>
      {children}
    </div>
  );
}

export function StaggerItem({ children, className = '', as: Tag = 'div', ...rest }) {
  return (
    <Tag className={className} {...rest}>
      {children}
    </Tag>
  );
}

// Stable default formatter.
const defaultFormat = (n) => Math.round(n).toLocaleString('en-US');

export function Counter({
  value,
  // eslint-disable-next-line no-unused-vars
  duration,
  format,
  suffix = '',
  className = '',
}) {
  const fmt = format || defaultFormat;
  return (
    <span className={['tabular-nums', className].join(' ')}>
      {fmt(value)}
      {suffix}
    </span>
  );
}
