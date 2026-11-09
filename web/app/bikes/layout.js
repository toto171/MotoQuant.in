// Server-component layout that owns /bikes (catalog listing) metadata.
// The catalog page itself is 'use client' for filter/pagination state.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE =
  'Motorcycle Spec Database India — 541 Bikes with Dyno, Aero & Quarter-Mile Data';
const DESCRIPTION =
  'Indian motorcycle specifications database — 541 bikes with full physics data for quarter-mile drag simulation. Hayabusa, ZX-14R, R15 V4, KTM Duke 390, KTM 890 Duke, Suzuki GSX-S750, Honda CB500X, Pulsar NS200, Apache RTR, Interceptor 650 and more. Individual Cd, frontal area, peak power, redline, wet mass, wheelbase, chain pitch, OEM tire fitments, and predicted ET at Aamby Valley + 19 other venues.';

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
    'yamaha mt-15 v1 specs',
    'yamaha mt-15 2019 specifications',
    'bajaj pulsar 125 neon specs',
    'suzuki gsx-r600 k8 specs',
    'gsxr 600 k8 quarter mile',
    'indian motorcycle database',
    'indian bike specifications',
    'valley run bikes',
    'pacejka tire model motorcycle',
    'harley nightster rh975 quarter mile',
    'harley davidson nightster drag time',
    'nightster rh975 vs sportster s drag',
    'husqvarna svartpilen 250 quarter mile',
    'svartpilen 250 drag time india',
    'husqvarna svartpilen 250 india price',
    'honda cb125r quarter mile',
    'honda cb125r drag time',
    'honda cb125r india',
    'ktm 1390 super duke r evo quarter mile india',
    'ktm 1390 evo drag time',
    'ktm 1390 india price',
    'kawasaki ninja h2 sx vs hayabusa india',
    'triumph street triple 765 rs quarter mile india',
    'street triple 765 rs vs 765 r',
    'hayabusa 2026 launch control 2.6 seconds',
    'pacejka motorcycle tire model calculator',
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
        alt: 'MotoQuant bike catalog — 541 motorcycles with full spec data',
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
    name: 'Motorcycle Catalog — MotoQuant',
    description: DESCRIPTION,
    url: `${SITE_URL}/bikes`,
    isPartOf: { '@id': `${SITE_URL}/#website` },
    about: {
      '@type': 'Thing',
      name: 'Motorcycle specifications and drag-racing physics data',
    },
    numberOfItems: 541,
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
