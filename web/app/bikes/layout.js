// Server-component layout that owns /bikes (catalog listing) metadata.
// The catalog page itself is 'use client' for filter/pagination state.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE =
  'Motorcycle Spec Database India — 751 Bikes with Dyno, Aero & Quarter-Mile Data';
const DESCRIPTION =
  'Indian motorcycle specifications database — 751 bikes with full physics data for quarter-mile drag simulation. Hayabusa, ZX-14R, R15 V4, KTM Duke 390, KTM 890 Duke, Suzuki GSX-S750, Honda CB500X, Pulsar NS200, Apache RTR, Interceptor 650 and more. Individual Cd, frontal area, peak power, redline, wet mass, wheelbase, chain pitch, OEM tire fitments, and predicted ET at Aamby Valley + 19 other venues.';

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/bikes' },
  keywords: [
    'motorcycle spec database india',
    'motorcycle catalog',
    'bike specifications database',
    'motorcycle dyno database',
    'motorcycle aero database',
    'motorcycle gear ratios',
    'hayabusa specs',
    'gsxr 1000 specs',
    'r1 specifications',
    'zx-10r specs',
    'ktm duke 390 specifications',
    'rc 390 specs',
    'bajaj pulsar ns200 specs',
    'apache rtr 200 specs',
    'yamaha r15 v4 specifications',
    'royal enfield interceptor 650 specs',
    'yezdi roadster 334 specs',
    'yezdi adventure 334 specs',
    'hero glamour 125 specs',
    'cfmoto 800nk specs',
    'hayabusa 2026 gen 3 specs',
    'pulsar n250 specifications',
    'ktm 890 duke specs',
    'ktm 890 duke r india',
    'suzuki gsx-s750 specs',
    'gsx-s750 quarter mile',
    'honda cb500x adventure specs',
    'honda cb500x india',
    'indian motorcycle database',
    'indian bike specifications',
    'valley run bikes',
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
        alt: 'MotoQuant Pro bike catalog — 751 motorcycles with full spec data',
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
    numberOfItems: 751,
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
