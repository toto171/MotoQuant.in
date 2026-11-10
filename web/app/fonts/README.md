# Fonts

These three typefaces are served from this folder so that building the site
needs no network access.

| File | Typeface | Licence |
| --- | --- | --- |
| `inter-latin-wght-normal.woff2` | Inter (variable weight 100–900) | SIL Open Font License 1.1 — `LICENSE-Inter.txt` |
| `space-grotesk-latin-wght-normal.woff2` | Space Grotesk (variable weight 300–700) | SIL Open Font License 1.1 — `LICENSE-SpaceGrotesk.txt` |
| `jetbrains-mono-latin-wght-normal.woff2` | JetBrains Mono (variable weight 100–800) | SIL Open Font License 1.1 — `LICENSE-JetBrainsMono.txt` |

Each file is the Latin subset, taken unmodified from the matching
`@fontsource-variable/*` package, version 5.3.0. They are loaded in
`web/app/layout.js` with `next/font/local`.

The fonts keep their own licence; the MIT licence at the repository root
covers the MotoQuant code, not these files.
