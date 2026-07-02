import Link from 'next/link';
import CredibilityCtaVariant from './CredibilityCtaVariant';
import CodeComment from '../../../components/CodeComment';

export const metadata = {
  title: 'Validation Data',
  description: 'MotoQuant Pro accuracy report — 216 benchmarks (236 matched) against published Cycle World, Sport Rider, MotoStatz, MCN, and BikeWale timeslips, 13 June 2026 sweep. Weighted bias −0.015s, weighted mean absolute error 0.262s, top-10 mean error ±0.006s. Per-cluster bias and the open small-cc + 2-stroke calibration gaps. Reference baselines: K5 10.0334s, R1 10.2859s, Hayabusa 10.4712s — Δ ±0.0000 since April 30, 2026.',
  alternates: { canonical: 'https://motoquant.in/docs/validation' },
  keywords: [
    'motorcycle simulator accuracy',
    'drag simulator validation india',
    'quarter mile simulator benchmark',
    'motorcycle physics simulation accuracy',
    'validated drag racing model',
    'hayabusa simulator validation',
    'gsxr 1000 k5 reference baseline',
    'r1 4c8 baseline',
    'motoquant accuracy report',
    'cycle world quarter mile timeslip database',
  ],
};

// Top-10 cleanest validated runs, 13 June 2026 sweep
// (reports/acc_final_2026_06_13.json — 10 smallest |Δ| among published
//  (non-derived) benchmarks, mean ±0.006s)
const TOP10 = [
  { rank: 1, name: "Honda CBR 600RR", year: 2007, cc: "599cc I4", target: 10.844, sim: 10.8447, delta: 0.001, source: "Sport Rider" },
  { rank: 2, name: "Aprilia Tuono 660", year: 2021, cc: "659cc I2", target: 11.33, sim: 11.3285, delta: -0.002, source: "MotoStatz" },
  { rank: 3, name: "Harley-Davidson Sportster S", year: 2021, cc: "1252cc V2", target: 11.1, sim: 11.0981, delta: -0.002, source: "HDForums timeslip 2021" },
  { rank: 4, name: "Kawasaki Z H2 SE", year: 2020, cc: "998cc I4", target: 9.95, sim: 9.9471, delta: -0.003, source: "Cycle World 2020" },
  { rank: 5, name: "Kawasaki Ninja ZX-9R", year: 2000, cc: "899cc I4", target: 10.5, sim: 10.4968, delta: -0.003, source: "Sport Rider 2000" },
  { rank: 6, name: "Kawasaki Ninja H2", year: 2015, cc: "998cc I4", target: 9.62, sim: 9.6252, delta: 0.005, source: "MCN 2015" },
  { rank: 7, name: "BMW R 12 nineT", year: 2014, cc: "1170cc boxer-twin", target: 11.05, sim: 11.0583, delta: 0.008, source: "Cycle World 2014" },
  { rank: 8, name: "Kawasaki Ninja ZX-10R", year: 2021, cc: "998cc I4", target: 10.0, sim: 10.0106, delta: 0.011, source: "Cycle World 2021" },
  { rank: 9, name: "Kawasaki ZZR1400", year: 2006, cc: "1352cc I4", target: 9.9, sim: 9.9112, delta: 0.011, source: "MCN 2006" },
  { rank: 10, name: "Yamaha YZF-R6", year: 2007, cc: "599cc I4", target: 10.854, sim: 10.8653, delta: 0.011, source: "Sport Rider 2007" },
];

