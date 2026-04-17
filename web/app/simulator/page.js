'use client';

import { useState, useEffect, useRef, useCallback, useMemo, useId } from 'react';
import {
  Zap, Search, ChevronDown, ChevronRight, X, MapPin, Gauge, Wrench,
  CircleDot, IndianRupee, ArrowLeft, Thermometer, Wind, Droplets,
  BarChart3, Table2, Settings2, Upload, RotateCcw, Play, Layers
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';

const API = process.env.NEXT_PUBLIC_API_URL || 'https://web-production-de6eb.up.railway.app';

/* ═══════════════════════════════════════════════════════════════════════════
   REUSABLE COMPONENTS
   ═══════════════════════════════════════════════════════════════════════════ */

// ─── Glass Card ──────────────────────────────────────────────────────────
function Card({ children, className = '', glow = false }) {
  return (
    <div className={`
      relative rounded-2xl border border-white/[0.06]
      bg-gradient-to-br from-white/[0.04] to-white/[0.01]
      backdrop-blur-xl shadow-[0_0_30px_rgba(0,0,0,0.3)]
      ${glow ? 'shadow-orange-500/5 border-orange-500/20' : ''}
      ${className}
    `}>
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
        <label className="flex items-center gap-1.5 text-[10px] text-gray-500 mb-1.5 uppercase tracking-widest font-medium">
          {icon}{label}
        </label>
      )}
      <button onClick={() => setOpen(!open)}
        className="w-full p-2.5 rounded-xl border border-white/[0.08] bg-white/[0.03] text-left flex items-center justify-between hover:border-orange-500/30 hover:bg-white/[0.05] transition-all text-sm group">
        {selected ? renderSelected(selected) : <span className="text-gray-600">Select...</span>}
        <ChevronDown size={13} className={`text-gray-600 group-hover:text-orange-500 transition-all ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute z-50 mt-1.5 w-full bg-[#0a0a0f] border border-white/[0.08] rounded-xl shadow-2xl shadow-black/50 max-h-72 overflow-hidden">
          <div className="p-2 border-b border-white/[0.06]">
            <div className="relative">
              <Search size={12} className="absolute left-2.5 top-2.5 text-gray-600" />
              <input type="text" value={q} onChange={e => setQ(e.target.value)} placeholder="Search..."
                className="w-full pl-8 pr-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-lg text-xs text-white placeholder-gray-700 focus:outline-none focus:border-orange-500/50" autoFocus />
            </div>
          </div>
          <div className="overflow-y-auto max-h-56 scrollbar-thin">
            {grouped ? Object.keys(grouped).sort().map(g => (
              <div key={g}>
                <div className="px-3 py-1 text-[10px] text-gray-600 font-semibold uppercase tracking-widest bg-white/[0.02] sticky top-0">{g}</div>
                {grouped[g].map((item, i) => (
                  <button key={i} onClick={() => { onSelect(item); setOpen(false); setQ(''); }}
                    className="w-full px-3 py-2 text-left text-xs hover:bg-orange-500/10 transition-colors text-gray-300 hover:text-orange-300">
                    {renderItem(item)}
                  </button>
                ))}
              </div>
            )) : filtered.map((item, i) => (
              <button key={i} onClick={() => { onSelect(item); setOpen(false); setQ(''); }}
                className="w-full px-3 py-2 text-left text-xs hover:bg-orange-500/10 transition-colors text-gray-300 hover:text-orange-300">
                {renderItem(item)}
              </button>
            ))}
            {filtered.length === 0 && <div className="px-3 py-4 text-center text-xs text-gray-700">{emptyMsg || 'No results'}</div>}
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
        <span className="text-gray-500">{label}</span>
        <span className={`font-medium tabular-nums ${color}`}>{display}{unit}</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        className="w-full h-1 accent-orange-500 cursor-pointer" />
    </div>
  );
}

// ─── Part Chip ───────────────────────────────────────────────────────────
function PartChip({ part, onRemove }) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-orange-500/10 border border-orange-500/20 rounded-full text-[10px] text-orange-300 group">
      <span className="font-medium">{part.brand} {part.model_name}</span>
      {part.price_inr > 0 && <span className="text-orange-500/50">₹{(part.price_inr / 1000).toFixed(1)}k</span>}
      <button onClick={onRemove} className="opacity-50 group-hover:opacity-100 hover:text-white transition-opacity"><X size={10} /></button>
    </div>
  );
}

// ─── Metric Card ─────────────────────────────────────────────────────────
function Metric({ label, value, unit, large, accent }) {
  return (
    <div className="text-center">
      <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">{label}</p>
      <p className={`font-bold tabular-nums ${large ? 'text-3xl' : 'text-xl'} ${accent ? 'text-orange-400' : 'text-white'}`}>
        {value}<span className={`${large ? 'text-base' : 'text-xs'} text-gray-500 ml-0.5`}>{unit}</span>
      </p>
    </div>
  );
}

// ─── Tab Button ──────────────────────────────────────────────────────────
function Tab({ active, onClick, icon, label }) {
  return (
    <button onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
        active
          ? 'bg-orange-500/15 text-orange-400 border border-orange-500/30'
          : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.03] border border-transparent'
      }`}>
      {icon}{label}
    </button>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   CHART COMPONENTS
   ═══════════════════════════════════════════════════════════════════════════ */

const CHART_COLORS = { a: '#f97316', b: '#60a5fa' };

function SimChart({ data, dataKey, label, unit, color = CHART_COLORS.a, domain }) {
  const gradId = useId();
  if (!data || data.length === 0) return null;
  const gid = `grad-${dataKey}-${gradId}`;
  return (
    <div className="h-44">
      <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-2">{label}</p>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.2} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="t" tick={{ fontSize: 9, fill: '#555' }} tickFormatter={v => `${v}s`} />
          <YAxis tick={{ fontSize: 9, fill: '#555' }} domain={domain} />
          <Tooltip
            contentStyle={{ background: '#0a0a0f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
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

export default function SimulatorPage() {
  // ─── Data from API ───────────────────────────────────────────────────
  const [bikes, setBikes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [allParts, setAllParts] = useState([]);
  const [allTires, setAllTires] = useState([]);
  const [venues, setVenues] = useState([]);
  const [loading, setLoading] = useState(true);

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

  // ─── Simulation ──────────────────────────────────────────────────────
  const [result, setResult] = useState(null);
  const [fullResult, setFullResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState(null);
  const [activeCategory, setActiveCategory] = useState(null);
  const [activeTab, setActiveTab] = useState('results');
  const [showEnv, setShowEnv] = useState(false);
  const debounceRef = useRef(null);
  const abortRef = useRef(null);

  // ─── A vs B Comparison ──────────────────────────────────────────────
  const [compareResult, setCompareResult] = useState(null);
  const [compareBike, setCompareBike] = useState(null);
  const [compareParts, setCompareParts] = useState([]);
  const [comparePower, setComparePower] = useState(0);
  const [compareMass, setCompareMass] = useState(0);

  // ─── Upload ─────────────────────────────────────────────────────────
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const fileInputRef = useRef(null);
  const dynoInputRef = useRef(null);

  // ─── Fetch all data on mount ─────────────────────────────────────────
  useEffect(() => {
    async function load() {
      try {
        const safeJson = async (res, fallback) => {
          try { return res.ok ? await res.json() : fallback; }
          catch (e) { console.warn('JSON parse error:', e); return fallback; }
        };
        const [bikesRes, catsRes, partsRes, tiresRes, venuesRes] = await Promise.all([
          fetch(`${API}/api/bikes?limit=200`),
          fetch(`${API}/api/parts/categories`),
          fetch(`${API}/api/parts?limit=200`),
          fetch(`${API}/api/tires?limit=200`),
          fetch(`${API}/api/venues`),
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
        if (bikesData.bikes?.length) setBike(bikesData.bikes[0]);
      } catch (e) {
        console.error('Failed to load data:', e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // ─── Quick sim (auto-run on changes) ─────────────────────────────────
  const runQuickSim = useCallback(async () => {
    if (!bike) return;
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setSimLoading(true);
    setSimError(null);
    try {
      const body = {
        rider_mass_kg: riderKg,
        power_boost_pct: powerBoost,
        mass_delta_kg: massChange,
        part_ids: selectedParts.map(p => p.id),
        ambient_temp_c: ambientTemp,
        track_temp_c: trackTemp,
        humidity_pct: humidity,
        headwind_kmh: headwind,
      };
      if (bike.id != null) body.bike_id = bike.id;
      else if (bike.preset) body.bike_preset = bike.preset;
      if (frontTire?.id != null) body.front_tire_id = frontTire.id;
      if (rearTire?.id != null) body.rear_tire_id = rearTire.id;
      if (venue?.id != null) body.venue_id = venue.id;

      const res = await fetch(`${API}/api/simulate/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      setResult(await res.json());
    } catch (e) {
      if (e.name !== 'AbortError') setSimError(e.message);
    } finally {
      setSimLoading(false);
    }
  }, [bike, selectedParts, frontTire, rearTire, venue, riderKg, powerBoost, massChange, ambientTemp, trackTemp, humidity, headwind]);

  useEffect(() => {
    if (!bike) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(runQuickSim, 400);
    return () => clearTimeout(debounceRef.current);
  }, [runQuickSim]);

  // ─── Full sim (on-demand for charts) ─────────────────────────────────
  const runFullSim = useCallback(async () => {
    if (!bike) return;
    setSimLoading(true);
    try {
      const body = {
        rider_mass_kg: riderKg,
        power_boost_pct: powerBoost,
        mass_delta_kg: massChange,
        ambient_temp_c: ambientTemp,
        track_temp_c: trackTemp,
        humidity_pct: humidity,
        headwind_kmh: headwind,
      };
      if (bike.id != null) body.bike_id = bike.id;
      else if (bike.preset) body.bike_preset = bike.preset;
      if (frontTire?.id != null) body.front_tire_id = frontTire.id;
      if (rearTire?.id != null) body.rear_tire_id = rearTire.id;
      if (venue?.id != null) body.venue_id = venue.id;

      const res = await fetch(`${API}/api/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json();
      setFullResult(data);
      setActiveTab('charts');
    } catch (e) {
      setSimError(e.message);
    } finally {
      setSimLoading(false);
    }
  }, [bike, frontTire, rearTire, venue, riderKg, powerBoost, massChange, ambientTemp, trackTemp, humidity, headwind]);

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
  }

  // ─── A vs B comparison ──────────────────────────────────────────────
  const runCompare = useCallback(async () => {
    if (!bike) return;
    const bBike = compareBike || bike;
    setSimLoading(true);
    setSimError(null);
    try {
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
      const res = await fetch(`${API}/api/simulate/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json();
      setCompareResult(data);
      setActiveTab('compare');
    } catch (e) {
      setSimError(e.message);
    } finally {
      setSimLoading(false);
    }
  }, [bike, compareBike, powerBoost, massChange, riderKg, selectedParts, compareParts, comparePower, compareMass, frontTire, rearTire, venue, ambientTemp, trackTemp, humidity, headwind]);

  // ─── File upload handlers ───────────────────────────────────────────
  const handleDragyUpload = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadLoading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (bike?.id != null) formData.append('bike_id', bike.id.toString());
      else if (bike?.preset) formData.append('bike_preset', bike.preset);

      const res = await fetch(`${API}/api/calibrate/dragy`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg);
      }
      const data = await res.json();
      setUploadResult({ type: 'dragy', ...data });
      setActiveTab('upload');
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploadLoading(false);
      e.target.value = '';
    }
  }, [bike]);

  const handleDynoUpload = useCallback(async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadLoading(true);
    setUploadError(null);
    setUploadResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API}/api/calibrate/dyno`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg);
      }
      const data = await res.json();
      setUploadResult({ type: 'dyno', ...data });
      setActiveTab('upload');
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploadLoading(false);
      e.target.value = '';
    }
  }, []);

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

  // ─── Loading screen ──────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-[#050508] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 text-sm">Loading MotoQuant Pro...</p>
        </div>
      </div>
    );
  }

  /* ═════════════════════════════════════════════════════════════════════
     RENDER
     ═════════════════════════════════════════════════════════════════════ */
  return (
    <div className="min-h-screen bg-[#050508] text-white">
      {/* ─── Header ───────────────────────────────────────────────────── */}
      <nav className="border-b border-white/[0.06] sticky top-0 bg-[#050508]/90 backdrop-blur-xl z-40">
        <div className="max-w-[1440px] mx-auto px-5 py-3 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <a href="/" className="text-gray-600 hover:text-white transition-colors"><ArrowLeft size={16} /></a>
            <div className="text-lg font-bold tracking-tight">
              <span className="text-orange-500">Moto</span>Quant
              <span className="text-[10px] text-gray-600 ml-1.5 font-normal uppercase tracking-widest">Simulator</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-[10px] text-gray-600 uppercase tracking-widest">
            {simLoading && (
              <div className="flex items-center gap-1.5 text-orange-400 normal-case tracking-normal">
                <div className="w-3 h-3 border border-orange-500/30 border-t-orange-500 rounded-full animate-spin" />
                Computing...
              </div>
            )}
            <span>{bikes.length} bikes</span>
            <span className="text-gray-800">·</span>
            <span>{allParts.length} parts</span>
            <span className="text-gray-800">·</span>
            <span>{allTires.length} tires</span>
          </div>
        </div>
      </nav>

      <div className="max-w-[1440px] mx-auto px-5 py-5">
        <div className="grid grid-cols-12 gap-5">

          {/* ═══════════════════════════════════════════════════════════
             LEFT PANEL — Configuration
             ═══════════════════════════════════════════════════════════ */}
          <div className="col-span-12 lg:col-span-3 space-y-4">

            {/* Bike Selector */}
            <Card className="p-4">
              <h3 className="text-xs font-semibold mb-3 flex items-center gap-2 uppercase tracking-widest text-gray-400">
                <Gauge size={13} className="text-orange-500" /> Motorcycle
              </h3>
              <Dropdown
                items={bikes}
                selected={bike}
                onSelect={b => { setBike(b); setSelectedParts([]); setFrontTire(null); setRearTire(null); setFullResult(null); }}
                searchKey={b => `${b.manufacturer} ${b.model} ${b.year} ${b.category || ''}`}
                groupKey={b => b.manufacturer || 'Other'}
                renderItem={b => (
                  <div className="flex justify-between items-center w-full">
                    <span>{b.model} {b.year ? `(${b.year})` : ''}</span>
                    <span className="text-[10px] text-gray-600">{b.displacement_cc}cc{b.peak_power_hp ? ` · ${Math.round(b.peak_power_hp)}hp` : ''}</span>
                  </div>
                )}
                renderSelected={b => (
                  <span className="text-white text-xs"><span className="text-orange-400 font-medium">{b.manufacturer}</span> {b.model} <span className="text-gray-600">({b.displacement_cc}cc)</span></span>
                )}
                emptyMsg="No bikes found"
              />
              {bike && (
                <div className="mt-2 flex gap-2 text-[10px] text-gray-600">
                  <span className="px-1.5 py-0.5 bg-white/[0.03] rounded">{bike.category}</span>
                  {bike.peak_power_hp && <span className="px-1.5 py-0.5 bg-white/[0.03] rounded">{Math.round(bike.peak_power_hp)} hp</span>}
                  {bike.dry_mass_kg && <span className="px-1.5 py-0.5 bg-white/[0.03] rounded">{Math.round(bike.dry_mass_kg)} kg</span>}
                </div>
              )}
            </Card>

            {/* Tuning Sliders */}
            <Card className="p-4">
              <h3 className="text-xs font-semibold mb-3 uppercase tracking-widest text-gray-400">Quick Tune</h3>
              <div className="space-y-3">
                <Slider label="Rider" value={riderKg} onChange={setRiderKg} min={50} max={130} unit=" kg"
                  colorFn={() => 'text-white'} />
                <Slider label="Power" value={powerBoost} onChange={setPowerBoost} min={-20} max={50} unit="%"
                  colorFn={v => v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-white'} />
                <Slider label="Mass" value={massChange} onChange={setMassChange} min={-30} max={30} unit=" kg"
                  colorFn={v => v < 0 ? 'text-green-400' : v > 0 ? 'text-red-400' : 'text-white'} />
              </div>
            </Card>

            {/* Environment (collapsible) */}
            <Card className="p-4">
              <button onClick={() => setShowEnv(!showEnv)}
                className="w-full flex items-center justify-between text-xs font-semibold uppercase tracking-widest text-gray-400">
                <span className="flex items-center gap-2"><Thermometer size={13} className="text-orange-500" /> Environment</span>
                <ChevronDown size={12} className={`transition-transform ${showEnv ? 'rotate-180' : ''}`} />
              </button>
              {showEnv && (
                <div className="mt-3 space-y-3">
                  <Slider label="Air Temp" value={ambientTemp} onChange={setAmbientTemp} min={0} max={50} unit="°C"
                    colorFn={v => v > 35 ? 'text-red-400' : v < 15 ? 'text-blue-400' : 'text-white'} />
                  <Slider label="Track Temp" value={trackTemp} onChange={setTrackTemp} min={10} max={65} unit="°C"
                    colorFn={v => v > 50 ? 'text-red-400' : 'text-white'} />
                  <Slider label="Humidity" value={humidity} onChange={setHumidity} min={0} max={100} unit="%"
                    colorFn={() => 'text-white'} />
                  <Slider label="Headwind" value={headwind} onChange={setHeadwind} min={-30} max={30} unit=" km/h"
                    colorFn={v => v > 0 ? 'text-red-400' : v < 0 ? 'text-green-400' : 'text-white'} />

                  {/* Venue */}
                  <Dropdown
                    label="Venue" icon={<MapPin size={10} className="text-orange-500" />}
                    items={[{ id: null, name: 'Standard (ISA)', country: 'Default' }, ...venues]}
                    selected={venue || { id: null, name: 'Standard (ISA)', country: 'Default' }}
                    onSelect={v => setVenue(v.id ? v : null)}
                    searchKey={v => `${v.name} ${v.country || ''}`}
                    groupKey={v => v.country || 'Default'}
                    renderItem={v => <div className="flex justify-between w-full"><span>{v.name}</span>{v.altitude_m && <span className="text-[10px] text-gray-600">{v.altitude_m}m</span>}</div>}
                    renderSelected={v => <span className="text-white text-xs">{v.name}</span>}
                  />
                </div>
              )}
            </Card>

            {/* Tires */}
            <Card className="p-4">
              <h3 className="text-xs font-semibold mb-3 flex items-center gap-2 uppercase tracking-widest text-gray-400">
                <CircleDot size={13} className="text-orange-500" /> Tires
              </h3>
              <div className="space-y-2.5">
                <Dropdown label="Front" icon={null}
                  items={[{ id: null, manufacturer: 'Stock', model: 'OEM Default' }, ...allTires]}
                  selected={frontTire || { id: null, manufacturer: 'Stock', model: 'OEM Default' }}
                  onSelect={t => setFrontTire(t.id ? t : null)}
                  searchKey={t => `${t.manufacturer} ${t.model} ${t.compound_type || ''}`}
                  groupKey={t => t.manufacturer || 'Stock'}
                  renderItem={t => <div className="flex justify-between w-full"><span>{t.model}</span><span className="text-[10px] text-gray-600">{t.compound_type || ''}</span></div>}
                  renderSelected={t => <span className="text-white text-xs">{t.manufacturer} {t.model}</span>}
                />
                <Dropdown label="Rear" icon={null}
                  items={[{ id: null, manufacturer: 'Stock', model: 'OEM Default' }, ...allTires]}
                  selected={rearTire || { id: null, manufacturer: 'Stock', model: 'OEM Default' }}
                  onSelect={t => setRearTire(t.id ? t : null)}
                  searchKey={t => `${t.manufacturer} ${t.model} ${t.compound_type || ''}`}
                  groupKey={t => t.manufacturer || 'Stock'}
                  renderItem={t => <div className="flex justify-between w-full"><span>{t.model}</span><span className="text-[10px] text-gray-600">{t.compound_type || ''}</span></div>}
                  renderSelected={t => <span className="text-white text-xs">{t.manufacturer} {t.model}</span>}
                />
              </div>
            </Card>

            {/* Actions */}
            <button onClick={resetAll}
              className="w-full py-2 text-xs text-gray-500 hover:text-white border border-white/[0.06] hover:border-white/[0.12] rounded-xl transition-all flex items-center justify-center gap-1.5">
              <RotateCcw size={11} /> Reset All
            </button>
          </div>

          {/* ═══════════════════════════════════════════════════════════
             CENTER PANEL — Parts Catalog
             ═══════════════════════════════════════════════════════════ */}
          <div className="col-span-12 lg:col-span-4">
            <Card className="p-4 h-full flex flex-col">
              <h3 className="text-xs font-semibold mb-3 flex items-center gap-2 uppercase tracking-widest text-gray-400">
                <Wrench size={13} className="text-orange-500" /> Parts Catalog
                {selectedParts.length > 0 && (
                  <span className="ml-auto text-[10px] bg-orange-500/15 text-orange-400 px-2 py-0.5 rounded-full font-medium">
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
                  const isActive = activeCategory?.id === cat.id;
                  const selectedInCat = selectedParts.filter(p => p.category_id === cat.id).length;
                  return (
                    <div key={cat.id}>
                      <button
                        onClick={() => setActiveCategory(isActive ? null : cat)}
                        className={`w-full px-3 py-2 rounded-xl text-left text-xs flex items-center justify-between transition-all ${
                          isActive ? 'bg-orange-500/10 text-orange-300 border border-orange-500/20' : 'hover:bg-white/[0.03] text-gray-400 border border-transparent'
                        }`}>
                        <div className="flex items-center gap-2">
                          <ChevronRight size={11} className={`transition-transform ${isActive ? 'rotate-90' : ''}`} />
                          <span className="font-medium">{cat.display_name || cat.name}</span>
                          <span className="text-[10px] text-gray-600">({catParts.length})</span>
                        </div>
                        {selectedInCat > 0 && (
                          <span className="text-[9px] bg-orange-500 text-black px-1.5 py-0.5 rounded-full font-bold">{selectedInCat}</span>
                        )}
                      </button>

                      {isActive && (
                        <div className="ml-5 mt-1 mb-2 space-y-1">
                          {catParts.length === 0 ? (
                            <p className="text-[10px] text-gray-700 py-2">No parts in this category</p>
                          ) : catParts.map(part => {
                            const sel = isPartSelected(part);
                            return (
                              <button key={part.id} onClick={() => togglePart(part)}
                                className={`w-full px-3 py-2.5 rounded-xl text-left text-xs transition-all border ${
                                  sel ? 'bg-orange-500/10 border-orange-500/30 text-orange-200' : 'border-white/[0.04] hover:border-white/[0.08] text-gray-400 hover:text-gray-300'
                                }`}>
                                <div className="flex justify-between items-start">
                                  <div>
                                    <div className="font-medium text-[11px]">{part.brand} {part.model_name}</div>
                                    {part.fitment_notes && <div className="text-[10px] text-gray-600 mt-0.5">{part.fitment_notes}</div>}
                                  </div>
                                  <div className="text-right shrink-0 ml-2">
                                    {part.price_inr > 0 && (
                                      <div className="text-[10px] text-gray-500">₹{part.price_inr.toLocaleString('en-IN')}</div>
                                    )}
                                    {sel && <div className="text-[10px] text-orange-400 mt-0.5">✓ Added</div>}
                                  </div>
                                </div>
                                {(part.param_deltas || part.param_multipliers) && (
                                  <div className="mt-1.5 flex flex-wrap gap-1">
                                    {part.param_deltas && typeof part.param_deltas === 'object' && Object.entries(part.param_deltas).map(([k, v]) => (
                                      <span key={k} className={`text-[9px] px-1.5 py-0.5 rounded-full ${v > 0 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                                        {k.split('.').pop()}: {v > 0 ? '+' : ''}{v}
                                      </span>
                                    ))}
                                    {part.param_multipliers && typeof part.param_multipliers === 'object' && Object.entries(part.param_multipliers).map(([k, v]) => (
                                      <span key={k} className={`text-[9px] px-1.5 py-0.5 rounded-full ${v > 1 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
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

            {/* Tab bar */}
            <div className="flex items-center gap-2 flex-wrap">
              <Tab active={activeTab === 'results'} onClick={() => setActiveTab('results')} icon={<Zap size={12} />} label="Results" />
              <Tab active={activeTab === 'charts'} onClick={() => { if (!fullResult) runFullSim(); else setActiveTab('charts'); }}
                icon={<BarChart3 size={12} />} label="Charts" />
              <Tab active={activeTab === 'splits'} onClick={() => setActiveTab('splits')} icon={<Table2 size={12} />} label="Splits" />
              <Tab active={activeTab === 'compare'} onClick={() => setActiveTab('compare')} icon={<Layers size={12} />} label="A vs B" />
              <Tab active={activeTab === 'upload'} onClick={() => setActiveTab('upload')} icon={<Upload size={12} />} label="Upload" />
              <Tab active={activeTab === 'specs'} onClick={() => setActiveTab('specs')} icon={<Settings2 size={12} />} label="Specs" />
            </div>

            {/* Error */}
            {simError && (
              <div className="p-3 bg-red-500/5 border border-red-500/20 rounded-xl text-red-400 text-xs">{simError}</div>
            )}

            {/* ─── Results Tab ───────────────────────────────────────── */}
            {activeTab === 'results' && (
              <Card className="p-5" glow={!!result}>
                {result ? (
                  <div className="space-y-4">
                    {/* Primary metrics */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-gradient-to-br from-orange-500/5 to-transparent rounded-xl p-5 text-center border border-orange-500/10">
                        <Metric label="Quarter-Mile ET" value={result.et_quarter_s?.toFixed(3) ?? '—'} unit="s" large accent />
                      </div>
                      <div className="bg-white/[0.02] rounded-xl p-5 text-center border border-white/[0.04]">
                        <Metric label="Trap Speed" value={result.trap_speed_kmh?.toFixed(1) ?? '—'} unit="km/h" large />
                      </div>
                    </div>

                    {/* Stock vs Modified */}
                    {result.stock_et_s && result.et_delta_s !== null && (
                      <div className={`p-3 rounded-xl border text-center ${
                        result.et_delta_s < 0 ? 'bg-green-500/5 border-green-500/20' : result.et_delta_s > 0 ? 'bg-red-500/5 border-red-500/20' : 'bg-white/[0.02] border-white/[0.04]'
                      }`}>
                        <div className="flex items-center justify-center gap-4 text-xs">
                          <div><span className="text-gray-500">Stock </span><span className="text-white font-medium">{result.stock_et_s.toFixed(3)}s</span></div>
                          <div className={`text-lg font-bold ${result.et_delta_s < 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {result.et_delta_s < 0 ? '' : '+'}{result.et_delta_s.toFixed(3)}s
                          </div>
                          <div><span className="text-gray-500">Modified </span><span className="text-orange-400 font-medium">{result.et_quarter_s?.toFixed(3)}s</span></div>
                        </div>
                      </div>
                    )}

                    {/* Splits & specs grid */}
                    <div className="bg-white/[0.02] rounded-xl p-4 border border-white/[0.04]">
                      <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs">
                        <div className="flex justify-between"><span className="text-gray-500">60 ft</span><span className="text-white font-medium tabular-nums">{result.et_60ft_s?.toFixed(3) ?? '—'}s</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">⅛ mile</span><span className="text-white font-medium tabular-nums">{result.et_eighth_s?.toFixed(3) ?? '—'}s</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">Power</span><span className="text-white font-medium tabular-nums">{result.peak_power_hp?.toFixed(0) ?? '—'} hp</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">Total mass</span><span className="text-white font-medium tabular-nums">{result.total_mass_kg?.toFixed(0) ?? '—'} kg</span></div>
                      </div>
                    </div>

                    {/* Build summary */}
                    {selectedParts.length > 0 && (
                      <div className="bg-white/[0.02] rounded-xl p-4 border border-white/[0.04]">
                        <div className="flex justify-between items-center text-xs mb-2">
                          <span className="text-gray-400 font-medium">Build Summary</span>
                          <span className="text-orange-400 font-bold">₹{buildCost.toLocaleString('en-IN')}</span>
                        </div>
                        {result.et_delta_s && result.et_delta_s < 0 && buildCost > 0 && (
                          <div className="text-[10px] text-green-400">
                            Cost per tenth: ₹{Math.round(buildCost / (Math.abs(result.et_delta_s) * 10)).toLocaleString('en-IN')}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Full sim button */}
                    <button onClick={runFullSim} disabled={simLoading}
                      className="w-full py-2.5 text-xs bg-white/[0.04] hover:bg-orange-500/10 border border-white/[0.06] hover:border-orange-500/30 rounded-xl text-gray-400 hover:text-orange-400 transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                      <BarChart3 size={13} /> View Detailed Charts & Analysis
                    </button>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-700 text-xs">
                    <Gauge size={32} className="mx-auto mb-3 opacity-20" />
                    Select a bike to start simulating
                  </div>
                )}
              </Card>
            )}

            {/* ─── Charts Tab ────────────────────────────────────────── */}
            {activeTab === 'charts' && (
              <Card className="p-5">
                {chartData.length > 0 ? (
                  <div className="space-y-5">
                    <div className="grid grid-cols-2 gap-4">
                      <SimChart data={chartData} dataKey="speed" label="Speed" unit="km/h" />
                      <SimChart data={chartData} dataKey="rpm" label="Engine RPM" unit="rpm" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <SimChart data={chartData} dataKey="gear" label="Gear" unit="" color="#a855f7" />
                      <SimChart data={chartData} dataKey="traction" label="Traction" unit="%" color="#22c55e" domain={[0, 110]} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <SimChart data={chartData} dataKey="power" label="Power" unit="kW" color="#eab308" />
                      <SimChart data={chartData} dataKey="tire_temp" label="Tire Temp" unit="°C" color="#ef4444" />
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <BarChart3 size={32} className="mx-auto mb-3 text-gray-800" />
                    <p className="text-gray-600 text-xs mb-3">Run a full simulation to see telemetry charts</p>
                    <button onClick={runFullSim} disabled={!bike || simLoading}
                      className="px-4 py-2 text-xs bg-orange-600 hover:bg-orange-700 rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-1.5">
                      <Play size={12} /> Run Full Simulation
                    </button>
                  </div>
                )}
              </Card>
            )}

            {/* ─── Splits Tab ────────────────────────────────────────── */}
            {activeTab === 'splits' && (
              <Card className="p-5">
                {fullResult ? (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">Split Times</h4>
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="text-gray-600 border-b border-white/[0.04]">
                          <th className="text-left py-2 font-medium">Distance</th>
                          <th className="text-right py-2 font-medium">Time</th>
                          <th className="text-right py-2 font-medium">Speed</th>
                        </tr>
                      </thead>
                      <tbody className="text-gray-300">
                        {[
                          { d: '60 ft (18.3m)', t: fullResult.splits?.['60ft_s'], s: null },
                          { d: '330 ft (100.6m)', t: fullResult.splits?.['330ft_s'], s: null },
                          { d: '⅛ mile (201.2m)', t: fullResult.splits?.['660ft_s'], s: null },
                          { d: '1000 ft (304.8m)', t: fullResult.splits?.['1000ft_s'], s: null },
                          { d: '¼ mile (402.3m)', t: fullResult.splits?.['1320ft_s'], s: fullResult.trap_speed_kmh },
                        ].map(row => (
                          <tr key={row.d} className="border-b border-white/[0.03]">
                            <td className="py-2 text-gray-500">{row.d}</td>
                            <td className="py-2 text-right font-medium tabular-nums">{row.t?.toFixed(3) ?? '—'}s</td>
                            <td className="py-2 text-right tabular-nums text-gray-500">{row.s ? `${row.s.toFixed(1)} km/h` : '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-600 text-xs">
                    {result ? (
                      <>
                        <p className="mb-1">Quick splits from last run:</p>
                        <p className="text-white font-medium tabular-nums">60ft: {result.et_60ft_s?.toFixed(3)}s · ⅛: {result.et_eighth_s?.toFixed(3)}s · ¼: {result.et_quarter_s?.toFixed(3)}s</p>
                        <button onClick={runFullSim} disabled={simLoading}
                          className="mt-3 px-4 py-2 text-xs bg-orange-600 hover:bg-orange-700 rounded-lg font-medium transition-colors disabled:opacity-50 inline-flex items-center gap-1.5">
                          <Play size={12} /> Get Full Splits
                        </button>
                      </>
                    ) : 'Run a simulation to see splits'}
                  </div>
                )}
              </Card>
            )}

            {/* ─── A vs B Compare Tab ────────────────────────────────── */}
            {activeTab === 'compare' && (
              <Card className="p-5">
                <h4 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-4 flex items-center gap-2">
                  <Layers size={13} className="text-orange-500" /> A vs B Comparison
                </h4>

                {/* Build B config */}
                <div className="space-y-3 mb-4">
                  <div className="bg-white/[0.02] rounded-xl p-3 border border-white/[0.04]">
                    <p className="text-[10px] text-orange-400 font-medium uppercase tracking-widest mb-2">Build A — Current Setup</p>
                    <p className="text-xs text-gray-400">
                      {bike?.manufacturer} {bike?.model} · {powerBoost !== 0 ? `${powerBoost > 0 ? '+' : ''}${powerBoost}% power` : 'Stock power'} · {selectedParts.length} parts
                    </p>
                  </div>

                  <div className="bg-white/[0.02] rounded-xl p-3 border border-blue-500/20">
                    <p className="text-[10px] text-blue-400 font-medium uppercase tracking-widest mb-2">Build B — Comparison</p>
                    <div className="space-y-2">
                      <Dropdown
                        label="Bike" icon={<Gauge size={10} className="text-blue-400" />}
                        items={bikes}
                        selected={compareBike || bike}
                        onSelect={b => setCompareBike(b)}
                        searchKey={b => `${b.manufacturer} ${b.model} ${b.year} ${b.category || ''}`}
                        groupKey={b => b.manufacturer || 'Other'}
                        renderItem={b => (
                          <div className="flex justify-between items-center w-full">
                            <span>{b.model} {b.year ? `(${b.year})` : ''}</span>
                            <span className="text-[10px] text-gray-600">{b.displacement_cc}cc</span>
                          </div>
                        )}
                        renderSelected={b => <span className="text-white text-xs">{b?.manufacturer} {b?.model}</span>}
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <Slider label="Power" value={comparePower} onChange={setComparePower} min={-20} max={50} unit="%"
                          colorFn={v => v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-white'} />
                        <Slider label="Mass" value={compareMass} onChange={setCompareMass} min={-30} max={30} unit=" kg"
                          colorFn={v => v < 0 ? 'text-green-400' : v > 0 ? 'text-red-400' : 'text-white'} />
                      </div>
                    </div>
                  </div>
                </div>

                <button onClick={runCompare} disabled={!bike || simLoading}
                  className="w-full py-2.5 text-xs bg-gradient-to-r from-orange-600/80 to-blue-600/80 hover:from-orange-600 hover:to-blue-600 rounded-xl font-medium transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                  <Layers size={13} /> {simLoading ? 'Comparing...' : 'Run A vs B Comparison'}
                </button>

                {/* Compare results */}
                {compareResult && (
                  <div className="mt-4 space-y-3">
                    {/* Delta banner */}
                    <div className={`p-4 rounded-xl border text-center ${
                      compareResult.delta.et_s < 0 ? 'bg-blue-500/5 border-blue-500/20' : compareResult.delta.et_s > 0 ? 'bg-orange-500/5 border-orange-500/20' : 'bg-white/[0.02] border-white/[0.04]'
                    }`}>
                      <div className="text-[10px] text-gray-500 uppercase tracking-widest mb-1">
                        {compareResult.delta.faster === 'B' ? 'Build B is faster' : compareResult.delta.faster === 'A' ? 'Build A is faster' : 'Dead heat'}
                      </div>
                      <div className={`text-2xl font-bold ${compareResult.delta.et_s < 0 ? 'text-blue-400' : compareResult.delta.et_s > 0 ? 'text-orange-400' : 'text-white'}`}>
                        {compareResult.delta.et_s > 0 ? '+' : ''}{compareResult.delta.et_s.toFixed(3)}s
                      </div>
                      <div className="text-[10px] text-gray-500 mt-1">
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
                        <div key={label} className={`bg-white/[0.02] rounded-xl p-3 border ${color === 'orange' ? 'border-orange-500/20' : 'border-blue-500/20'}`}>
                          <p className={`text-[10px] font-medium uppercase tracking-widest mb-2 ${color === 'orange' ? 'text-orange-400' : 'text-blue-400'}`}>{label}</p>
                          <div className="space-y-1 text-xs">
                            <div className="flex justify-between"><span className="text-gray-500">ET</span><span className="text-white font-bold tabular-nums">{data.et_quarter_s?.toFixed(3)}s</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">Trap</span><span className="text-white tabular-nums">{data.trap_speed_kmh?.toFixed(1)} km/h</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">60ft</span><span className="text-white tabular-nums">{data.et_60ft_s?.toFixed(3)}s</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">Power</span><span className="text-white tabular-nums">{data.peak_power_hp?.toFixed(0)} hp</span></div>
                            <div className="flex justify-between"><span className="text-gray-500">Mass</span><span className="text-white tabular-nums">{data.total_mass_kg?.toFixed(0)} kg</span></div>
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
                          <p className="text-[10px] text-gray-500 uppercase tracking-widest">Overlay Charts</p>
                          {[
                            { key: 'speed', label: 'Speed (km/h)', unit: 'km/h' },
                            { key: 'rpm', label: 'Engine RPM', unit: 'rpm' },
                            { key: 'power', label: 'Power (kW)', unit: 'kW' },
                          ].map(chart => (
                            <div key={chart.key} className="h-44">
                              <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-2">{chart.label}</p>
                              <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={overlayData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                                  <XAxis dataKey="t" tick={{ fontSize: 9, fill: '#555' }} tickFormatter={v => `${v}s`} />
                                  <YAxis tick={{ fontSize: 9, fill: '#555' }} />
                                  <Tooltip
                                    contentStyle={{ background: '#0a0a0f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
                                    labelFormatter={v => `${v}s`}
                                  />
                                  <Line type="monotone" dataKey={`a_${chart.key}`} stroke="#f97316" strokeWidth={1.5} dot={false} name="Build A" />
                                  <Line type="monotone" dataKey={`b_${chart.key}`} stroke="#60a5fa" strokeWidth={1.5} dot={false} name="Build B" />
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
                <h4 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-4 flex items-center gap-2">
                  <Upload size={13} className="text-orange-500" /> Upload Run Data
                </h4>

                {/* Upload buttons */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <div>
                    <input type="file" ref={fileInputRef} accept=".csv,.json" onChange={handleDragyUpload} className="hidden" />
                    <button onClick={() => fileInputRef.current?.click()} disabled={uploadLoading}
                      className="w-full p-4 bg-white/[0.02] hover:bg-orange-500/5 border border-white/[0.06] hover:border-orange-500/20 rounded-xl transition-all text-center disabled:opacity-50">
                      <Zap size={20} className="mx-auto mb-2 text-orange-400" />
                      <p className="text-xs font-medium text-white">Dragy GPS</p>
                      <p className="text-[10px] text-gray-600 mt-1">CSV or JSON export</p>
                    </button>
                  </div>
                  <div>
                    <input type="file" ref={dynoInputRef} accept=".csv,.txt" onChange={handleDynoUpload} className="hidden" />
                    <button onClick={() => dynoInputRef.current?.click()} disabled={uploadLoading}
                      className="w-full p-4 bg-white/[0.02] hover:bg-blue-500/5 border border-white/[0.06] hover:border-blue-500/20 rounded-xl transition-all text-center disabled:opacity-50">
                      <BarChart3 size={20} className="mx-auto mb-2 text-blue-400" />
                      <p className="text-xs font-medium text-white">Dyno Curve</p>
                      <p className="text-[10px] text-gray-600 mt-1">DynoJet / MoTeC CSV</p>
                    </button>
                  </div>
                </div>

                {uploadLoading && (
                  <div className="text-center py-6">
                    <div className="w-8 h-8 border-2 border-orange-500/30 border-t-orange-500 rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-xs text-gray-500">Parsing file...</p>
                  </div>
                )}

                {uploadError && (
                  <div className="p-3 bg-red-500/5 border border-red-500/20 rounded-xl text-red-400 text-xs mb-3">{uploadError}</div>
                )}

                {/* Dragy results */}
                {uploadResult?.type === 'dragy' && (
                  <div className="space-y-3">
                    <div className="bg-white/[0.02] rounded-xl p-4 border border-white/[0.04]">
                      <div className="flex justify-between items-center mb-2">
                        <p className="text-[10px] text-orange-400 font-medium uppercase tracking-widest">Dragy Run — Best of {uploadResult.runs_detected}</p>
                        <p className="text-[10px] text-gray-600">{uploadResult.filename}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4 mb-3">
                        <Metric label="Real ET" value={uploadResult.best_run?.et_quarter_s?.toFixed(3) ?? '—'} unit="s" large accent />
                        <Metric label="Trap Speed" value={uploadResult.best_run?.trap_speed_kmh?.toFixed(1) ?? '—'} unit="km/h" large />
                      </div>
                      {uploadResult.best_run?.splits && (
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          {Object.entries(uploadResult.best_run.splits).map(([k, v]) => (
                            <div key={k} className="flex justify-between">
                              <span className="text-gray-500">{k}</span>
                              <span className="text-white tabular-nums">{v?.toFixed(3)}s</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Overlay vs sim */}
                    {uploadResult.overlay && (
                      <div className={`rounded-xl p-4 border ${Math.abs(uploadResult.overlay.et_error_s) < 0.15 ? 'bg-green-500/5 border-green-500/20' : 'bg-yellow-500/5 border-yellow-500/20'}`}>
                        <p className={`text-[10px] uppercase tracking-widest mb-2 font-medium ${Math.abs(uploadResult.overlay.et_error_s) < 0.15 ? 'text-green-400' : 'text-yellow-400'}`}>
                          Sim vs Real — {uploadResult.overlay.bike_name}
                        </p>
                        <div className="grid grid-cols-3 gap-3 text-xs">
                          <div><span className="text-gray-500 block">Sim ET</span><span className="text-white font-medium tabular-nums">{uploadResult.overlay.sim_et_s?.toFixed(3)}s</span></div>
                          <div><span className="text-gray-500 block">Error</span><span className={`font-bold tabular-nums ${Math.abs(uploadResult.overlay.et_error_s) < 0.15 ? 'text-green-400' : 'text-yellow-400'}`}>{uploadResult.overlay.et_error_s > 0 ? '+' : ''}{uploadResult.overlay.et_error_s?.toFixed(3)}s</span></div>
                          <div><span className="text-gray-500 block">RMSE</span><span className="text-white tabular-nums">{uploadResult.overlay.v_rmse_kmh?.toFixed(1)} km/h</span></div>
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
                          <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-2">Speed Overlay — Real vs Sim</p>
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={overlayData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                              <XAxis dataKey="t" tick={{ fontSize: 9, fill: '#555' }} tickFormatter={v => `${v}s`} />
                              <YAxis tick={{ fontSize: 9, fill: '#555' }} />
                              <Tooltip contentStyle={{ background: '#0a0a0f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }} labelFormatter={v => `${v}s`} />
                              <Line type="monotone" dataKey="real" stroke="#22c55e" strokeWidth={2} dot={false} name="Real (Dragy)" />
                              <Line type="monotone" dataKey="sim" stroke="#f97316" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Sim" />
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
                    <div className="bg-white/[0.02] rounded-xl p-4 border border-white/[0.04]">
                      <div className="flex justify-between items-center mb-3">
                        <p className="text-[10px] text-blue-400 font-medium uppercase tracking-widest">Dyno Curve</p>
                        <p className="text-[10px] text-gray-600">{uploadResult.filename}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4 mb-3">
                        <Metric label="Peak Power" value={uploadResult.peak_power_hp?.toFixed(1) ?? '—'} unit="hp" large accent />
                        <Metric label="Peak Torque" value={uploadResult.peak_torque_nm?.toFixed(1) ?? '—'} unit="Nm" large />
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="flex justify-between"><span className="text-gray-500">RPM @ peak power</span><span className="text-white tabular-nums">{uploadResult.rpm_at_peak_power?.toFixed(0)}</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">RPM @ peak torque</span><span className="text-white tabular-nums">{uploadResult.rpm_at_peak_torque?.toFixed(0)}</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">SAE CF</span><span className="text-white tabular-nums">{uploadResult.correction_factor?.toFixed(4)}</span></div>
                        <div className="flex justify-between"><span className="text-gray-500">Data points</span><span className="text-white tabular-nums">{uploadResult.n_points}</span></div>
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
                          <p className="text-[10px] text-gray-500 uppercase tracking-widest mb-2">Power & Torque vs RPM</p>
                          <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={curveData} margin={{ top: 0, right: 0, left: -10, bottom: 0 }}>
                              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                              <XAxis dataKey="rpm" tick={{ fontSize: 9, fill: '#555' }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                              <YAxis yAxisId="power" tick={{ fontSize: 9, fill: '#f97316' }} orientation="left" />
                              <YAxis yAxisId="torque" tick={{ fontSize: 9, fill: '#60a5fa' }} orientation="right" />
                              <Tooltip contentStyle={{ background: '#0a0a0f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }} labelFormatter={v => `${v} RPM`} />
                              <Line yAxisId="power" type="monotone" dataKey="power" stroke="#f97316" strokeWidth={2} dot={false} name="Power (hp)" />
                              <Line yAxisId="torque" type="monotone" dataKey="torque" stroke="#60a5fa" strokeWidth={1.5} dot={false} name="Torque (Nm)" />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      );
                    })()}
                  </div>
                )}

                {/* Empty state */}
                {!uploadResult && !uploadLoading && !uploadError && (
                  <div className="text-center py-8 text-gray-700 text-xs">
                    <Upload size={32} className="mx-auto mb-3 opacity-20" />
                    <p className="mb-1">Upload your Dragy GPS run or dyno pull</p>
                    <p className="text-[10px] text-gray-600">We'll parse it, show splits, and overlay against our sim for accuracy validation</p>
                  </div>
                )}
              </Card>
            )}

            {/* ─── Specs Tab ─────────────────────────────────────────── */}
            {activeTab === 'specs' && (
              <Card className="p-5">
                {(fullResult?.config || result) ? (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-3">Configuration</h4>
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
                        <div key={k} className="flex justify-between py-1 border-b border-white/[0.03]">
                          <span className="text-gray-500">{k}</span>
                          <span className="text-white font-medium tabular-nums">{v}</span>
                        </div>
                      ))}
                    </div>
                    {/* Environment conditions */}
                    <h4 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mt-5 mb-3">Conditions</h4>
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
                        <div key={k} className="flex justify-between py-1 border-b border-white/[0.03]">
                          <span className="text-gray-500">{k}</span>
                          <span className="text-white font-medium">{v}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-600 text-xs">Run a simulation to see specs</div>
                )}
              </Card>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-white/[0.04] mt-12 py-6 text-center text-[10px] text-gray-700 uppercase tracking-widest">
        MotoQuant Pro · First-principles RK4 physics · 15 sub-models · 1ms timestep · motoquant.in
      </div>
    </div>
  );
}
