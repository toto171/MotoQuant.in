'use client';

/**
 * Lazy chart exports (F10). Importing recharts at the top of the simulator
 * page put the whole chart library in the first-load bundle; here it becomes
 * its own chunk, fetched only when a chart tab is actually opened. The page
 * still prerenders (ssr:false + a skeleton of the same height).
 */

import dynamic from 'next/dynamic';

function Fallback({ h = 204 }) {
  return <div aria-hidden="true" className="skeleton w-full" style={{ height: h }} />;
}

export const SimChart = dynamic(() => import('./SimCharts').then((m) => m.SimChart), {
  ssr: false, loading: () => <Fallback h={204} />,
});
export const OverlayChart = dynamic(() => import('./SimCharts').then((m) => m.OverlayChart), {
  ssr: false, loading: () => <Fallback h={204} />,
});
export const RealVsSimChart = dynamic(() => import('./SimCharts').then((m) => m.RealVsSimChart), {
  ssr: false, loading: () => <Fallback h={224} />,
});
export const DynoChart = dynamic(() => import('./SimCharts').then((m) => m.DynoChart), {
  ssr: false, loading: () => <Fallback h={244} />,
});

// Plain colour strings (no recharts import) so tabs can colour a chart without
// pulling the chart chunk into the main bundle.
export const COLOR_NAMES = {
  a: 'rgb(var(--accent))',
  b: 'rgb(var(--go))',
  stage: 'rgb(var(--stage))',
  foul: 'rgb(var(--foul))',
};
