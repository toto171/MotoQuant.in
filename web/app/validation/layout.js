// Owns the <head> metadata for /validation. The page renders a client
// component (AccuracyExplorer), so metadata is declared here on the server
// layout — same pattern as /features and the other tool routes.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = 'Accuracy — Real vs Simulated Quarter-Mile ET (246 Benchmarks)';
const DESCRIPTION =
  "MotoQuant Pro's accuracy report: every simulated quarter-mile ET plotted against its published real timeslip. 221 source-quality-weighted benchmarks (246 matched), weighted mean absolute error 0.22s, bias +0.021s, top-10 cleanest ±0.006s, 137/246 within 0.20s. Interactive scatter, residual histogram, and per-cluster breakdown against Cycle World, Sport Rider, MCN and MotoStatz data. Reference baselines K5 10.0334s, R1 10.2859s, Hayabusa 10.4712s — Δ ±0.0000 since April 2026.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/validation' },
  keywords: [
    'motorcycle simulator accuracy',
    'real vs simulated quarter mile',
    'drag simulator validation',
    'quarter mile prediction accuracy',
    'motorcycle physics simulation accuracy',
    'validated drag racing model',
    'cycle world quarter mile timeslip',
    'hayabusa simulator validation',
    'gsxr 1000 k5 reference baseline',
    'motoquant accuracy report',
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/validation`,
    type: 'website',
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: TITLE,
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: TITLE,
    description: DESCRIPTION,
  },
  robots: { index: true, follow: true },
};

function breadcrumbs() {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Accuracy', item: `${SITE_URL}/validation` },
    ],
  };
}

export default function ValidationLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
