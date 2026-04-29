/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        display: ['var(--font-space-grotesk)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jetbrains-mono)', 'ui-monospace', 'monospace'],
      },
      colors: {
        brand: {
          orange: '#FF5E1F',
          orangeLight: '#FF8F57',
          orangeDeep: '#CC4000',
          accent: '#00FFB2',
          green: '#22C55E',
          greenGlow: '#16A34A',
          amber: '#F59E0B',
          red: '#EF4444',
        },
        ink: {
          0: '#000000',
          1: '#0A0A0B',
          2: '#111113',
          3: '#1A1A1D',
          4: '#27272A',
        },
      },
      keyframes: {
        shimmer: {
          '0%, 100%': { backgroundPosition: '-200% 0' },
          '50%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '1' },
        },
        'lamp-pulse': {
          '0%, 100%': { filter: 'brightness(1)' },
          '50%': { filter: 'brightness(1.25)' },
        },
        'live-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.4' },
        },
      },
      animation: {
        shimmer: 'shimmer 3s linear infinite',
        float: 'float 4s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 2.5s ease-in-out infinite',
        'lamp-pulse': 'lamp-pulse 1.6s ease-in-out infinite',
        'live-pulse': 'live-pulse 1.4s ease-in-out infinite',
      },
      backgroundImage: {
        'grid-fade': 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,1) 70%), linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
        'hero-fade': 'linear-gradient(180deg, transparent 0%, transparent 60%, rgba(0,0,0,0.8) 85%, #000 100%)',
        'tree-glow': 'radial-gradient(circle at 50% 50%, rgba(34,197,94,0.30) 0%, rgba(34,197,94,0) 70%)',
      },
      boxShadow: {
        'lamp-amber': '0 0 28px rgba(245,158,11,0.7), inset 0 4px 10px rgba(0,0,0,0.3)',
        'lamp-green': '0 0 36px rgba(34,197,94,0.85), inset 0 4px 10px rgba(0,0,0,0.3)',
        'lamp-red':   '0 0 28px rgba(239,68,68,0.7),  inset 0 4px 10px rgba(0,0,0,0.3)',
        'orange-soft': '0 0 40px rgba(255,94,31,0.25), 0 0 80px rgba(255,94,31,0.10)',
      },
    },
  },
  plugins: [],
};
