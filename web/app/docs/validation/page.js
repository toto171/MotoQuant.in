import Link from 'next/link';
import CredibilityCtaVariant from './CredibilityCtaVariant';
import CodeComment from '../../../components/CodeComment';

export const metadata = {
  title: 'Validation Data',
  description: 'MotoQuant Pro accuracy report — 74 bikes matched against published Cycle World, Sport Rider, MotoStatz, and BikeWale timeslips. Per-cluster bias and mean absolute error, full methodology, and the open small-cc + 2-stroke calibration gaps. Reference baselines: K5 10.0334s, R1 10.2859s, Hayabusa 10.4712s — Δ ±0.0000 since April 30, 2026.',
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

// Top-10 post-fix sweep data (Apr-24-PM)
const TOP10 = [
  { rank: 1, name: 'Kawasaki Ninja ZX-10R', year: 2021, cc: '998cc I4', target: 10.00, sim: 10.011, delta: 0.011, source: 'Cycle World 2021' },
  { rank: 2, name: 'Kawasaki Z 650', year: 2017, cc: '649cc I2', target: 12.40, sim: 12.412, delta: 0.012, source: 'MotoStatz 2017' },
  { rank: 3, name: 'Suzuki TL1000R', year: 1998, cc: '996cc V-twin', target: 10.50, sim: 10.518, delta: 0.018, source: 'Cycle World 1998' },
  { rank: 4, name: 'Honda CBR1000RR-R', year: 2020, cc: '999cc I4', target: 9.95, sim: 9.928, delta: -0.022, source: 'Cycle World 2020' },
  { rank: 5, name: 'Kawasaki Ninja ZX-9R', year: 2000, cc: '899cc I4', target: 10.50, sim: 10.526, delta: 0.026, source: 'Sport Rider 2000' },
  { rank: 6, name: 'Yamaha YZF-R1', year: 2009, cc: '998cc I4 CF', target: 10.20, sim: 10.172, delta: -0.028, source: 'Sport Rider 2009' },
  { rank: 7, name: 'BMW M1000RR', year: 2021, cc: '999cc I4', target: 9.80, sim: 9.837, delta: 0.037, source: 'Cycle World 2021' },
  { rank: 8, name: 'Ducati Streetfighter V4', year: 2020, cc: '1103cc V4', target: 10.10, sim: 10.143, delta: 0.043, source: 'Cycle World 2020' },
  { rank: 9, name: 'MV Agusta Brutale 1000 RR', year: 2019, cc: '998cc I4', target: 10.15, sim: 10.103, delta: -0.047, source: 'Cycle World 2019' },
  { rank: 10, name: 'TVS Apache RR 310', year: 2020, cc: '312cc I1', target: 15.46, sim: 15.537, delta: 0.077, source: 'BikeWale 2020' },
];

const CLUSTERS = [
  { name: 'Litre sport ≥195 hp', bias: '−0.11s', status: 'closed', note: 'Bias flipped; previously +0.25s slow' },
  { name: '600–1000cc sport', bias: '+0.15s', status: 'good', note: 'Closed from +0.23s pre-fix' },
  { name: '500–700cc twin', bias: '+0.16s', status: 'good', note: 'Closed from +0.64s; Z650 enters top-10' },
  { name: 'Hayabusa/ZX-14R 1300+', bias: '+0.21s', status: 'good', note: 'Closed from +0.46s' },
  { name: '300–500cc twin', bias: '+1.06s', status: 'open', note: 'Was +2.88s — 63% closure' },
  { name: '200–300cc entry', bias: '+2.53s', status: 'open', note: 'Per-bike calibration work pending' },
  { name: '150–200cc entry', bias: '+2.86s', status: 'open', note: 'Per-bike calibration work pending' },
  { name: '2-stroke vintage', bias: '+2.70s', status: 'open', note: 'Was +5.6s — 52% closure' },
];

export default function ValidationPage() {
  return (
    <article>
      <header className="mb-12">
        <CodeComment className="mb-3">validation · 156 benchmarks</CodeComment>
        <h1 className="font-display font-bold text-4xl text-white mb-4 tracking-tight">Benchmark Results — April 2026</h1>
        <p className="text-white/60 text-base leading-relaxed">
          Post-calibration sweep results across 74 matched benchmarks. Metrics, per-cluster bias, and methodology.
          Last updated 24 April 2026 (post-DB-reseed pass).
        </p>
      </header>

      {/* Headline stats */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-6">Aggregate Metrics (74 matched benchmarks)</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {[
            { num: '0.726s', label: 'Mean |Δ|' },
            { num: '0.240s', label: 'Median |Δ|' },
            { num: '+0.550s', label: 'Bias (sim − real)' },
            { num: '±0.032s', label: 'Top-10 mean error' },
          ].map((s, i) => (
            <div key={i} className="glass rounded-xl p-4 border border-brand-orange/20 text-center">
              <div className="font-display font-bold text-xl text-brand-orange tabular-nums">{s.num}</div>
              <div className="font-mono text-[10px] text-white/50 uppercase tracking-wide mt-1">{s.label}</div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { num: '15', label: 'Within ±0.10s' },
            { num: '30', label: 'Within ±0.20s' },
            { num: '54', label: 'Within ±0.50s' },
            { num: '58', label: 'Within ±1.00s' },
          ].map((s, i) => (
            <div key={i} className="glass rounded-xl p-4 border border-white/10 text-center">
              <div className="font-display font-bold text-xl text-white tabular-nums">{s.num}<span className="text-white/40 text-sm">/74</span></div>
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
        <div className="glass rounded-xl border border-brand-orange/20 overflow-hidden">
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
          From the 74 matched catalog bikes. Sources: Cycle World, Sport Rider, MCN, Motorcyclist, BikeWale, MotoStatz.
          Conditions: race fuel, professional rider, ideal strip.
        </p>
        <div className="glass rounded-xl border border-brand-orange/20 overflow-hidden">
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
        <div className="glass rounded-xl border border-brand-orange/20 overflow-hidden">
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
        <div className="font-mono text-[10px] text-white/45 uppercase tracking-[0.25em] mb-4">Next</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Link href="/docs/getting-started" className="glass rounded-xl p-4 border border-white/10 hover:border-brand-orange/40 transition-colors group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Getting Started →</div>
            <div className="text-xs text-white/50">Run your first simulation in under 60 seconds.</div>
          </Link>
          <Link href="/simulator" className="glass rounded-xl p-4 border border-white/10 hover:border-brand-orange/40 transition-colors group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Try the simulator →</div>
            <div className="text-xs text-white/50">501 bikes, free in the browser, no account needed.</div>
          </Link>
        </div>
      </div>
    </article>
  );
}
