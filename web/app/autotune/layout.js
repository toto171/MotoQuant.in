// Server-component layout whose only purpose is to own the <head> metadata
// for /autotune. The actual page (page.js) is 'use client' and therefore
// cannot export `metadata` itself — App Router pulls it from the nearest
// server layout instead.
//
// NOTE: do not hard-code catalog counts (bike / parts / venue numbers) in
// the copy below — those are in flux and reconciled separately. Describe
// the feature generically.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE =
  'Motorcycle ECU Autotune India — Density-Altitude-Aware Setup Sheet Calculator';
const DESCRIPTION =
  'Free motorcycle ECU autotune for Indian drag strips — enter your bike, venue, and weather, and MotoQuant computes the live density altitude and returns a printable setup sheet: gearing (front + rear sprocket + final drive), launch RPM, tyre pressure, and fuel/timing guidance. Each recommendation comes with the predicted quarter-mile ET delta. Pre-configured for Aamby Valley, MMRT, BIC, Kari and 16 more venues.';

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
        alt: 'MotoQuant ECU Autotune — density-altitude-aware setup sheet',
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
    { '@type': 'ListItem', position: 2, name: 'ECU Autotune', item: `${SITE_URL}/autotune` },
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
