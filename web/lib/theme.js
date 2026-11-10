/**
 * Theme helpers (CLARITY v6). The theme lives on <html data-theme="light|dark">
 * and in localStorage['mq-theme']. A tiny inline script in app/layout.js
 * applies it before first paint; everything here is the client-side half.
 *
 * Non-Tailwind consumers (SVG/canvas/recharts props, inline style) read the
 * CSS variables instead of hard-coding colours:
 *
 *   cssVar('--fg', 0.6)      -> 'rgb(var(--fg) / 0.6)'
 *   cssVar('--accent')       -> 'rgb(var(--accent))'
 *
 * The string resolves live in CSS, so it follows theme changes with no
 * re-render. Canvas 2D contexts cannot parse `var()`: use resolveVar().
 */

export const THEME_KEY = 'mq-theme';

/** CSS colour string referencing a theme variable, optional alpha 0..1. */
export function cssVar(name, alpha) {
  return alpha == null ? `rgb(var(${name}))` : `rgb(var(${name}) / ${alpha})`;
}

/** Resolve a variable to a concrete `rgb(r g b / a)` string (for <canvas>). */
export function resolveVar(name, alpha) {
  if (typeof window === 'undefined') return alpha == null ? 'rgb(255 255 255)' : `rgb(255 255 255 / ${alpha})`;
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const ch = raw || '255 255 255';
  return alpha == null ? `rgb(${ch})` : `rgb(${ch} / ${alpha})`;
}

/** 'light' | 'dark' — what is applied right now (SSR-safe, defaults dark). */
export function getTheme() {
  if (typeof document === 'undefined') return 'dark';
  const t = document.documentElement.dataset.theme;
  return t === 'light' ? 'light' : 'dark';
}

/** Apply + persist a theme. Persistence failures (private mode) are ignored. */
export function setTheme(theme) {
  const next = theme === 'light' ? 'light' : 'dark';
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = next;
    const meta = document.querySelector('meta[name="theme-color"]:not([media])');
    if (meta) meta.setAttribute('content', next === 'light' ? '#fafaf9' : '#09090b');
  }
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    /* storage unavailable — theme still applies for this page view */
  }
  return next;
}

/**
 * Source of the no-flash script injected into <head>. Kept here so the
 * layout and any test share one definition. Pure ES5, wrapped in try/catch.
 */
export const THEME_INIT_SCRIPT = `(function(){try{var t=null;try{t=localStorage.getItem('${THEME_KEY}')}catch(e){}if(t!=='light'&&t!=='dark'){t=window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark'}document.documentElement.dataset.theme=t;var m=document.querySelector('meta[name="theme-color"]:not([media])');if(m)m.setAttribute('content',t==='light'?'#fafaf9':'#09090b')}catch(e){document.documentElement.dataset.theme='dark'}})();`;
