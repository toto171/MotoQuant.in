'use client';

/**
 * BikeSilhouette — realistic SVG superbike profile.
 *
 * Design language modelled on the MV Agusta F4: sharp angular front
 * fairing with stacked twin headlights, deep tank cut-outs, raised
 * pilot tail hump, single-sided swingarm exposed on the right side,
 * and the brand's signature quad-tip underseat exhaust array.
 *
 * Rendered as inline SVG so it scales cleanly, themes via currentColor,
 * and takes a `glow` prop to drop the orange aura when used in the
 * pinned telemetry HUD.
 *
 * Geometry hand-tuned at viewBox 720×320:
 *   - Wheelbase:  ~470 px (centre-to-centre, scales to ~1430 mm)
 *   - Wheel ID:   80 px outer / 50 px hub
 *   - Front rake:  ~24°  (sharp sport rake)
 *   - Rider tank line peak: y=92 (matches F4 hump silhouette)
 */

export default function BikeSilhouette({
  className = '',
  glow = true,
  primary = '#FF5E1F',      // brand orange — bodywork
  secondary = '#FF8F57',    // brand orange light — fairing highlight
  shadow = '#000000',
  ariaLabel = 'MV-style superbike silhouette',
}) {
  return (
    <svg
      viewBox="0 0 720 320"
      role="img"
      aria-label={ariaLabel}
      className={className}
      style={{
        filter: glow
          ? 'drop-shadow(0 0 24px rgba(255,94,31,0.45)) drop-shadow(0 8px 14px rgba(0,0,0,0.7))'
          : 'drop-shadow(0 8px 14px rgba(0,0,0,0.7))',
      }}
    >
      <defs>
        <linearGradient id="bsBody" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={secondary} />
          <stop offset="0.55" stopColor={primary} />
          <stop offset="1" stopColor="#9C2E00" />
        </linearGradient>
        <linearGradient id="bsFairing" x1="0" x2="1" y1="0" y2="0.6">
          <stop offset="0" stopColor={primary} />
          <stop offset="1" stopColor={secondary} />
        </linearGradient>
        <linearGradient id="bsExhaust" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#525252" />
          <stop offset="0.5" stopColor="#9CA3AF" />
          <stop offset="1" stopColor="#404040" />
        </linearGradient>
        <linearGradient id="bsRim" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#3F3F46" />
          <stop offset="1" stopColor="#18181B" />
        </linearGradient>
        <linearGradient id="bsWindscreen" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#1F2937" stopOpacity="0.85" />
          <stop offset="1" stopColor="#0F172A" stopOpacity="0.95" />
        </linearGradient>
        <radialGradient id="bsHeadlight" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#FFE9C4" />
          <stop offset="0.4" stopColor="#FFAF60" />
          <stop offset="1" stopColor="#7A2A00" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Ground shadow */}
      <ellipse cx="360" cy="284" rx="270" ry="6" fill={shadow} opacity="0.45" />

      {/* ─── Rear wheel (single-sided swingarm visible behind) ─── */}
      <g>
        {/* Hub-side disc + caliper */}
        <circle cx="600" cy="222" r="60" fill="url(#bsRim)" />
        <circle cx="600" cy="222" r="58" fill="#0a0a0a" />
        <circle cx="600" cy="222" r="48" fill="url(#bsRim)" />
        <circle cx="600" cy="222" r="22" fill="#27272A" />
        {/* Spokes (Y-spoke pattern, sharp italian style) */}
        <g stroke="#52525B" strokeWidth="3" strokeLinecap="round">
          <line x1="600" y1="178" x2="600" y2="266" />
          <line x1="562" y1="200" x2="638" y2="244" />
          <line x1="562" y1="244" x2="638" y2="200" />
        </g>
        {/* Single-sided swingarm */}
        <path
          d="M 380 218 Q 460 214 590 222 L 600 222 L 600 226 Q 470 222 380 226 Z"
          fill="#3F3F46"
          stroke="#27272A"
          strokeWidth="0.6"
        />
        {/* Chain line */}
        <path
          d="M 392 230 L 590 230"
          stroke="#FF5E1F"
          strokeWidth="1.2"
          strokeDasharray="4 3"
          opacity="0.7"
        />
      </g>

      {/* ─── Front wheel ─── */}
      <g>
        <circle cx="120" cy="222" r="60" fill="url(#bsRim)" />
        <circle cx="120" cy="222" r="58" fill="#0a0a0a" />
        <circle cx="120" cy="222" r="48" fill="url(#bsRim)" />
        <circle cx="120" cy="222" r="22" fill="#27272A" />
        <g stroke="#52525B" strokeWidth="3" strokeLinecap="round">
          <line x1="120" y1="178" x2="120" y2="266" />
          <line x1="82"  y1="200" x2="158" y2="244" />
          <line x1="82"  y1="244" x2="158" y2="200" />
        </g>
        {/* Front brake disc detail */}
        <circle cx="120" cy="222" r="44" fill="none" stroke="#71717A" strokeWidth="2" opacity="0.5" />
        {/* Brake caliper */}
        <rect x="148" y="188" width="14" height="20" rx="3" fill="#FF5E1F" opacity="0.85" />
      </g>

      {/* ─── Front forks (USD inverted — gold sliders) ─── */}
      <g>
        <path
          d="M 116 222 L 156 130 L 168 130 L 130 222 Z"
          fill="#D4A745"
          stroke="#7C5A1B"
          strokeWidth="0.6"
        />
        <path
          d="M 158 132 L 162 88 L 172 88 L 168 132 Z"
          fill="#71717A"
        />
        {/* Triple clamp */}
        <rect x="156" y="78" width="22" height="14" rx="2" fill="#27272A" />
      </g>

      {/* ─── Rear shock (visible through swingarm gap, F4-style horizontal) ─── */}
      <rect x="404" y="178" width="64" height="10" rx="3" fill="#FF5E1F" opacity="0.9" />
      <rect x="404" y="178" width="64" height="10" rx="3" fill="none" stroke="#0a0a0a" strokeWidth="1" />
      <circle cx="404" cy="183" r="6" fill="#A1A1AA" />
      <circle cx="468" cy="183" r="6" fill="#A1A1AA" />

      {/* ─── Engine block (compact inline-4, signature F4 quad-stacked exhaust) ─── */}
      <g>
        {/* Crankcase */}
        <path
          d="M 240 210 L 240 178 Q 250 168 268 168 L 380 168 Q 398 170 402 188 L 402 220 Q 398 232 380 232 L 268 232 Q 248 232 240 220 Z"
          fill="#1F2937"
          stroke="#0F172A"
          strokeWidth="1"
        />
        {/* Cylinder fins */}
        <g stroke="#404040" strokeWidth="0.8">
          <line x1="270" y1="174" x2="270" y2="200" />
          <line x1="290" y1="174" x2="290" y2="200" />
          <line x1="310" y1="174" x2="310" y2="200" />
          <line x1="330" y1="174" x2="330" y2="200" />
          <line x1="350" y1="174" x2="350" y2="200" />
          <line x1="370" y1="174" x2="370" y2="200" />
        </g>
        {/* Engine highlight stripe */}
        <path d="M 250 174 L 396 174" stroke="#FF5E1F" strokeWidth="1.2" opacity="0.55" />
      </g>

      {/* ─── Trellis frame (visible Italian-style tubular frame) ─── */}
      <g stroke="#9CA3AF" strokeWidth="3.2" strokeLinecap="round" fill="none" opacity="0.85">
        <path d="M 178 90 L 250 130" />
        <path d="M 250 130 L 250 175" />
        <path d="M 178 90 L 250 158" />
        <path d="M 250 130 L 320 130" />
        <path d="M 320 130 L 320 168" />
        <path d="M 250 158 L 320 168" />
      </g>

      {/* ─── Quad-tip underseat exhaust (MV F4 signature) ─── */}
      <g>
        <path
          d="M 396 196 Q 440 192 488 198 L 540 200 L 568 196 L 568 220 L 540 224 L 488 222 Q 440 216 396 220 Z"
          fill="url(#bsExhaust)"
          stroke="#0a0a0a"
          strokeWidth="0.6"
        />
        {/* Four-tip exit detail */}
        <g fill="#0a0a0a">
          <circle cx="566" cy="200" r="3" />
          <circle cx="566" cy="208" r="3" />
          <circle cx="566" cy="216" r="3" />
          <circle cx="566" cy="224" r="3" />
        </g>
        {/* Heat shield highlight */}
        <path d="M 410 196 L 555 200" stroke="#FFAF60" strokeWidth="0.8" opacity="0.6" />
      </g>

      {/* ─── Body / fuel tank (sculpted, with deep knee cut-outs) ─── */}
      <path
        d="M 232 168
           Q 246 122 286 110
           L 372 102
           Q 416 100 432 124
           L 446 158
           Q 444 170 432 174
           L 256 174
           Q 240 174 232 168 Z"
        fill="url(#bsBody)"
        stroke="#7A1F00"
        strokeWidth="0.8"
      />
      {/* Tank highlight */}
      <path
        d="M 252 130 Q 290 116 360 112 Q 410 112 430 130"
        stroke={secondary}
        strokeWidth="2"
        fill="none"
        opacity="0.85"
      />
      {/* Filler cap */}
      <circle cx="346" cy="120" r="6" fill="#27272A" stroke="#0a0a0a" strokeWidth="0.8" />
      <circle cx="346" cy="120" r="3" fill="#52525B" />

      {/* ─── Pilot seat + tail hump (raised F4 hump silhouette) ─── */}
      <path
        d="M 432 124
           Q 478 116 514 116
           Q 562 116 580 138
           L 588 168
           Q 580 180 560 180
           L 466 180
           Q 444 178 432 168 Z"
        fill="url(#bsBody)"
        stroke="#7A1F00"
        strokeWidth="0.8"
      />
      {/* Seat split line */}
      <path
        d="M 446 156 Q 500 152 580 156"
        stroke="#0a0a0a"
        strokeWidth="1.2"
        fill="none"
        opacity="0.85"
      />
      {/* Tail tuck — racing single-seat hump */}
      <path
        d="M 524 116 Q 580 110 596 138 L 600 174 L 580 174"
        fill={primary}
        opacity="0.9"
      />
      {/* Tail-light slot */}
      <path
        d="M 588 168 L 600 174 L 600 178 L 586 175 Z"
        fill="#FCA5A5"
        opacity="0.8"
      />

      {/* ─── Front fairing (sharp angular MV nose) ─── */}
      <path
        d="M 178 90
           Q 192 60 218 56
           L 252 60
           Q 274 64 282 86
           L 286 130
           Q 282 162 254 168
           L 232 168
           Q 218 162 214 144
           L 198 110 Z"
        fill="url(#bsFairing)"
        stroke="#7A1F00"
        strokeWidth="0.8"
      />
      {/* Side air intake slot */}
      <path
        d="M 232 110 Q 250 108 268 116 L 268 132 Q 248 130 232 134 Z"
        fill="#0a0a0a"
        opacity="0.85"
      />

      {/* ─── Twin stacked headlights (MV signature) ─── */}
      <g>
        <ellipse cx="206" cy="84" rx="14" ry="9" fill="url(#bsHeadlight)" />
        <ellipse cx="206" cy="100" rx="14" ry="9" fill="url(#bsHeadlight)" opacity="0.85" />
        <ellipse cx="206" cy="84" rx="14" ry="9" fill="none" stroke="#0a0a0a" strokeWidth="1" />
        <ellipse cx="206" cy="100" rx="14" ry="9" fill="none" stroke="#0a0a0a" strokeWidth="1" />
      </g>

      {/* ─── Windscreen ─── */}
      <path
        d="M 226 60 L 270 56 Q 282 56 286 78 L 282 94 Q 256 80 226 76 Z"
        fill="url(#bsWindscreen)"
        stroke="#0F172A"
        strokeWidth="0.6"
      />
      {/* Windscreen highlight */}
      <path
        d="M 232 64 L 268 60"
        stroke="#9CA3AF"
        strokeWidth="0.8"
        opacity="0.7"
      />

      {/* ─── Clip-on bars peeking through ─── */}
      <line x1="244" y1="92" x2="262" y2="80" stroke="#27272A" strokeWidth="3" strokeLinecap="round" />

      {/* ─── Mirror stalks (small details) ─── */}
      <path
        d="M 250 70 Q 240 56 224 56"
        stroke="#27272A"
        strokeWidth="2"
        fill="none"
      />
      <ellipse cx="222" cy="56" rx="6" ry="3" fill="#0a0a0a" />

      {/* ─── Footpeg + rearset ─── */}
      <line x1="412" y1="220" x2="426" y2="240" stroke="#27272A" strokeWidth="3" strokeLinecap="round" />
      <circle cx="426" cy="240" r="3" fill="#FF5E1F" />

      {/* Number plate / racing dot — adds Italian race-bike charm */}
      <circle cx="540" cy="146" r="14" fill="#0a0a0a" stroke={secondary} strokeWidth="1.5" />
      <text
        x="540"
        y="151"
        textAnchor="middle"
        fontFamily="ui-monospace, monospace"
        fontSize="12"
        fontWeight="800"
        fill={secondary}
      >
        F4
      </text>
    </svg>
  );
}
