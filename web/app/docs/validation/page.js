import Link from 'next/link';

export const metadata = {
  title: 'Validation Data',
  description: 'MotoQuant accuracy report: 250 published tests (263 matched) from Cycle World, Sport Rider, MotoStatz, MCN and BikeWale. Weighted bias +0.023s, weighted mean absolute error 0.25s, top-10 mean error ±0.006s. Per-cluster bias across the cylinder-aware 12-cluster taxonomy, and the open gaps for small bikes and two-strokes. Reference bikes, held to four decimals by CI: K5 10.0436s, R1 10.1092s, Hayabusa 10.1100s.',
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

// Top-10 cleanest validated runs, 10 November 2026 sweep
// (web/app/validation/accuracy_data.json: the 10 smallest |Δ| among
// non-derived benchmarks, mean ±0.006s; the same rows as the landing page).
const TOP10 = [
  { rank: 1,  name: 'Kawasaki Ninja ZX-10R',     year: 2011, cc: '998 cc',  target: 10.08, sim: 10.0786, delta: -0.001, source: 'Sport Rider, July 2011' },
  { rank: 2,  name: 'Aprilia RS 660 Factory',    year: 2025, cc: '659 cc',  target: 11.24, sim: 11.2439, delta:  0.004, source: 'MotoStatz (Dragy)' },
  { rank: 3,  name: 'Yamaha FZ6 Fazer',          year: 2004, cc: '600 cc',  target: 11.53, sim: 11.5347, delta:  0.005, source: 'Cycle World 2004' },
  { rank: 4,  name: 'BMW M 1000 RR',             year: 2021, cc: '999 cc',  target: 9.80,  sim: 9.8051,  delta:  0.005, source: 'Cycle World 2021' },
  { rank: 5,  name: 'BMW S 1000 RR',             year: 2019, cc: '999 cc',  target: 9.85,  sim: 9.8446,  delta: -0.005, source: 'Cycle World 2019' },
  { rank: 6,  name: 'Yamaha RD350',              year: 1973, cc: '347 cc',  target: 14.30, sim: 14.3058, delta:  0.006, source: 'Cycle World (period test)' },
  { rank: 7,  name: 'Yamaha VMAX 1700',          year: 2009, cc: '1679 cc', target: 10.30, sim: 10.3063, delta:  0.006, source: 'Cycle World 2009' },
  { rank: 8,  name: 'Suzuki SV650X',             year: 2018, cc: '645 cc',  target: 12.10, sim: 12.1075, delta:  0.007, source: 'motorcyclespecs.com' },
  { rank: 9,  name: 'Triumph Speed Triple 1050', year: 2005, cc: '1050 cc', target: 11.01, sim: 11.0190, delta:  0.009, source: 'Sport Rider 2005' },
  { rank: 10, name: 'Yamaha MT-10',              year: 2016, cc: '998 cc',  target: 10.35, sim: 10.3610, delta:  0.011, source: 'Cycle World 2016' },
];

// Per-cluster weighted bias and weighted |Δ|, 10 November 2026 sweep
// (reports/acc_final_2026_11_10.json, clusters). N is the number of matches.
// Badge rule: "Closed" = weighted |bias| ≤ 0.05s AND weighted |Δ| ≤ 0.30s.
const CLUSTERS = [
  { name: '600–1000cc sport (I4/triple)', bias: '−0.016s', status: 'closed', note: 'N=76 · weighted |Δ| 0.146s. The largest cluster and the tightest.' },
  { name: 'Sport twins 600–1300cc', bias: '−0.001s', status: 'closed', note: 'N=44 · weighted |Δ| 0.208s' },
  { name: 'Litre sport ≥195 hp', bias: '−0.011s', status: 'closed', note: 'N=29 · weighted |Δ| 0.171s' },
  { name: 'Cruiser 1300+', bias: '+0.034s', status: 'closed', note: 'N=4 · weighted |Δ| 0.220s. Only four matches, so treat it as indicative.' },
  { name: '500–700cc twin', bias: '+0.135s', status: 'open', note: 'N=6 · weighted |Δ| 0.199s. Small spread, but predicted slow on average.' },
  { name: '200–300cc entry', bias: '+0.265s', status: 'open', note: 'N=14 · weighted |Δ| 0.325s. Predicted slow on average.' },
  { name: 'Singles 300–500cc', bias: '−0.265s', status: 'open', note: 'N=17 · weighted |Δ| 0.620s (unweighted 1.339s). Predicted quick, with wide spread from derived benchmarks.' },
  { name: '300–500cc twin', bias: '+0.189s', status: 'open', note: 'N=8 · weighted |Δ| 0.355s' },
  { name: '150–200cc entry', bias: '−0.106s', status: 'open', note: 'N=13 · weighted |Δ| 0.651s (unweighted 1.154s). Wide spread against the instrumented Racelogic rows.' },
  { name: 'Small-cc I4 screamers', bias: '−0.195s', status: 'open', note: 'N=2 · weighted |Δ| 0.270s. Two matches are too few to call this cluster closed.' },
  { name: '2-stroke vintage', bias: '+0.259s', status: 'open', note: 'N=9 · weighted |Δ| 0.339s. Predicted slow on average.' },
  { name: 'Other', bias: '+0.154s', status: 'open', note: 'N=41 · weighted |Δ| 0.367s. A mixed bucket of heavy adventure bikes and tourers.' },
];

export default function ValidationPage() {
  return (
    <article>
      <header className="mb-12">
        <p className="eyebrow mb-2">Accuracy</p>
        <h1 className="font-display font-bold text-3xl md:text-4xl text-white mb-4 tracking-tight">Benchmark results, November 2026</h1>
        <p className="text-white/70 text-base leading-relaxed mb-5">
          Results of the 10 November 2026 sweep against 250 published tests, weighted by source quality
          (263 matches to catalog bikes): the headline numbers, the bias of each class of bike, and how the
          comparison is made.
        </p>
        <p className="rounded-xl border border-accent/25 bg-accent/5 px-4 py-3 text-base leading-relaxed text-white/85">
          <strong className="font-semibold text-white">In short:</strong> we compare the simulator with real
          timeslips from magazines and instrumented tests. On average it lands within about a quarter of a
          second, and it is neither systematically quick nor slow. Small bikes and two-strokes are the weakest
          spot, and we say so below.
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
        <h2 className="font-display font-bold text-2xl text-white mb-6">Aggregate metrics (263 matched benchmarks)</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {[
            { num: '0.25s', label: 'Weighted |Δ|' },
            { num: '0.202s', label: 'Median |Δ|' },
            { num: '+0.023s', label: 'Weighted bias (sim − real)' },
            { num: '±0.006s', label: 'Top-10 mean error' },
          ].map((s, i) => (
            <div key={i} className="card p-4 border-brand-orange/20 text-center">
              <div className="font-display font-bold text-xl text-brand-orange tabular-nums">{s.num}</div>
              <div className="text-xs text-white/60 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { num: '72', label: 'Within ±0.10s' },
            { num: '130', label: 'Within ±0.20s' },
            { num: '219', label: 'Within ±0.50s' },
            { num: '245', label: 'Within ±1.00s' },
          ].map((s, i) => (
            <div key={i} className="card p-4 text-center">
              <div className="font-display font-bold text-xl text-white tabular-nums">{s.num}<span className="text-white/60 text-sm">/263</span></div>
              <div className="text-xs text-white/60 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Reference baselines */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Reference baselines</h2>
        <p className="text-white/60 text-sm mb-6">
          Three hand-built configurations in <code className="font-mono text-brand-accent break-words">defaults.py</code> anchor the physics.
          CI holds them to four decimals: a code change that moves any of them by 0.0001 s fails, unless it is a
          deliberate accuracy pass backed by a full sweep. They are simulated at sea level, 25 °C and 50 % humidity.
        </p>
        <div className="card border-brand-orange/20 overflow-x-auto">
         <div className="min-w-[440px]">
          <div className="grid grid-cols-[1fr_90px_90px_90px] gap-4 px-5 py-3 border-b border-brand-orange/20 bg-white/[0.02] text-xs font-medium text-white/60">
            <div>Bike</div>
            <div className="text-right">Target</div>
            <div className="text-right">Simulated</div>
            <div className="text-right">Δ</div>
          </div>
          {[
            { name: 'GSX-R 1000 K5 (2005)', target: 9.970, sim: 10.044, delta: +0.074 },
            { name: 'YZF-R1 4C8 (2007)', target: 10.300, sim: 10.109, delta: -0.191 },
            { name: 'Hayabusa Gen1 (1999)', target: 10.400, sim: 10.110, delta: -0.290 },
          ].map((b, i) => (
            <div key={i} className="grid grid-cols-[1fr_90px_90px_90px] gap-4 px-5 py-3 border-b border-white/[0.04] last:border-0">
              <div className="font-display font-semibold text-white text-sm">{b.name}</div>
              <div className="text-right font-mono text-white/70 tabular-nums text-sm">{b.target.toFixed(3)}s</div>
              <div className="text-right font-mono text-white tabular-nums text-sm">{b.sim.toFixed(3)}s</div>
              <div className="text-right font-display font-bold tabular-nums text-sm text-brand-accent">
                {b.delta > 0 ? '+' : ''}{b.delta.toFixed(3)}s
              </div>
            </div>
          ))}
         </div>
        </div>
      </section>

      {/* Top 10 */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Top 10 most accurate bikes</h2>
        <p className="text-white/60 text-sm mb-6">
          The 10 smallest residuals among published (non-derived) benchmarks: top-10 mean absolute error ±0.006s.
          Sources: Cycle World, Sport Rider, MotoStatz and motorcyclespecs.com. DERIVED estimates are excluded.
          Conditions: race fuel, professional rider, ideal strip.
        </p>
        <div className="card border-brand-orange/20 overflow-hidden">
          <div className="hidden md:grid grid-cols-[36px_1fr_100px_100px_90px_130px] gap-3 px-5 py-3 border-b border-brand-orange/20 bg-white/[0.02] text-xs font-medium text-white/60">
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
                  <div><div className="text-white/60 text-xs">Year</div><div className="text-white/80 font-mono">{b.year}</div></div>
                  <div><div className="text-white/60 text-xs">Target</div><div className="text-white/80 font-mono tabular-nums">{b.target.toFixed(2)}s</div></div>
                  <div><div className="text-white/60 text-xs">Sim</div><div className="text-white/80 font-mono tabular-nums">{b.sim.toFixed(2)}s</div></div>
                </div>
                <div className="md:hidden mt-1.5 text-xs text-white/60">{b.cc} · {b.source}</div>
                {/* Desktop */}
                <div className="hidden md:block font-bold text-brand-orange font-display">{b.rank}</div>
                <div className="hidden md:block">
                  <div className="font-bold text-white text-sm">{b.name}</div>
                  <div className="font-mono text-xs text-white/60">{b.year} · {b.cc}</div>
                </div>
                <div className="hidden md:block text-right font-mono text-white/70 tabular-nums text-sm">{b.target.toFixed(2)}s</div>
                <div className="hidden md:block text-right font-mono text-white tabular-nums text-sm font-semibold">{b.sim.toFixed(2)}s</div>
                <div className={`hidden md:block text-right font-display font-bold tabular-nums text-sm ${color}`}>{sign}{b.delta.toFixed(3)}s</div>
                <div className="hidden md:block text-right text-xs text-white/60 self-center">{b.source}</div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Per-cluster bias */}
      <section className="mb-14">
        <h2 className="font-display font-bold text-2xl text-white mb-4">Per-cluster bias</h2>
        <p className="text-white/60 text-sm mb-6">
          Positive bias means the simulator predicts slower than reality. Clusters follow a cylinder-aware
          12-cluster taxonomy that splits twins, singles and small four-cylinder bikes out of plain
          displacement buckets. A cluster is marked <span className="text-brand-accent">Closed</span> only when its
          weighted bias is inside ±0.05s <em>and</em> its weighted |Δ| is inside 0.30s, so a centred cluster that
          still scatters widely stays <span className="text-brand-amber">Open</span>. Four clusters are closed. The
          small-bike, single and two-stroke clusters are open, with biases of up to a quarter of a second in
          either direction; the known causes are listed under Known limitations below.
        </p>
        <div className="card border-brand-orange/20 overflow-hidden">
          {CLUSTERS.map((c, i) => (
            <div key={i} className="flex items-center justify-between gap-4 px-5 py-3.5 border-b border-white/[0.04] last:border-0">
              <div className="flex-1">
                <div className="font-display font-semibold text-sm text-white">{c.name}</div>
                <div className="text-xs text-white/60 mt-0.5">{c.note}</div>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <span className={`font-display font-bold tabular-nums text-sm ${
                  c.status === 'closed' ? 'text-brand-accent' :
                  c.status === 'good' ? 'text-brand-green' : 'text-brand-amber'
                }`}>{c.bias}</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
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
        <div className="space-y-4 text-white/75 text-base leading-relaxed">
          <p>
            <strong className="text-white">Benchmark sources:</strong> Published magazine timeslips from Cycle World,
            Sport Rider, MCN, Motorcyclist, and BikeWale. Indian community strip records from MotoStatz, Facebook
            drag groups, and drag event published results. All benchmarks use professional rider / race fuel / ideal
            strip conditions unless explicitly noted.
          </p>
          <p>
            <strong className="text-white">Simulation conditions:</strong> Every benchmark is simulated at sea level
            (1013.25 hPa), 25 °C and 50 % relative humidity, the conditions the three reference bikes are pinned at.
            Most magazine tests correct to standard conditions or do not state them. Bikes use their stock
            configuration from the seeded database, with no per-bike tuning of Cd or μ.
          </p>
          <p>
            <strong className="text-white">Matching:</strong> Benchmark-to-bike matching uses word-boundary regex
            to prevent false positives (YZF-R1 ≠ YZF-R15). Year ranges are respected: a 2009 benchmark does not
            match a 2015 model that shares a name but has different internals.
          </p>
          <p>
            <strong className="text-white">Known limitations:</strong> Small bikes are the weakest class, and many
            still carry a known gearing limitation, documented in{' '}
            <a
              href="https://github.com/toto171/MotoQuant.in/blob/main/reports/gearing_experiment_2026_11_10.md"
              className="text-brand-accent underline underline-offset-2"
              rel="noopener"
            >
              the repository
            </a>
            . The other cause is thin data: few instrumented timeslips exist for small bikes and two-strokes, so their
            clusters lean on derived benchmarks with a declared ±0.7 s uncertainty. If you have a Dragy run, upload the
            CSV on the simulator&apos;s My data tab to see your real run against the simulation, and send it in with the
            &ldquo;Submit a timeslip&rdquo; form on GitHub so it can join the benchmark set.
          </p>
          <p>
            <strong className="text-white">Regression testing:</strong> Every change to the physics code runs
            <code className="font-mono text-brand-accent mx-1">scripts/check_baselines.py</code>, which holds the three reference bikes
            to the fourth decimal, and
            <code className="font-mono text-brand-accent mx-1">tests/test_regression_snapshot.py</code>, which re-simulates a
            stratified sample of about 35 catalog bikes against stored results to within 2 ms. The same snapshot
            covers every catalog bike when run with <code className="font-mono text-brand-accent">MOTOQUANT_SLOW_TESTS=1</code>.
          </p>
        </div>
      </section>

      {/* Next */}
      <div className="pt-8 border-t border-brand-orange/10">
        <div className="label-mono mb-4">Next</div>
        <div className="grid sm:grid-cols-2 gap-4">
          <Link href="/docs/getting-started" className="card card-hover block p-4 group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Getting started →</div>
            <div className="text-xs text-white/60">Run your first simulation in under 60 seconds.</div>
          </Link>
          <Link href="/simulator" className="card card-hover block p-4 group">
            <div className="font-display font-bold text-white mb-1 group-hover:text-brand-orange transition-colors">Try the simulator →</div>
            <div className="text-xs text-white/60">534 bikes, free in the browser, no account needed.</div>
          </Link>
        </div>
      </div>
    </article>
  );
}
