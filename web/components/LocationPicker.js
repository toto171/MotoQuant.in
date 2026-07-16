'use client';

import { useState, useCallback, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, AlertCircle, Check, Locate, X } from 'lucide-react';
import { API_URL } from '../lib/api';
import SimProgress from './SimProgress';

/**
 * LocationPicker — asks the backend to resolve a race venue from text,
 * a quick-pick venue chip, or browser GPS, and exposes the resolved
 * environment (temperature, humidity, pressure, altitude, density
 * altitude) to its parent via the `onResolved` callback.
 *
 * Three input paths:
 *   1. Quick-pick chip — instant click on a seeded venue (Aamby Valley,
 *      MMRT, BIC, etc.). Resolves via the seeded-venue branch of
 *      /api/venues/resolve, no OWM key required.
 *   2. Free-text query — types a city or venue name; resolves seeded
 *      first, OWM fallback if no match.
 *   3. Browser GPS — geolocation API → proximity-matches the closest
 *      seeded venue within 50 km (so works without an OWM key as long
 *      as the user is near a tracked drag strip); falls back to OWM by
 *      lat/lon if no nearby venue.
 *
 * Props
 * -----
 *   value           current resolved env (object) or null
 *   onResolved      (env) => void — called with the resolved env payload
 *   onCleared       () => void     — called when the user clears the picker
 *   compact         boolean        — tighter layout for sidebar use
 */

// Haversine distance in km between two GPS points
function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius km
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// Module-level cache so we don't refetch /api/venues on every mount
let _cachedVenues = null;

async function fetchVenues() {
  if (_cachedVenues) return _cachedVenues;
  try {
    const res = await fetch(`${API_URL}/api/venues`);
    if (!res.ok) return [];
    const data = await res.json();
    _cachedVenues = Array.isArray(data?.venues) ? data.venues : [];
    return _cachedVenues;
  } catch {
    return [];
  }
}

