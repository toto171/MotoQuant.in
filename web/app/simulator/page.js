'use client';

import { useState, useEffect, useRef, useCallback, useMemo, useId, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Zap, Search, ChevronDown, ChevronRight, X, MapPin, Gauge, Wrench,
  CircleDot, Thermometer,
  BarChart3, Table2, Settings2, Upload, RotateCcw, Layers, MessageSquare,
  Locate, AlertCircle, Share2, Check } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import {
  API_URL as API, simulateJob, topspeedJob, compareJob, saveRun, partLabel,
} from '../../lib/api';
import useAsyncTask from '../../lib/useAsyncTask';
import SimProgress from '../../components/SimProgress';
import ActionButton from '../../components/ActionButton';
import { Skeleton, SkeletonCard } from '../../components/Skeleton';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import { useAuth } from '../../components/AuthProvider';
import { track, trackSimRun, installErrorHandlers } from '../../lib/telemetry';
import ChatPanel from '../../components/ChatPanel';
import CodeComment from '../../components/CodeComment';
import ScoreboardDigits from '../../components/ScoreboardDigits';

// ──────────────────────────────────────────────────────────────────────────
// GROWTH_EXP_003: default-bike A/B test.
// A (control / SEO-stable) = Hayabusa — aspirational, matches layout.js
//                            keywords and OG copy ("hayabusa quarter mile").
// B (variant)              = Pulsar NS 200 — high-volume Indian commuter,
//                            most likely to match the visitor's actual bike,
//                            tests whether localising the default reduces the
//                            "is this for me?" friction on /simulator.
// Picker is name-substring matched against the DB-loaded bike list so that
// catalog reshuffles (Hayabusa Gen1 vs 2008-2012 vs 2021-2024) don't break
// the variant. Falls back to bikes[0] if no name match (e.g. unseeded DB).
// See data/growth_experiments.json (id: EXP-003) for full design + decision.
// ──────────────────────────────────────────────────────────────────────────
const EXP003_DEFAULT_BIKE_PATTERNS = {
  A: [/hayabusa/i],
  B: [/pulsar\s*ns\s*200/i, /pulsar ns 200/i],
};

function pickDefaultBikeForVariant(bikes, variant) {
  if (!bikes || bikes.length === 0) return null;
  const patterns = EXP003_DEFAULT_BIKE_PATTERNS[variant] || EXP003_DEFAULT_BIKE_PATTERNS.A;
  for (const re of patterns) {
    const match = bikes.find(b => {
      const label = `${b.manufacturer || ''} ${b.model || b.model_name || ''}`;
      return re.test(label);
    });
    if (match) return match;
  }
  // Fallback: alphabetical-first (existing pre-EXP-003 behaviour).
  return bikes[0];
}

/* ═══════════════════════════════════════════════════════════════════════════
   REUSABLE COMPONENTS
   ═══════════════════════════════════════════════════════════════════════════ */

