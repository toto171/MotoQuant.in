/**
 * GaugeMark — the MotoQuant "redline Q" mark as an inline SVG.
 *
 * Exact geometry from MotoQuant_Identity_Kit/motoquant-mark-dark.svg:
 * a heavyweight dial ring with a 30° sector gap at 315°, a tapered needle
 * that accelerates outward through the gap (45° speed cut), and the hub.
 * Colors per the kit: static parts white, moving parts Signal #FF5E1F.
 * Do not rotate — the 315° axis is the identity.
 *
 *   <GaugeMark size={28} />
 *   <GaugeMark size={20} className="opacity-80" />
 *
 * Server-component-safe (no hooks). `ring` defaults to white; pass e.g.
 * ring="#0A0A0B" for light surfaces (kit mark-light variant).
 */

export default function GaugeMark({ size = 28, ring = '#FFFFFF', className = '' }) {
  return (
    <svg
      viewBox="0 0 600 600"
      width={size}
      height={size}
      className={className}
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M 464.54 213.93 A 190 190 0 1 1 395.00 144.39 L 366.50 193.75 A 133.0 133.0 0 1 0 415.18 242.43 Z"
        fill={ring}
      />
      <path
        d="M 329.02 293.61 L 474.69 172.53 L 468.95 101.69 L 315.32 279.91 Z"
        fill="#FF5E1F"
      />
      <circle cx="300" cy="308.93" r="15.96" fill="#FF5E1F" />
    </svg>
  );
}
