'use client';

import { useState } from 'react';
import { Zap, Clock } from 'lucide-react';

const BIKES = [
  { id: 'gsxr1000_k5',   label: 'Suzuki GSX-R 1000 K5', cc: '999cc',   hp: 178 },
  { id: 'yzfr1_4c8',     label: 'Yamaha YZF-R1 (4C8)',  cc: '998cc',   hp: 180 },
  { id: 'hayabusa_gen1', label: 'Suzuki Hayabusa Gen1',  cc: '1299cc',  hp: 175 },
];

export default function SimulatorWidget() {
  const [bike,       setBike]       = useState('gsxr1000_k5');
  const [riderKg,    setRiderKg]    = useState(75);
  const [powerBoost, setPowerBoost] = useState(0);
  const [massChange, setMassChange] = useState(0);

  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/8 rounded-2xl p-8 max-w-2xl mx-auto">
      <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-white/80">
        <Zap className="text-orange-500" size={18} />
        Quarter-Mile Simulator
        <span className="ml-auto inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-orange-500/10 border border-orange-500/25 text-orange-400 text-xs font-medium">
          <Clock size={11} /> API Launching Soon
        </span>
      </h3>

      {/* Bike selector */}
      <div className="mb-5">
        <label className="block text-xs text-white/40 mb-2 uppercase tracking-wide">Select Bike</label>
        <div className="grid grid-cols-3 gap-2">
          {BIKES.map(b => (
            <button
              key={b.id}
              onClick={() => setBike(b.id)}
              className={`p-3 rounded-xl border text-left text-xs transition-colors ${
                bike === b.id
                  ? 'border-orange-500/60 bg-orange-500/10 text-orange-300'
                  : 'border-white/8 text-white/50 hover:border-white/20 hover:text-white/70'
              }`}
            >
              <div className="font-semibold leading-tight">{b.label.split(' ').slice(1).join(' ')}</div>
              <div className="text-white/30 mt-1">{b.cc} · {b.hp} hp</div>
            </button>
          ))}
        </div>
      </div>

      {/* Sliders */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div>
          <label className="block text-xs text-white/40 mb-1.5">
            Rider weight: <span className="text-white/70 font-medium">{riderKg} kg</span>
          </label>
          <input type="range" min={50} max={130} value={riderKg}
            onChange={e => setRiderKg(Number(e.target.value))}
            className="w-full accent-orange-500 opacity-60" />
        </div>
        <div>
          <label className="block text-xs text-white/40 mb-1.5">
            Power boost: <span className={`font-medium ${powerBoost > 0 ? 'text-green-400' : 'text-white/70'}`}>
              {powerBoost > 0 ? `+${powerBoost}%` : `${powerBoost}%`}
            </span>
          </label>
          <input type="range" min={-10} max={30} value={powerBoost}
            onChange={e => setPowerBoost(Number(e.target.value))}
            className="w-full accent-orange-500 opacity-60" />
        </div>
        <div>
          <label className="block text-xs text-white/40 mb-1.5">
            Mass change: <span className={`font-medium ${massChange < 0 ? 'text-green-400' : massChange > 0 ? 'text-red-400' : 'text-white/70'}`}>
              {massChange > 0 ? `+${massChange}` : massChange} kg
            </span>
          </label>
          <input type="range" min={-15} max={15} value={massChange}
            onChange={e => setMassChange(Number(e.target.value))}
            className="w-full accent-orange-500 opacity-60" />
        </div>
      </div>

      {/* Coming soon button */}
      <div className="w-full py-3.5 bg-white/5 border border-white/10 rounded-xl flex items-center justify-center gap-2 text-white/35 text-sm cursor-not-allowed select-none">
        <Clock size={15} />
        Simulation API launching soon
      </div>

      {/* Sample output preview */}
      <div className="mt-5 grid grid-cols-2 gap-3 opacity-30 pointer-events-none select-none">
        <div className="bg-white/5 border border-white/8 rounded-xl p-4 text-center">
          <p className="text-xs text-white/40 mb-1">Quarter-Mile ET</p>
          <p className="text-3xl font-bold text-orange-400">10.039s</p>
          <p className="text-xs text-white/20 mt-1">example output</p>
        </div>
        <div className="bg-white/5 border border-white/8 rounded-xl p-4 text-center">
          <p className="text-xs text-white/40 mb-1">Trap Speed</p>
          <p className="text-3xl font-bold text-white">239.8</p>
          <p className="text-xs text-white/30 mt-1">km/h</p>
        </div>
      </div>

      <p className="text-xs text-white/20 text-center mt-4">
        First-principles RK4 physics · 15 sub-models · 1 ms timestep
      </p>
    </div>
  );
}
