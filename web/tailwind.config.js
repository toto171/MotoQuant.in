/** @type {import('tailwindcss').Config} */
//
// CLARITY design system (v6, November 2026) — see web/DESIGN.md §3.
//
// Every colour is a CSS variable (defined per theme in app/globals.css) so
// the whole site can switch between dark and light. The class NAMES from
// v4/v5 are unchanged, which is how ~80 content/blog pages re-skin with no
// edits:
//   white       = foreground ink   (white in dark, near-black in light)
//   black       = deepest background (black in dark, white in light)
//   asphalt-*   = surfaces 0..4
//   accent      = brand orange (primary actions)
//   signal-*    = go / stage / foul — state only
//   on-accent   = text that sits ON an accent fill (never theme-inverted)
//   mint        = alias of signal-go (no longer a tier colour)
//   ink-*/brand-* = legacy aliases onto the same variables

const v = (name) => `rgb(var(${name}) / <alpha-value>)`;

const asphalt = {
  0: v('--surface-0'),
  1: v('--surface-1'),
  2: v('--surface-2'),
  3: v('--surface-3'),
  4: v('--surface-4'),
};

const accent = {
  DEFAULT: v('--accent'),
  bright: v('--accent-bright'),
  deep: v('--accent-deep'),
};

const signal = {
  go: v('--go'),
  stage: v('--stage'),
  foul: v('--foul'),
};

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
        white: v('--fg'),
        black: v('--bg-deep'),
        asphalt,
        accent,
        signal,
        'on-accent': v('--on-accent'),
        mint: v('--go'),
        // ── legacy aliases (blog/content compatibility — do not use in new code)
        ink: asphalt,
        brand: {
          orange: v('--accent'),
          orangeLight: v('--accent-bright'),
          orangeDeep: v('--accent-deep'),
          accent: v('--go'),
          green: v('--go'),
          greenGlow: v('--go'),
          amber: v('--stage'),
          red: v('--foul'),
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
        'lamp-amber': '0 0 28px rgb(var(--stage) / 0.7)',
        'lamp-green': '0 0 36px rgb(var(--go) / 0.85)',
        'lamp-red': '0 0 28px rgb(var(--foul) / 0.7)',
        'orange-soft': '0 0 40px rgb(var(--accent) / 0.22), 0 0 80px rgb(var(--accent) / 0.08)',
        // legacy v4 name — same orange glow
        'volt-soft': '0 0 40px rgb(var(--accent) / 0.22), 0 0 80px rgb(var(--accent) / 0.08)',
      },
    },
  },
  plugins: [],
};
