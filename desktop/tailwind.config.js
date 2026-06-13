/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "monospace",
        ],
      },
      colors: {
        // MotoQuant brand palette — near-black "ink" surfaces + signal orange.
        // Tuned to the web cockpit identity (web/tailwind.config.js): the
        // darkest carbon steps mirror ink.1 (#0A0A0B) / ink.2 (#111113) so a
        // desktop window and motoquant.in read as the same product.
        carbon: {
          950: "#000000",
          900: "#0a0a0b",
          850: "#111113",
          800: "#1a1a1d",
          700: "#27272a",
          600: "#33333a",
          500: "#3b424f",
          400: "#5a6170",
          300: "#8b93a3",
          200: "#c6cbd4",
          100: "#e7eaef",
        },
        signal: {
          // primary action — web brand.orange ramp (#FF5E1F)
          50: "#fff4ee",
          300: "#ff8f57", // brand.orangeLight
          500: "#ff5e1f", // brand.orange — primary action
          600: "#cc4000", // brand.orangeDeep
          700: "#a33300",
        },
        // Sparing emphasis accent — web brand.accent.
        accent: {
          500: "#00ffb2",
        },
        go: {
          500: "#22c55e",
          600: "#16a34a",
        },
        warn: {
          500: "#f59e0b", // web brand.amber
        },
        stop: {
          500: "#ef4444",
        },
      },
      boxShadow: {
        // web "orange-soft" glow, retuned to the new #FF5E1F primary.
        glow: "0 0 28px rgba(255, 94, 31, 0.30), 0 0 64px rgba(255, 94, 31, 0.10)",
      },
    },
  },
  plugins: [],
};
