/** @type {import('tailwindcss').Config} */
//
// STAGED design system (v4, July 2026) — see web/DESIGN.md.
//
// Token model:
//   asphalt-*  surfaces (blue-cast near-black)
//   accent     volt — THE brand color (primary actions, one detail/viewport)
//   signal-*   go / stage / foul — state only, never decoration
//   mint       PRO/Studio tier chips only
//
// `ink-*` and `brand-*` are LEGACY ALIASES pointing at the new palette so the
// ~50 untouched blog/content pages re-skin without churn. New code must use
// the v4 names — the aliases exist for compatibility, not for new work.

const asphalt = {
  0: '#07090C',
  1: '#0B0E13',
  2: '#10141B',
  3: '#171C25',
  4: '#232A37',
};

const accent = {
  DEFAULT: '#C9F231',
  bright: '#DBFF57',
  deep: '#9CBE1E',
};

const signal = {
  go: '#34D97B',
  stage: '#FFB224',
  foul: '#FF5A48',
};

const mint = '#6FE3B2';

module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'Arial Narrow', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jetbrains-mono)', 'ui-monospace', 'monospace'],
      },
      colors: {
        asphalt,
        accent,
        signal,
        mint,
        // ── legacy aliases (blog/content compatibility — do not use in new code)
        ink: asphalt,
        brand: {
          orange: accent.DEFAULT,
          orangeLight: accent.bright,
          orangeDeep: accent.deep,
          accent: mint,
          green: signal.go,
          greenGlow: signal.go,
          amber: signal.stage,
          red: signal.foul,
        },
      },
      keyframes: {
        // opacity-only on purpose: compositor-friendly on every GPU tier.
        'lamp-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.72' },
        },
        'live-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
        // StageDots one-shot light-up (amber → amber → green), driven by
        // per-dot animation-delay. Opacity only.
        'stage-light': {
          from: { opacity: '0.25' },
          to: { opacity: '1' },
        },
      },
      animation: {
        'lamp-pulse': 'lamp-pulse 1.6s ease-in-out infinite',
        'live-pulse': 'live-pulse 1.4s ease-in-out infinite',
        'stage-light': 'stage-light 0.3s ease-out both',
      },
      boxShadow: {
        'lamp-amber': '0 0 20px rgba(255,178,36,0.55)',
        'lamp-green': '0 0 24px rgba(52,217,123,0.65)',
        'lamp-red': '0 0 20px rgba(255,90,72,0.55)',
        // legacy name — now a volt glow (used by .btn-primary hover)
        'orange-soft': '0 0 32px rgba(201,242,49,0.22), 0 0 64px rgba(201,242,49,0.08)',
        'volt-soft': '0 0 32px rgba(201,242,49,0.22), 0 0 64px rgba(201,242,49,0.08)',
      },
    },
  },
  plugins: [],
};