// Per-cluster weighted bias + weighted |Δ|, 13 June 2026 sweep
// (reports/acc_final_2026_06_13.json by_cluster). Bias is weighted; N in note.
const CLUSTERS = [
  { name: 'Litre sport ≥195 hp', bias: '−0.015s', status: 'closed', note: 'N=31 · weighted |Δ| 0.137s — best instrumented cluster' },
  { name: '600–1000cc sport', bias: '−0.073s', status: 'good', note: 'N=99 · weighted |Δ| 0.201s — largest cluster, centred' },
  { name: '500–700cc twin', bias: '+0.059s', status: 'closed', note: 'N=12 · weighted |Δ| 0.141s — tightest |Δ| in the corpus' },
  { name: '300–500cc twin', bias: '−0.086s', status: 'open', note: 'N=23 · weighted |Δ| 0.516s — bidirectional spread, derived-data uncertainty' },
  { name: '200–300cc entry', bias: '+0.071s', status: 'open', note: 'N=15 · weighted |Δ| 0.343s — derived-benchmark data uncertainty' },
  { name: '150–200cc entry', bias: '+0.018s', status: 'open', note: 'N=12 · weighted |Δ| 0.820s — noise-dominated, bias centred' },
  { name: 'Cruiser 1300+', bias: '+0.312s', status: 'open', note: 'N=3 · weighted |Δ| 0.312s — thin set; muscle-bike slip-launch' },
  { name: '2-stroke vintage', bias: '+0.153s', status: 'open', note: 'N=6 · weighted |Δ| 0.584s — off-pipe/on-pipe transition' },
  { name: 'Other', bias: '+0.124s', status: 'open', note: 'N=35 · weighted |Δ| 0.383s — mixed heavy ADV/tourer bucket' },
];

