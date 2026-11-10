// Server-component layout whose only purpose is to own the <head> metadata
// for /autotune (page.js composes the page chrome and the client tool).
//
// NOTE: do not hard-code catalog counts (bike / parts / venue numbers) in
// the copy below — those are in flux and reconciled separately. Describe
// the feature generically.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = 'Race-day setup for your motorcycle: gearing, launch RPM and tyre pressure';
const DESCRIPTION =
  'Free race-day setup tool for Indian drag strips. Pick your bike and where you are racing, and MotoQuant works out how the air and altitude change your power, then suggests gearing (sprockets), launch RPM, tyre pressure and fuel/timing guidance. Gearing and launch advice come with the simulated quarter-mile time change; tyre and fuel advice are general guidance. Works for Aamby Valley, MMRT, BIC, Kari and more.';

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/autotune' },
  keywords: [
    'motorcycle ecu autotune india',
    'motorcycle ecu autotune',
    'density altitude motorcycle setup',
    'density altitude motorcycle drag racing',
    'density altitude calculator motorcycle india',
    'drag bike gearing calculator',
    'launch rpm calculator motorcycle',
    'sprocket calculator quarter mile',
    'tyre pressure drag motorcycle',
    'fuel trim altitude motorcycle',
    'motorcycle track setup tool india',
    'aamby valley setup calculator',
    'aamby valley density altitude',
    'mmrt chennai motorcycle setup',
    'bic drag setup motorcycle',
    'final drive ratio drag',
    'powertronic ecu setup india',
    'launch control motorcycle india',
    'two-step launch rpm calculator',
    'altitude correction motorcycle tuning',
    'sea level vs altitude motorcycle power',
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/autotune`,
    type: 'website',
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'MotoQuant race-day setup: gearing, launch RPM and tyre pressure',
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

const breadcrumb = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
    { '@type': 'ListItem', position: 2, name: 'Race-day setup', item: `${SITE_URL}/autotune` },
  ],
};

export default function AutotuneLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumb} />
      {children}
    </>
  );
}
