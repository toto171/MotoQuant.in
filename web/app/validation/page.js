// Accuracy — the flagship real-vs-simulated report (IGNITION v5 skin).
// Server component: imports the frozen sweep JSON statically and hands it to
// the client-side <AccuracyExplorer/>. Chrome (SiteNav/SiteFooter) matches
// every other route; metadata lives in the sibling layout.js.

import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import AccuracyExplorer from '../../components/AccuracyExplorer';
import accuracyData from './accuracy_data.json';

// Aggregate hero tiles — DERIVED from accuracy_data.json, never hardcoded.
// These used to be literals and drifted: after the July-17 sweep the hero read
// "74 WITHIN ±0.10s / 137 WITHIN ±0.20s" while the Distribution tiles rendered
// one section below on the SAME page read 75 and 138 from this very file, so
// the flagship accuracy page stated two different values for one metric
// (2026-07-25 audit). Reading them from the data makes that impossible: a
// regenerated accuracy_data.json now updates the hero automatically.
const HERO_TILES = [
  { value: accuracyData.n_matched, label: 'Matched runs' },
  { value: accuracyData.distribution.within_0_10, label: 'Within ±0.10s' },
  { value: accuracyData.distribution.within_0_20, label: 'Within ±0.20s' },
];

export default function ValidationPage() {
  return (
    <>
      <SiteNav />
      <main id="main" className="min-h-screen bg-asphalt-0">
        <PageHero
          kicker="Accuracy"
          title="How accurate is the simulator?"
          sub={`We compare it with 250 published timeslips from Cycle World, Sport Rider, MCN and MotoStatz (${accuracyData.n_matched} bike-to-timeslip matches). On average it is within about a quarter of a second, and neither systematically quick nor slow.`}
        >
          <p className="max-w-2xl rounded-xl border border-accent/25 bg-accent/5 px-4 py-3 text-base leading-relaxed text-white/85">
            <strong className="font-semibold text-white">In short:</strong> every dot below is one real run against what
            MotoQuant predicted. Dots on the diagonal line are perfect predictions. The weak spots are small bikes and
            two-strokes, where good timeslips are scarce, and we mark them clearly. Small bikes are the weakest class, and many
            still carry a known gearing limitation, documented in{' '}
            <a
              href="https://github.com/toto171/MotoQuant.in/blob/main/reports/session_2026_11_10_epoch.md"
              className="text-accent underline underline-offset-2 hover:text-accent-bright"
              rel="noopener"
            >
              the repository
            </a>
            .
          </p>
          <div className="mt-2 flex flex-wrap gap-x-10 gap-y-4">
            {HERO_TILES.map((s) => (
              <div key={s.label} className="flex flex-col gap-1">
                <p className="font-display text-3xl font-bold tabular-nums text-accent">{s.value}</p>
                <p className="text-sm text-white/65">{s.label}</p>
              </div>
            ))}
            <div className="flex flex-col gap-1">
              <p className="font-display text-3xl font-bold tabular-nums text-accent">±0.007 s</p>
              <p className="text-sm text-white/65">Top-10 mean error</p>
            </div>
          </div>
        </PageHero>
        <AccuracyExplorer data={accuracyData} />
      </main>
      <SiteFooter />
    </>
  );
}