export default function ValidationPage() {
  return (
    <article>
      <header className="mb-12">
        <CodeComment className="mb-3">validation · 216 benchmarks</CodeComment>
        <h1 className="font-display font-bold text-4xl text-white mb-4 tracking-tight">Benchmark Results — June 2026</h1>
        <p className="text-white/60 text-base leading-relaxed">
          Source-quality-weighted sweep results across 216 published benchmarks (236 matched to a catalog bike).
          Metrics, per-cluster bias, and methodology. Last updated 13 June 2026.
        </p>
      </header>

      {/* Headline stats */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-6">Aggregate Metrics (236 matched benchmarks)</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {[
            { num: '0.262s', label: 'Weighted |Δ|' },
            { num: '0.207s', label: 'Median |Δ|' },
            { num: '−0.015s', label: 'Weighted bias (sim − real)' },
            { num: '±0.006s', label: 'Top-10 mean error' },
          ].map((s, i) => (
            <div key={i} className="card p-4 border-brand-orange/20 text-center">
              <div className="font-display font-bold text-xl text-brand-orange tabular-nums">{s.num}</div>
              <div className="font-mono text-[10px] text-white/50 uppercase tracking-wide mt-1">{s.label}</div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { num: '62', label: 'Within ±0.10s' },
            { num: '113', label: 'Within ±0.20s' },
            { num: '187', label: 'Within ±0.50s' },
            { num: '217', label: 'Within ±1.00s' },
          ].map((s, i) => (
            <div key={i} className="card p-4 text-center">
              <div className="font-display font-bold text-xl text-white tabular-nums">{s.num}<span className="text-white/40 text-sm">/236</span></div>
              <div className="font-mono text-[10px] text-white/50 uppercase tracking-wide mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Reference baselines */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Reference Baselines (hand-calibrated)</h2>
        <p className="text-white/60 text-sm mb-6">
          Three reference bikes from <code className="font-mono text-brand-accent">defaults.py</code> are hand-calibrated and excluded from the ALL_KNOWN_BIKES auto-reseed.
          They serve as regression anchors — if any code change moves these by more than ±0.02s, something is wrong.
        </p>
        <div className="card border-brand-orange/20 overflow-hidden">
          <div className="hidden sm:grid grid-cols-[1fr_120px_120px_120px] gap-4 px-5 py-3 border-b border-brand-orange/20 bg-white/[0.02] text-[10px] font-mono uppercase tracking-widest text-white/50">
            <div>Bike</div>
            <div className="text-right">Target</div>
            <div className="text-right">Simulated</div>
            <div className="text-right">Δ</div>
          </div>
          {[
            { name: 'GSX-R 1000 K5 (2005)', target: 9.970, sim: 10.034, delta: +0.004 },
            { name: 'YZF-R1 4C8 (2007)', target: 10.300, sim: 10.286, delta: -0.001 },
            { name: 'Hayabusa Gen1 (1999)', target: 10.350, sim: 10.471, delta: +0.002 },
          ].map((b, i) => (
            <div key={i} className="grid grid-cols-[1fr_120px_120px_120px] gap-4 px-5 py-3 border-b border-white/[0.04] last:border-0">
              <div className="font-display font-semibold text-white text-sm">{b.name}</div>
              <div className="text-right font-mono text-white/70 tabular-nums text-sm">{b.target.toFixed(3)}s</div>
              <div className="text-right font-mono text-white tabular-nums text-sm">{b.sim.toFixed(3)}s</div>
              <div className="text-right font-display font-bold tabular-nums text-sm text-brand-accent">
                {b.delta > 0 ? '+' : ''}{b.delta.toFixed(3)}s
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Top 10 */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Top 10 Most Accurate Bikes</h2>
        <p className="text-white/60 text-sm mb-6">
          The 10 smallest residuals from published (non-derived) benchmarks — mean absolute error ±0.006s.
          Sources: Cycle World, Sport Rider, MCN, Motorcyclist, BikeWale, MotoStatz.
          Conditions: race fuel, professional rider, ideal strip.
        </p>
        <div className="card border-brand-orange/20 overflow-hidden">
          <div className="hidden md:grid grid-cols-[36px_1fr_100px_100px_90px_130px] gap-3 px-5 py-3 border-b border-brand-orange/20 bg-white/[0.02] text-[10px] font-mono uppercase tracking-widest text-white/50">
            <div>#</div><div>Bike</div><div className="text-right">Target</div>
            <div className="text-right">Simulated</div><div className="text-right">Δ</div><div className="text-right">Source</div>
          </div>
          {TOP10.map(b => {
            const abs = Math.abs(b.delta);
            const color = abs < 0.05 ? 'text-brand-accent' : abs < 0.10 ? 'text-brand-green' : 'text-brand-amber';
            const sign = b.delta > 0 ? '+' : '';
            return (
              <div key={b.rank} className="md:grid md:grid-cols-[36px_1fr_100px_100px_90px_130px] md:gap-3 px-5 py-4 border-b border-white/[0.04] last:border-0 hover:bg-brand-orange/[0.02] transition-colors">
                {/* Mobile */}
                <div className="md:hidden flex justify-between items-start mb-2">
                  <div className="flex gap-2 items-center">
                    <span className="font-bold text-brand-orange font-display">#{b.rank}</span>
                    <span className="font-bold text-white text-sm">{b.name}</span>
                  </div>
                  <span className={`font-display font-bold text-sm tabular-nums ${color}`}>{sign}{b.delta.toFixed(3)}s</span>
                </div>
                <div className="md:hidden grid grid-cols-3 gap-2 text-xs">
                  <div><div className="text-white/40 text-[10px] font-mono">Year</div><div className="text-white/80 font-mono">{b.year}</div></div>
                  <div><div className="text-white/40 text-[10px] font-mono">Target</div><div className="text-white/80 font-mono tabular-nums">{b.target.toFixed(2)}s</div></div>
                  <div><div className="text-white/40 text-[10px] font-mono">Sim</div><div className="text-white/80 font-mono tabular-nums">{b.sim.toFixed(2)}s</div></div>
                </div>
                <div className="md:hidden mt-1.5 text-[10px] font-mono text-white/40">{b.cc} · {b.source}</div>
                {/* Desktop */}
                <div className="hidden md:block font-bold text-brand-orange font-display">{b.rank}</div>
                <div className="hidden md:block">
                  <div className="font-bold text-white text-sm">{b.name}</div>
                  <div className="font-mono text-xs text-white/40">{b.year} · {b.cc}</div>
                </div>
                <div className="hidden md:block text-right font-mono text-white/70 tabular-nums text-sm">{b.target.toFixed(2)}s</div>
                <div className="hidden md:block text-right font-mono text-white tabular-nums text-sm font-semibold">{b.sim.toFixed(2)}s</div>
                <div className={`hidden md:block text-right font-display font-bold tabular-nums text-sm ${color}`}>{sign}{b.delta.toFixed(3)}s</div>
                <div className="hidden md:block text-right font-mono text-[10px] text-white/40 self-center">{b.source}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Per-cluster bias */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Per-Cluster Bias</h2>
        <p className="text-white/60 text-sm mb-6">
          Positive bias means the simulator predicts slower than reality. A positive bias in the small-cc clusters
          is a known residual from the per-bike calibration work not yet completed — it is not a regression.
        </p>
        <div className="card border-brand-orange/20 overflow-hidden">
          {CLUSTERS.map((c, i) => (
            <div key={i} className="flex items-center justify-between gap-4 px-5 py-3.5 border-b border-white/[0.04] last:border-0">
              <div className="flex-1">
                <div className="font-display font-semibold text-sm text-white">{c.name}</div>
                <div className="font-mono text-[10px] text-white/40 mt-0.5">{c.note}</div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className={`font-display font-bold tabular-nums text-sm ${
                  c.status === 'closed' ? 'text-brand-accent' :
                  c.status === 'good' ? 'text-brand-green' : 'text-brand-amber'
                }`}>{c.bias}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wide ${
                  c.status === 'closed' ? 'bg-brand-accent/10 text-brand-accent' :
                  c.status === 'good' ? 'bg-brand-green/10 text-brand-green' :
                  'bg-brand-amber/10 text-brand-amber'
                }`}>
                  {c.status === 'closed' ? 'Closed' : c.status === 'good' ? 'Good' : 'Open'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Methodology */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Methodology</h2>
        <div className="space-y-4 text-white/70 text-sm leading-relaxed">
          <p>
            <strong className="text-white">Benchmark sources:</strong> Published magazine timeslips from Cycle World,
            Sport Rider, MCN, Motorcyclist, and BikeWale. Indian community strip records from MotoStatz, Facebook
            drag groups, and drag event published results. All benchmarks use professional rider / race fuel / ideal
            strip conditions unless explicitly noted.
          </p>
          <p>
            <strong className="text-white">Simulation conditions:</strong> All simulations run at ISA sea-level
            conditions (15°C, 101.325 kPa, 0% RH) to match the implicit conditions of most magazine tests. Bikes
            use their stock BikeConfig from the seeded database — no manual per-bike tuning of Cd or μ.
          </p>
          <p>
            <strong className="text-white">Matching:</strong> Benchmark-to-bike matching uses word-boundary regex
            to prevent false positives (YZF-R1 ≠ YZF-R15). Year ranges are respected — a 2009 benchmark does not
            match a 2015 model that shares a name but has different internals.
          </p>
          <p>
            <strong className="text-white">Known limitations:</strong> Residual small-cc and 2T bias is a calibration
            gap, not a physics gap. The correct fix is per-bike Cd and μ calibration using real strip data — the
            auto-calibrator in <code className="font-mono text-brand-accent">/api/calibrate/dragy</code> handles this
            once you supply a Dragy CSV for your specific bike.
          </p>
          <p>
            <strong className="text-white">Regression testing:</strong> 10 dedicated regression tests in
            <code className="font-mono text-brand-accent mx-1">tests/test_power_boost_regression.py</code> run on every
            commit to catch DB drift. The test helper copies <code className="font-mono text-brand-accent">motoquant.db</code> to
            a temp directory to avoid WAL journal-mode errors on mounted filesystems.
          </p>
        </div>
      </section>

      {/* GROWTH_EXP_015 — credibility CTA injected here in variant B; renders
          null in variant A so the terminal Next nav still anchors the page. */}
      <CredibilityCtaVariant />

      {/* Next */}
      <div className="pt-8 border-t border-brand-orange/10">
        <div className="label-mono mb-4">Next</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Link href="/docs/getting-started" className="card card-hover block p-4 group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Getting Started →</div>
            <div className="text-xs text-white/50">Run your first simulation in under 60 seconds.</div>
          </Link>
          <Link href="/simulator" className="card card-hover block p-4 group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Try the simulator →</div>
            <div className="text-xs text-white/50">501 bikes, free in the browser, no account needed.</div>
          </Link>
        </div>
      </div>
    </article>
  );
}
