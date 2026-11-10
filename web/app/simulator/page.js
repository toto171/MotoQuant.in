'use client';

/**
 * /simulator — Quarter-mile simulator (CLARITY v6 "Simple ⇄ Advanced").
 *
 * This file is only the shell: header, mode switch, boot/error states and the
 * choice between the two views. All state lives in useSimulatorState and all
 * UI in components/sim/*. Simple mode (default) answers one question in plain
 * words; Advanced is the full workbench with every capability intact.
 */

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { RotateCcw } from 'lucide-react';
import SiteNav from '../../components/SiteNav';
import SiteFooter from '../../components/SiteFooter';
import PageHeader from '../../components/PageHeader';
import SimProgress from '../../components/SimProgress';
import useSimulatorState from '../../components/sim/useSimulatorState';
import SimpleMode from '../../components/sim/SimpleMode';
import AdvancedWorkbench from '../../components/sim/AdvancedWorkbench';
import AskPanel from '../../components/sim/AskPanel';

const TITLE = 'Quarter-mile simulator';
const LEDE = 'Pick a bike and see how fast it runs the quarter mile.';
const WIDTH = 'max-w-[1400px]';

function BootSkeleton({ progress = null }) {
  return (
    <div aria-busy="true" aria-label="Loading the simulator" className="space-y-5">
      <SimProgress active label="Loading bikes" progress={progress} />
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="card card-pad space-y-4">
          <div className="skeleton h-6 w-1/2" />
          <div className="skeleton h-12 w-full" />
          <div className="skeleton h-11 w-3/4" />
        </div>
        <div className="card card-pad space-y-4 lg:row-span-2">
          <div className="skeleton h-6 w-1/3" />
          <div className="skeleton h-16 w-56" />
          <div className="skeleton h-4 w-full" />
          <div className="skeleton h-4 w-2/3" />
        </div>
        <div className="card card-pad space-y-4">
          <div className="skeleton h-6 w-2/3" />
          <div className="skeleton h-11 w-full" />
        </div>
      </div>
    </div>
  );
}

function ModeSwitch({ mode, onChange }) {
  return (
    <div className="seg-control" role="tablist" aria-label="Simulator mode">
      <button type="button" role="tab" aria-selected={mode === 'simple'} onClick={() => onChange('simple')}>
        Simple
      </button>
      <button type="button" role="tab" aria-selected={mode === 'advanced'} onClick={() => onChange('advanced')}>
        Advanced
      </button>
    </div>
  );
}

function SimulatorPageInner() {
  const searchParams = useSearchParams();
  const sim = useSimulatorState(searchParams);
  const { mode, modeReady, setMode, bikesStatus, bootError, bootProgress, reloadCore } = sim;

  const booting = !modeReady || bikesStatus === 'loading';

  return (
    <>
      <PageHeader
        title={TITLE}
        lede={LEDE}
        maxWidth={WIDTH}
        right={modeReady ? <ModeSwitch mode={mode} onChange={setMode} /> : null}
      />
      <div className={`mx-auto px-4 pb-16 sm:px-6 md:pb-24 ${WIDTH}`}>
        {booting ? (
          <BootSkeleton progress={bootProgress > 0 ? bootProgress : null} />
        ) : bikesStatus === 'error' ? (
          <div role="alert" className="card card-pad border-signal-foul/30">
            <h2 className="font-display text-xl font-semibold text-white">We could not load the simulator</h2>
            <p className="mt-1 text-base text-white/70">{bootError}</p>
            <button type="button" onClick={reloadCore} className="btn-primary mt-4">
              <RotateCcw size={16} aria-hidden="true" /> Try again
            </button>
          </div>
        ) : (
          <div className="space-y-5">
            {sim.bikeNotice && (
              <div role="status" className="flex items-center justify-between gap-3 rounded-xl border border-signal-stage/30 bg-signal-stage/[0.07] p-3 text-sm text-white/85">
                <span>We couldn&apos;t find that bike — pick one below.</span>
                <button type="button" onClick={sim.dismissBikeNotice} className="btn-ghost btn-sm shrink-0">Dismiss</button>
              </div>
            )}
            <AskPanel />
            {mode === 'advanced' ? <AdvancedWorkbench sim={sim} /> : <SimpleMode sim={sim} />}
          </div>
        )}
      </div>
    </>
  );
}

// useSearchParams() must live under <Suspense> or `next build` fails the
// static prerender (missing-suspense-with-csr-bailout). The fallback carries
// the real heading so the server HTML is never empty.
export default function SimulatorPage() {
  return (
    <div className="min-h-screen bg-asphalt-0 text-white">
      <SiteNav />
      <main id="main">
        <Suspense
          fallback={
            <>
              <PageHeader title={TITLE} lede={LEDE} maxWidth={WIDTH} />
              <div className={`mx-auto px-4 pb-16 sm:px-6 ${WIDTH}`}>
                <BootSkeleton />
              </div>
            </>
          }
        >
          <SimulatorPageInner />
        </Suspense>
      </main>
      <SiteFooter />
    </div>
  );
}
