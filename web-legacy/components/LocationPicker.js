'use client';

import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, Loader2, AlertCircle, Check, Locate, X } from 'lucide-react';
import { API_URL } from '../lib/api';

/**
 * LocationPicker — asks the backend to resolve a race venue from text
 * or GPS and exposes the environment (temperature, humidity, pressure,
 * altitude, density altitude) to its parent via the `onResolved` callback.
 *
 * Two inputs are supported:
 *   1. Typed location (matches seeded venues first, then falls back to OWM)
 *   2. Browser GPS (geolocation API → OWM by lat/lon)
 *
 * Props
 * -----
 *   value           current resolved env (object) or null
 *   onResolved      (env) => void — called with the resolved env payload
 *   onCleared       () => void     — called when the user clears the picker
 *   compact         boolean        — tighter layout for sidebar use
 */
export default function LocationPicker({ value, onResolved, onCleared, compact = false }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const resolve = useCallback(async (body, label) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/venues/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        let msg = `Failed (${res.status})`;
        try {
          const j = await res.json();
          if (j?.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
        } catch {
          try { msg = await res.text(); } catch {}
        }
        throw new Error(msg);
      }
      const data = await res.json();
      // Attach the user-visible label for display
      onResolved?.({ ...data, _label: label || data.resolved_name || query });
    } catch (e) {
      setError(e.message || 'Failed to resolve location');
    } finally {
      setLoading(false);
    }
  }, [onResolved, query]);

  async function handleText(e) {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please type a place name.');
      return;
    }
    await resolve({ location: query.trim() }, query.trim());
  }

  async function useMyLocation() {
    setError(null);
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setError('Your browser does not support geolocation.');
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude, altitude } = pos.coords;
        const body = { lat: latitude, lon: longitude };
        if (altitude != null && Number.isFinite(altitude)) body.altitude_m = altitude;
        await resolve(body, 'My location');
      },
      (err) => {
        setLoading(false);
        setError(`Location denied: ${err.message}`);
      },
      { timeout: 10000, maximumAge: 60000 }
    );
  }

  function clear() {
    setQuery('');
    setError(null);
    onCleared?.();
  }

  return (
    <div className={`w-full ${compact ? '' : 'p-1'}`}>
      {!value ? (
        <form onSubmit={handleText} className="space-y-2">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" size={15} />
              <input
                type="text"
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Venue or city (e.g. Aamby Valley, MMRT, Pune)"
                disabled={loading}
                className="w-full pl-9 pr-3 py-2 bg-black/40 border border-white/10 rounded-lg text-sm text-white placeholder:text-white/30 focus:border-brand-orange focus:outline-none font-mono disabled:opacity-50"
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-3 py-2 bg-brand-orange hover:bg-brand-orangeLight disabled:opacity-40 disabled:cursor-not-allowed text-black font-display font-semibold rounded-lg text-xs transition-colors"
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : 'Set'}
            </button>
          </div>
          <button
            type="button"
            onClick={useMyLocation}
            disabled={loading}
            className="inline-flex items-center gap-1.5 text-xs font-mono text-white/50 hover:text-brand-orange transition-colors disabled:opacity-50"
          >
            <Locate size={12} /> Use my GPS location
          </button>
        </form>
      ) : (
        <ResolvedCard value={value} onClear={clear} compact={compact} />
      )}

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg text-red-300 text-xs flex items-start gap-2"
          >
            <AlertCircle size={13} className="shrink-0 mt-0.5" /> {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ResolvedCard({ value, onClear, compact }) {
  // /api/venues/resolve returns a flat payload (not nested under "environment")
  const source = value?.source || 'unknown';
  const label =
    value?._label ||
    value?.venue_name ||
    value?.location_name ||
    'Resolved location';

  const rows = [
    { label: 'Temp', v: value?.temperature_c, suffix: '°C', dec: 1 },
    { label: 'Humidity', v: value?.humidity_pct, suffix: '%', dec: 0 },
    { label: 'Pressure', v: value?.pressure_hpa, suffix: ' hPa', dec: 0 },
    { label: 'Altitude', v: value?.altitude_m, suffix: ' m', dec: 0 },
    { label: 'Air density', v: value?.air_density_kgm3, suffix: ' kg/m³', dec: 3 },
    { label: 'Density alt', v: value?.density_altitude_m, suffix: ' m', dec: 0, highlight: true },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-brand-accent/40 bg-brand-accent/5 p-3"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Check size={14} className="text-brand-accent shrink-0" />
          <div className="min-w-0">
            <p className="text-sm text-white font-semibold truncate">{label}</p>
            <p className="text-[10px] font-mono text-white/50 uppercase tracking-wider">
              {source === 'seeded_venue'
                ? 'Matched seeded venue'
                : source === 'openweathermap'
                  ? 'Live weather (OpenWeatherMap)'
                  : source}
              {value?.fetched_at && ` · ${new Date(value.fetched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
            </p>
          </div>
        </div>
        <button
          onClick={onClear}
          className="p-1 -mt-1 -mr-1 text-white/50 hover:text-white transition-colors"
          aria-label="Clear location"
        >
          <X size={14} />
        </button>
      </div>

      <div className={`grid ${compact ? 'grid-cols-3 gap-x-2 gap-y-1.5' : 'grid-cols-3 gap-2'} mt-2`}>
        {rows.map((r, i) => (
          <div key={i} className="text-left">
            <p className="text-[9px] font-mono uppercase tracking-wider text-white/40">{r.label}</p>
            <p className={`text-xs font-mono tabular-nums mt-0.5 ${
              r.highlight ? 'text-brand-orange' : 'text-white/90'
            }`}>
              {r.v == null ? '—' : `${Number(r.v).toFixed(r.dec)}${r.suffix}`}
            </p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

/**
 * Helper: given a LocationPicker `value` (the raw /api/venues/resolve response),
 * build the simulator environment override fields. Maps flat resolve-endpoint
 * fields to QuickSimRequest names.
 *
 *   temperature_c → ambient_temp_c
 *   humidity_pct  → humidity_pct
 *
 * If the resolved location matched a seeded venue, `venue_id` is also set
 * so the backend can apply the venue's surface grip / altitude profile.
 */
export function environmentOverridesFromLocation(value) {
  if (!value) return {};
  const out = {};
  if (value.temperature_c != null) out.ambient_temp_c = value.temperature_c;
  if (value.humidity_pct != null) out.humidity_pct = value.humidity_pct;
  if (value.matched_venue_id != null) out.venue_id = value.matched_venue_id;
  return out;
}
