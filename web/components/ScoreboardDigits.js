/**
 * ScoreboardDigits — big display numerals (CLARITY v6).
 *
 * The seven-segment look is retired (it made "541" read as "54|"). The
 * exports and props are unchanged so every caller keeps working, but this now
 * renders clean tabular display text with the final value in server HTML:
 *
 *   <ScoreboardDigits value="10.0334" h={36} />
 *   <ScoreboardCounter value={541} h={34} />   // static — no count-up from 0
 *
 * Props (both): value, h (digit height in px, default 36 / 34), color (any CSS
 * colour; default = the theme accent), ghost (ignored, kept for callers),
 * className, label (aria-label override). ScoreboardCounter also tolerates
 * `duration` (ignored).
 *
 * Server-component safe: no hooks, no animation.
 */

const LEGACY_ACCENT = /^#ff5e1f$/i;
const LEGACY_WHITE = /^(#fff|#ffffff|white)$/i;

// Old call sites pass raw hex. Map the two literals they use onto theme
// variables so they stay legible in the light theme.
function resolveColor(color) {
  if (!color || LEGACY_ACCENT.test(color)) return 'rgb(var(--accent))';
  if (LEGACY_WHITE.test(color)) return 'rgb(var(--fg))';
  return color;
}

export default function ScoreboardDigits({
  value,
  h = 36,
  color,
  // eslint-disable-next-line no-unused-vars
  ghost,
  className = '',
  label,
}) {
  const text = String(value);
  return (
    <span
      className={['inline-block font-display font-bold tabular-nums tracking-tight', className].join(' ')}
      style={{
        fontSize: Math.round(h * 1.1),
        lineHeight: 1,
        color: resolveColor(color),
      }}
      role={label ? 'img' : undefined}
      aria-label={label || undefined}
    >
      {text}
    </span>
  );
}

/**
 * ScoreboardCounter — historically a count-up. Rule 7 forbids showing a wrong
 * number (a count-up starts from 0), so it now renders the final value
 * directly. Same API, same look as ScoreboardDigits.
 */
export function ScoreboardCounter({
  value,
  h = 34,
  color,
  ghost,
  // eslint-disable-next-line no-unused-vars
  duration,
  className = '',
}) {
  return <ScoreboardDigits value={value} h={h} color={color} ghost={ghost} className={className} />;
}