export default function LocationPicker({ value, onResolved, onCleared, compact = false }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [venues, setVenues] = useState([]);

  useEffect(() => {
    let mounted = true;
    fetchVenues().then((v) => {
      if (mounted) setVenues(v);
    });
    return () => {
      mounted = false;
    };
  }, []);

  // Quick-pick chip set: Indian venues first (active drag scene), then by name.
  const quickPickVenues = useMemo(() => {
    if (!venues.length) return [];
    const indianFirst = [...venues].sort((a, b) => {
      const aIN = (a.country || '').toUpperCase() === 'IN' ? 0 : 1;
      const bIN = (b.country || '').toUpperCase() === 'IN' ? 0 : 1;
      if (aIN !== bIN) return aIN - bIN;
      return (a.name || '').localeCompare(b.name || '');
    });
    return indianFirst.slice(0, compact ? 6 : 8);
  }, [venues, compact]);

  const resolve = useCallback(
    async (body, label) => {
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
            if (j?.detail)
              msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
          } catch {
            try { msg = await res.text(); } catch {}
          }
          throw new Error(msg);
        }
        const data = await res.json();
        onResolved?.({ ...data, _label: label || data.resolved_name || data.venue_name || query });
      } catch (e) {
        setError(e.message || 'Failed to resolve location');
      } finally {
        setLoading(false);
      }
    },
    [onResolved, query],
  );

  async function handleText(e) {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please type a place name.');
      return;
    }
    await resolve({ location: query.trim() }, query.trim());
  }

  async function pickVenue(v) {
    setError(null);
    await resolve({ location: v.name }, v.name);
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
        // Try proximity-match against seeded venues first — no OWM key needed.
        try {
          const seeded = venues.length ? venues : await fetchVenues();
          let closest = null;
          let closestKm = Infinity;
          for (const v of seeded) {
            if (v.latitude == null || v.longitude == null) continue;
            const km = haversineKm(latitude, longitude, v.latitude, v.longitude);
            if (km < closestKm) {
              closestKm = km;
              closest = v;
            }
          }
          if (closest && closestKm <= 50) {
            const label = `Near ${closest.name} (${closestKm.toFixed(0)} km)`;
            await resolve({ location: closest.name }, label);
            return;
          }
        } catch {
          // fall through to OWM
        }
        const body = { lat: latitude, lon: longitude };
        if (altitude != null && Number.isFinite(altitude)) body.altitude_m = altitude;
        await resolve(body, 'My location');
      },
      (err) => {
        setLoading(false);
        const map = {
          1: 'Permission denied. Allow location access in your browser.',
          2: 'Location unavailable. Check GPS / network and try again.',
          3: 'Location request timed out.',
        };
        setError(map[err.code] || `Location error: ${err.message}`);
      },
      { timeout: 10000, maximumAge: 60000, enableHighAccuracy: false },
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
        <div className="space-y-2.5">
          {quickPickVenues.length > 0 && (
            <div>
              <p className="label-mono mb-1.5">Quick pick</p>
              <div className="flex flex-wrap gap-1.5">
                {quickPickVenues.map((v) => (
                  <button
                    key={v.id}
                    type="button"
                    onClick={() => pickVenue(v)}
                    disabled={loading}
                    className="chip transition-colors hover:border-accent/40 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <MapPin size={10} className="text-white/40" aria-hidden="true" />
                    {v.name}
                    {v.altitude_m != null && (
                      <span className="text-[9px] text-white/40 ml-0.5 tabular-nums">
                        {Math.round(v.altitude_m)}m
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleText} className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40" size={15} />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Or type any city / venue (e.g. Pune)"
                  disabled={loading}
                  className="input-base pl-9 font-mono disabled:opacity-50"
                />
              </div>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="btn-primary btn-sm disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Set
              </button>
            </div>
            <button
              type="button"
              onClick={useMyLocation}
              disabled={loading}
              className="inline-flex items-center gap-1.5 text-xs font-mono text-white/50 hover:text-white transition-colors disabled:opacity-50"
            >
              <Locate size={12} aria-hidden="true" />
              Use my GPS location
            </button>
            {/* Staged progress while resolving (replaces the old spinner) */}
            {loading && <SimProgress active compact label="Resolving" className="mt-1" />}
          </form>
        </div>
      ) : (
        <ResolvedCard value={value} onClear={clear} compact={compact} />
      )}

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 p-2 bg-signal-foul/10 border border-signal-foul/30 rounded-lg text-signal-foul text-xs flex items-start gap-2"
          >
            <AlertCircle size={13} className="shrink-0 mt-0.5" /> {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ResolvedCard({ value, onClear, compact }) {
  const source = value?.source || 'unknown';
  const label =
    value?._label || value?.venue_name || value?.location_name || 'Resolved location';

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
      className="rounded-lg border border-signal-go/30 bg-signal-go/[0.05] p-3"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <Check size={14} className="text-signal-go shrink-0" aria-hidden="true" />
          <div className="min-w-0">
            <p className="font-display text-sm font-semibold text-white truncate">
              {label}
            </p>
            <p className="text-[10px] font-mono text-white/50 uppercase tracking-wider">
              {source === 'seeded_venue'
                ? 'Matched seeded venue'
                : source === 'openweathermap'
                  ? 'Live weather (OpenWeatherMap)'
                  : source}
              {value?.fetched_at &&
                ` · ${new Date(value.fetched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
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
            <p className={`text-xs font-mono tabular-nums mt-0.5 ${r.highlight ? 'text-accent' : 'text-white/85'}`}>
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
 * build the simulator environment override fields.
 */
export function environmentOverridesFromLocation(value) {
  if (!value) return {};
  const out = {};
  if (value.temperature_c != null) out.ambient_temp_c = value.temperature_c;
  if (value.humidity_pct != null) out.humidity_pct = value.humidity_pct;
  if (value.matched_venue_id != null) out.venue_id = value.matched_venue_id;
  return out;
}
