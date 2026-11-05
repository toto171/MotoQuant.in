import Link from 'next/link';
import CredibilityCtaVariant from './CredibilityCtaVariant';
import CodeComment from '../../../components/CodeComment';

export const metadata = {
  title: 'Validation Data',
  description: 'MotoQuant accuracy report — 250 benchmarks (266 matched) against published Cycle World, Sport Rider, MotoStatz, MCN, and BikeWale timeslips. Weighted bias +0.022s, weighted mean absolute error 0.249s, top-10 mean error ±0.006s. Per-cluster bias across the cylinder-aware 12-cluster taxonomy and the open small-cc, entry and 2-stroke calibration gaps. Reference baselines: K5 10.0436s, R1 10.1092s, Hayabusa 10.1100s — re-pinned by the November 2026 accuracy epoch.',
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

// Top-10 cleanest validated runs, 5 November 2026 sweep
// (reports/acc_final_2026_11_05.json / web/app/validation/accuracy_data.json —
//  10 smallest |Δ| among NON-derived rows, mean ±0.006s. DERIVED estimates
//  are excluded from the showcase. MUST equal the landing-page TOP10.)
const TOP10 = [
  { rank: 1, name: "Kawasaki Ninja ZX-10R", year: 2011, cc: "998cc I4", target: 10.08, sim: 10.0786, delta: -0.001, source: "Sport Rider 7/11" },
  { rank: 2, name: "Aprilia RS 660 Factory", year: 2025, cc: "659cc I2", target: 11.24, sim: 11.2439, delta: 0.004, source: "MotoStatz (Dragy, instrumented)" },
  { rank: 3, name: "Yamaha FZ6 Fazer", year: 2004, cc: "600cc I4", target: 11.53, sim: 11.5347, delta: 0.005, source: "Cycle World 2004" },
  { rank: 4, name: "BMW M1000RR", year: 2021, cc: "999cc I4", target: 9.80, sim: 9.8051, delta: 0.005, source: "Cycle World 2021" },
  { rank: 5, name: "BMW S 1000 RR", year: 2019, cc: "999cc I4", target: 9.85, sim: 9.8446, delta: -0.005, source: "Cycle World 2019" },
  { rank: 6, name: "Yamaha RD350", year: 1973, cc: "347cc I2 2T", target: 14.30, sim: 14.3058, delta: 0.006, source: "Cycle World (period test)" },
  { rank: 7, name: "Yamaha VMAX 1700", year: 2009, cc: "1679cc V4", target: 10.30, sim: 10.3063, delta: 0.006, source: "Cycle World 2009" },
  { rank: 8, name: "Suzuki SV650X", year: 2018, cc: "645cc V2", target: 12.10, sim: 12.1075, delta: 0.007, source: "motorcyclespecs.com (aggregator)" },
  { rank: 9, name: "Triumph Speed Triple 1050", year: 2005, cc: "1050cc I3", target: 11.01, sim: 11.0190, delta: 0.009, source: "Sport Rider 2005" },
  { rank: 10, name: "Yamaha MT-10", year: 2016, cc: "998cc I4", target: 10.35, sim: 10.3610, delta: 0.011, source: "Cycle World 2016" },
];

// Per-cluster weighted bias + weighted |Δ|, 5 November 2026 sweep
// (reports/acc_final_2026_11_05.json clusters, epoch rules — cylinder-aware 12-cluster
// taxonomy: twins/singles/small-I4s are split out from the old
// displacement-only buckets). Bias is weighted; N in note.
// Badge rule: "Closed" = weighted |bias| ≤ 0.05s AND weighted |Δ| ≤ 0.30s.
const CLUSTERS = [
  { name: '600–1000cc sport (I4/triple)', bias: '−0.016s', status: 'closed', note: 'N=76 · weighted |Δ| 0.146s — largest cluster, centred' },
  { name: 'Sport twins 600–1300cc', bias: '−0.004s', status: 'closed', note: 'N=46 · weighted |Δ| 0.210s — second-largest cluster, centred' },
  { name: 'Litre sport ≥195 hp', bias: '−0.007s', status: 'closed', note: 'N=29 · weighted |Δ| 0.168s — centred; two accepted ms-level dry-mass inversions (HP4 Race, Panigale V4R)' },
  { name: 'Cruiser 1300+', bias: '+0.034s', status: 'closed', note: 'N=4 · weighted |Δ| 0.220s — thin set; muscle-bike slip-launch' },
  { name: '500–700cc twin', bias: '+0.144s', status: 'open', note: 'N=7 · weighted |Δ| 0.206s — slow bias at rated rubber (the 2026-07/08 x1.14 class grip corrector is retired)' },
  { name: '200–300cc entry', bias: '+0.265s', status: 'open', note: 'N=14 · weighted |Δ| 0.325s — slow bias; the unweighted |Δ| of 0.646s reflects derived-benchmark spread' },
  { name: 'Singles 300–500cc', bias: '−0.265s', status: 'open', note: 'N=17 · weighted |Δ| 0.620s — quick bias and wide spread (unweighted |Δ| 1.339s); derived-benchmark uncertainty' },
  { name: '300–500cc twin', bias: '+0.189s', status: 'open', note: 'N=8 · weighted |Δ| 0.355s — derived-data uncertainty' },
  { name: '150–200cc entry', bias: '−0.106s', status: 'open', note: 'N=13 · weighted |Δ| 0.651s — per-bike spread against the instrumented Racelogic rows stays wide' },
  { name: 'Small-cc I4 screamers', bias: '−0.195s', status: 'open', note: 'N=2 · weighted |Δ| 0.270s — a two-bike cluster is far too thin to call closed' },
  { name: '2-stroke vintage', bias: '+0.259s', status: 'open', note: 'N=9 · weighted |Δ| 0.339s — slow bias; off-pipe/on-pipe transition' },
  { name: 'Other', bias: '+0.154s', status: 'open', note: 'N=41 · weighted |Δ| 0.367s — mixed heavy ADV/tourer bucket, runs slow' },
];

export default function ValidationPage() {
  return (
    <article>
      <header className="mb-12">
        <CodeComment className="mb-3">validation · 250 benchmarks</CodeComment>
        <h1 className="font-display font-bold text-4xl text-white mb-4 tracking-tight">Benchmark Results — November 2026</h1>
        <p className="text-white/60 text-base leading-relaxed">
          Source-quality-weighted sweep results across 250 published benchmarks (266 matched to a catalog bike
          under the epoch binding). Metrics, per-cluster bias, and methodology. Last updated 5 November 2026.
        </p>
        <Link
          href="/validation"
          className="mt-4 inline-flex items-center gap-2 text-brand-accent hover:text-white transition-colors font-mono text-sm"
        >
          Open the interactive accuracy explorer
          <span aria-hidden="true">→</span>
        </Link>
      </header>

      {/* Headline stats */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-6">Aggregate Metrics (266 matched benchmarks)</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {[
            { num: '0.249s', label: 'Weighted |Δ|' },
            { num: '0.199s', label: 'Median |Δ|' },
            { num: '+0.022s', label: 'Weighted bias (sim − real)' },
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
            { num: '72', label: 'Within ±0.10s' },
            { num: '133', label: 'Within ±0.20s' },
            { num: '222', label: 'Within ±0.50s' },
            { num: '248', label: 'Within ±1.00s' },
          ].map((s, i) => (
            <div key={i} className="card p-4 text-center">
              <div className="font-display font-bold text-xl text-white tabular-nums">{s.num}<span className="text-white/40 text-sm">/266</span></div>
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
            { name: 'GSX-R 1000 K5 (2005)', target: 9.970, sim: 10.044, delta: +0.074 },
            { name: 'YZF-R1 4C8 (2007)', target: 10.300, sim: 10.109, delta: -0.191 },
            { name: 'Hayabusa Gen1 (1999)', target: 10.350, sim: 10.110, delta: -0.240 },
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
          The 10 smallest residuals among the non-derived matched rows — top-10 mean absolute error ±0.006s.
          Sources: Cycle World, Sport Rider, MotoStatz and one aggregator figure. DERIVED estimates are
          excluded from this showcase.
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
          Positive bias means the simulator predicts slower than reality. Clusters follow the cylinder-aware
          12-cluster taxonomy introduced in the July 2026 retune — twins, singles, and small-cc I4 screamers are
          split out from the old displacement-only buckets and each cluster is re-centred against the full weighted
          corpus. A cluster is marked <span className="text-brand-accent">Closed</span> only when its weighted bias
          is inside ±0.05s <em>and</em> its weighted |Δ| is inside 0.30s — a centred cluster that still scatters
          widely stays <span className="text-brand-amber">Open</span>. The remaining spread in the small-cc and
          two-stroke buckets is a known residual from per-bike calibration work not yet completed — it is not a
          regression.
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
            <strong className="text-white">Timing convention:</strong> Since the November 2026 accuracy epoch every
            elapsed time is clocked from the 1-ft stage-beam rollout — ET = t(402.336 m) − t(0.3048 m) — the way
            strip timeslips, North American magazine tests and Dragy runs are timed. Benchmark rows timed from first
            motion (the Indonesian Racelogic tests) are scored against a sim timed from first motion.
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
            gap, not a physics gap. The correct fix is per-bike Cd and μ calibration using real strip data — upload
            a Dragy CSV to <code className="font-mono text-brand-accent">/api/calibrate/dragy</code> to overlay your
            real run against the sim and quantify the gap for your specific bike; the engine&apos;s offline
            calibrator then fits Cd and μ from measured runs.
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
            <div className="text-xs text-white/50">541 bikes, free in the browser, no account needed.</div>
          </Link>
        </div>
      </div>
    </article>
  );
}
