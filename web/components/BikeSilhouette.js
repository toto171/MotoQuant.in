'use client';

/**
 * BikeSilhouette — MV-Agusta-F4-faithful superbike profile.
 *
 * Reference: the user's F4 photo. Key design cues we carry over:
 *
 *   - RIGHT-FACING profile (front fairing on the right side) — matches
 *     the cinematic motion direction of the rest of the page.
 *   - Sharp wedge nose with TWIN STACKED LED headlights deep-set in
 *     the lower fairing slot.
 *   - Tank flowing rearward into a DRAMATIC TAIL HUMP that peaks high
 *     and drops sharply to the tail-light.
 *   - Signature MV QUAD-TIP underseat exhaust array tucked under the
 *     tail cowl.
 *   - SINGLE-SIDED swingarm exposing the rear wheel detail.
 *   - 5-spoke Y-pattern wheels with a red rim accent.
 *   - Visible silver TRELLIS frame above the engine.
 *   - GOLD USD inverted forks at the front.
 *   - Brembo-style red brake calipers.
 *   - Brand-orange livery (so it reads as MotoQuant, not as a stock
 *     MV in factory red).
 *
 * Geometry is hand-tuned at viewBox 720×320:
 *   - Front wheel cx=620 (right side, 17 inch)
 *   - Rear wheel cx=140 (left side, 17 inch)
 *   - Wheelbase 480 px (~1430 mm scaled)
 *   - Aggressive sport rake — steering stem leans forward 22°
 *   - Tail hump peaks at y=66 (highest point of bodywork)
 */

