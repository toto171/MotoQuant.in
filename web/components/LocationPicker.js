'use client';

import { useState, useCallback, useEffect, useMemo, useId } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MapPin, AlertCircle, Check, Locate, X } from 'lucide-react';
import { API_URL } from '../lib/api';
import SimProgress from './SimProgress';
import Term from './Term';

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
 *
 * Restyled for CLARITY v6 (plain labels, sentence case, 44 px tap targets,
 * 16 px inputs). Props are unchanged.
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

const isIndia = (c) => ['IN', 'INDIA'].includes(String(c || '').toUpperCase());

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
  const uid = useId().replace(/:/g, '');

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
      const aIN = isIndia(a.country) ? 0 : 1;
      const bIN = isIndia(b.country) ? 0 : 1;
      if (aIN !== bIN) return aIN - bIN;
      return (a.name || '').localeCompare(b.name || '');
    });
    return indianFirst.slice(0, compact ? 7 : 8);
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
          let msg = `Request failed (${res.status})`;
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
        setError(e.message || 'Could not look up that place.');
      } finally {
        setLoading(false);
      }
    },
    [onResolved, query],
  );

  async function handleText(e) {
    e.preventDefault();
    if (!query.trim()) {
      setError('Type a place name first.');
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
          1: 'Location access is blocked. Allow it in your browser settings.',
          2: 'Your location is not available. Check GPS or your network and try again.',
          3: 'Finding your location took too long. Try again.',
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
        <div className="space-y-3">
          {quickPickVenues.length > 0 && (
            <div>
              <p className="field-label">Pick a track</p>
              <div className="flex flex-wrap gap-2" role="group" aria-label="Known tracks">
                {quickPickVenues.map((v) => (
                  <button
                    key={v.id}
                    type="button"
                    onClick={() => pickVenue(v)}
                    disabled={loading}
                    className="inline-flex min-h-[44px] items-center gap-1.5 rounded-full border border-white/15 px-3.5 text-sm font-medium text-white/80 transition-colors hover:border-accent/60 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <MapPin size={14} className="shrink-0 text-white/55" aria-hidden="true" />
                    <span>{v.name}</span>
                    {v.altitude_m != null && (
                      <span className="text-xs tabular-nums text-white/55">
                        {Math.round(v.altitude_m)} m
                      </span>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}

          <form onSubmit={handleText} className="space-y-2">
            <label htmlFor={`${uid}-place`} className="field-label">
              Or search for a place
            </label>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <MapPin
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-white/55"
                  size={16}
                  aria-hidden="true"
                />
                <input
                  id={`${uid}-place`}
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="A city or track, e.g. Pune"
                  autoComplete="off"
                  disabled={loading}
                  className="input-base pl-9 disabled:opacity-50"
                />
              </div>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="btn-primary btn-sm disabled:cursor-not-allowed disabled:opacity-40"
              >
                Set location
              </button>
            </div>
            <button
              type="button"
              onClick={useMyLocation}
              disabled={loading}
              className="inline-flex min-h-[44px] items-center gap-2 text-sm font-medium text-white/70 transition-colors hover:text-white disabled:opacity-50"
            >
              <Locate size={16} aria-hidden="true" />
              Use my current location
            </button>
            {/* Staged progress while resolving (replaces the old spinner) */}
            {loading && <SimProgress active compact label="Finding conditions" className="mt-1" />}
          </form>
        </div>
      ) : (
        <ResolvedCard value={value} onClear={clear} compact={compact} />
      )}

      <AnimatePresence>
        {error && (
          <motion.div
            role="alert"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 flex items-start gap-2 rounded-lg border border-signal-foul/30 bg-signal-foul/10 p-2.5 text-sm text-signal-foul"
          >
            <AlertCircle size={16} className="mt-0.5 shrink-0" aria-hidden="true" /> {error}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function ResolvedCard({ value, onClear, compact }) {
  const source = value?.source || 'unknown';
  const label =
    value?._label || value?.venue_name || value?.location_name || 'Chosen location';

  const rows = [
    { label: 'Temperature', v: value?.temperature_c, suffix: ' °C', dec: 1 },
    { label: 'Humidity', v: value?.humidity_pct, suffix: ' %', dec: 0 },
    { label: 'Altitude', v: value?.altitude_m, suffix: ' m', dec: 0 },
    { label: 'Air density', v: value?.air_density_kgm3, suffix: ' kg/m³', dec: 3 },
    { label: 'da', v: value?.density_altitude_m, suffix: ' m', dec: 0, highlight: true },
  ].filter((r) => r.v != null);

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border border-signal-go/30 bg-signal-go/[0.06] p-3.5"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <Check size={16} className="shrink-0 text-signal-go" aria-hidden="true" />
          <div className="min-w-0">
            <p className="truncate font-display text-sm font-semibold text-white">{label}</p>
            <p className="text-xs text-white/60">
              {source === 'seeded_venue'
                ? 'Known drag strip'
                : source === 'openweathermap'
                  ? 'Live weather'
                  : 'Conditions found'}
              {value?.fetched_at &&
                ` · ${new Date(value.fetched_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClear}
          className="-mr-1.5 -mt-1.5 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-white/60 transition-colors hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/70"
          aria-label="Clear location"
        >
          <X size={16} aria-hidden="true" />
        </button>
      </div>

      {rows.length > 0 && (
        <dl className={`mt-2 grid grid-cols-2 gap-x-3 gap-y-2 ${compact ? 'sm:grid-cols-3' : 'sm:grid-cols-3'}`}>
          {rows.map((r) => (
            <div key={r.label} className="text-left">
              <dt className="text-xs text-white/60">
                {r.label === 'da' ? <Term k="da">Effective altitude</Term> : r.label}
              </dt>
              <dd
                className={`mt-0.5 font-mono text-sm tabular-nums ${r.highlight ? 'text-accent' : 'text-white/90'}`}
              >
                {`${Number(r.v).toFixed(r.dec)}${r.suffix}`}
              </dd>
            </div>
          ))}
        </dl>
      )}
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
  // Same bounds as the API (-30..60 °C, 0..100 %): never send what it would reject.
  if (value.temperature_c != null) out.ambient_temp_c = Math.max(-30, Math.min(60, value.temperature_c));
  if (value.humidity_pct != null) out.humidity_pct = Math.max(0, Math.min(100, value.humidity_pct));
  if (value.matched_venue_id != null) {
    out.venue_id = value.matched_venue_id;
  } else {
    // Not a known venue: send the place itself so the server simulates the
    // altitude it was resolved at (a known venue is sent by id instead).
    const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : null);
    const label = value.venue_name || value.location_name || value._label || value.resolved_name;
    if (label) out.location = label;
    if (num(value.latitude) != null) out.lat = value.latitude;
    if (num(value.longitude) != null) out.lon = value.longitude;
    if (num(value.altitude_m) != null) out.altitude_m = value.altitude_m;
  }
  return out;
}
