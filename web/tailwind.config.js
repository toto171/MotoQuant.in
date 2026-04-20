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
      },
      animation: {
        shimmer: 'shimmer 3s linear infinite',
        float: 'float 4s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 2.5s ease-in-out infinite',
      },
      backgroundImage: {
        'grid-fade': 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,1) 70%), linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)',
        'hero-fade': 'linear-gradient(180deg, transparent 0%, transparent 60%, rgba(0,0,0,0.8) 85%, #000 100%)',
      },
    },
  },
  plugins: [],
};