// ─── Panel Card — IGNITION v5 `.card` surface (rest props spread so
//     data-exp / role="tabpanel" attributes reach the DOM) ────────────────
function Card({ children, className = '', glow = false, ...rest }) {
  return (
    <div
      className={`card relative ${glow ? 'border-white/[0.14]' : ''} ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}

// ─── Searchable Dropdown ─────────────────────────────────────────────────
function Dropdown({ label, items, selected, onSelect, renderItem, renderSelected, searchKey, groupKey, emptyMsg, icon }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const filtered = items.filter(i => !q || searchKey(i).toLowerCase().includes(q.toLowerCase()));
  const grouped = groupKey ? {} : null;
  if (grouped) filtered.forEach(i => { const g = groupKey(i); if (!grouped[g]) grouped[g] = []; grouped[g].push(i); });

  return (
    <div className="relative" ref={ref}>
      {label && (
        <label className="label-mono flex items-center gap-1.5 mb-1.5">
          {icon}{label}
        </label>
      )}
      <button
        onClick={() => setOpen(!open)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="w-full p-2.5 rounded-lg border border-white/[0.08] bg-asphalt-3 text-left flex items-center justify-between hover:border-white/25 transition-colors text-sm group">
        {selected ? renderSelected(selected) : <span className="text-white/35">Select...</span>}
        <ChevronDown size={13} className={`text-white/35 group-hover:text-white/70 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute z-50 mt-1.5 w-full bg-asphalt-2 border border-white/[0.12] rounded-lg shadow-2xl shadow-black/50 max-h-72 overflow-hidden">
          <div className="p-2 border-b border-white/[0.06]">
            <div className="relative">
              <Search size={12} className="absolute left-2.5 top-2.5 text-white/35 z-10" />
              <input type="text" value={q} onChange={e => setQ(e.target.value)} placeholder="Search..."
                className="input-base h-9 pl-8 pr-3 text-xs rounded-lg" autoFocus />
            </div>
          </div>
          <div className="overflow-y-auto max-h-56 scrollbar-thin" role="listbox">
            {grouped ? Object.keys(grouped).sort().map(g => (
              <div key={g}>
                <div className="label-mono px-3 py-1 font-semibold bg-asphalt-2 sticky top-0">{g}</div>
                {grouped[g].map((item, i) => (
                  <button key={i} role="option" aria-selected={selected === item}
                    onClick={() => { onSelect(item); setOpen(false); setQ(''); }}
                    className="w-full px-3 py-2 text-left text-xs hover:bg-white/[0.05] transition-colors text-white/75 hover:text-white">
                    {renderItem(item)}
                  </button>
                ))}
              </div>
            )) : filtered.map((item, i) => (
              <button key={i} role="option" aria-selected={selected === item}
                onClick={() => { onSelect(item); setOpen(false); setQ(''); }}
                className="w-full px-3 py-2 text-left text-xs hover:bg-white/[0.05] transition-colors text-white/75 hover:text-white">
                {renderItem(item)}
              </button>
            ))}
            {filtered.length === 0 && <div className="px-3 py-4 text-center text-xs text-white/30">{emptyMsg || 'No results'}</div>}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Slider ──────────────────────────────────────────────────────────────
function Slider({ label, value, onChange, min, max, step = 1, unit = '', colorFn }) {
  const color = colorFn ? colorFn(value) : 'text-white';
  const display = value > 0 && unit !== 'kg' && unit !== '°C' && unit !== '%' ? `+${value}` : `${value}`;
  return (
    <div>
      <div className="flex justify-between text-[11px] mb-1">
        <span className="label-mono">{label}</span>
        <span className={`font-mono font-medium tabular-nums ${color}`}>{display}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        aria-label={label}
        aria-valuetext={`${display}${unit}`}
        className="w-full h-1 accent-accent cursor-pointer" />
    </div>
  );
}

// ─── Part Chip ───────────────────────────────────────────────────────────
function PartChip({ part, onRemove }) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded border border-white/[0.12] bg-white/[0.04] font-mono text-[10px] text-white/75 group">
      <span className="font-medium">{partLabel(part.brand, part.model_name)}</span>
      {part.price_inr > 0 && <span className="text-white/40">₹{(part.price_inr / 1000).toFixed(1)}k</span>}
      <button onClick={onRemove} className="opacity-50 group-hover:opacity-100 hover:text-white transition-opacity"><X size={10} /></button>
    </div>
  );
}

// ─── Metric Card ─────────────────────────────────────────────────────────
function Metric({ label, value, unit, large, accent }) {
  return (
    <div className="text-center">
      <p className="label-mono mb-1">{label}</p>
      <p className={`font-mono font-bold tabular-nums ${large ? 'text-3xl' : 'text-xl'} ${accent ? 'text-accent' : 'text-white'}`}>
        {value}<span className={`${large ? 'text-base' : 'text-xs'} font-mono text-white/40 ml-0.5`}>{unit}</span>
      </p>
    </div>
  );
}

// ─── Tab Button ──────────────────────────────────────────────────────────
function Tab({ active, onClick, icon, label }) {
  return (
    <button onClick={onClick}
      role="tab"
      aria-selected={active}
      aria-controls="sim-tabpanel"
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded font-mono text-[11px] uppercase tracking-wide transition-colors ${
        active
          ? 'bg-accent/[0.12] text-accent border border-accent/30'
          : 'text-white/45 hover:text-white/75 hover:bg-white/[0.03] border border-transparent'
      }`}>
      {icon}{label}
    </button>
  );
}

// ─── Inline error tile with Retry — the one branded error pattern ───────
function ErrorTile({ message, onRetry, retryLabel = 'Retry', className = '' }) {
  return (
    <div className={`rounded-lg border border-signal-foul/25 bg-signal-foul/5 p-3 text-signal-foul text-xs flex items-center justify-between gap-3 ${className}`}>
      <span className="flex items-start gap-1.5 min-w-0">
        <AlertCircle size={13} className="shrink-0 mt-0.5" />
        <span className="break-words">{message}</span>
      </span>
      {onRetry && (
        <button onClick={onRetry} className="btn-ghost btn-sm shrink-0">{retryLabel}</button>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHART COMPONENTS
   ═══════════════════════════════════════════════════════════════════════════ */

const CHART_COLORS = { a: '#FF5E1F', b: '#6FE3B2' };

function SimChart({ data, dataKey, label, unit, color = CHART_COLORS.a, domain }) {
  const gradId = useId();
  if (!data || data.length === 0) return null;
  const gid = `grad-${dataKey}-${gradId}`;
  return (
    <div className="h-44">
      <p className="label-mono mb-2">{label}</p>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.2} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} tickFormatter={v => `${v}s`} />
          <YAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} domain={domain} />
          <Tooltip
            contentStyle={{ background: '#10141B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
            labelFormatter={v => `${v}s`}
            formatter={v => [`${typeof v === 'number' ? v.toFixed(1) : v} ${unit}`, label]}
          />
          <Area type="monotone" dataKey={dataKey} stroke={color} strokeWidth={1.5}
            fill={`url(#${gid})`} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════════════════ */

function SimulatorPageInner() {
  // ─── GROWTH_EXP_003: read ?variant=B (default A = Hayabusa control) ──
  // Same canonical URL, same h1, same meta — the only difference is which
  // bike pre-selects. data-exp/data-variant on the bike-picker Card lets
  // analytics attribute simulator runs to the right arm.
  const searchParams = useSearchParams();
  const defaultBikeVariant = searchParams?.get('variant') === 'B' ? 'B' : 'A';
  // One-tap starting points — the bikes the Indian drag scene actually asks for.
  const POPULAR_BIKE_PATTERNS = useMemo(() => ([
    { label: 'Hayabusa',    re: /hayabusa/i },
    { label: 'R15 V4',      re: /yzf[- ]?r15 v4/i },
    { label: 'Duke 390',    re: /\bduke 390/i },
    { label: 'Classic 350', re: /classic 350/i },
    { label: 'ZX-10R',      re: /zx[- ]?10r/i },
    { label: 'GSX-R1000',   re: /gsx[- ]?r ?1000/i },
  ]), []);

  // ─── Data from API ───────────────────────────────────────────────────
  const [bikes, setBikes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [allParts, setAllParts] = useState([]);
  const [allTires, setAllTires] = useState([]);
  const [venues, setVenues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bootProgress, setBootProgress] = useState(0); // 0..1 — counts the 5 boot fetches
  const [loadError, setLoadError] = useState(null);

  // ─── User selections ────────────────────────────────────────────────
  const [bike, setBike] = useState(null);
  const [selectedParts, setSelectedParts] = useState([]);
  const [frontTire, setFrontTire] = useState(null);
  const [rearTire, setRearTire] = useState(null);
  const [venue, setVenue] = useState(null);
  const [riderKg, setRiderKg] = useState(75);
  const [powerBoost, setPowerBoost] = useState(0);
  const [massChange, setMassChange] = useState(0);

  // ─── Environment ─────────────────────────────────────────────────────
  const [ambientTemp, setAmbientTemp] = useState(25);
  const [trackTemp, setTrackTemp] = useState(30);
  const [humidity, setHumidity] = useState(40);
  const [headwind, setHeadwind] = useState(0);

  // ─── "Use my location" geolocation flow ─────────────────────────────
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoMessage, setGeoMessage] = useState(null);  // { tone: 'ok'|'err', text: string }

  // ─── Results + view state ────────────────────────────────────────────
  const [result, setResult] = useState(null);          // quick sim
  const [fullResult, setFullResult] = useState(null);  // full RK4 sim
  const [topSpeedResult, setTopSpeedResult] = useState(null);
  const [compareResult, setCompareResult] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [liveSim, setLiveSim] = useState(true); // Live = quick sim re-runs as you tune; Manual = button only
  const [activeCategory, setActiveCategory] = useState(null);
  const [activeTab, setActiveTab] = useState('results');
  const [showEnv, setShowEnv] = useState(false);
  const debounceRef = useRef(null);

  // ─── A vs B Comparison config ───────────────────────────────────────
  const [compareBike, setCompareBike] = useState(null);
  const [compareParts, setCompareParts] = useState([]);
  const [comparePower, setComparePower] = useState(0);
  const [compareMass, setCompareMass] = useState(0);

  // ─── Upload refs ────────────────────────────────────────────────────
  const fileInputRef = useRef(null);
  const dynoInputRef = useRef(null);
  const lastDragyFileRef = useRef(null);
  const lastDynoFileRef = useRef(null);

  // ─── Auth (read-only) — bearer token for "Save this run" ────────────
  const { accessToken } = useAuth();
  const [savedRun, setSavedRun] = useState(null);

  // ─── Shared sim request body ─────────────────────────────────────────
  // Read fresh from state at call time (useAsyncTask keeps its fn current).
  function baseSimBody(extra = {}) {
    const body = {
      rider_mass_kg: riderKg,
      power_boost_pct: powerBoost,
      mass_delta_kg: massChange,
      ambient_temp_c: ambientTemp,
      track_temp_c: trackTemp,
      humidity_pct: humidity,
      headwind_kmh: headwind,
      ...extra,
    };
    if (bike?.id != null) body.bike_id = bike.id;
    else if (bike?.preset) body.bike_preset = bike.preset;
    if (frontTire?.id != null) body.front_tire_id = frontTire.id;
    if (rearTire?.id != null) body.rear_tire_id = rearTire.id;
    if (venue?.id != null) body.venue_id = venue.id;
    return body;
  }

  /* ─── Per-op async tasks (own {loading, progress, error} each) ─────── */

  // Every sim flow on this page: open a trackSimRun handle as the FIRST
  // statement of the TASK BODY (never the button wrapper — wrappers can
  // early-return before the sim starts, logging phantom starts) and settle
  // it on every exit path. Errors are re-thrown so useAsyncTask still owns
  // the UI state. Full history: lib/telemetry.js.

  // Quick sim (~50 ms warm) — staged feedback only, per the progress doctrine.
  // `trigger` distinguishes the Live-mode debounced auto-run from an explicit
  // Run/Retry press, so the funnel can be read either way.
  const quickTask = useAsyncTask(async (signal, _onProgress, trigger = 'auto') => {
    if (!bike) return null;
    const runEvent = trackSimRun('simulator_page', 'quarter', {
      trigger,
      bike_id: bike?.id ?? null,
      part_count: selectedParts.length,
    });
    try {
      const body = baseSimBody({ part_ids: selectedParts.map(p => p.id) });
      const res = await fetch(`${API}/api/simulate/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal,
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json();
      setResult(data);
      runEvent.success({
        et_quarter_s: data?.et_quarter_s ?? null,
        trap_speed_kmh: data?.trap_speed_kmh ?? null,
      });
      return data;
    } catch (e) {
      if (e?.name === 'AbortError') runEvent.cancelled();
      else runEvent.error(e);
      throw e;
    }
  });

  // Full sim — job-backed with real RK4 progress.
  // NOTE (preserved behaviour): the full-sim body deliberately mirrors the
  // pre-redesign request and does NOT attach part_ids.
  const fullSimTask = useAsyncTask(async (signal, onProgress) => {
    const runEvent = trackSimRun('simulator_page', 'full', {
      bike_id: bike?.id ?? null,
    });
    try {
      const data = await simulateJob(baseSimBody(), onProgress, signal);
      setFullResult(data);
      runEvent.success({
        et_quarter_s: data?.et_quarter_s ?? null,
        trap_speed_kmh: data?.trap_speed_kmh ?? null,
      });
      return data;
    } catch (e) {
      if (e?.name === 'AbortError') runEvent.cancelled();
      else runEvent.error(e);
      throw e;
    }
  });

  // Top speed / LSR — job-backed.
  const topSpeedTask = useAsyncTask(async (signal, onProgress) => {
    const runEvent = trackSimRun('simulator_page', 'topspeed', {
      bike_label: bike?.model_name ?? bike?.model ?? 'unknown',
      bike_id: bike?.id ?? null,
    });
    try {
      const body = baseSimBody({
        part_ids: selectedParts.map(p => p.id),
        include_timeseries: true,
      });
      const data = await topspeedJob(body, onProgress, signal);
      setTopSpeedResult(data);
      runEvent.success({
        terminal_velocity_kmh: data?.terminal_velocity_kmh ?? null,
        reached_plateau: data?.reached_plateau ?? null,
      });
      return data;
    } catch (e) {
      if (e?.name === 'AbortError') runEvent.cancelled();
      else runEvent.error(e);
      throw e;
    }
  });

  // A vs B compare — job-backed (falls back to the sync route on old backends).
  const compareTask = useAsyncTask(async (signal, onProgress) => {
    const bBike = compareBike || bike;
    const body = {
      a_bike_id: bike.id != null ? bike.id : undefined,
      a_bike_preset: bike.preset || undefined,
      a_power_boost_pct: powerBoost,
      a_mass_delta_kg: massChange,
      a_rider_mass_kg: riderKg,
      a_part_ids: selectedParts.map(p => p.id),
      a_front_tire_id: frontTire?.id ?? undefined,
      a_rear_tire_id: rearTire?.id ?? undefined,
      b_bike_id: bBike.id != null ? bBike.id : undefined,
      b_bike_preset: bBike.preset || undefined,
      b_power_boost_pct: comparePower,
      b_mass_delta_kg: compareMass,
      b_rider_mass_kg: riderKg,
      b_part_ids: compareParts.map(p => p.id),
      venue_id: venue?.id ?? undefined,
      ambient_temp_c: ambientTemp,
      track_temp_c: trackTemp,
      humidity_pct: humidity,
      headwind_kmh: headwind,
    };
    const runEvent = trackSimRun('simulator_page', 'compare', {
      bike_id: bike?.id ?? null,
      compare_bike_id: bBike?.id ?? null,
    });
    try {
      const data = await compareJob(body, onProgress, signal);
      setCompareResult(data);
      runEvent.success({
        // Response shape is { a, b, delta: { et_s, trap_kmh, … } }.
        delta_et_s: data?.delta?.et_s ?? null,
        faster: data?.delta?.faster ?? null,
      });
      return data;
    } catch (e) {
      if (e?.name === 'AbortError') runEvent.cancelled();
      else runEvent.error(e);
      throw e;
    }
  });

  // Uploads — plain POSTs with staged feedback + Retry (file kept in a ref).
  const dragyTask = useAsyncTask(async (signal, onProgress, file) => {
    const formData = new FormData();
    formData.append('file', file);
    if (bike?.id != null) formData.append('bike_id', bike.id.toString());
    else if (bike?.preset) formData.append('bike_preset', bike.preset);
    const res = await fetch(`${API}/api/calibrate/dragy`, {
      method: 'POST',
      body: formData,
      signal,
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    setUploadResult({ type: 'dragy', ...data });
    setActiveTab('upload');
    return data;
  });

  const dynoTask = useAsyncTask(async (signal, onProgress, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API}/api/calibrate/dyno`, {
      method: 'POST',
      body: formData,
      signal,
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    setUploadResult({ type: 'dyno', ...data });
    setActiveTab('upload');
    return data;
  });

  // Save this run — anonymous saves allowed (beta); the bearer token binds
  // the run to the signed-in user's Garage when present.
  const saveTask = useAsyncTask(async (signal) => {
    const r = result;
    if (!r || r.et_quarter_s == null || bike?.id == null) return null;
    const body = {
      bike_id: bike.id,
      venue_id: venue?.id ?? null,
      et_quarter_s: r.et_quarter_s,
      trap_speed_kmh: r.trap_speed_kmh,
      et_60ft_s: r.et_60ft_s ?? null,
      et_eighth_s: r.et_eighth_s ?? null,
    };
    const resp = await saveRun(body, accessToken, signal);
    setSavedRun(resp);
    track('save_run', { bike_id: bike.id, surface: 'simulator_page' });
    return resp;
  });

  // A fresh quick-sim result invalidates the previous "Saved" state
  // (and any stale save error).
  const resetSave = saveTask.reset;
  useEffect(() => { setSavedRun(null); resetSave(); }, [result, resetSave]);

  /* ─── Run wrappers — a run force-switches to its tab AT START ───────── */
  const startFullSim = useCallback(() => {
    if (!bike || fullSimTask.active) return;
    setActiveTab('charts'); // show the progress bar where the result will land
    fullSimTask.run();
  }, [bike, fullSimTask]);

  // sim_run_start for this flow is emitted inside topSpeedTask, not here —
  // it used to fire above the guard below, so a click with no bike selected
  // (or while a run was already active) logged a start for a sim that never
  // happened, and no success could ever match it.
  const startTopSpeed = useCallback(() => {
    if (!bike || topSpeedTask.active) return;
    setActiveTab('topspeed');
    topSpeedTask.run();
  }, [bike, topSpeedTask]);

  const startCompare = useCallback(() => {
    if (!bike || compareTask.active) return;
    setActiveTab('compare');
    compareTask.run();
  }, [bike, compareTask]);

  // ─── Share this build (URL with bike/venue/sliders/parts/tires/env) ──
  const [shareCopied, setShareCopied] = useState(false);
  const shareBuild = useCallback(async () => {
    const params = new URLSearchParams();
    if (bike?.id) params.set('bike', String(bike.id));
    if (venue?.id) params.set('venue', String(venue.id));
    if (riderKg !== 75) params.set('rider', String(riderKg));
    if (powerBoost !== 0) params.set('boost', String(powerBoost));
    if (massChange !== 0) params.set('mass', String(massChange));
    // Lossless share (July 2026): parts + tires + environment overrides.
    // Old links without these params keep working — every param is optional.
    if (selectedParts.length > 0) params.set('parts', selectedParts.map(p => p.id).join(','));
    if (frontTire?.id != null) params.set('ft', String(frontTire.id));
    if (rearTire?.id != null) params.set('rt', String(rearTire.id));
    if (ambientTemp !== 25) params.set('temp', String(ambientTemp));
    if (trackTemp !== 30) params.set('track', String(trackTemp));
    if (humidity !== 40) params.set('hum', String(humidity));
    if (headwind !== 0) params.set('wind', String(headwind));
    const url = `${window.location.origin}/simulator?${params.toString()}`;
    try {
      if (navigator.share) {
        await navigator.share({ title: `MotoQuant — ${bike?.manufacturer ?? ''} ${bike?.model ?? ''}`.trim(), url });
        return;
      }
    } catch (e) { /* user dismissed the share sheet — fall through to copy */ }
    try {
      await navigator.clipboard.writeText(url);
      setShareCopied(true);
      setTimeout(() => setShareCopied(false), 2000);
      track('share_build', { bike_id: bike?.id });
    } catch (e) { /* clipboard unavailable — silently ignore */ }
  }, [bike, venue, riderKg, powerBoost, massChange, selectedParts, frontTire, rearTire, ambientTemp, trackTemp, humidity, headwind]);

  // ─── Boot: fetch all data (retryable — no full-page loader) ──────────
  useEffect(() => { installErrorHandlers(); track('page_view', { surface: 'simulator_page' }); }, []);

  const boot = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    setBootProgress(0);
    try {
      const safeJson = async (res, fallback) => {
        try { return res.ok ? await res.json() : fallback; }
        catch (e) { console.warn('JSON parse error:', e); return fallback; }
      };
      // Each settled fetch ticks the boot progress bar by 1/5.
      const tick = (p) => p.then((r) => {
        setBootProgress((v) => Math.min(1, v + 0.2));
        return r;
      });
      const [bikesRes, catsRes, partsRes, tiresRes, venuesRes] = await Promise.all([
        tick(fetch(`${API}/api/bikes?limit=2000`)),
        tick(fetch(`${API}/api/parts/categories`)),
        tick(fetch(`${API}/api/parts?limit=2000`)),
        tick(fetch(`${API}/api/tires?limit=2000`)),
        tick(fetch(`${API}/api/venues`)),
      ]);
      const [bikesData, catsData, partsData, tiresData, venuesData] = await Promise.all([
        safeJson(bikesRes, { bikes: [] }),
        safeJson(catsRes, { categories: [] }),
        safeJson(partsRes, { parts: [] }),
        safeJson(tiresRes, { tires: [] }),
        safeJson(venuesRes, { venues: [] }),
      ]);
      setBikes(bikesData.bikes || []);
      setCategories(catsData.categories || []);
      setAllParts(partsData.parts || []);
      setAllTires(tiresData.tires || []);
      setVenues(venuesData.venues || []);
      // Shared-build links win over the GROWTH_EXP_003 variant-aware default
      // (A=Hayabusa, B=Pulsar NS 200). `?bike_id=` (used by the /bikes/[id]
      // CTAs) is accepted as an alias of `?bike=`.
      const sharedBikeId = parseInt(
        searchParams?.get('bike') ?? searchParams?.get('bike_id') ?? '', 10,
      );
      const sharedBike = Number.isFinite(sharedBikeId)
        ? (bikesData.bikes || []).find((b) => b.id === sharedBikeId)
        : null;
      if (sharedBike) setBike(sharedBike);
      else if (bikesData.bikes?.length) setBike(pickDefaultBikeForVariant(bikesData.bikes, defaultBikeVariant));
      const sharedVenueId = parseInt(searchParams?.get('venue') ?? '', 10);
      if (Number.isFinite(sharedVenueId)) {
        const sv = (venuesData.venues || []).find((v) => v.id === sharedVenueId);
        if (sv) setVenue(sv);
      }
      const qsNum = (key, set, min, max) => {
        const v = parseFloat(searchParams?.get(key) ?? '');
        if (Number.isFinite(v) && v >= min && v <= max) set(v);
      };
      qsNum('rider', setRiderKg, 50, 130);
      qsNum('boost', setPowerBoost, -20, 50);
      qsNum('mass', setMassChange, -30, 30);
      // Lossless-share read-back: selected parts, tires, env overrides.
      const partIdsRaw = searchParams?.get('parts');
      if (partIdsRaw) {
        const ids = partIdsRaw.split(',').map((s) => parseInt(s, 10)).filter(Number.isFinite);
        const found = ids
          .map((id) => (partsData.parts || []).find((p) => p.id === id))
          .filter(Boolean);
        if (found.length) setSelectedParts(found);
      }
      const ftId = parseInt(searchParams?.get('ft') ?? '', 10);
      if (Number.isFinite(ftId)) {
        const t = (tiresData.tires || []).find((x) => x.id === ftId);
        if (t) setFrontTire(t);
      }
      const rtId = parseInt(searchParams?.get('rt') ?? '', 10);
      if (Number.isFinite(rtId)) {
        const t = (tiresData.tires || []).find((x) => x.id === rtId);
        if (t) setRearTire(t);
      }
      qsNum('temp', setAmbientTemp, 0, 50);
      qsNum('track', setTrackTemp, 10, 65);
      qsNum('hum', setHumidity, 0, 100);
      qsNum('wind', setHeadwind, -30, 30);
      // If /api/bikes came back empty, the backend is reachable but
      // either unseeded or filtering killed the request body -- either
      // way the user deserves to see *something* instead of an empty
      // dropdown with no explanation.
      if (!(bikesData.bikes?.length > 0)) {
        setLoadError('Backend reachable but returned zero bikes. Check that the API is pointing at a seeded DB.');
      }
    } catch (e) {
      console.error('Failed to load data:', e);
      setLoadError(e.message || 'Could not reach the MotoQuant backend.');
    } finally {
      setLoading(false);
    }
  }, [searchParams, defaultBikeVariant]);

  useEffect(() => {
    boot();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ─── Re-annotate parts whenever the selected bike changes ────────────
  // Hits `/api/parts?bike_id=X&compatible_only=false` so every row comes back
  // with a `compatible` + `fitment_reason` annotation. The UI uses this to
  // grey-out parts that don't fit the selected bike (instead of hiding them,
  // so the user can still discover what's available for other bikes).
  useEffect(() => {
    if (!bike?.id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `${API}/api/parts?bike_id=${bike.id}&compatible_only=false&limit=1000`,
        );
        if (!res.ok) return;
        const data = await res.json();
        if (!cancelled && Array.isArray(data.parts)) {
          setAllParts(data.parts);
          // Drop any already-selected parts that are now incompatible with the
          // newly-picked bike -- silently, because the UI already cleared
          // selectedParts on bike change, but belt-and-braces for other paths.
          setSelectedParts(prev => prev.filter(p => {
            const hit = data.parts.find(x => x.id === p.id);
            return !hit || hit.compatible !== false;
          }));
        }
      } catch (e) {
        console.warn('parts re-annotation failed:', e);
      }
    })();
    return () => { cancelled = true; };
  }, [bike?.id]);

  // ─── Quick sim auto-run (Live mode, 400 ms debounce) ─────────────────
  const runQuick = quickTask.run;
  useEffect(() => {
    if (!bike || !liveSim) return; // Manual mode: quick sim only fires from the Run button
    if (debounceRef.current) clearTimeout(debounceRef.current);
    // 'auto' → the trigger prop on this flow's sim_run_start/success pair.
    debounceRef.current = setTimeout(() => runQuick('auto'), 400);
    return () => clearTimeout(debounceRef.current);
  }, [bike, selectedParts, frontTire, rearTire, venue, riderKg, powerBoost, massChange,
      ambientTemp, trackTemp, humidity, headwind, liveSim, runQuick]);

  // ─── Computed ────────────────────────────────────────────────────────
  const buildCost = selectedParts.reduce((s, p) => s + (p.price_inr || 0), 0);
  const isPartSelected = (p) => selectedParts.some(s => s.id === p.id);
  function togglePart(part) {
    if (isPartSelected(part)) setSelectedParts(prev => prev.filter(p => p.id !== part.id));
    else setSelectedParts(prev => [...prev, part]);
  }
  function resetAll() {
    setSelectedParts([]); setFrontTire(null); setRearTire(null); setVenue(null);
    setPowerBoost(0); setMassChange(0); setRiderKg(75);
    setAmbientTemp(25); setTrackTemp(30); setHumidity(40); setHeadwind(0);
    setFullResult(null); setCompareResult(null); setUploadResult(null);
    setGeoMessage(null);
  }

  // ─── "Use my location" — proximity match seeded venues, fall back to OWM
  // We don't rely on the LocationPicker component here because the full sim
  // already has its own venue Dropdown + ambient/humidity sliders; we just
  // need to populate them from the user's GPS in one click.
  function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const toRad = (d) => (d * Math.PI) / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) ** 2 +
      Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  async function applyResolved(payload, label) {
    if (payload?.matched_venue_id != null) {
      const v = venues.find((x) => x.id === payload.matched_venue_id);
      if (v) setVenue(v);
    }
    if (payload?.temperature_c != null) setAmbientTemp(Math.round(payload.temperature_c));
    if (payload?.humidity_pct != null) setHumidity(Math.round(payload.humidity_pct));
    setGeoMessage({ tone: 'ok', text: label || 'Location applied' });
  }

  async function useMyLocation() {
    setGeoMessage(null);
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setGeoMessage({ tone: 'err', text: 'Your browser does not support geolocation.' });
      return;
    }
    setGeoLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords;
          // Step 1: client-side proximity match against seeded venues (50 km radius).
          let closest = null;
          let closestKm = Infinity;
          for (const v of venues) {
            if (v.latitude == null || v.longitude == null) continue;
            const km = haversineKm(latitude, longitude, v.latitude, v.longitude);
            if (km < closestKm) {
              closestKm = km;
              closest = v;
            }
          }
          // Step 2: ask backend to resolve. If a nearby seeded venue exists,
          // hand over the venue NAME (no OWM key required). Otherwise pass
          // GPS coords for OWM fallback.
          const useSeeded = closest && closestKm <= 50;
          const body = useSeeded
            ? { location: closest.name }
            : { lat: latitude, lon: longitude };
          const res = await fetch(`${API}/api/venues/resolve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          });
          if (!res.ok) {
            let msg = `Resolve failed (${res.status})`;
            try {
              const j = await res.json();
              if (j?.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
            } catch {}
            throw new Error(msg);
          }
          const data = await res.json();
          const label = useSeeded
            ? `Near ${closest.name} (${closestKm.toFixed(0)} km)`
            : data.venue_name || data.location_name || 'My location';
          await applyResolved(data, label);
        } catch (e) {
          setGeoMessage({ tone: 'err', text: e.message || 'Failed to resolve location' });
        } finally {
          setGeoLoading(false);
        }
      },
      (err) => {
        setGeoLoading(false);
        const map = {
          1: 'Permission denied. Allow location access in your browser.',
          2: 'Location unavailable. Check GPS / network and try again.',
          3: 'Location request timed out.',
        };
        setGeoMessage({ tone: 'err', text: map[err.code] || `Location error: ${err.message}` });
      },
      { timeout: 10000, maximumAge: 60000, enableHighAccuracy: false },
    );
  }

  // ─── File upload handlers ───────────────────────────────────────────
  const onDragyFile = (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    lastDragyFileRef.current = file;
    setUploadResult(null);
    dragyTask.run(file);
  };

  const onDynoFile = (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    lastDynoFileRef.current = file;
    setUploadResult(null);
    dynoTask.run(file);
  };

  // Chart data transform — memoized to avoid re-computing on every render
  const chartData = useMemo(() => {
    if (!fullResult?.timeseries?.t_s) return [];
    return fullResult.timeseries.t_s.map((t, i) => ({
      t: +t.toFixed(2),
      speed: fullResult.timeseries.v_kmh?.[i] ?? 0,
      rpm: fullResult.timeseries.rpm?.[i] ?? 0,
      gear: fullResult.timeseries.gear?.[i] ?? 0,
      accel: fullResult.timeseries.accel_g?.[i] ?? 0,
      traction: fullResult.timeseries.traction_pct?.[i] ?? 0,
      tire_temp: fullResult.timeseries.tire_temp_c?.[i] ?? 0,
      power: fullResult.timeseries.power_kw?.[i] ?? 0,
      F_drive: fullResult.timeseries.F_drive_N?.[i] ?? 0,
      F_drag: fullResult.timeseries.F_drag_N?.[i] ?? 0,
    }));
  }, [fullResult]);

  // Which op feeds the toolbar's compact progress chip (jobs first, quick
  // last). In Manual mode the quick sim already has its own Stop button in
  // the toolbar, so the chip skips it to avoid double feedback.
  const activeOp = fullSimTask.active
    ? { task: fullSimTask, label: 'Full sim' }
    : topSpeedTask.active
      ? { task: topSpeedTask, label: 'Top speed' }
      : compareTask.active
        ? { task: compareTask, label: 'Comparing' }
        : quickTask.active && liveSim
          ? { task: quickTask, label: 'Quick sim' }
          : null;

  /* ═════════════════════════════════════════════════════════════════════
     RENDER
     ═════════════════════════════════════════════════════════════════════ */
  return (
    <div className="min-h-screen bg-asphalt-0 text-white pt-16">
      <SiteNav />

      {/* ─── Simulator toolbar (slim, sticky under SiteNav) ───────────── */}
      <div className="sticky top-16 z-40 bg-asphalt-0/85 backdrop-blur-xl border-b border-white/[0.08]">
        <div className="max-w-[1400px] mx-auto px-4 sm:px-5 py-2.5 flex flex-wrap items-center gap-x-4 gap-y-2">
          <span className="label-mono text-white/60">Simulator</span>
          <button
            type="button"
            onClick={() => setLiveSim((v) => !v)}
            title={liveSim
              ? 'Live preview ON — the quick sim re-runs as you tune. Click to switch to manual.'
              : 'Manual mode — the quick sim runs only when you press Run. Click to go live.'}
            className={`flex items-center gap-1.5 font-mono text-[11px] px-2 py-1 rounded-md border transition-colors ${
              liveSim
                ? 'border-signal-go/30 bg-signal-go/10 text-signal-go'
                : 'border-white/[0.08] bg-white/[0.02] text-white/45 hover:text-white/75'
            }`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${liveSim ? 'bg-signal-go' : 'bg-white/30'}`} />
            {liveSim ? 'Live' : 'Manual'}
          </button>
          {!liveSim && (
            <ActionButton
              task={quickTask}
              onRun={() => quickTask.run('manual')}
              label="Run quick sim"
              runningLabel="Quick sim"
              disabled={!bike}
              className="btn-sm"
            />
          )}
          {activeOp && (
            <SimProgress
              active
              compact
              progress={activeOp.task.progress}
              label={activeOp.label}
              onStop={activeOp.task.stop}
            />
          )}
          <div className="ml-auto hidden sm:flex items-center gap-3 label-mono">
            <span>{loading ? '—' : bikes.length} bikes</span>
            <span className="text-white/20">·</span>
            <span>{loading ? '—' : allParts.length} parts</span>
            <span className="text-white/20">·</span>
            <span>{loading ? '—' : allTires.length} tires</span>
          </div>
        </div>
        {/* Boot progress — determinate fetch-count bar pinned to the toolbar */}
        {loading && (
          <SimProgress
            active
            edge
            progress={bootProgress > 0 ? bootProgress : null}
            className="absolute inset-x-0 bottom-0"
          />
        )}
      </div>

      <div id="main" className="max-w-[1400px] mx-auto px-4 sm:px-5 py-5">
        {/* Boot failure — branded error card with Retry */}
        {loadError && !loading && (
          <div className="card border-signal-foul/30 bg-signal-foul/5 p-4 mb-4">
            <div className="flex items-start gap-2 text-signal-foul text-xs">
              <AlertCircle size={14} className="shrink-0 mt-0.5" />
              <span>{loadError}</span>
            </div>
            <button onClick={boot} className="btn-ghost btn-sm mt-3">
              <RotateCcw size={12} /> Retry
            </button>
          </div>
        )}

        {/* Natural-language chat */}
        <Card glow className="mb-5 p-5">
          <div className="flex items-center gap-2 mb-3">
            <MessageSquare size={14} className="text-white/40" />
            <CodeComment>ask motoquant</CodeComment>
            <h3 className="sr-only">Ask MotoQuant</h3>
          </div>
          <ChatPanel apiUrl={API} />
        </Card>

        {loading ? (
          /* ─── Progressive boot: per-panel skeletons, workbench shape ── */
          <div className="grid grid-cols-12 gap-5" aria-busy="true" aria-label="Loading simulator data">
            <div className="col-span-12 lg:col-span-3 space-y-4">
              <SkeletonCard rows={3} />
              <SkeletonCard rows={3} />
              <SkeletonCard rows={2} />
              <SkeletonCard rows={2} />
            </div>
            <div className="col-span-12 lg:col-span-4">
              {/* Parts-list skeleton (rows shaped like the category list) */}
              <div className="card p-4" aria-hidden="true">
                <div className="skeleton h-4 w-1/3 mb-4" />
                <div className="space-y-2">
                  {Array.from({ length: 10 }, (_, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <Skeleton className="h-3.5 w-3.5 rounded" />
                      <Skeleton className="h-3.5 flex-1" />
                      <Skeleton className="h-3.5 w-10" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="col-span-12 lg:col-span-5 space-y-4">
              <div className="flex gap-2" aria-hidden="true">
                {Array.from({ length: 5 }, (_, i) => (
                  <Skeleton key={i} className="h-8 w-20 rounded-lg" />
                ))}
              </div>
              <SkeletonCard rows={6} />
            </div>
          </div>
        ) : (
        <div className="grid grid-cols-12 gap-5">

          {/* ═══════════════════════════════════════════════════════════
             LEFT PANEL — Configuration
             ═══════════════════════════════════════════════════════════ */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            <CodeComment>staging · configure the run</CodeComment>

            {/* Bike Selector — z-10 so dropdown overlaps cards below */}
            {/* GROWTH_EXP_003: data-exp/data-variant attrs let analytics attribute
                pre-selected default bike (A=Hayabusa control, B=Pulsar NS 200).
                See data/growth_experiments.json. */}
            <Card className="p-4 z-10 overflow-visible" data-exp="EXP-003" data-variant={defaultBikeVariant}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="label-mono font-semibold flex items-center gap-2">
                  <Gauge size={13} className="text-white/40" /> Motorcycle
                </h3>
                <button
                  onClick={shareBuild}
                  disabled={!bike}
                  title="Copy a link to this exact build"
                  className="label-mono flex items-center gap-1 hover:text-white disabled:opacity-40 transition-colors"
                >
                  {shareCopied ? <Check size={11} className="text-signal-go" /> : <Share2 size={11} />}
                  {shareCopied ? 'Link copied' : 'Share'}
                </button>
              </div>
              <Dropdown
                items={bikes}
                selected={bike}
                onSelect={b => { setBike(b); setSelectedParts([]); setFrontTire(null); setRearTire(null); setFullResult(null); }}
                searchKey={b => `${b.manufacturer} ${b.model} ${b.year} ${b.category || ''}`}
                groupKey={b => b.manufacturer || 'Other'}
                renderItem={b => (
                  <div className="flex justify-between items-center w-full">
                    <span>{b.model} {b.year ? `(${b.year})` : ''}</span>
                    <span className="text-[10px] text-white/35">{b.displacement_cc}cc{b.peak_power_hp ? ` · ${Math.round(b.peak_power_hp)}hp` : ''}</span>
                  </div>
                )}
                renderSelected={b => (
                  <span className="text-white text-xs"><span className="font-medium">{b.manufacturer}</span> {b.model} <span className="text-white/35">({b.displacement_cc}cc)</span></span>
                )}
                emptyMsg="No bikes found"
              />
              {bikes.length > 0 && (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {POPULAR_BIKE_PATTERNS.map(({ label, re }) => {
                    const match = bikes.find((b) => re.test(`${b.manufacturer} ${b.model}`));
                    if (!match) return null;
                    const active = bike?.id === match.id;
                    return (
                      <button
                        key={label}
                        onClick={() => { setBike(match); setSelectedParts([]); setFrontTire(null); setRearTire(null); setFullResult(null); }}
                        className={`px-2 py-0.5 rounded text-[10px] font-mono border transition-colors ${
                          active
                            ? 'border-accent/50 text-accent bg-accent/[0.08]'
                            : 'border-white/10 text-white/45 hover:text-white hover:border-white/25'
                        }`}
                      >
                        {label}
                      </button>
                    );
                  })}
                </div>
              )}
              {bike && (
                <div className="mt-2 flex gap-2 text-[10px] text-white/35">
                  <span className="px-1.5 py-0.5 bg-white/[0.03] rounded">{bike.category}</span>
                  {bike.peak_power_hp && <span className="px-1.5 py-0.5 bg-white/[0.03] rounded">{Math.round(bike.peak_power_hp)} hp</span>}
                  {bike.dry_mass_kg && <span className="px-1.5 py-0.5 bg-white/[0.03] rounded">{Math.round(bike.dry_mass_kg)} kg</span>}
                </div>
              )}
            </Card>

            {/* Tuning Sliders */}
            <Card className="p-4">
              <h3 className="label-mono font-semibold mb-3">Quick Tune</h3>
              <div className="space-y-3">
                <Slider label="Rider" value={riderKg} onChange={setRiderKg} min={50} max={130} unit=" kg"
                  colorFn={() => 'text-white'} />
                <Slider label="Power" value={powerBoost} onChange={setPowerBoost} min={-20} max={50} unit="%"
                  colorFn={v => v > 0 ? 'text-signal-go' : v < 0 ? 'text-signal-foul' : 'text-white'} />
                <Slider label="Mass" value={massChange} onChange={setMassChange} min={-30} max={30} unit=" kg"
                  colorFn={v => v < 0 ? 'text-signal-go' : v > 0 ? 'text-signal-foul' : 'text-white'} />
              </div>
            </Card>

            {/* Environment (collapsible) — z-[8] so venue dropdown overlaps cards below */}
            <Card className="p-4 z-[8] overflow-visible">
              <button onClick={() => setShowEnv(!showEnv)}
                aria-expanded={showEnv}
                className="label-mono w-full flex items-center justify-between font-semibold">
                <span className="flex items-center gap-2"><Thermometer size={13} className="text-white/40" /> Environment</span>
                <ChevronDown size={12} className={`transition-transform ${showEnv ? 'rotate-180' : ''}`} />
              </button>
              {showEnv && (
                <div className="mt-3 space-y-3">
                  <Slider label="Air Temp" value={ambientTemp} onChange={setAmbientTemp} min={0} max={50} unit="°C"
                    colorFn={v => v > 35 ? 'text-signal-foul' : v < 15 ? 'text-signal-go' : 'text-white'} />
                  <Slider label="Track Temp" value={trackTemp} onChange={setTrackTemp} min={10} max={65} unit="°C"
                    colorFn={v => v > 50 ? 'text-signal-foul' : 'text-white'} />
                  <Slider label="Humidity" value={humidity} onChange={setHumidity} min={0} max={100} unit="%"
                    colorFn={() => 'text-white'} />
                  <Slider label="Headwind" value={headwind} onChange={setHeadwind} min={-30} max={30} unit=" km/h"
                    colorFn={v => v > 0 ? 'text-signal-foul' : v < 0 ? 'text-signal-go' : 'text-white'} />

                  {/* Venue */}
                  <Dropdown
                    label="Venue" icon={<MapPin size={10} className="text-white/40" />}
                    items={[{ id: null, name: 'Standard (ISA)', country: 'Default' }, ...venues]}
                    selected={venue || { id: null, name: 'Standard (ISA)', country: 'Default' }}
                    onSelect={v => setVenue(v.id ? v : null)}
                    searchKey={v => `${v.name} ${v.country || ''}`}
                    groupKey={v => v.country || 'Default'}
                    renderItem={v => <div className="flex justify-between w-full"><span>{v.name}</span>{v.altitude_m && <span className="text-[10px] text-white/35">{v.altitude_m}m</span>}</div>}
                    renderSelected={v => <span className="text-white text-xs">{v.name}</span>}
                  />

                  {/* Use my location — proximity-matches a seeded venue
                      within 50 km, else falls back to OWM by GPS.
                      Populates venue + ambient temp + humidity. */}
                  <div className="space-y-1.5">
                    <button
                      type="button"
                      onClick={useMyLocation}
                      disabled={geoLoading}
                      className="w-full inline-flex items-center justify-center gap-1.5 py-2 rounded-lg border border-white/[0.1] hover:border-white/25 bg-white/[0.03] text-xs text-white/60 hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Locate size={12} className="text-white/40" />
                      {geoLoading ? 'Locating…' : 'Use my location'}
                    </button>
                    {geoLoading && (
                      <SimProgress active compact label="Locating" className="justify-center" />
                    )}
                    {geoMessage && (
                      <div className={`flex items-start gap-1.5 px-2 py-1.5 rounded-md text-[11px] ${
                        geoMessage.tone === 'ok'
                          ? 'bg-signal-go/10 border border-signal-go/20 text-signal-go'
                          : 'bg-signal-foul/10 border border-signal-foul/30 text-signal-foul'
                      }`}>
                        {geoMessage.tone === 'ok'
                          ? <Locate size={11} className="shrink-0 mt-0.5" />
                          : <AlertCircle size={11} className="shrink-0 mt-0.5" />}
                        <span className="font-mono">{geoMessage.text}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </Card>

            {/* Tires — z-[6] so tire dropdowns overlap cards/buttons below */}
            <Card className="p-4 z-[6] overflow-visible">
              <h3 className="label-mono font-semibold mb-3 flex items-center gap-2">
                <CircleDot size={13} className="text-white/40" /> Tires
              </h3>
              <div className="space-y-2.5">
                {/* Size is part of the label: several tires ship the same
                    model name in multiple sizes (Pilot Power 3 in 180/190/200)
                    and without it the list reads as duplicate entries. */}
                <Dropdown label="Front" icon={null}
                  items={[{ id: null, manufacturer: 'Stock', model: 'OEM Default' }, ...allTires]}
                  selected={frontTire || { id: null, manufacturer: 'Stock', model: 'OEM Default' }}
                  onSelect={t => setFrontTire(t.id ? t : null)}
                  searchKey={t => `${t.manufacturer} ${t.model} ${t.size_designation || ''} ${t.compound_type || ''}`}
                  groupKey={t => t.manufacturer || 'Stock'}
                  renderItem={t => <div className="flex justify-between w-full gap-2"><span>{t.model}{t.size_designation ? <span className="text-white/45"> · {t.size_designation}</span> : null}</span><span className="text-[10px] text-white/35 shrink-0">{t.compound_type || ''}</span></div>}
                  renderSelected={t => <span className="text-white text-xs">{t.manufacturer} {t.model}{t.size_designation ? ` · ${t.size_designation}` : ''}</span>}
                />
                <Dropdown label="Rear" icon={null}
                  items={[{ id: null, manufacturer: 'Stock', model: 'OEM Default' }, ...allTires]}
                  selected={rearTire || { id: null, manufacturer: 'Stock', model: 'OEM Default' }}
                  onSelect={t => setRearTire(t.id ? t : null)}
                  searchKey={t => `${t.manufacturer} ${t.model} ${t.size_designation || ''} ${t.compound_type || ''}`}
                  groupKey={t => t.manufacturer || 'Stock'}
                  renderItem={t => <div className="flex justify-between w-full gap-2"><span>{t.model}{t.size_designation ? <span className="text-white/45"> · {t.size_designation}</span> : null}</span><span className="text-[10px] text-white/35 shrink-0">{t.compound_type || ''}</span></div>}
                  renderSelected={t => <span className="text-white text-xs">{t.manufacturer} {t.model}{t.size_designation ? ` · ${t.size_designation}` : ''}</span>}
                />
              </div>
            </Card>

            {/* Actions */}
            <button onClick={resetAll} className="btn-ghost btn-sm w-full">
              <RotateCcw size={11} /> Reset All
            </button>
          </div>

          {/* ═══════════════════════════════════════════════════════════
             CENTER PANEL — Parts Catalog
             ═══════════════════════════════════════════════════════════ */}
          <div className="col-span-12 lg:col-span-4">
            <Card className="p-4 h-full flex flex-col">
              <h3 className="label-mono font-semibold mb-3 flex items-center gap-2">
                <Wrench size={13} className="text-white/40" /> Parts Catalog
                {selectedParts.length > 0 && (
                  <span className="ml-auto font-mono text-[10px] bg-accent/[0.12] text-accent px-2 py-0.5 rounded">
                    {selectedParts.length} selected · ₹{(buildCost / 1000).toFixed(1)}k
                  </span>
                )}
              </h3>

              {/* Selected parts chips */}
              {selectedParts.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3 pb-3 border-b border-white/[0.04]">
                  {selectedParts.map(p => (
                    <PartChip key={p.id} part={p} onRemove={() => setSelectedParts(prev => prev.filter(x => x.id !== p.id))} />
                  ))}
                </div>
              )}

              {/* Category list */}
              <div className="flex-1 overflow-y-auto space-y-0.5 scrollbar-thin">
                {categories.map(cat => {
                  const catParts = allParts.filter(p => p.category_id === cat.id);
                  const compatInCat = catParts.filter(p => p.compatible !== false).length;
                  const isActive = activeCategory?.id === cat.id;
                  const selectedInCat = selectedParts.filter(p => p.category_id === cat.id).length;
                  return (
                    <div key={cat.id}>
                      <button
                        onClick={() => setActiveCategory(isActive ? null : cat)}
                        aria-expanded={isActive}
                        className={`w-full px-3 py-2 rounded-lg text-left text-xs flex items-center justify-between transition-colors ${
                          isActive ? 'bg-white/[0.06] text-white border border-white/[0.1]' : 'hover:bg-white/[0.03] text-white/55 border border-transparent'
                        }`}>
                        <div className="flex items-center gap-2">
                          <ChevronRight size={11} className={`transition-transform ${isActive ? 'rotate-90' : ''}`} />
                          <span className="font-medium">{cat.display_name || cat.name}</span>
                          <span className="text-[10px] text-white/35">
                            ({compatInCat}{catParts.length !== compatInCat ? `/${catParts.length}` : ''})
                          </span>
                        </div>
                        {selectedInCat > 0 && (
                          <span className="font-mono text-[9px] bg-accent text-asphalt-0 px-1.5 py-0.5 rounded font-bold">{selectedInCat}</span>
                        )}
                      </button>

                      {isActive && (
                        <div className="ml-5 mt-1 mb-2 space-y-1">
                          {catParts.length === 0 ? (
                            <p className="text-[10px] text-white/30 py-2">No parts in this category</p>
                          ) : catParts.map(part => {
                            const sel = isPartSelected(part);
                            // Compatibility annotation comes from /api/parts?bike_id=X&compatible_only=false.
                            // Backwards-compat: if the field is missing (e.g. stale fetch), treat as compatible.
                            const compat = part.compatible !== false;
                            const disabled = !compat && !sel;
                            return (
                              <button key={part.id} onClick={() => { if (!disabled) togglePart(part); }}
                                disabled={disabled}
                                title={compat ? undefined : `Not compatible: ${part.fitment_reason || 'does not fit this bike'}`}
                                className={`w-full px-3 py-2.5 rounded-lg text-left text-xs transition-colors border ${
                                  sel
                                    ? 'bg-accent/[0.08] border-accent/30 text-white'
                                    : disabled
                                      ? 'border-white/[0.03] text-white/35 opacity-50 cursor-not-allowed'
                                      : 'border-white/[0.04] hover:border-white/[0.08] text-white/55 hover:text-white/75'
                                }`}>
                                <div className="flex justify-between items-start">
                                  <div>
                                    <div className="font-medium text-[11px] flex items-center gap-1.5">
                                      {partLabel(part.brand, part.model_name)}
                                      {!compat && (
                                        <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-signal-foul/10 text-signal-foul font-normal">
                                          no fit
                                        </span>
                                      )}
                                    </div>
                                    {part.fitment_notes && <div className="text-[10px] text-white/35 mt-0.5">{part.fitment_notes}</div>}
                                  </div>
                                  <div className="text-right shrink-0 ml-2">
                                    {part.price_inr > 0 && (
                                      <div className="text-[10px] text-white/45">₹{part.price_inr.toLocaleString('en-IN')}</div>
                                    )}
                                    {sel && <div className="text-[10px] text-accent mt-0.5">✓ Added</div>}
                                  </div>
                                </div>
                                {(part.param_deltas || part.param_multipliers) && (
                                  <div className="mt-1.5 flex flex-wrap gap-1">
                                    {part.param_deltas && typeof part.param_deltas === 'object' && Object.entries(part.param_deltas).map(([k, v]) => (
                                      <span key={k} className={`text-[9px] px-1.5 py-0.5 rounded ${v > 0 ? 'bg-signal-go/10 text-signal-go' : 'bg-signal-foul/10 text-signal-foul'}`}>
                                        {k.split('.').pop()}: {v > 0 ? '+' : ''}{v}
                                      </span>
                                    ))}
                                    {part.param_multipliers && typeof part.param_multipliers === 'object' && Object.entries(part.param_multipliers).map(([k, v]) => (
                                      <span key={k} className={`text-[9px] px-1.5 py-0.5 rounded ${v > 1 ? 'bg-signal-go/10 text-signal-go' : 'bg-signal-foul/10 text-signal-foul'}`}>
                                        {k.split('.').pop()}: ×{v}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </Card>
          </div>

          {/* ═══════════════════════════════════════════════════════════
             RIGHT PANEL — Results & Charts
             ═══════════════════════════════════════════════════════════ */}
          <div className="col-span-12 lg:col-span-5 space-y-4">
            <CodeComment>telemetry · live results feed</CodeComment>

            {/* Tab bar — tabs ONLY switch views; runs start from explicit buttons */}
            <div className="flex items-center gap-2 flex-wrap" role="tablist" aria-label="Result views">
              <Tab active={activeTab === 'results'} onClick={() => setActiveTab('results')} icon={<Zap size={12} />} label="1/4 Mile" />
              <Tab active={activeTab === 'topspeed'} onClick={() => setActiveTab('topspeed')} icon={<Gauge size={12} />} label="Top Speed" />
              <Tab active={activeTab === 'charts'} onClick={() => setActiveTab('charts')} icon={<BarChart3 size={12} />} label="Charts" />
              <Tab active={activeTab === 'splits'} onClick={() => setActiveTab('splits')} icon={<Table2 size={12} />} label="Splits" />
              <Tab active={activeTab === 'compare'} onClick={() => setActiveTab('compare')} icon={<Layers size={12} />} label="A vs B" />
              <Tab active={activeTab === 'upload'} onClick={() => setActiveTab('upload')} icon={<Upload size={12} />} label="Upload" />
              <Tab active={activeTab === 'specs'} onClick={() => setActiveTab('specs')} icon={<Settings2 size={12} />} label="Specs" />
            </div>

            {/* Quick-sim error (own state — never collides with full/topspeed/compare) */}
            {quickTask.error && !quickTask.active && (
              <ErrorTile
                message={`Quick sim failed — ${quickTask.error}`}
                onRetry={() => quickTask.run('manual')}
              />
            )}

            <div id="sim-tabpanel" role="tabpanel">

            {/* ─── Results Tab ───────────────────────────────────────── */}
            {activeTab === 'results' && (
              <Card className="p-5 overflow-hidden" glow={!!result}>
                {/* Staged edge bar while the quick sim recomputes */}
                {quickTask.active && (
                  <SimProgress active edge className="absolute inset-x-0 top-0" />
                )}
                {result ? (
                  <div className="space-y-4">
                    {/* The slip — big mono ET + ruled split rows */}
                    <div className="timeslip">
                      <p className="label-mono mb-2">Quarter-Mile ET</p>
                      {result.et_quarter_s != null ? (
                        <div className="flex items-end gap-1.5">
                          <ScoreboardDigits value={result.et_quarter_s.toFixed(3)} h={44} label={`${result.et_quarter_s.toFixed(3)} seconds`} />
                          <span className="font-mono text-sm text-white/40 mb-0.5">s</span>
                        </div>
                      ) : (
                        <p className="font-mono font-bold text-4xl text-white">—</p>
                      )}
                      <div className="mt-3">
                        <div className="timeslip-row"><span className="text-white/45">60 ft</span><span className="text-white">{result.et_60ft_s?.toFixed(3) ?? '—'}s</span></div>
                        <div className="timeslip-row"><span className="text-white/45">⅛ mile</span><span className="text-white">{result.et_eighth_s?.toFixed(3) ?? '—'}s</span></div>
                        <div className="timeslip-row"><span className="text-white/45">Trap speed</span><span className="text-white">{result.trap_speed_kmh?.toFixed(1) ?? '—'} km/h</span></div>
                        <div className="timeslip-row"><span className="text-white/45">Power</span><span className="text-white">{result.peak_power_hp?.toFixed(0) ?? '—'} hp</span></div>
                        <div className="timeslip-row"><span className="text-white/45">Total mass</span><span className="text-white">{result.total_mass_kg?.toFixed(0) ?? '—'} kg</span></div>
                      </div>
                    </div>

                    {/* Stock vs Modified — negative ET delta = faster = green */}
                    {result.stock_et_s && result.et_delta_s !== null && (
                      <div className={`p-3 rounded-lg border text-center ${
                        result.et_delta_s < 0 ? 'bg-signal-go/5 border-signal-go/25' : result.et_delta_s > 0 ? 'bg-signal-foul/5 border-signal-foul/25' : 'bg-white/[0.02] border-white/[0.06]'
                      }`}>
                        <div className="flex items-center justify-center gap-4 font-mono text-xs tabular-nums">
                          <div><span className="text-white/45">Stock </span><span className="text-white font-medium">{result.stock_et_s.toFixed(3)}s</span></div>
                          <div className={`text-lg font-bold ${result.et_delta_s < 0 ? 'delta-down' : 'delta-up'}`}>
                            {result.et_delta_s < 0 ? '' : '+'}{result.et_delta_s.toFixed(3)}s
                          </div>
                          <div><span className="text-white/45">Modified </span><span className="text-white font-medium">{result.et_quarter_s?.toFixed(3)}s</span></div>
                        </div>
                      </div>
                    )}

                    {/* Build summary */}
                    {selectedParts.length > 0 && (
                      <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.06]">
                        <div className="flex justify-between items-center text-xs mb-2">
                          <span className="label-mono">Build summary</span>
                          <span className="font-mono font-bold text-white tabular-nums">₹{buildCost.toLocaleString('en-IN')}</span>
                        </div>
                        {result.et_delta_s && result.et_delta_s < 0 && buildCost > 0 && (
                          <div className="font-mono text-[10px] text-white/50 tabular-nums">
                            Cost per tenth: ₹{Math.round(buildCost / (Math.abs(result.et_delta_s) * 10)).toLocaleString('en-IN')}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Save this run — anonymous allowed (beta); token binds to Garage */}
                    {bike?.id != null && result.et_quarter_s != null && (
                      savedRun ? (
                        <Link
                          href="/leaderboard"
                          className="w-full h-9 inline-flex items-center justify-center gap-2 rounded-lg border border-signal-go/30 bg-signal-go/10 text-signal-go text-xs font-display font-semibold transition-colors hover:bg-signal-go/15"
                        >
                          <Check size={13} /> Saved — view leaderboard
                        </Link>
                      ) : (
                        <div className="space-y-1.5">
                          <ActionButton
                            task={saveTask}
                            onRun={() => saveTask.run()}
                            label="Save this run"
                            runningLabel="Saving"
                            variant="ghost"
                            className="w-full btn-sm"
                          />
                          {saveTask.error && !saveTask.active && (
                            <ErrorTile message={saveTask.error} onRetry={() => saveTask.run()} />
                          )}
                        </div>
                      )
                    )}

                    {/* Full sim button — own task; Stop while running */}
                    <ActionButton
                      task={fullSimTask}
                      onRun={startFullSim}
                      label="View detailed charts & analysis"
                      runningLabel="Full sim"
                      variant="ghost"
                      disabled={!bike}
                      className="w-full btn-sm"
                    />
                  </div>
                ) : (
                  <div className="text-center py-12 text-white/30 text-xs">
                    <Gauge size={32} className="mx-auto mb-3 opacity-20" />
                    Select a bike to start simulating
                  </div>
                )}
              </Card>
            )}

            {/* ─── Top Speed Tab ─────────────────────────────────────── */}
            {activeTab === 'topspeed' && (
              <Card className="p-5" glow={!!topSpeedResult}>
                {topSpeedTask.active ? (
                  <div className="py-12 px-6 max-w-md mx-auto">
                    <SimProgress
                      active
                      progress={topSpeedTask.progress}
                      stage={topSpeedTask.stage}
                      label="Running top-speed simulation"
                      onStop={topSpeedTask.stop}
                    />
                    <div className="text-[10px] text-white/30 mt-2 text-center">Simulating up to 120 s of terminal velocity</div>
                  </div>
                ) : topSpeedTask.error ? (
                  <div className="text-center py-12 text-xs">
                    <div className="text-signal-foul mb-3">Top speed simulation failed</div>
                    <div className="text-white/35 text-[10px] mb-4">{topSpeedTask.error}</div>
                    <ActionButton
                      task={topSpeedTask}
                      onRun={startTopSpeed}
                      label="Retry"
                      runningLabel="Top speed"
                      disabled={!bike}
                      className="btn-sm"
                    />
                  </div>
                ) : topSpeedResult ? (
                  <div className="space-y-4">
                    {/* Primary terminal velocity */}
                    <div className="timeslip text-center">
                      <div className="label-mono mb-2">Terminal Velocity</div>
                      {topSpeedResult.terminal_velocity_kmh != null ? (
                        <div className="flex items-end justify-center gap-2">
                          <ScoreboardDigits
                            value={topSpeedResult.terminal_velocity_kmh.toFixed(1)}
                            h={40}
                            label={`${topSpeedResult.terminal_velocity_kmh.toFixed(1)} km/h`}
                          />
                          <span className="font-mono text-xl text-white/40 mb-0.5">km/h</span>
                        </div>
                      ) : (
                        <div className="font-mono font-bold text-5xl text-white tabular-nums leading-none">—</div>
                      )}
                      <div className="font-mono text-sm text-white/55 mt-2 tabular-nums">
                        {topSpeedResult.terminal_velocity_mph?.toFixed(1)} mph
                        <span className="text-white/35 mx-2">·</span>
                        {topSpeedResult.terminal_velocity_ms?.toFixed(1)} m/s
                      </div>
                      {topSpeedResult.reached_plateau ? (
                        <div className="chip chip-go mt-3">
                          <span className="w-1.5 h-1.5 rounded-full bg-signal-go" />
                          Plateau reached
                        </div>
                      ) : (
                        <div className="chip chip-stage mt-3 normal-case tracking-normal">
                          Still accelerating at sim end — extend max_time
                        </div>
                      )}
                    </div>

                    {/* Time / distance / power grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.06]">
                        <div className="label-mono mb-1">Time to terminal</div>
                        <div className="font-mono text-2xl text-white tabular-nums">{topSpeedResult.time_to_terminal_s?.toFixed(2)}<span className="text-sm text-white/45 ml-1">s</span></div>
                      </div>
                      <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.06]">
                        <div className="label-mono mb-1">Distance to terminal</div>
                        <div className="font-mono text-2xl text-white tabular-nums">
                          {topSpeedResult.distance_to_terminal_m >= 1000
                            ? `${(topSpeedResult.distance_to_terminal_m / 1000).toFixed(2)}`
                            : topSpeedResult.distance_to_terminal_m?.toFixed(0)}
                          <span className="text-sm text-white/45 ml-1">{topSpeedResult.distance_to_terminal_m >= 1000 ? 'km' : 'm'}</span>
                        </div>
                      </div>
                    </div>

                    {/* Terminal power / gear / rpm */}
                    <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.06]">
                      <div className="grid grid-cols-3 gap-3 text-center">
                        <div>
                          <div className="label-mono mb-1">Power @ terminal</div>
                          <div className="font-mono text-lg text-white tabular-nums">{topSpeedResult.terminal_power_hp?.toFixed(0)}<span className="text-[10px] text-white/45 ml-1">hp</span></div>
                          <div className="text-[10px] text-white/35 tabular-nums">{topSpeedResult.terminal_power_kw?.toFixed(1)} kW</div>
                        </div>
                        <div>
                          <div className="label-mono mb-1">Gear</div>
                          <div className="font-mono text-lg text-white tabular-nums">{topSpeedResult.terminal_gear}</div>
                        </div>
                        <div>
                          <div className="label-mono mb-1">Engine RPM</div>
                          <div className="font-mono text-lg text-white tabular-nums">{topSpeedResult.terminal_rpm?.toLocaleString('en-US')}</div>
                        </div>
                      </div>
                    </div>

                    {/* LSR splits table */}
                    {topSpeedResult.lsr_splits && Object.keys(topSpeedResult.lsr_splits).length > 0 && (
                      <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.06]">
                        <div className="flex items-center justify-between mb-3">
                          <div className="label-mono font-medium">Land Speed Splits</div>
                          <div className="text-[9px] text-white/35">SAE J1349</div>
                        </div>
                        <div className="space-y-1.5">
                          {[
                            { key: 'quarter_mile', label: '¼ mile', sub: '402 m' },
                            { key: 'half_mile', label: '½ mile', sub: '805 m' },
                            { key: 'one_km', label: '1 km', sub: '1000 m' },
                            { key: 'one_mile', label: '1 mile', sub: '1609 m' },
                            { key: 'two_mile', label: '2 miles', sub: '3219 m' },
                          ].filter(s => topSpeedResult.lsr_splits[s.key]).map(s => {
                            const v = topSpeedResult.lsr_splits[s.key];
                            return (
                              <div key={s.key} className="grid grid-cols-4 gap-2 text-xs items-center py-1.5 border-b border-white/[0.03] last:border-0">
                                <div>
                                  <div className="text-white font-medium">{s.label}</div>
                                  <div className="text-[9px] text-white/35">{s.sub}</div>
                                </div>
                                <div className="text-right font-mono tabular-nums text-white/75">{v.time_s?.toFixed(3)}<span className="text-white/35 ml-0.5">s</span></div>
                                <div className="text-right font-mono tabular-nums text-white">{v.speed_kmh?.toFixed(1)}<span className="text-white/35 ml-0.5 text-[9px]">km/h</span></div>
                                <div className="text-right font-mono tabular-nums text-white/55 text-[10px]">{v.speed_mph?.toFixed(1)} mph</div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Velocity chart if timeseries present */}
                    {topSpeedResult.timeseries?.t?.length > 0 && (
                      <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.06]">
                        <SimChart
                          data={topSpeedResult.timeseries.t.map((t, i) => ({
                            t: +t.toFixed(2),
                            speed: +topSpeedResult.timeseries.v_kmh[i].toFixed(1),
                          }))}
                          dataKey="speed"
                          label="Velocity vs Time"
                          unit="km/h"
                          color="#FF5E1F"
                        />
                      </div>
                    )}

                    {/* Re-run button */}
                    <ActionButton
                      task={topSpeedTask}
                      onRun={startTopSpeed}
                      label="Re-run top-speed simulation"
                      runningLabel="Top speed"
                      variant="ghost"
                      disabled={!bike}
                      className="w-full btn-sm"
                    />
                  </div>
                ) : (
                  <div className="text-center py-12 text-xs">
                    <Gauge size={32} className="mx-auto mb-3 text-white/20" />
                    <p className="text-white/35 mb-1">Top Speed &amp; Land Speed Record mode</p>
                    <p className="text-white/30 text-[10px] mb-4 max-w-xs mx-auto">Simulates until terminal velocity is reached. Returns ¼ mi / ½ mi / 1 km / 1 mi / 2 mi splits for LSR events at Bonneville, El Mirage, Texas Mile, and more.</p>
                    <ActionButton
                      task={topSpeedTask}
                      onRun={startTopSpeed}
                      label="Run top-speed pull"
                      runningLabel="Top speed"
                      disabled={!bike}
                      className="btn-sm"
                    />
                  </div>
                )}
              </Card>
            )}

            {/* ─── Charts Tab ────────────────────────────────────────── */}
            {activeTab === 'charts' && (
              <Card className="p-5">
                {fullSimTask.active ? (
                  <div className="py-12 px-6 max-w-md mx-auto">
                    <SimProgress
                      active
                      progress={fullSimTask.progress}
                      stage={fullSimTask.stage}
                      label="Running full simulation"
                      onStop={fullSimTask.stop}
                    />
                    <div className="text-[10px] text-white/30 mt-2 text-center">
                      Full RK4 physics — telemetry charts will appear here
                    </div>
                  </div>
                ) : (
                  <>
                    {fullSimTask.error && (
                      <ErrorTile
                        className="mb-4"
                        message={`Full simulation failed — ${fullSimTask.error}`}
                        onRetry={startFullSim}
                      />
                    )}
                    {chartData.length > 0 ? (
                      <div className="space-y-5">
                        <div className="grid grid-cols-2 gap-4">
                          <SimChart data={chartData} dataKey="speed" label="Speed" unit="km/h" />
                          <SimChart data={chartData} dataKey="rpm" label="Engine RPM" unit="rpm" />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <SimChart data={chartData} dataKey="gear" label="Gear" unit="" color="#6FE3B2" />
                          <SimChart data={chartData} dataKey="traction" label="Traction" unit="%" color="#34D97B" domain={[0, 110]} />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <SimChart data={chartData} dataKey="power" label="Power" unit="kW" color="#FFB224" />
                          <SimChart data={chartData} dataKey="tire_temp" label="Tire Temp" unit="°C" color="#FF5A48" />
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <BarChart3 size={32} className="mx-auto mb-3 text-white/20" />
                        <p className="text-white/35 text-xs mb-3">Run a full simulation to see telemetry charts</p>
                        <ActionButton
                          task={fullSimTask}
                          onRun={startFullSim}
                          label="Run full simulation"
                          runningLabel="Full sim"
                          disabled={!bike}
                          className="btn-sm"
                        />
                      </div>
                    )}
                  </>
                )}
              </Card>
            )}

            {/* ─── Splits Tab ────────────────────────────────────────── */}
            {activeTab === 'splits' && (
              <Card className="p-5">
                {fullResult ? (
                  <div className="timeslip overflow-x-auto">
                    <h4 className="label-mono font-semibold mb-3">Split Times</h4>
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="label-mono border-b border-dashed border-white/15">
                          <th className="text-left py-2 font-medium">Distance</th>
                          <th className="text-right py-2 font-medium">Time</th>
                          <th className="text-right py-2 font-medium">Speed</th>
                        </tr>
                      </thead>
                      <tbody className="text-white/75">
                        {[
                          { d: '60 ft (18.3m)', t: fullResult.splits?.['60ft_s'], s: null },
                          { d: '330 ft (100.6m)', t: fullResult.splits?.['330ft_s'], s: null },
                          { d: '⅛ mile (201.2m)', t: fullResult.splits?.['660ft_s'], s: null },
                          { d: '1000 ft (304.8m)', t: fullResult.splits?.['1000ft_s'], s: null },
                          { d: '¼ mile (402.3m)', t: fullResult.splits?.['1320ft_s'], s: fullResult.trap_speed_kmh },
                        ].map(row => (
                          <tr key={row.d} className="border-b border-dashed border-white/10">
                            <td className="py-2 text-white/45">{row.d}</td>
                            <td className="py-2 text-right font-mono font-medium tabular-nums">{row.t?.toFixed(3) ?? '—'}s</td>
                            <td className="py-2 text-right font-mono tabular-nums text-white/45">{row.s ? `${row.s.toFixed(1)} km/h` : '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12 text-white/35 text-xs">
                    {result ? (
                      <>
                        <p className="mb-1">Quick splits from last run:</p>
                        <p className="font-mono text-white font-medium tabular-nums">60ft: {result.et_60ft_s?.toFixed(3)}s · ⅛: {result.et_eighth_s?.toFixed(3)}s · ¼: {result.et_quarter_s?.toFixed(3)}s</p>
                        <div className="mt-3 flex justify-center">
                          <ActionButton
                            task={fullSimTask}
                            onRun={startFullSim}
                            label="Get full splits"
                            runningLabel="Full sim"
                            disabled={!bike}
                            className="btn-sm"
                          />
                        </div>
                        {fullSimTask.error && !fullSimTask.active && (
                          <ErrorTile
                            className="mt-3 text-left"
                            message={fullSimTask.error}
                            onRetry={startFullSim}
                          />
                        )}
                      </>
                    ) : 'Run a simulation to see splits'}
                  </div>
                )}
              </Card>
            )}

            {/* ─── A vs B Compare Tab ────────────────────────────────── */}
            {activeTab === 'compare' && (
              <Card className="p-5 overflow-visible">
                <h4 className="label-mono font-semibold mb-4 flex items-center gap-2">
                  <Layers size={13} className="text-white/40" /> A vs B Comparison
                </h4>

                {/* Build B config */}
                <div className="space-y-3 mb-4">
                  <div className="bg-white/[0.02] rounded-lg p-3 border border-white/[0.04]">
                    <p className="label-mono text-accent font-medium mb-2">Build A — Current Setup</p>
                    <p className="text-xs text-white/55">
                      {bike?.manufacturer} {bike?.model} · {powerBoost !== 0 ? `${powerBoost > 0 ? '+' : ''}${powerBoost}% power` : 'Stock power'} · {selectedParts.length} parts
                    </p>
                  </div>

                  <div className="bg-white/[0.02] rounded-lg p-3 border border-mint/20">
                    <p className="label-mono text-mint font-medium mb-2">Build B — Comparison</p>
                    <div className="space-y-2">
                      <Dropdown
                        label="Bike" icon={<Gauge size={10} className="text-mint" />}
                        items={bikes}
                        selected={compareBike || bike}
                        onSelect={b => setCompareBike(b)}
                        searchKey={b => `${b.manufacturer} ${b.model} ${b.year} ${b.category || ''}`}
                        groupKey={b => b.manufacturer || 'Other'}
                        renderItem={b => (
                          <div className="flex justify-between items-center w-full">
                            <span>{b.model} {b.year ? `(${b.year})` : ''}</span>
                            <span className="text-[10px] text-white/35">{b.displacement_cc}cc</span>
                          </div>
                        )}
                        renderSelected={b => <span className="text-white text-xs">{b?.manufacturer} {b?.model}</span>}
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <Slider label="Power" value={comparePower} onChange={setComparePower} min={-20} max={50} unit="%"
                          colorFn={v => v > 0 ? 'text-signal-go' : v < 0 ? 'text-signal-foul' : 'text-white'} />
                        <Slider label="Mass" value={compareMass} onChange={setCompareMass} min={-30} max={30} unit=" kg"
                          colorFn={v => v < 0 ? 'text-signal-go' : v > 0 ? 'text-signal-foul' : 'text-white'} />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Run — job-backed with real progress + Stop */}
                <ActionButton
                  task={compareTask}
                  onRun={startCompare}
                  label="Run A vs B comparison"
                  runningLabel="Comparing"
                  disabled={!bike}
                  className="w-full"
                />
                {compareTask.active && (
                  <div className="mt-3">
                    <SimProgress
                      active
                      progress={compareTask.progress}
                      stage={compareTask.stage}
                      label="Running both builds"
                      onStop={compareTask.stop}
                    />
                  </div>
                )}
                {compareTask.error && !compareTask.active && (
                  <ErrorTile
                    className="mt-3"
                    message={`Comparison failed — ${compareTask.error}`}
                    onRetry={startCompare}
                  />
                )}

                {/* Compare results */}
                {compareResult && (
                  <div className="mt-4 space-y-3">
                    {/* Delta banner */}
                    <div className={`p-4 rounded-lg border text-center ${
                      compareResult.delta.et_s < 0 ? 'bg-signal-go/5 border-signal-go/25' : compareResult.delta.et_s > 0 ? 'bg-signal-foul/5 border-signal-foul/25' : 'bg-white/[0.02] border-white/[0.06]'
                    }`}>
                      <div className="label-mono mb-1">
                        {compareResult.delta.faster === 'B' ? 'Build B is faster' : compareResult.delta.faster === 'A' ? 'Build A is faster' : 'Dead heat'}
                      </div>
                      <div className={`text-2xl font-bold ${compareResult.delta.et_s < 0 ? 'delta-down' : compareResult.delta.et_s > 0 ? 'delta-up' : 'font-mono tabular-nums text-white'}`}>
                        {compareResult.delta.et_s > 0 ? '+' : ''}{compareResult.delta.et_s.toFixed(3)}s
                      </div>
                      <div className="font-mono text-[10px] text-white/45 mt-1 tabular-nums">
                        Trap: {compareResult.delta.trap_kmh > 0 ? '+' : ''}{compareResult.delta.trap_kmh.toFixed(1)} km/h
                        {compareResult.delta.cost_diff_inr !== 0 && ` · Cost: ${compareResult.delta.cost_diff_inr > 0 ? '+' : ''}₹${Math.abs(compareResult.delta.cost_diff_inr).toLocaleString('en-IN')}`}
                      </div>
                    </div>

                    {/* Side-by-side metrics */}
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { label: 'Build A', data: compareResult.a, color: 'orange' },
                        { label: 'Build B', data: compareResult.b, color: 'blue' },
                      ].map(({ label, data, color }) => (
                        <div key={label} className={`bg-white/[0.02] rounded-lg p-3 border ${color === 'orange' ? 'border-accent/25' : 'border-mint/25'}`}>
                          <p className={`label-mono font-medium mb-2 ${color === 'orange' ? 'text-accent' : 'text-mint'}`}>{label}</p>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between"><span className="text-white/45">ET</span><span className="text-white font-bold tabular-nums">{data.et_quarter_s?.toFixed(3)}s</span></div>
                            <div className="flex justify-between"><span className="text-white/45">Trap</span><span className="font-mono text-white tabular-nums">{data.trap_speed_kmh?.toFixed(1)} km/h</span></div>
                            <div className="flex justify-between"><span className="text-white/45">60ft</span><span className="font-mono text-white tabular-nums">{data.et_60ft_s?.toFixed(3)}s</span></div>
                            <div className="flex justify-between"><span className="text-white/45">Power</span><span className="font-mono text-white tabular-nums">{data.peak_power_hp?.toFixed(0)} hp</span></div>
                            <div className="flex justify-between"><span className="text-white/45">Mass</span><span className="font-mono text-white tabular-nums">{data.total_mass_kg?.toFixed(0)} kg</span></div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Overlay charts */}
                    {compareResult.a?.timeseries && compareResult.b?.timeseries && (() => {
                      const overlayData = compareResult.a.timeseries.t_s.map((t, i) => ({
                        t: +t.toFixed(2),
                        a_speed: compareResult.a.timeseries.v_kmh?.[i] ?? 0,
                        b_speed: compareResult.b.timeseries.v_kmh?.[i] ?? 0,
                        a_rpm: compareResult.a.timeseries.rpm?.[i] ?? 0,
                        b_rpm: compareResult.b.timeseries.rpm?.[i] ?? 0,
                        a_power: compareResult.a.timeseries.power_kw?.[i] ?? 0,
                        b_power: compareResult.b.timeseries.power_kw?.[i] ?? 0,
                      }));
                      return (
                        <div className="space-y-4">
                          <p className="label-mono">Overlay Charts</p>
                          {[
                            { key: 'speed', label: 'Speed (km/h)', unit: 'km/h' },
                            { key: 'rpm', label: 'Engine RPM', unit: 'rpm' },
                            { key: 'power', label: 'Power (kW)', unit: 'kW' },
                          ].map(chart => (
                            <div key={chart.key} className="h-44">
                              <p className="label-mono mb-2">{chart.label}</p>
                              <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={overlayData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                                  <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} tickFormatter={v => `${v}s`} />
                                  <YAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} />
                                  <Tooltip
                                    contentStyle={{ background: '#10141B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
                                    labelFormatter={v => `${v}s`}
                                  />
                                  <Line type="monotone" dataKey={`a_${chart.key}`} stroke="#FF5E1F" strokeWidth={1.5} dot={false} name="Build A" />
                                  <Line type="monotone" dataKey={`b_${chart.key}`} stroke="#6FE3B2" strokeWidth={1.5} dot={false} name="Build B" />
                                </LineChart>
                              </ResponsiveContainer>
                            </div>
                          ))}
                        </div>
                      );
                    })()}
                  </div>
                )}
              </Card>
            )}

            {/* ─── Upload Tab ───────────────────────────────────────────── */}
            {activeTab === 'upload' && (
              <Card className="p-5">
                <h4 className="label-mono font-semibold mb-4 flex items-center gap-2">
                  <Upload size={13} className="text-white/40" /> Upload Run Data
                </h4>

                {/* Upload buttons */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div>
                    <input type="file" ref={fileInputRef} accept=".csv,.json" onChange={onDragyFile} className="hidden" />
                    <button onClick={() => fileInputRef.current?.click()} disabled={dragyTask.active || dynoTask.active}
                      className="w-full p-4 bg-white/[0.02] rounded-lg border border-dashed border-white/15 hover:border-white/30 transition-colors text-center disabled:opacity-50">
                      <Zap size={20} className="mx-auto mb-2 text-white/50" />
                      <p className="text-xs font-medium text-white">Dragy GPS</p>
                      <p className="font-mono text-[10px] text-white/35 mt-1">CSV or JSON export</p>
                    </button>
                  </div>
                  <div>
                    <input type="file" ref={dynoInputRef} accept=".csv,.txt" onChange={onDynoFile} className="hidden" />
                    <button onClick={() => dynoInputRef.current?.click()} disabled={dragyTask.active || dynoTask.active}
                      className="w-full p-4 bg-white/[0.02] rounded-lg border border-dashed border-white/15 hover:border-white/30 transition-colors text-center disabled:opacity-50">
                      <BarChart3 size={20} className="mx-auto mb-2 text-white/50" />
                      <p className="text-xs font-medium text-white">Dyno Curve</p>
                      <p className="font-mono text-[10px] text-white/35 mt-1">DynoJet / MoTeC CSV</p>
                    </button>
                  </div>
                </div>

                {/* Per-upload staged progress (cold-start caption comes free) */}
                {(dragyTask.active || dynoTask.active) && (
                  <div className="py-4 px-4 max-w-sm mx-auto">
                    <SimProgress
                      active
                      label={dragyTask.active ? 'Uploading Dragy run' : 'Parsing dyno CSV'}
                      onStop={dragyTask.active ? dragyTask.stop : dynoTask.stop}
                    />
                  </div>
                )}

                {/* Per-upload inline errors with Retry (same file, from ref) */}
                {dragyTask.error && !dragyTask.active && (
                  <ErrorTile
                    className="mb-3"
                    message={`Dragy upload failed — ${dragyTask.error}`}
                    onRetry={lastDragyFileRef.current ? () => dragyTask.run(lastDragyFileRef.current) : undefined}
                  />
                )}
                {dynoTask.error && !dynoTask.active && (
                  <ErrorTile
                    className="mb-3"
                    message={`Dyno upload failed — ${dynoTask.error}`}
                    onRetry={lastDynoFileRef.current ? () => dynoTask.run(lastDynoFileRef.current) : undefined}
                  />
                )}

                {/* Dragy results */}
                {uploadResult?.type === 'dragy' && (
                  <div className="space-y-3">
                    <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.06]">
                      <div className="flex justify-between items-center mb-2">
                        <p className="label-mono text-white/60 font-medium">Dragy Run — Best of {uploadResult.runs_detected}</p>
                        <p className="text-[10px] text-white/35">{uploadResult.filename}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4 mb-3">
                        <Metric label="Real ET" value={uploadResult.best_run?.et_quarter_s?.toFixed(3) ?? '—'} unit="s" large accent />
                        <Metric label="Trap Speed" value={uploadResult.best_run?.trap_speed_kmh?.toFixed(1) ?? '—'} unit="km/h" large />
                      </div>
                      {uploadResult.best_run?.splits && (
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          {Object.entries(uploadResult.best_run.splits).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-white/45">{k}</span>
                              <span className="font-mono text-white tabular-nums">{v?.toFixed(3)}s</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Overlay vs sim */}
                    {uploadResult.overlay && (
                      <div className={`rounded-lg p-4 border ${Math.abs(uploadResult.overlay.et_error_s) < 0.15 ? 'bg-signal-go/5 border-signal-go/25' : 'bg-signal-stage/5 border-signal-stage/25'}`}>
                        <p className={`label-mono mb-2 font-medium ${Math.abs(uploadResult.overlay.et_error_s) < 0.15 ? 'text-signal-go' : 'text-signal-stage'}`}>
                          Sim vs Real — {uploadResult.overlay.bike_name}
                        </p>
                        <div className="grid grid-cols-3 gap-3 text-xs">
                          <div><span className="text-white/45 block">Sim ET</span><span className="font-mono text-white font-medium tabular-nums">{uploadResult.overlay.sim_et_s?.toFixed(3)}s</span></div>
                          <div><span className="text-white/45 block">Error</span><span className={`font-mono font-bold tabular-nums ${Math.abs(uploadResult.overlay.et_error_s) < 0.15 ? 'text-signal-go' : 'text-signal-stage'}`}>{uploadResult.overlay.et_error_s > 0 ? '+' : ''}{uploadResult.overlay.et_error_s?.toFixed(3)}s</span></div>
                          <div><span className="text-white/45 block">RMSE</span><span className="font-mono text-white tabular-nums">{uploadResult.overlay.v_rmse_kmh?.toFixed(1)} km/h</span></div>
                        </div>
                      </div>
                    )}

                    {/* Real vs Sim speed overlay chart */}
                    {uploadResult.best_run?.timeseries && uploadResult.overlay?.sim_timeseries && (() => {
                      const realTs = uploadResult.best_run.timeseries;
                      const simTs = uploadResult.overlay.sim_timeseries;
                      const maxLen = Math.max(realTs.t_s.length, simTs.t_s.length);
                      const overlayData = [];
                      for (let i = 0; i < maxLen; i++) {
                        overlayData.push({
                          t: (realTs.t_s[i] ?? simTs.t_s[i] ?? 0).toFixed(2),
                          real: realTs.v_kmh?.[i] ?? null,
                          sim: simTs.v_kmh?.[i] ?? null,
                        });
                      }
                      return (
                        <div className="h-48">
                          <p className="label-mono mb-2">Speed Overlay — Real vs Sim</p>
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={overlayData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                              <XAxis dataKey="t" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} tickFormatter={v => `${v}s`} />
                              <YAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} />
                              <Tooltip contentStyle={{ background: '#10141B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }} labelFormatter={v => `${v}s`} />
                              <Line type="monotone" dataKey="real" stroke="#34D97B" strokeWidth={2} dot={false} name="Real (Dragy)" />
                              <Line type="monotone" dataKey="sim" stroke="#FF5E1F" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Sim" />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      );
                    })()}
                  </div>
                )}

                {/* Dyno results */}
                {uploadResult?.type === 'dyno' && (
                  <div className="space-y-3">
                    <div className="bg-white/[0.02] rounded-lg p-4 border border-white/[0.06]">
                      <div className="flex justify-between items-center mb-3">
                        <p className="label-mono text-white/60 font-medium">Dyno Curve</p>
                        <p className="text-[10px] text-white/35">{uploadResult.filename}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4 mb-3">
                        <Metric label="Peak Power" value={uploadResult.peak_power_hp?.toFixed(1) ?? '—'} unit="hp" large accent />
                        <Metric label="Peak Torque" value={uploadResult.peak_torque_nm?.toFixed(1) ?? '—'} unit="Nm" large />
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex justify-between"><span className="text-white/45">RPM @ peak power</span><span className="font-mono text-white tabular-nums">{uploadResult.rpm_at_peak_power?.toFixed(0)}</span></div>
                        <div className="flex justify-between"><span className="text-white/45">RPM @ peak torque</span><span className="font-mono text-white tabular-nums">{uploadResult.rpm_at_peak_torque?.toFixed(0)}</span></div>
                        <div className="flex justify-between"><span className="text-white/45">SAE CF</span><span className="font-mono text-white tabular-nums">{uploadResult.correction_factor?.toFixed(4)}</span></div>
                        <div className="flex justify-between"><span className="text-white/45">Data points</span><span className="font-mono text-white tabular-nums">{uploadResult.n_points}</span></div>
                      </div>
                    </div>

                    {/* Dyno chart */}
                    {uploadResult.curve && (() => {
                      const curveData = uploadResult.curve.rpm.map((rpm, i) => ({
                        rpm,
                        power: uploadResult.curve.power_hp?.[i] ?? 0,
                        torque: uploadResult.curve.torque_nm?.[i] ?? 0,
                      }));
                      return (
                        <div className="h-52">
                          <p className="label-mono mb-2">Power & Torque vs RPM</p>
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={curveData} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                              <XAxis dataKey="rpm" tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.4)' }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                              <YAxis yAxisId="power" tick={{ fontSize: 9, fill: '#FF5E1F' }} orientation="left" />
                              <YAxis yAxisId="torque" tick={{ fontSize: 9, fill: '#6FE3B2' }} orientation="right" />
                              <Tooltip contentStyle={{ background: '#10141B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }} labelFormatter={v => `${v} RPM`} />
                              <Line yAxisId="power" type="monotone" dataKey="power" stroke="#FF5E1F" strokeWidth={2} dot={false} name="Power (hp)" />
                              <Line yAxisId="torque" type="monotone" dataKey="torque" stroke="#6FE3B2" strokeWidth={1.5} dot={false} name="Torque (Nm)" />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      );
                    })()}
                  </div>
                )}

                {/* Empty state */}
                {!uploadResult && !dragyTask.active && !dynoTask.active && !dragyTask.error && !dynoTask.error && (
                  <div className="text-center py-8 text-white/30 text-xs">
                    <Upload size={32} className="mx-auto mb-3 opacity-20" />
                    <p className="mb-1">Upload your Dragy GPS run or dyno pull</p>
                    <p className="text-[10px] text-white/35">We'll parse it, show splits, and overlay against our sim for accuracy validation</p>
                  </div>
                )}
              </Card>
            )}

            {/* ─── Specs Tab ─────────────────────────────────────────── */}
            {activeTab === 'specs' && (
              <Card className="p-5">
                {(fullResult?.config || result) ? (
                  <div>
                    <h4 className="label-mono font-semibold mb-3">Configuration</h4>
                    <div className="space-y-1.5 text-xs">
                      {[
                        ['Bike', result?.bike_name || bike?.manufacturer + ' ' + bike?.model],
                        ['Peak Power', `${(fullResult?.config?.peak_power_hp || result?.peak_power_hp)?.toFixed(1)} hp`],
                        ['Peak Torque', fullResult?.config?.peak_torque_nm ? `${fullResult.config.peak_torque_nm.toFixed(1)} Nm` : '—'],
                        ['Total Mass', `${(fullResult?.config?.total_mass_kg || result?.total_mass_kg)?.toFixed(1)} kg`],
                        ['Displacement', `${fullResult?.config?.displacement_cc || bike?.displacement_cc} cc`],
                        ['Redline', fullResult?.config?.redline_rpm ? `${fullResult.config.redline_rpm.toFixed(0)} RPM` : '—'],
                        ['Drag Coeff', fullResult?.config?.cd ? `${fullResult.config.cd}` : '—'],
                        ['Rider', `${riderKg} kg`],
                        ['Power Boost', powerBoost !== 0 ? `${powerBoost > 0 ? '+' : ''}${powerBoost}%` : 'Stock'],
                        ['Mass Change', massChange !== 0 ? `${massChange > 0 ? '+' : ''}${massChange} kg` : 'Stock'],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between py-1 border-b border-dashed border-white/10">
                          <span className="text-white/45">{k}</span>
                          <span className="font-mono text-white font-medium tabular-nums">{v}</span>
                        </div>
                      ))}
                    </div>
                    {/* Environment conditions */}
                    <h4 className="label-mono font-semibold mt-5 mb-3">Conditions</h4>
                    <div className="space-y-1.5 text-xs">
                      {[
                        ['Air Temp', `${ambientTemp}°C`],
                        ['Track Temp', `${trackTemp}°C`],
                        ['Humidity', `${humidity}%`],
                        ['Wind', headwind === 0 ? 'None' : `${headwind > 0 ? 'Headwind' : 'Tailwind'} ${Math.abs(headwind)} km/h`],
                        ['Venue', venue?.name || 'Standard (ISA)'],
                        ['Front Tire', frontTire ? `${frontTire.manufacturer} ${frontTire.model}` : 'OEM'],
                        ['Rear Tire', rearTire ? `${rearTire.manufacturer} ${rearTire.model}` : 'OEM'],
                      ].map(([k, v]) => (
                        <div key={k} className="flex justify-between py-1 border-b border-dashed border-white/10">
                          <span className="text-white/45">{k}</span>
                          <span className="font-mono text-white font-medium">{v}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-white/35 text-xs">Run a simulation to see specs</div>
                )}
              </Card>
            )}
            </div>
          </div>
        </div>
        )}
      </div>

      <SiteFooter />
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Default export wraps SimulatorPageInner in <Suspense> so the static
// prerender of `/simulator` doesn't bail out on the EXP-003 useSearchParams()
// call. Without this boundary, `next build` errors with
// "missing-suspense-with-csr-bailout". See web/CONTRIBUTING.md for the rule
// and web/app/page.js for the matching pattern used by EXP-001.
// ──────────────────────────────────────────────────────────────────────────
export default function SimulatorPage() {
  return (
    <Suspense fallback={null}>
      <SimulatorPageInner />
    </Suspense>
  );
}
