// Owns the <head> metadata for /validation. The page renders a client
// component (AccuracyExplorer), so metadata is declared here on the server
// layout — same pattern as /features and the other tool routes.

import StructuredData, { SITE_URL, OG_IMAGE } from '../StructuredData';

const TITLE =
  'Accuracy: simulated vs 250 published times';
const DESCRIPTION =
  'Every simulated quarter-mile time against its published timeslip: 250 published tests, 263 matched, weighted mean absolute error 0.25s, 130/263 within 0.20 s.';

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
    images: [OG_IMAGE],
  },
  twitter: {
    card: 'summary_large_image',
    title: TITLE,
    description: DESCRIPTION,
    images: [OG_IMAGE],
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
