'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Zap, Search, ChevronDown, ChevronRight, X, MapPin, Gauge, Wrench, CircleDot, TrendingDown, IndianRupee, ArrowLeft } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'https://web-production-de6eb.up.railway.app';

// ─── Searchable Dropdown ─────────────────────────────────────────────────
function Dropdown({ label, items, selected, onSelect, renderItem, renderSelected, searchKey, groupKey, emptyMsg }) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const filtered = items.filter(i => {
    if (!q) return true;
    return searchKey(i).toLowerCase().includes(q.toLowerCase());
  });

  const grouped = groupKey ? {} : null;
  if (grouped) {
    filtered.forEach(i => {
      const g = groupKey(i);
      if (!grouped[g]) grouped[g] = [];
      grouped[g].push(i);
    });
  }

  return (
    <div className="relative" ref={ref}>
      <label className="block text-xs text-gray-500 mb-1 uppercase tracking-wider">{label}</label>
      <button onClick={() => setOpen(!open)}
        className="w-full p-2.5 rounded-lg border border-gray-800 bg-gray-950 text-left flex items-center justify-between hover:border-gray-600 transition-colors text-sm">
        {selected ? renderSelected(selected) : <span className="text-gray-600">Select...</span>}
        <ChevronDown size={14} className={`text-gray-600 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-gray-950 border border-gray-700 rounded-lg shadow-2xl max-h-72 overflow-hidden">
          <div className="p-2 border-b border-gray-800">
            <div className="relative">
              <Search size={12} className="absolute left-2 top-2.5 text-gray-600" />
              <input type="text" value={q} onChange={e => setQ(e.target.value)} placeholder="Search..."
                className="w-full pl-7 pr-3 py-1.5 bg-black border border-gray-800 rounded text-xs text-white placeholder-gray-700 focus:outline-none focus:border-orange-500" autoFocus />
            </div>
          </div>
          <div className="overflow-y-auto max-h-56">
            {grouped ? Object.keys(grouped).sort().map(g => (
              <div key={g}>
                <div className="px-3 py-1 text-[10px] text-gray-600 font-semibold uppercase tracking-wider bg-gray-900/50 sticky top-0">{g}</div>
                {grouped[g].map((item, i) => (
                  <button key={i} onClick={() => { onSelect(item); setOpen(false); setQ(''); }}
                    className="w-full px-3 py-2 text-left text-xs hover:bg-gray-800 transition-colors text-gray-300">
                    {renderItem(item)}
                  </button>
                ))}
              </div>
            )) : filtered.map((item, i) => (
              <button key={i} onClick={() => { onSelect(item); setOpen(false); setQ(''); }}
                className="w-full px-3 py-2 text-left text-xs hover:bg-gray-800 transition-colors text-gray-300">
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

// ─── Part Chip ───────────────────────────────────────────────────────────
function PartChip({ part, onRemove }) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-orange-500/10 border border-orange-500/30 rounded-full text-xs text-orange-300">
      <span className="font-medium">{part.brand} {part.model_name}</span>
      {part.price_inr && <span className="text-orange-500/60">₹{(part.price_inr / 1000).toFixed(1)}k</span>}
      <button onClick={onRemove} className="ml-0.5 hover:text-white transition-colors"><X size={12} /></button>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────
export default function SimulatorPage() {
  // Data from API
  const [bikes, setBikes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [allParts, setAllParts] = useState([]);
  const [allTires, setAllTires] = useState([]);
  const [venues, setVenues] = useState([]);
  const [loading, setLoading] = useState(true);

  // User selections
  const [bike, setBike] = useState(null);
  const [selectedParts, setSelectedParts] = useState([]);
  const [frontTire, setFrontTire] = useState(null);
  const [rearTire, setRearTire] = useState(null);
  const [venue, setVenue] = useState(null);
  const [riderKg, setRiderKg] = useState(75);
  const [powerBoost, setPowerBoost] = useState(0);
  const [massChange, setMassChange] = useState(0);

  // Simulation
  const [result, setResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [simError, setSimError] = useState(null);
  const [activeCategory, setActiveCategory] = useState(null);
  const debounceRef = useRef(null);
  const abortRef = useRef(null);

  // Fetch all data on mount
  useEffect(() => {
    async function load() {
      try {
        const [bikesRes, catsRes, partsRes, tiresRes, venuesRes] = await Promise.all([
          fetch(`${API}/api/bikes?limit=200`),
          fetch(`${API}/api/parts/categories`),
          fetch(`${API}/api/parts?limit=200`),
          fetch(`${API}/api/tires?limit=200`),
          fetch(`${API}/api/venues`),
        ]);
        const [bikesData, catsData, partsData, tiresData, venuesData] = await Promise.all([
          bikesRes.ok ? bikesRes.json() : { bikes: [] },
          catsRes.ok ? catsRes.json() : { categories: [] },
          partsRes.ok ? partsRes.json() : { parts: [] },
          tiresRes.ok ? tiresRes.json() : { tires: [] },
          venuesRes.ok ? venuesRes.json() : { venues: [] },
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

  // Auto-simulate on any change
  const runSim = useCallback(async () => {
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
  }, [bike, selectedParts, frontTire, rearTire, venue, riderKg, powerBoost, massChange]);

  useEffect(() => {
    if (!bike) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(runSim, 400);
    return () => clearTimeout(debounceRef.current);
  }, [runSim]);

  // Computed
  const buildCost = selectedParts.reduce((s, p) => s + (p.price_inr || 0), 0);
  const partsForCategory = activeCategory
    ? allParts.filter(p => p.category_id === activeCategory.id)
    : [];
  const isPartSelected = (p) => selectedParts.some(s => s.id === p.id);

  function togglePart(part) {
    if (isPartSelected(part)) {
      setSelectedParts(prev => prev.filter(p => p.id !== part.id));
    } else {
      setSelectedParts(prev => [...prev, part]);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-8 w-8 text-orange-500 mx-auto mb-4" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
          </svg>
          <p className="text-gray-400">Loading MotoQuant Pro...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <nav className="border-b border-gray-800 sticky top-0 bg-black/95 backdrop-blur z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <a href="/" className="text-gray-500 hover:text-white transition-colors"><ArrowLeft size={18} /></a>
            <div className="text-xl font-bold tracking-tight">
              <span className="text-orange-500">Moto</span>Quant Pro
              <span className="text-xs text-gray-600 ml-2 font-normal">Simulator</span>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-500">
            {simLoading && (
              <div className="flex items-center gap-1.5 text-orange-400">
                <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                Simulating...
              </div>
            )}
            <span>{bikes.length} bikes</span>
            <span>·</span>
            <span>{allParts.length} parts</span>
            <span>·</span>
            <span>{allTires.length} tires</span>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6">

          {/* ─── LEFT PANEL: Config ─── */}
          <div className="col-span-12 lg:col-span-4 space-y-4">

            {/* Bike Selector */}
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Gauge size={14} className="text-orange-500" /> Bike
              </h3>
              <Dropdown
                label=""
                items={bikes}
                selected={bike}
                onSelect={b => { setBike(b); setSelectedParts([]); setFrontTire(null); setRearTire(null); }}
                searchKey={b => `${b.manufacturer} ${b.model} ${b.year} ${b.category || ''}`}
                groupKey={b => b.manufacturer || 'Other'}
                renderItem={b => (
                  <div className="flex justify-between items-center w-full">
                    <span>{b.model} {b.year ? `(${b.year})` : ''}</span>
                    <span className="text-[10px] text-gray-600">{b.displacement_cc}cc · {b.peak_power_hp ? `${Math.round(b.peak_power_hp)}hp` : ''}</span>
                  </div>
                )}
                renderSelected={b => (
                  <span className="text-white text-xs"><span className="text-orange-400">{b.manufacturer}</span> {b.model} <span className="text-gray-500">({b.displacement_cc}cc)</span></span>
                )}
                emptyMsg="No bikes found"
              />
            </div>

            {/* Rider & Tuning Sliders */}
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold mb-3">Rider & Quick Tune</h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-500">Rider weight</span>
                    <span className="text-white font-medium">{riderKg} kg</span>
                  </div>
                  <input type="range" min={50} max={130} value={riderKg}
                    onChange={e => setRiderKg(Number(e.target.value))} className="w-full accent-orange-500 h-1.5" />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-500">Power adjustment</span>
                    <span className={`font-medium ${powerBoost > 0 ? 'text-green-400' : powerBoost < 0 ? 'text-red-400' : 'text-white'}`}>
                      {powerBoost > 0 ? '+' : ''}{powerBoost}%
                    </span>
                  </div>
                  <input type="range" min={-20} max={50} value={powerBoost}
                    onChange={e => setPowerBoost(Number(e.target.value))} className="w-full accent-orange-500 h-1.5" />
                </div>
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-gray-500">Mass change</span>
                    <span className={`font-medium ${massChange < 0 ? 'text-green-400' : massChange > 0 ? 'text-red-400' : 'text-white'}`}>
                      {massChange > 0 ? '+' : ''}{massChange} kg
                    </span>
                  </div>
                  <input type="range" min={-30} max={30} value={massChange}
                    onChange={e => setMassChange(Number(e.target.value))} className="w-full accent-orange-500 h-1.5" />
                </div>
              </div>
            </div>

            {/* Venue Selector */}
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <MapPin size={14} className="text-orange-500" /> Venue
              </h3>
              <Dropdown
                label=""
                items={[{ id: null, name: 'Standard Conditions (ISA)', country: 'Default' }, ...venues]}
                selected={venue || { id: null, name: 'Standard Conditions (ISA)', country: 'Default' }}
                onSelect={v => setVenue(v.id ? v : null)}
                searchKey={v => `${v.name} ${v.country || ''}`}
                groupKey={v => v.country || 'Default'}
                renderItem={v => (
                  <div className="flex justify-between items-center w-full">
                    <span>{v.name}</span>
                    {v.altitude_m && <span className="text-[10px] text-gray-600">{v.altitude_m}m alt</span>}
                  </div>
                )}
                renderSelected={v => <span className="text-white text-xs">{v.name}</span>}
                emptyMsg="No venues found"
              />
            </div>

            {/* Tire Selector */}
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <CircleDot size={14} className="text-orange-500" /> Tires
              </h3>
              <div className="space-y-2">
                <Dropdown
                  label="Front"
                  items={[{ id: null, manufacturer: 'Stock', model: 'OEM Default' }, ...allTires]}
                  selected={frontTire || { id: null, manufacturer: 'Stock', model: 'OEM Default' }}
                  onSelect={t => setFrontTire(t.id ? t : null)}
                  searchKey={t => `${t.manufacturer} ${t.model} ${t.compound_type || ''}`}
                  groupKey={t => t.manufacturer || 'Stock'}
                  renderItem={t => (
                    <div className="flex justify-between items-center w-full">
                      <span>{t.model}</span>
                      <span className="text-[10px] text-gray-600">{t.compound_type || ''}</span>
                    </div>
                  )}
                  renderSelected={t => <span className="text-white text-xs">{t.manufacturer} {t.model}</span>}
                />
                <Dropdown
                  label="Rear"
                  items={[{ id: null, manufacturer: 'Stock', model: 'OEM Default' }, ...allTires]}
                  selected={rearTire || { id: null, manufacturer: 'Stock', model: 'OEM Default' }}
                  onSelect={t => setRearTire(t.id ? t : null)}
                  searchKey={t => `${t.manufacturer} ${t.model} ${t.compound_type || ''}`}
                  groupKey={t => t.manufacturer || 'Stock'}
                  renderItem={t => (
                    <div className="flex justify-between items-center w-full">
                      <span>{t.model}</span>
                      <span className="text-[10px] text-gray-600">{t.compound_type || ''}</span>
                    </div>
                  )}
                  renderSelected={t => <span className="text-white text-xs">{t.manufacturer} {t.model}</span>}
                />
              </div>
            </div>
          </div>

          {/* ─── CENTER PANEL: Parts Picker ─── */}
          <div className="col-span-12 lg:col-span-4">
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-4 h-full flex flex-col">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Wrench size={14} className="text-orange-500" /> Parts Catalog
                {selectedParts.length > 0 && (
                  <span className="ml-auto text-[10px] bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded-full">
                    {selectedParts.length} selected
                  </span>
                )}
              </h3>

              {/* Selected parts chips */}
              {selectedParts.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3 pb-3 border-b border-gray-800">
                  {selectedParts.map(p => (
                    <PartChip key={p.id} part={p} onRemove={() => setSelectedParts(prev => prev.filter(x => x.id !== p.id))} />
                  ))}
                </div>
              )}

              {/* Category list */}
              <div className="flex-1 overflow-y-auto space-y-0.5">
                {categories.map(cat => {
                  const catParts = allParts.filter(p => p.category_id === cat.id);
                  const isActive = activeCategory?.id === cat.id;
                  const selectedInCat = selectedParts.filter(p => p.category_id === cat.id).length;
                  return (
                    <div key={cat.id}>
                      <button
                        onClick={() => setActiveCategory(isActive ? null : cat)}
                        className={`w-full px-3 py-2 rounded-lg text-left text-xs flex items-center justify-between transition-colors ${
                          isActive ? 'bg-orange-500/10 text-orange-300 border border-orange-500/30' : 'hover:bg-gray-900 text-gray-400 border border-transparent'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <ChevronRight size={12} className={`transition-transform ${isActive ? 'rotate-90' : ''}`} />
                          <span className="font-medium">{cat.display_name || cat.name}</span>
                          <span className="text-[10px] text-gray-600">({catParts.length})</span>
                        </div>
                        {selectedInCat > 0 && (
                          <span className="text-[10px] bg-orange-500 text-black px-1.5 rounded-full font-bold">{selectedInCat}</span>
                        )}
                      </button>

                      {/* Expanded parts list */}
                      {isActive && (
                        <div className="ml-5 mt-1 mb-2 space-y-1">
                          {catParts.length === 0 ? (
                            <p className="text-[10px] text-gray-700 py-2">No parts in this category</p>
                          ) : catParts.map(part => {
                            const sel = isPartSelected(part);
                            return (
                              <button
                                key={part.id}
                                onClick={() => togglePart(part)}
                                className={`w-full px-3 py-2 rounded-lg text-left text-xs transition-colors border ${
                                  sel
                                    ? 'bg-orange-500/15 border-orange-500/40 text-orange-200'
                                    : 'border-gray-800 hover:border-gray-700 text-gray-400 hover:text-gray-300'
                                }`}
                              >
                                <div className="flex justify-between items-start">
                                  <div>
                                    <div className="font-medium text-[11px]">{part.brand} {part.model_name}</div>
                                    {part.fitment_notes && <div className="text-[10px] text-gray-600 mt-0.5">{part.fitment_notes}</div>}
                                  </div>
                                  <div className="text-right shrink-0 ml-2">
                                    {part.price_inr && (
                                      <div className="text-[10px] text-gray-500">
                                        <IndianRupee size={8} className="inline" />{part.price_inr.toLocaleString('en-IN')}
                                      </div>
                                    )}
                                    {sel && <div className="text-[10px] text-orange-400 mt-0.5">Selected</div>}
                                  </div>
                                </div>
                                {/* Show what the part does */}
                                {(part.param_deltas || part.param_multipliers) && (
                                  <div className="mt-1.5 flex flex-wrap gap-1">
                                    {part.param_deltas && typeof part.param_deltas === 'object' && Object.entries(part.param_deltas).map(([k, v]) => (
                                      <span key={k} className={`text-[9px] px-1.5 py-0.5 rounded ${v > 0 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                                        {k.split('.').pop()}: {v > 0 ? '+' : ''}{v}
                                      </span>
                                    ))}
                                    {part.param_multipliers && typeof part.param_multipliers === 'object' && Object.entries(part.param_multipliers).map(([k, v]) => (
                                      <span key={k} className={`text-[9px] px-1.5 py-0.5 rounded ${v > 1 ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                                        {k.split('.').pop()}: x{v}
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
            </div>
          </div>

          {/* ─── RIGHT PANEL: Results ─── */}
          <div className="col-span-12 lg:col-span-4 space-y-4">

            {/* Primary Results */}
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <Zap size={14} className="text-orange-500" /> Results
              </h3>

              {simError && (
                <div className="p-2.5 bg-red-900/20 border border-red-700/30 rounded-lg text-red-400 text-xs mb-3">{simError}</div>
              )}

              {result ? (
                <div className="space-y-3">
                  {/* ET + Trap Speed */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-black rounded-xl p-4 text-center border border-gray-800">
                      <p className="text-[10px] text-gray-500 mb-1 uppercase tracking-wider">Quarter-Mile ET</p>
                      <p className="text-3xl font-bold text-orange-400">{result.et_quarter_s?.toFixed(3) ?? '—'}<span className="text-lg">s</span></p>
                    </div>
                    <div className="bg-black rounded-xl p-4 text-center border border-gray-800">
                      <p className="text-[10px] text-gray-500 mb-1 uppercase tracking-wider">Trap Speed</p>
                      <p className="text-3xl font-bold text-white">{result.trap_speed_kmh?.toFixed(1) ?? '—'}</p>
                      <p className="text-[10px] text-gray-600">km/h</p>
                    </div>
                  </div>

                  {/* Stock vs Modified comparison */}
                  {result.stock_et_s && result.et_delta_s !== null && (
                    <div className={`p-3 rounded-lg border text-center ${
                      result.et_delta_s < 0
                        ? 'bg-green-500/5 border-green-500/30'
                        : result.et_delta_s > 0
                        ? 'bg-red-500/5 border-red-500/30'
                        : 'bg-gray-900 border-gray-800'
                    }`}>
                      <div className="flex items-center justify-center gap-4 text-xs">
                        <div>
                          <span className="text-gray-500">Stock: </span>
                          <span className="text-white font-medium">{result.stock_et_s.toFixed(3)}s</span>
                        </div>
                        <div className={`text-lg font-bold ${result.et_delta_s < 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {result.et_delta_s < 0 ? '' : '+'}{result.et_delta_s.toFixed(3)}s
                        </div>
                        <div>
                          <span className="text-gray-500">Modified: </span>
                          <span className="text-orange-400 font-medium">{result.et_quarter_s.toFixed(3)}s</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Splits */}
                  <div className="bg-black rounded-xl p-3 border border-gray-800">
                    <p className="text-[10px] text-gray-500 mb-2 uppercase tracking-wider">Splits</p>
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
                      <div className="flex justify-between"><span className="text-gray-500">60 ft</span><span className="text-white font-medium">{result.et_60ft_s?.toFixed(3) ?? '—'}s</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">1/8 mile</span><span className="text-white font-medium">{result.et_eighth_s?.toFixed(3) ?? '—'}s</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Power</span><span className="text-white font-medium">{result.peak_power_hp?.toFixed(0) ?? '—'} hp</span></div>
                      <div className="flex justify-between"><span className="text-gray-500">Total mass</span><span className="text-white font-medium">{result.total_mass_kg?.toFixed(0) ?? '—'} kg</span></div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-700 text-xs">
                  Select a bike to start simulating
                </div>
              )}
            </div>

            {/* Build Summary */}
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <IndianRupee size={14} className="text-orange-500" /> Build Summary
              </h3>

              {selectedParts.length > 0 ? (
                <div className="space-y-2">
                  {selectedParts.map(p => (
                    <div key={p.id} className="flex justify-between items-center text-xs py-1 border-b border-gray-800/50 last:border-0">
                      <span className="text-gray-400">{p.brand} {p.model_name}</span>
                      <span className="text-gray-500">{p.price_inr ? `₹${p.price_inr.toLocaleString('en-IN')}` : '—'}</span>
                    </div>
                  ))}
                  <div className="flex justify-between items-center text-xs pt-2 border-t border-gray-700">
                    <span className="text-white font-semibold">Total Build Cost</span>
                    <span className="text-orange-400 font-bold text-sm">₹{buildCost.toLocaleString('en-IN')}</span>
                  </div>
                  {result?.et_delta_s && result.et_delta_s < 0 && buildCost > 0 && (
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gray-500">Cost per tenth</span>
                      <span className="text-green-400 font-medium">
                        ₹{Math.round(buildCost / (Math.abs(result.et_delta_s) * 10)).toLocaleString('en-IN')}/tenth
                      </span>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-xs text-gray-700 text-center py-4">
                  Add parts from the catalog to build your setup
                </p>
              )}
            </div>

            {/* Quick Actions */}
            <div className="flex gap-2">
              <button
                onClick={() => { setSelectedParts([]); setFrontTire(null); setRearTire(null); setVenue(null); setPowerBoost(0); setMassChange(0); setRiderKg(75); }}
                className="flex-1 py-2 px-3 text-xs border border-gray-800 hover:border-gray-600 rounded-lg text-gray-400 hover:text-white transition-colors"
              >
                Reset All
              </button>
              <button
                onClick={runSim}
                className="flex-1 py-2 px-3 text-xs bg-orange-600 hover:bg-orange-700 rounded-lg text-white font-medium transition-colors flex items-center justify-center gap-1.5"
              >
                <Zap size={12} /> Re-run Simulation
              </button>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
