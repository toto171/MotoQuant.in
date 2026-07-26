// Accuracy — the flagship real-vs-simulated report (IGNITION v5 skin).
// Server component: imports the frozen sweep JSON statically and hands it to
// the client-side <AccuracyExplorer/>. Chrome (SiteNav/SiteFooter) matches
// every other route; metadata lives in the sibling layout.js.

import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import AccuracyExplorer from '../../components/AccuracyExplorer';
import ScoreboardDigits, { ScoreboardCounter } from '../../components/ScoreboardDigits';
import { Reveal } from '../../components/Reveal';
import accuracyData from './accuracy_data.json';

// Aggregate hero tiles — DERIVED from accuracy_data.json, never hardcoded.
// These used to be literals and drifted: after the July-17 sweep the hero read
// "74 WITHIN ±0.10s / 137 WITHIN ±0.20s" while the Distribution tiles rendered
// one section below on the SAME page read 75 and 138 from this very file, so
// the flagship accuracy page stated two different values for one metric
// (2026-07-25 audit). Reading them from the data makes that impossible: a
// regenerated accuracy_data.json now updates the hero automatically.
const HERO_TILES = [
  { value: accuracyData.n_matched, label: 'MATCHED RUNS' },
  { value: accuracyData.distribution.within_0_10, label: 'WITHIN ±0.10s' },
  { value: accuracyData.distribution.within_0_20, label: 'WITHIN ±0.20s' },
];

export default function ValidationPage() {
  return (
    <>
      <SiteNav />
      <main id="main" className="min-h-screen bg-asphalt-0">
        <PageHero
          kicker="Accuracy report · weighted benchmark sweep"
          title={
            <>
              How <span className="text-gradient-orange">honest</span> is the physics?
            </>
          }
          sub="277 benchmarks matched to catalog bikes, cross-checked against published Cycle World, Sport Rider, MCN and MotoStatz timeslips. Weighted mean absolute error 0.27s, bias −0.005s, and the three reference baselines preserved to four decimals since July 13, 2026."
        >
          <Reveal y={14} duration={0.6} delay={0.22}>
            <div className="mt-2 flex flex-wrap gap-x-10 gap-y-4">
              {HERO_TILES.map((s) => (
                <div key={s.label} className="flex flex-col gap-1.5">
                  <ScoreboardCounter value={s.value} h={28} />
                  <span className="label-mono">{s.label}</span>
                </div>
              ))}
              <div className="flex flex-col gap-1.5">
                <div className="flex items-end gap-1">
                  <span className="mb-0.5 font-mono text-sm text-white/50" aria-hidden="true">±</span>
                  <ScoreboardDigits value="0.009" h={28} label="±0.009s" />
                  <span className="mb-0.5 font-mono text-xs text-white/40" aria-hidden="true">s</span>
                </div>
                <span className="label-mono">TOP-10 MEAN |Δ|</span>
              </div>
            </div>
          </Reveal>
        </PageHero>
        <AccuracyExplorer data={accuracyData} />
      </main>
      <SiteFooter />
    </>
  );
}
