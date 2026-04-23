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
        // MotoQuant brand palette — carbon + signal orange
        carbon: {
          950: "#08090b",
          900: "#0d0f13",
          850: "#11141a",
          800: "#161a21",
          700: "#1f242d",
          600: "#2a303b",
          500: "#3b424f",
          400: "#5a6170",
          300: "#8b93a3",
          200: "#c6cbd4",
          100: "#e7eaef",
        },
        signal: {
          // drag-strip Christmas-tree amber → go-green
          50: "#fff7ed",
          300: "#fdba74",
          500: "#f97316", // primary action
          600: "#ea580c",
          700: "#c2410c",
        },
        go: {
          500: "#22c55e",
          600: "#16a34a",
        },
        warn: {
          500: "#eab308",
        },
        stop: {
          500: "#ef4444",
        },
      },
      boxShadow: {
        glow: "0 0 24px rgba(249, 115, 22, 0.35)",
      },
    },
  },
  plugins: [],
};