export default function BikeSilhouette({
  className = '',
  glow = true,
  primary = '#FF5E1F',
  secondary = '#FF8F57',
  shadow = '#000000',
  ariaLabel = 'MV-Agusta-F4-style superbike silhouette',
}) {
  return (
    <svg
      viewBox="0 0 720 320"
      role="img"
      aria-label={ariaLabel}
      className={className}
      style={{
        filter: glow
          ? 'drop-shadow(0 0 28px rgba(255,94,31,0.55)) drop-shadow(0 10px 18px rgba(0,0,0,0.7))'
          : 'drop-shadow(0 10px 18px rgba(0,0,0,0.7))',
      }}
    >
      <defs>
        {/* Body: bright top, deep shadow on the bottom edge */}
        <linearGradient id="bsBody" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0"    stopColor={secondary} />
          <stop offset="0.45" stopColor={primary} />
          <stop offset="1"    stopColor="#7A1E00" />
        </linearGradient>
        <linearGradient id="bsBodyDark" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#9C2E00" />
          <stop offset="1" stopColor="#3D0E00" />
        </linearGradient>
        <linearGradient id="bsWheel" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#3F3F46" />
          <stop offset="1" stopColor="#0A0A0A" />
        </linearGradient>
        <linearGradient id="bsExhaust" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0"   stopColor="#9CA3AF" />
          <stop offset="0.5" stopColor="#71717A" />
          <stop offset="1"   stopColor="#3F3F46" />
        </linearGradient>
        <linearGradient id="bsFork" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0"   stopColor="#FCD34D" />
          <stop offset="0.5" stopColor="#D4A745" />
          <stop offset="1"   stopColor="#7C5A1B" />
        </linearGradient>
        <linearGradient id="bsScreen" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="#1F2937" stopOpacity="0.85" />
          <stop offset="1" stopColor="#0F172A" stopOpacity="0.95" />
        </linearGradient>
        <radialGradient id="bsHeadlight" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0"   stopColor="#FFE9C4" />
          <stop offset="0.5" stopColor="#FFAF60" />
          <stop offset="1"   stopColor="#7A2A00" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Ground shadow — slightly offset under the bike */}
      <ellipse cx="380" cy="290" rx="290" ry="6" fill={shadow} opacity="0.45" />

      {/* ─── REAR WHEEL (left side) — 5-spoke Y pattern ─── */}
      <g>
        {/* Tyre */}
        <circle cx="140" cy="225" r="62" fill="#0A0A0A" />
        {/* Sidewall red stripe (Pirelli accent) */}
        <circle cx="140" cy="225" r="60" fill="none" stroke="#DC2626" strokeWidth="0.8" opacity="0.55" />
        {/* Rim */}
        <circle cx="140" cy="225" r="48" fill="url(#bsWheel)" />
        <circle cx="140" cy="225" r="46" fill="#0A0A0A" />
        <circle cx="140" cy="225" r="40" fill="url(#bsWheel)" />
        {/* Hub */}
        <circle cx="140" cy="225" r="14" fill="#27272A" />
        <circle cx="140" cy="225" r="6"  fill="#52525B" />
        {/* 5 Y-spokes */}
        <g stroke="#52525B" strokeWidth="3" strokeLinecap="round" fill="none">
          {/* spoke 1: 12 o'clock */}
          <path d="M 140 225 L 140 183" />
          {/* spoke 2: ~72° */}
          <path d="M 140 225 L 180 200" />
          {/* spoke 3: ~144° */}
          <path d="M 140 225 L 165 263" />
          {/* spoke 4: ~216° */}
          <path d="M 140 225 L 115 263" />
          {/* spoke 5: ~288° */}
          <path d="M 140 225 L 100 200" />
        </g>
        {/* Y-split detail at outer end of each spoke */}
        <g stroke="#3F3F46" strokeWidth="1.5" fill="none" opacity="0.7">
          <path d="M 134 188 L 146 188" />
          <path d="M 175 192 L 184 207" />
          <path d="M 154 256 L 175 268" />
          <path d="M 105 268 L 126 256" />
          <path d="M 96 207 L 105 192" />
        </g>
      </g>

      {/* ─── SINGLE-SIDED SWINGARM ─── */}
      <g>
        <path
          d="M 320 218 Q 240 217 158 222 L 158 232 Q 240 227 320 230 Z"
          fill="#3F3F46"
          stroke="#1F2937"
          strokeWidth="0.8"
        />
        {/* Pivot bolt at the engine end */}
        <circle cx="320" cy="225" r="5" fill="#71717A" stroke="#0A0A0A" strokeWidth="0.6" />
        {/* Hub-mount detail at wheel end */}
        <rect x="148" y="218" width="14" height="14" rx="2" fill="#27272A" />
      </g>

      {/* ─── REAR SHOCK (red, tucked diagonally) ─── */}
      <g>
        <rect x="290" y="158" width="42" height="9" rx="3" fill={primary} />
        <rect x="290" y="158" width="42" height="9" rx="3" fill="none" stroke="#0A0A0A" strokeWidth="0.6" />
        <circle cx="290" cy="162.5" r="5" fill="#A1A1AA" />
        <circle cx="332" cy="162.5" r="5" fill="#A1A1AA" />
        {/* Spring coils */}
        <g stroke="#9C2E00" strokeWidth="0.7" opacity="0.55">
          <line x1="296" y1="159" x2="326" y2="159" />
          <line x1="296" y1="161" x2="326" y2="161" />
          <line x1="296" y1="163" x2="326" y2="163" />
          <line x1="296" y1="165" x2="326" y2="165" />
        </g>
      </g>

      {/* ─── ENGINE BLOCK (compact 4-cyl, tucked low) ─── */}
      <g>
        <path
          d="M 290 200 L 290 175 Q 296 165 312 165 L 410 165 Q 432 168 438 188 L 438 218 Q 432 232 410 232 L 312 232 Q 294 232 290 218 Z"
          fill="#1F2937"
          stroke="#0F172A"
          strokeWidth="1"
        />
        {/* Cylinder fins */}
        <g stroke="#404040" strokeWidth="0.7" opacity="0.85">
          <line x1="312" y1="170" x2="312" y2="200" />
          <line x1="328" y1="170" x2="328" y2="200" />
          <line x1="344" y1="170" x2="344" y2="200" />
          <line x1="360" y1="170" x2="360" y2="200" />
          <line x1="376" y1="170" x2="376" y2="200" />
          <line x1="392" y1="170" x2="392" y2="200" />
          <line x1="408" y1="170" x2="408" y2="200" />
        </g>
        {/* Highlight stripe along cam-cover */}
        <path d="M 296 170 L 432 170" stroke={primary} strokeWidth="1.4" opacity="0.55" />
        {/* Sprocket cover on the engine's left side */}
        <circle cx="318" cy="222" r="9" fill="#27272A" stroke="#0A0A0A" strokeWidth="0.6" />
      </g>

      {/* ─── CHAIN line ─── */}
      <path
        d="M 158 230 L 318 230"
        stroke="#FF5E1F"
        strokeWidth="1.5"
        strokeDasharray="5 3"
        opacity="0.65"
      />

      {/* ─── TRELLIS FRAME (silver tubes, F4 signature) ─── */}
      <g stroke="#A1A1AA" strokeWidth="3" strokeLinecap="round" fill="none" opacity="0.85">
        {/* Top rail from steering head → tank */}
        <path d="M 506 100 L 432 130" />
        {/* Diagonal trellis tubes */}
        <path d="M 506 100 L 446 158" />
        <path d="M 478 122 L 432 168" />
        <path d="M 506 100 L 410 162" />
        {/* Lower rail to swingarm pivot */}
        <path d="M 432 168 L 320 218" />
        <path d="M 446 158 L 320 218" />
      </g>

      {/* ─── FOUR-TIP UNDERSEAT EXHAUST (MV F4 signature) ─── */}
      <g>
        {/* Heat-shield tunnel running back from engine */}
        <path
          d="M 250 198 Q 200 196 158 200 L 130 196 L 124 218 L 158 222 Q 200 220 250 222 Z"
          fill="url(#bsExhaust)"
          stroke="#0A0A0A"
          strokeWidth="0.6"
        />
        {/* Inner four-tip outlet — two stacked rows of 2 */}
        <g>
          <circle cx="126" cy="201" r="3.2" fill="#0A0A0A" />
          <circle cx="126" cy="210" r="3.2" fill="#0A0A0A" />
          <circle cx="118" cy="201" r="3.2" fill="#0A0A0A" />
          <circle cx="118" cy="210" r="3.2" fill="#0A0A0A" />
        </g>
        {/* Faint metallic highlight along the heat-shield */}
        <path d="M 140 200 L 244 202" stroke="#FFAF60" strokeWidth="0.6" opacity="0.5" />
      </g>

      {/* ─── FUEL TANK (sculpted with knee cutouts) ─── */}
      <path
        d="M 432 168
           L 446 130
           Q 460 105 502 100
           L 545 102
           Q 556 105 558 122
           L 555 158
           Q 548 168 532 170
           L 442 170
           Q 434 170 432 168 Z"
        fill="url(#bsBody)"
        stroke="#7A1F00"
        strokeWidth="0.8"
      />
      {/* Tank knee-cutout shadow */}
      <path
        d="M 458 138 Q 480 124 530 122"
        stroke={secondary}
        strokeWidth="2"
        fill="none"
        opacity="0.85"
      />
      {/* Filler cap */}
      <circle cx="500" cy="115" r="6" fill="#27272A" stroke="#0A0A0A" strokeWidth="0.8" />
      <circle cx="500" cy="115" r="3" fill="#52525B" />

      {/* ─── PILOT SEAT + DRAMATIC TAIL HUMP ─── */}
      <path
        d="M 340 124
           Q 342 96 372 80
           Q 408 70 444 76
           Q 460 80 462 110
           L 460 148
           Q 458 168 442 170
           L 360 170
           Q 344 168 340 152 Z"
        fill="url(#bsBodyDark)"
        stroke="#7A1F00"
        strokeWidth="0.8"
      />
      {/* Tall tail-cowl peak — the F4's trademark sharp dorsal fin */}
      <path
        d="M 280 140
           Q 285 84 332 70
           Q 380 60 412 70
           L 412 80
           Q 380 76 348 88
           Q 312 102 296 144 Z"
        fill="url(#bsBody)"
        stroke="#7A1F00"
        strokeWidth="0.8"
      />
      {/* Subtle shadow gusset on the tail */}
      <path
        d="M 296 144 L 340 124 L 340 168 L 280 168 Z"
        fill={primary}
        opacity="0.35"
      />
      {/* Tail brake-light slot */}
      <path
        d="M 282 158 L 296 144 L 304 158 Z"
        fill="#FCA5A5"
        opacity="0.85"
      />

      {/* Seat split-line */}
      <path
        d="M 358 144 Q 410 138 458 142"
        stroke="#0A0A0A"
        strokeWidth="1.2"
        fill="none"
        opacity="0.85"
      />

      {/* ─── FRONT FAIRING (sharp wedge) ─── */}
      <path
        d="M 545 102
           Q 565 86 596 84
           L 632 88
           Q 658 96 666 122
           L 660 168
           Q 656 184 638 188
           L 600 188
           Q 580 184 572 168
           L 558 122 Z"
        fill="url(#bsBody)"
        stroke="#7A1F00"
        strokeWidth="0.8"
      />
      {/* Side air intake louvre */}
      <path
        d="M 600 138 Q 620 134 638 142 L 638 158 Q 618 156 600 162 Z"
        fill="#0A0A0A"
        opacity="0.85"
      />
      {/* Black accent stripe along the fairing — F4 signature */}
      <path
        d="M 558 122 L 580 130 L 596 144 L 612 168"
        stroke="#0A0A0A"
        strokeWidth="3"
        fill="none"
        opacity="0.85"
      />

      {/* ─── TWIN STACKED HEADLIGHTS (deep-set in nose) ─── */}
      <g>
        <ellipse cx="638" cy="116" rx="14" ry="9" fill="url(#bsHeadlight)" />
        <ellipse cx="638" cy="132" rx="14" ry="9" fill="url(#bsHeadlight)" opacity="0.85" />
        <ellipse cx="638" cy="116" rx="14" ry="9" fill="none" stroke="#0A0A0A" strokeWidth="1" />
        <ellipse cx="638" cy="132" rx="14" ry="9" fill="none" stroke="#0A0A0A" strokeWidth="1" />
      </g>

      {/* ─── WINDSCREEN ─── */}
      <path
        d="M 596 84
           Q 622 76 642 84
           L 656 102
           Q 638 96 614 92
           Q 600 90 596 96 Z"
        fill="url(#bsScreen)"
        stroke="#0F172A"
        strokeWidth="0.6"
      />
      <path
        d="M 600 88 Q 620 84 642 90"
        stroke="#9CA3AF"
        strokeWidth="0.7"
        opacity="0.7"
      />

      {/* ─── MIRROR STALK ─── */}
      <path
        d="M 614 90 Q 628 76 644 76"
        stroke="#27272A"
        strokeWidth="2.5"
        fill="none"
      />
      <ellipse cx="646" cy="76" rx="6" ry="3" fill="#0A0A0A" />

      {/* ─── CLIP-ON BARS peeking through ─── */}
      <line x1="566" y1="108" x2="586" y2="98" stroke="#27272A" strokeWidth="3" strokeLinecap="round" />

      {/* ─── FRONT FORK (USD inverted, gold sliders) ─── */}
      <g>
        {/* Outer slider */}
        <path
          d="M 614 168 L 588 230 L 600 230 L 626 168 Z"
          fill="url(#bsFork)"
          stroke="#7C5A1B"
          strokeWidth="0.6"
        />
        {/* Inner stanchion (chrome upper) */}
        <path
          d="M 612 168 L 610 110 L 622 110 L 624 168 Z"
          fill="#9CA3AF"
        />
        {/* Triple clamp */}
        <rect x="606" y="100" width="22" height="14" rx="2" fill="#27272A" />
        {/* Steering damper detail (small horizontal bar) */}
        <rect x="608" y="118" width="22" height="3" rx="1" fill="#52525B" />
      </g>

      {/* ─── FRONT WHEEL (right side) — 5-spoke Y pattern, BIG ─── */}
      <g>
        <circle cx="620" cy="225" r="62" fill="#0A0A0A" />
        <circle cx="620" cy="225" r="60" fill="none" stroke="#DC2626" strokeWidth="0.8" opacity="0.55" />
        <circle cx="620" cy="225" r="48" fill="url(#bsWheel)" />
        <circle cx="620" cy="225" r="46" fill="#0A0A0A" />
        <circle cx="620" cy="225" r="40" fill="url(#bsWheel)" />
        <circle cx="620" cy="225" r="14" fill="#27272A" />
        <circle cx="620" cy="225" r="6"  fill="#52525B" />
        <g stroke="#52525B" strokeWidth="3" strokeLinecap="round" fill="none">
          <path d="M 620 225 L 620 183" />
          <path d="M 620 225 L 660 200" />
          <path d="M 620 225 L 645 263" />
          <path d="M 620 225 L 595 263" />
          <path d="M 620 225 L 580 200" />
        </g>
        {/* Brake disc (twin-disc visible) */}
        <circle cx="620" cy="225" r="44" fill="none" stroke="#71717A" strokeWidth="2" opacity="0.55" />
        {/* Brembo-style red caliper */}
        <rect x="588" y="195" width="14" height="22" rx="3" fill="#DC2626" stroke="#0A0A0A" strokeWidth="0.5" />
        <rect x="589" y="200" width="12" height="3" rx="1" fill="#7F1D1D" />
        <rect x="589" y="208" width="12" height="3" rx="1" fill="#7F1D1D" />
      </g>

      {/* ─── FOOTPEG + REARSET (mid-bike, hint of rider position) ─── */}
      <line x1="376" y1="232" x2="362" y2="252" stroke="#27272A" strokeWidth="3" strokeLinecap="round" />
      <circle cx="362" cy="252" r="3" fill={primary} />

      {/* ─── F4 number-plate dot on the tail (Italian race-bike charm) ─── */}
      <circle cx="376" cy="118" r="14" fill="#0A0A0A" stroke={secondary} strokeWidth="1.5" />
      <text
        x="376"
        y="123"
        textAnchor="middle"
        fontFamily="ui-monospace, monospace"
        fontSize="11"
        fontWeight="800"
        fill={secondary}
      >
        F4
      </text>
    </svg>
  );
}
