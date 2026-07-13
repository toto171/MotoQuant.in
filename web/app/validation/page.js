// Accuracy — the flagship real-vs-simulated report (STAGED v4 skin).
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

// Aggregate hero tiles — canonical July-2026 corpus numbers. Do NOT edit
// without a fresh sweep + sitewide stat sync (scripts/audit_headline_stats.py).
const HERO_TILES = [
  { value: 221, label: 'BENCHMARKS' },
  { value: 82, label: 'WITHIN ±0.10s' },
  { value: 137, label: 'WITHIN ±0.20s' },
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
              How honest is <span className="text-gradient-volt">the physics?</span>
            </>
          }
          sub="246 benchmarks matched to catalog bikes, cross-checked against published Cycle World, Sport Rider, MCN and MotoStatz timeslips. Weighted mean absolute error 0.22s, bias +0.021s, and the three reference baselines preserved to four decimals since April 2026."
        >
          <Reveal y={14} duration={0.6} delay={0.22}>
            <div className="mt-2 flex flex-wrap gap-x-10 gap-y-4">
              {HERO_TILES.map((s) => (
                <div key={s.label} className="flex flex-col gap-1.5">
                  <ScoreboardCounter value={s.value} h={24} />
                  <span className="label-mono">{s.label}</span>
                </div>
              ))}
              <div className="flex flex-col gap-1.5">
                <ScoreboardDigits value="±0.006s" h={24} color="#FFFFFF" label="±0.006s" />
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
