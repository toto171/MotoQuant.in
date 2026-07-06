// Accuracy — the flagship real-vs-simulated report.
// Server component: imports the frozen sweep JSON statically and hands it to
// the client-side <AccuracyExplorer/>. Chrome (SiteNav/SiteFooter) matches
// every other route; metadata lives in the sibling layout.js.

import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHero from '../../components/PageHero';
import AccuracyExplorer from '../../components/AccuracyExplorer';
import accuracyData from './accuracy_data.json';

export default function ValidationPage() {
  return (
    <>
      <SiteNav />
      <main id="main" className="min-h-screen bg-black">
        <PageHero
          kicker="sweep loaded [246/246] · residuals armed"
          badge="Accuracy Report"
          title={
            <>
              Accuracy — every prediction,{' '}
              <span className="text-gradient-orange">measured.</span>
            </>
          }
          sub="246 benchmarks matched to catalog bikes, cross-checked against published Cycle World, Sport Rider, MCN and MotoStatz timeslips. Weighted mean absolute error 0.22s, bias +0.021s, and the three reference baselines preserved to four decimals since April 2026."
          stats={[
            { value: 246, label: 'MATCHED' },
            { value: 221, label: 'BENCHMARKS' },
            { value: 137, label: 'WITHIN 0.20s' },
          ]}
        />
        <AccuracyExplorer data={accuracyData} />
      </main>
      <SiteFooter />
    </>
  );
}
