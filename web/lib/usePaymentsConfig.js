'use client';

/**
 * usePaymentsConfig — cached client fetch of GET /api/payments/config.
 *
 * The config (beta flag, prices_inr price book, provider status booleans)
 * drives billing-aware UI. The fetch is module-level single-flight: many
 * components can mount the hook and exactly one request goes out per page
 * load; later mounts resolve from the memoized promise.
 *
 * Returns {cfg, loading}. A settled failure (after retries) resolves to
 * cfg null / loading false — each caller fails toward ITS safe side: gating
 * surfaces (e.g. save-run) keep today's open behavior, sales copy (pricing)
 * falls back to paid copy rather than promising "free during beta" while
 * billing may be live. A failed fetch is not memoized, so a later mount
 * retries.
 */

import { useEffect, useState } from 'react';
// Billing surfaces use the direct backend base (identical fetch semantics to
// /pricing and AuthProvider) — see the API_URL_DIRECT rationale in lib/api.js.
import { API_URL_DIRECT } from './api';

let cfgPromise = null;

const RETRY_DELAYS_MS = [1500, 4000]; // Render free-tier cold starts are real

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function fetchOnce() {
  try {
    const r = await fetch(`${API_URL_DIRECT}/api/payments/config`);
    return r.ok ? await r.json() : null;
  } catch {
    return null;
  }
}

function fetchConfig() {
  if (!cfgPromise) {
    // Retry with backoff before settling null: once billing is live, a
    // settled failure makes billing-aware UI guess, so failures should be
    // rare and transient-only.
    cfgPromise = (async () => {
      let cfg = await fetchOnce();
      for (const delay of RETRY_DELAYS_MS) {
        if (cfg != null) break;
        await sleep(delay);
        cfg = await fetchOnce();
      }
      if (cfg == null) cfgPromise = null; // don't memoize a failure
      return cfg;
    })();
  }
  return cfgPromise;
}

export function usePaymentsConfig() {
  const [state, setState] = useState({ cfg: null, loading: true });

  useEffect(() => {
    let cancelled = false;
    fetchConfig().then((cfg) => {
      if (!cancelled) setState({ cfg, loading: false });
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

export default usePaymentsConfig;
