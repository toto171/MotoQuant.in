// Server-component layout whose only purpose is to own the <head> metadata
// for /simulator. The actual page (page.js) is 'use client' and therefore
// cannot export `metadata` itself — App Router pulls it from the nearest
// server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE =
  'Free Motorcycle Quarter-Mile Simulator — Predict ET in Seconds';
const DESCRIPTION =
  'Run a live quarter-mile drag simulation for any of 334 motorcycles. Tweak rider weight, power delta, mass, and venue, then read ET, trap speed, 60-ft split, and a full v(t) / RPM / accel chart. Validated to ±0.2s on K5, R1, and Hayabusa.';

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/simulator' },
  keywords: [
    'motorcycle quarter mile simulator',
    'bike 1/4 mile calculator',
    'ET predictor online',
    'drag racing calculator motorcycle',
    'free quarter mile simulator',
    'motorcycle ET calculator',
    'dragy simulator',
    'hayabusa quarter mile calculator',
    'gsxr 1000 drag simulator',
    '60 ft time motorcycle',
    'trap speed calculator',
    'acceleration simulator motorcycle',
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/simulator`,
    type: 'website',
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'MotoQuant Pro Simulator — live quarter-mile drag simulation for 334 motorcycles',
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

// BreadcrumbList helps Google render the little "motoquant.in > Simulator"
// breadcrumb trail under search results — clickable + higher CTR.
function breadcrumbs() {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: 'Simulator', item: `${SITE_URL}/simulator` },
    ],
  };
}

// WebApplication schema — distinct from the site-wide SoftwareApplication;
// this one specifically marks /simulator as an interactive web tool (Google
// gives a subtle "Web App" badge on mobile results for these).
function webApplicationSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebApplication',
    name: 'MotoQuant Pro Quarter-Mile Simulator',
    url: `${SITE_URL}/simulator`,
    applicationCategory: 'AutomotiveApplication',
    operatingSystem: 'Any (web browser)',
    browserRequirements: 'Requires JavaScript and modern browser (Chrome 90+, Safari 14+, Firefox 88+)',
    isAccessibleForFree: true,
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'INR',
    },
    featureList: [
      '334 motorcycles in catalog',
      '20 drag strip venues with seasonal weather',
      'ET + trap + splits in <1 second',
      'Dragy GPS import for calibration',
      'Parts ROI with cost per tenth',
    ],
  };
}

export default function SimulatorLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      <StructuredData data={webApplicationSchema()} />
      {children}
    </>
  );
}
