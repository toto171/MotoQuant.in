// Owns the <head> metadata for /validation. The page renders a client
// component (AccuracyExplorer), so metadata is declared here on the server
// layout — same pattern as /features and the other tool routes.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = 'Accuracy — Real vs Simulated Quarter-Mile ET (263 Matched Benchmarks)';
const DESCRIPTION =
  "MotoQuant's accuracy report: every simulated quarter-mile ET plotted against its published timeslip. 250 published tests weighted by source quality (263 matched), weighted mean absolute error 0.25s, bias +0.023s, top-10 cleanest ±0.006s, 130/263 within 0.20s. Interactive scatter, residual histogram and per-cluster breakdown against Cycle World, Sport Rider, MCN and MotoStatz data. Reference bikes, held to four decimals by CI: K5 10.0436s, R1 10.1092s, Hayabusa 10.1100s.";

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
