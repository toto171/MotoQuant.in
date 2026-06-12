'use client';

/**
 * MotoQuant Pro — Anonymous client telemetry.
 * =============================================
 * Goal: catch bugs and usage signals from real users without storing PII.
 *
 * What we send to /api/telemetry/event:
 *   - event: string label (e.g. 'sim_run_start', 'sim_run_error', 'js_error')
 *   - props: { ...arbitrary key/value details }
 *   - session_id: random uuid generated once per browser session, NOT
 *                 persisted across tabs/refreshes
 *   - ts: client clock epoch ms
 *   - ua: navigator.userAgent (for diagnosing browser-specific issues)
 *   - viewport: { w, h }
 *   - path: location.pathname
 *
 * What we DO NOT send: user id, email, IP (server-side strips that),
 * URL search params, scroll positions, cursor positions, or any free-text
 * input. Only enumerated event labels + numeric/categorical props.
 *
 * Transport: navigator.sendBeacon when available (fires-and-forgets even
 * during page unload), else fetch with keepalive: true. Both calls swallow
 * all errors silently — telemetry MUST NEVER break the page.
 *
 * Backend: see motoquant/api.py @app.post('/api/telemetry/event'). The
 * Render log stream is the source-of-truth; for prod-scale aggregation
 * later, the same JSON can be rerouted to PostHog/Logfire without changing
 * the client.
 */

import { API_URL } from './api';

// Session id = one per page-load. Resets when user reloads or closes tab.
// Per-tab is intentional — it keeps the data narrow (one short session per
// row) and avoids the privacy-trap of an effectively-permanent cookie.
const SESSION_ID = (() => {
  if (typeof window === 'undefined') return 'ssr';
  // Prefer crypto.randomUUID where supported; fall back to a simple random.
  try {
    return crypto.randomUUID();
  } catch {
    return Math.random().toString(36).slice(2) + '_' + Date.now().toString(36);
  }
})();

let _errorsHandlerInstalled = false;
let _disabled = false;

function safeViewport() {
  if (typeof window === 'undefined') return { w: 0, h: 0 };
  return { w: window.innerWidth || 0, h: window.innerHeight || 0 };
}

function safePath() {
  if (typeof window === 'undefined') return '';
  return window.location?.pathname ?? '';
}

/**
 * Send an event to the telemetry endpoint. Fire-and-forget, never throws.
 * Suppress in development unless explicitly enabled.
 */
export function track(event, props = {}) {
  if (_disabled || typeof window === 'undefined') return;
  // Skip on localhost / preview unless explicitly enabled — keeps dev iterations
  // out of the prod usage funnel.
  const host = window.location.hostname;
  const isDev = host === 'localhost' || host === '127.0.0.1' || host.endsWith('.local');
  if (isDev && !window.__MOTOQUANT_TELEMETRY_FORCE) return;

  // Strip anything funky from props — only allow numbers, booleans, short
  // strings (<= 200 chars), and null. Truncate strings, reject objects.
  const safeProps = {};
  for (const [k, v] of Object.entries(props || {})) {
    if (typeof k !== 'string' || k.length > 64) continue;
    if (v === null || typeof v === 'boolean' || typeof v === 'number') {
      safeProps[k] = v;
    } else if (typeof v === 'string') {
      safeProps[k] = v.length > 200 ? v.slice(0, 200) : v;
    }
    // objects, arrays, functions silently dropped
  }

  const payload = {
    event: String(event).slice(0, 64),
    props: safeProps,
    session_id: SESSION_ID,
    ts: Date.now(),
    ua: (navigator.userAgent || '').slice(0, 200),
    viewport: safeViewport(),
    path: safePath(),
  };

  const url = `${API_URL}/api/telemetry/event`;
  const body = JSON.stringify(payload);

  try {
    // sendBeacon is the right tool: queued by the browser, fires even if
    // the user is navigating away. Falls back to keepalive fetch if not
    // supported (older Safari).
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: 'application/json' });
      navigator.sendBeacon(url, blob);
    } else {
      fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
        keepalive: true,
      }).catch(() => {});
    }
  } catch {
    // Telemetry must never break the page — swallow everything.
  }
}

/**
 * Install global handlers for uncaught JS errors and unhandled promise
 * rejections. Idempotent — safe to call from multiple components.
 */
export function installErrorHandlers() {
  if (_errorsHandlerInstalled || typeof window === 'undefined') return;
  _errorsHandlerInstalled = true;

  window.addEventListener('error', (ev) => {
    track('js_error', {
      message: (ev.message || '').slice(0, 200),
      source: (ev.filename || '').slice(0, 200),
      line: ev.lineno || 0,
      col: ev.colno || 0,
    });
  });

  window.addEventListener('unhandledrejection', (ev) => {
    const reason = ev?.reason;
    const msg = reason instanceof Error ? reason.message : String(reason || '');
    track('js_unhandled_rejection', { message: msg.slice(0, 200) });
  });
}

/** Disable telemetry entirely (e.g. for Cypress / Playwright runs). */
export function disable() {
  _disabled = true;
}

export const TELEMETRY_SESSION_ID = SESSION_ID;
