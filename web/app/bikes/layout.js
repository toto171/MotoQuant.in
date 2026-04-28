// Server-component layout that owns /bikes (catalog listing) metadata.
// The catalog page itself is 'use client' for filter/pagination state.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE =
  'Motorcycle Catalog — 327 Bikes with Dyno, Aero, and Gear-Ratio Data';
const DESCRIPTION =
  'Browse every motorcycle modelled in MotoQuant Pro. 327 bikes across 25+ manufacturers — Suzuki, Yamaha, Honda, Kawasaki, Ducati, BMW, KTM, Royal Enfield, Bajaj, TVS, Aprilia, Triumph, Harley-Davidson, CFMoto and more. Individual Cd, frontal area, peak power, redline, wet mass, wheelbase, chain pitch, and OEM tire fitments for each.';

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/bikes' },
  keywords: [
    'motorcycle spec database',
    'motorcycle catalog',
    'bike specifications database',
    'motorcycle dyno database',
    'motorcycle aero database',
    'motorcycle gear ratios',
    'hayabusa specs',
    'gsxr 1000 specs',
    'r1 specifications',
    'zx-10r specs',
    'ktm duke specifications',
    'bajaj pulsar specs',
    'yamaha r15 specifications',
    'royal enfield interceptor specs',
    'indian motorcycle database',
    'indian bike specifications',
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/bikes`,
    type: 'website',
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'MotoQuant Pro bike catalog — 327 motorcycles with full spec data',
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
      { '@type': 'ListItem', position: 2, name: 'Bikes', item: `${SITE_URL}/bikes` },
    ],
  };
}

// CollectionPage schema tells Google this is a browseable list — lets it
// pick winning child pages (bike detail pages) as direct results instead
// of sending traffic to the list page every time.
function collectionSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Motorcycle Catalog — MotoQuant Pro',
    description: DESCRIPTION,
    url: `${SITE_URL}/bikes`,
    isPartOf: { '@id': `${SITE_URL}/#website` },
    about: {
      '@type': 'Thing',
      name: 'Motorcycle specifications and drag-racing physics data',
    },
    numberOfItems: 327,
    inLanguage: 'en',
  };
}

export default function BikesLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      <StructuredData data={collectionSchema()} />
      {children}
    </>
  );
}
