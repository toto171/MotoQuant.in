'use client';

import { useState } from 'react';
import { Zap } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://web-production-de6eb.up.railway.app';

const BIKES = [
  { id: 'gsxr1000_k5',   label: 'Suzuki GSX-R 1000 K5',   cc: '999cc',  hp: 178 },
  { id: 'yzfr1_4c8',     label: 'Yamaha YZF-R1 (4C8)',     cc: '998cc',  hp: 180 },
  { id: 'hayabusa_gen1', label: 'Suzuki Hayabusa Gen1',     cc: '1299cc', hp: 175 },
];

export default function SimulatorWidget() {
  const [bike,        setBike]        = useState('gsxr1000_k5');
  const [riderKg,     setRiderKg]     = useState(75);
  const [powerBoost,  setPowerBoost]  = useState(0);
  const [massChange,  setMassChange]  = useState(0);
  const [result,      setResult]      = useState(null);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState(null);

  async function runSim() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/api/simulate/quick`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          bike_preset:     bike,
          rider_mass_kg:   riderKg,
          power_boost_pct: powerBoost,
          mass_delta_kg:   massChange,
        }),
      });
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`API error ${res.status}: ${msg}`);
      }
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const selectedBike = BIKES.find(b => b.id === bike);

  return (
    <div className="bg-black border border-gray-800 rounded-2xl p-8 max-w-2xl mx-auto">
      <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
        <Zap className="text-orange-500" size={20} />
        Live Quarter-Mile Simulator
      </h3>

      {/* Bike select */}
      <div className="mb-5">
        <label className="block text-sm text-gray-400 mb-2">Bike</label>
        <div className="grid grid-cols-3 gap-2">
          {BIKES.map(b => (
            <button
              key={b.id}
              onClick={() => setBike(b.id)}
              className={`p-3 rounded-lg border text-left text-xs transition-colors ${
                bike === b.id
                  ? 'border-orange-500 bg-orange-500/10 text-orange-300'
                  : 'border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              <div className="font-semibold text-sm leading-tight">{b.label.split(' ').slice(1).join(' ')}</div>
              <div className="text-gray-500 mt-1">{b.cc} · {b.hp} hp</div>
            </button>
          ))}
        </div>
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

      {/* Run button */}
      <button
        onClick={runSim}
        disabled={loading}
        className="w-full py-3 bg-orange-600 hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-semibold text-white transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Simulating…
          </>
        ) : (
          <><Zap size={16} /> Run Simulation</>
        )}
      </button>

      {/* Error */}
      {error && (
        <div className="mt-4 p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="mt-6 grid grid-cols-2 gap-4 animate-in fade-in duration-500">
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
                { label: 'Bike',   val: null, text: result.bike_name?.split(' ').slice(-2).join(' ') },
                { label: 'Power',  val: null, text: `${result.peak_power_hp.toFixed(0)} hp` },
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
        First-principles RK4 physics · 15 sub-models · 1 ms timestep
      </p>
    </div>
  );
}
