'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Zap, Search, ChevronDown } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://web-production-de6eb.up.railway.app';

// Fallback presets if DB bikes aren't available
const PRESET_BIKES = [
  { id: null, preset: 'gsxr1000_k5',   manufacturer: 'Suzuki',  model: 'GSX-R 1000 K5',  year: 2005, displacement_cc: 999,  peak_power_hp: 178, category: 'sport' },
  { id: null, preset: 'yzfr1_4c8',     manufacturer: 'Yamaha',  model: 'YZF-R1 (4C8)',    year: 2007, displacement_cc: 998,  peak_power_hp: 180, category: 'sport' },
  { id: null, preset: 'hayabusa_gen1', manufacturer: 'Suzuki',  model: 'Hayabusa Gen1',   year: 2006, displacement_cc: 1299, peak_power_hp: 175, category: 'sport' },
];

export default function SimulatorWidget() {
  const [bikes,       setBikes]       = useState(PRESET_BIKES);
  const [selected,    setSelected]    = useState(null);
  const [search,      setSearch]      = useState('');
  const [dropOpen,    setDropOpen]    = useState(false);
  const [riderKg,     setRiderKg]     = useState(75);
  const [powerBoost,  setPowerBoost]  = useState(0);
  const [massChange,  setMassChange]  = useState(0);
  const [result,      setResult]      = useState(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState(null);
  const [bikesLoading, setBikesLoading] = useState(true);
  const debounceRef = useRef(null);
  const abortRef    = useRef(null);
  const dropRef     = useRef(null);

  // Fetch all bikes from API on mount
  useEffect(() => {
    async function loadBikes() {
      try {
        const res = await fetch(`${API_URL}/api/bikes?limit=200`);
        if (res.ok) {
          const data = await res.json();
          if (data.bikes && data.bikes.length > 0) {
            setBikes(data.bikes);
            setSelected(data.bikes[0]);
          } else {
            setSelected(PRESET_BIKES[0]);
          }
        } else {
          setSelected(PRESET_BIKES[0]);
        }
      } catch {
        setSelected(PRESET_BIKES[0]);
      } finally {
        setBikesLoading(false);
      }
    }
    loadBikes();
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e) {
      if (dropRef.current && !dropRef.current.contains(e.target)) {
        setDropOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const runSim = useCallback(async (bike, r, p, m) => {
    if (!bike) return;
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);
    try {
      const body = {
        rider_mass_kg:   r,
        power_boost_pct: p,
        mass_delta_kg:   m,
      };
      // Use bike_id for DB bikes, bike_preset for fallback presets
      if (bike.id) {
        body.bike_id = bike.id;
      } else if (bike.preset) {
        body.bike_preset = bike.preset;
      }

      const res = await fetch(`${API_URL}/api/simulate/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`API error ${res.status}: ${msg}`);
      }
      setResult(await res.json());
    } catch (e) {
      if (e.name !== 'AbortError') setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-simulate on any change (300ms debounce)
  useEffect(() => {
    if (!selected) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      runSim(selected, riderKg, powerBoost, massChange);
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [selected, riderKg, powerBoost, massChange, runSim]);

  // Filter bikes by search
  const filtered = bikes.filter(b => {
    const q = search.toLowerCase();
    if (!q) return true;
    const text = `${b.manufacturer} ${b.model} ${b.year} ${b.category || ''}`.toLowerCase();
    return text.includes(q);
  });

  // Group filtered bikes by manufacturer
  const grouped = {};
  filtered.forEach(b => {
    const mfr = b.manufacturer || 'Other';
    if (!grouped[mfr]) grouped[mfr] = [];
    grouped[mfr].push(b);
  });

  const bikeLabel = (b) => `${b.manufacturer} ${b.model}${b.year ? ` (${b.year})` : ''}`;

  return (
    <div className="bg-black border border-gray-800 rounded-2xl p-8 max-w-2xl mx-auto">
      <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
        <Zap className="text-orange-500" size={20} />
        Live Quarter-Mile Simulator
        {loading && (
          <svg className="animate-spin h-4 w-4 text-orange-500 ml-2" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
        )}
      </h3>

      {/* Bike selector */}
      <div className="mb-5 relative" ref={dropRef}>
        <label className="block text-sm text-gray-400 mb-2">
          Bike {!bikesLoading && <span className="text-gray-600">({bikes.length} available)</span>}
        </label>
        <button
          onClick={() => setDropOpen(!dropOpen)}
          className="w-full p-3 rounded-lg border border-gray-700 bg-gray-950 text-left flex items-center justify-between hover:border-gray-500 transition-colors"
        >
          <span className="text-sm">
            {selected ? (
              <>
                <span className="text-white font-medium">{bikeLabel(selected)}</span>
                <span className="text-gray-500 ml-2">
                  {selected.displacement_cc}cc · {selected.peak_power_hp ? `${Math.round(selected.peak_power_hp)} hp` : ''}
                </span>
              </>
            ) : (
              <span className="text-gray-500">Select a bike...</span>
            )}
          </span>
          <ChevronDown size={16} className={`text-gray-500 transition-transform ${dropOpen ? 'rotate-180' : ''}`} />
        </button>

        {dropOpen && (
          <div className="absolute z-50 mt-1 w-full bg-gray-950 border border-gray-700 rounded-lg shadow-2xl max-h-80 overflow-hidden">
            {/* Search */}
            <div className="p-2 border-b border-gray-800">
              <div className="relative">
                <Search size={14} className="absolute left-2.5 top-2.5 text-gray-500" />
                <input
                  type="text"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  placeholder="Search by make, model, or category..."
                  className="w-full pl-8 pr-3 py-2 bg-black border border-gray-800 rounded text-sm text-white placeholder-gray-600 focus:outline-none focus:border-orange-500"
                  autoFocus
                />
              </div>
            </div>

            {/* Bike list */}
            <div className="overflow-y-auto max-h-60">
              {Object.keys(grouped).sort().map(mfr => (
                <div key={mfr}>
                  <div className="px-3 py-1.5 text-xs text-gray-500 font-semibold uppercase tracking-wider bg-gray-900/50 sticky top-0">
                    {mfr}
                  </div>
                  {grouped[mfr].map((b, i) => (
                    <button
                      key={b.id || b.preset || i}
                      onClick={() => { setSelected(b); setDropOpen(false); setSearch(''); }}
                      className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-800 transition-colors flex justify-between items-center ${
                        selected && (b.id === selected.id && b.model === selected.model) ? 'bg-orange-500/10 text-orange-300' : 'text-gray-300'
                      }`}
                    >
                      <span>{b.model} {b.year ? `(${b.year})` : ''}</span>
                      <span className="text-xs text-gray-600">
                        {b.displacement_cc}cc{b.peak_power_hp ? ` · ${Math.round(b.peak_power_hp)} hp` : ''}
                      </span>
                    </button>
                  ))}
                </div>
              ))}
              {filtered.length === 0 && (
                <div className="px-3 py-6 text-center text-sm text-gray-600">No bikes match "{search}"</div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Sliders */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-xs text-gray-400 mb-1">
            Rider weight: <span className="text-white font-medium">{riderKg} kg</span>
          </label>
          <input type="range" min={50} max={130} value={riderKg}
            onChange={e => setRiderKg(Number(e.target.value))}
            className="w-full accent-orange-500" />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">
            Power boost: <span className={`font-medium ${powerBoost > 0 ? 'text-green-400' : 'text-white'}`}>
              {powerBoost > 0 ? `+${powerBoost}%` : `${powerBoost}%`}
            </span>
          </label>
          <input type="range" min={-10} max={30} value={powerBoost}
            onChange={e => setPowerBoost(Number(e.target.value))}
            className="w-full accent-orange-500" />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">
            Mass change: <span className={`font-medium ${massChange < 0 ? 'text-green-400' : massChange > 0 ? 'text-red-400' : 'text-white'}`}>
              {massChange > 0 ? `+${massChange}` : massChange} kg
            </span>
          </label>
          <input type="range" min={-15} max={15} value={massChange}
            onChange={e => setMassChange(Number(e.target.value))}
            className="w-full accent-orange-500" />
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-950 rounded-xl p-5 text-center border border-gray-800">
            <p className="text-xs text-gray-400 mb-1">Quarter-Mile ET</p>
            <p className="text-4xl font-bold text-orange-400">{result.et_quarter_s.toFixed(3)}s</p>
          </div>
          <div className="bg-gray-950 rounded-xl p-5 text-center border border-gray-800">
            <p className="text-xs text-gray-400 mb-1">Trap Speed</p>
            <p className="text-4xl font-bold text-white">{result.trap_speed_kmh.toFixed(1)}</p>
            <p className="text-xs text-gray-500 mt-1">km/h</p>
          </div>
          <div className="col-span-2 bg-gray-950 rounded-xl p-4 border border-gray-800">
            <p className="text-xs text-gray-400 mb-3">Splits</p>
            <div className="grid grid-cols-4 gap-2 text-center">
              {[
                { label: '60 ft',  val: result.et_60ft_s },
                { label: '⅛ mile', val: result.et_eighth_s },
                { label: 'Bike',   val: null, text: result.bike_name?.split(' ').slice(-2).join(' ') || selected?.model },
                { label: 'Power',  val: null, text: `${result.peak_power_hp?.toFixed(0) || '—'} hp` },
              ].map(s => (
                <div key={s.label}>
                  <p className="text-xs text-gray-500 mb-1">{s.label}</p>
                  <p className="text-sm font-semibold text-white">
                    {s.val != null ? `${s.val.toFixed(3)}s` : s.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <p className="text-xs text-gray-600 text-center mt-4">
        First-principles RK4 physics · 15 sub-models · 1 ms timestep · updates live as you adjust
      </p>
    </div>
  );
}
