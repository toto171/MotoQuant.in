/** @type {import('tailwindcss').Config} */
//
// STAGED design system (v4, July 2026) — see web/DESIGN.md.
//
// Token model:
//   asphalt-*  surfaces (blue-cast near-black)
//   accent     signal orange — THE brand color (primary actions + live data)
//   signal-*   go / stage / foul — state only, never decoration
//   mint       secondary accent/meta (e.g. simulator readouts, brand.accent)
//
// `ink-*` and `brand-*` are LEGACY ALIASES pointing at the new palette so the
// ~50 untouched blog/content pages re-skin without churn. New code must use
// the v4 names — the aliases exist for compatibility, not for new work.

// IGNITION v5 (July 2026): the orange cockpit identity, rebuilt flagship on
// the v4 token architecture. Values follow MotoQuant_Identity_Kit (Ink
// #0A0A0B / Signal #FF5E1F / white) + the Cockpit v3 carbon inks. The key
// names are stable, so every page re-skins without churn.
const asphalt = {
  0: '#050506',
  1: '#0A0A0B',
  2: '#111113',
  3: '#1A1A1D',
  4: '#27272A',
};

const accent = {
  DEFAULT: '#FF5E1F',
  bright: '#FF8F57',
  deep: '#CC4000',
};

const signal = {
  go: '#22C55E',
  stage: '#F59E0B',
  foul: '#EF4444',
};

const mint = '#00FFB2';

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
        'lamp-amber': '0 0 28px rgba(245,158,11,0.7)',
        'lamp-green': '0 0 36px rgba(34,197,94,0.85)',
        'lamp-red': '0 0 28px rgba(239,68,68,0.7)',
        'orange-soft': '0 0 40px rgba(255,94,31,0.25), 0 0 80px rgba(255,94,31,0.10)',
        // legacy v4 name — same orange glow
        'volt-soft': '0 0 40px rgba(255,94,31,0.25), 0 0 80px rgba(255,94,31,0.10)',
      },
    },
  },
  plugins: [],
};
