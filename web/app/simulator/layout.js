// Server-component layout whose only purpose is to own the <head> metadata
// for /simulator. The actual page (page.js) is 'use client' and therefore
// cannot export `metadata` itself — App Router pulls it from the nearest
// server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE =
  'Motorcycle Quarter-Mile Calculator — Physics-Based ET Predictor for 796 Bikes';
const DESCRIPTION =
  'Free physics-based motorcycle quarter-mile calculator — not a power-to-weight formula. Predict ET, trap speed, and 60-ft split for 796 bikes at Aamby Valley, MMRT, BIC, and 17 more venues. Tweak rider weight, power delta, mass, and conditions live. Validated to ±0.2s on GSX-R K5, YZF-R1, and Hayabusa.';

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/simulator' },
  keywords: [
    'motorcycle quarter mile calculator',
    'motorcycle quarter mile simulator',
    'motorcycle quarter mile calculator india',
    'bike 1/4 mile calculator',
    'ET predictor online',
    'drag racing calculator motorcycle',
    'free quarter mile simulator',
    'motorcycle ET calculator',
    'dragy simulator',
    'hayabusa quarter mile calculator',
    'gsxr 1000 drag simulator',
    'aamby valley drag simulator',
    'valley run quarter mile predictor',
    '60 ft time motorcycle',
    'trap speed calculator',
    'acceleration simulator motorcycle',
    'physics based quarter mile calculator',
    'kawasaki zx-4r quarter mile',
    'yamaha xsr900 gp drag',
    'pulsar n125 quarter mile',
    'kawasaki ninja 400 quarter mile india',
    'honda hornet 2.0 drag',
    'honda cbr150r drag time',
    'kari motor speedway drag',
    'yezdi roadster quarter mile',
    'yezdi adventure 334 drag time',
    'hero glamour 125 drag',
    'motorcycle drag time predictor india',
    'cfmoto 800nk vs ktm 790 duke',
    'pulsar n250 vs apache rtr 200 4v',
    'hayabusa 2026 gen 3 quarter mile india',
    'ktm 890 duke quarter mile',
    'ktm 890 duke r drag time india',
    'suzuki gsx-s750 quarter mile',
    'honda cb500x quarter mile',
    'yamaha mt-15 v1 quarter mile',
    'mt-15 v1 vs r15 v3',
    'bajaj pulsar 125 neon quarter mile',
    'suzuki gsx-r600 k8 quarter mile',
    'motorcycle 60 ft calculator',
    'pacejka tire model motorcycle',
    'harley nightster rh975 quarter mile',
    'husqvarna svartpilen 250 quarter mile india',
    'honda cb125r drag time',
    'ktm 1390 super duke r evo quarter mile',
    'ktm 1390 evo india drag',
    '60 foot time motorcycle',
    '60 ft time predictor motorcycle',
    'motorcycle launch rpm calculator',
    'pulsar ns400z 0-100',
    'ktm rc 390 gen 3 quarter mile',
    'royal enfield hunter 350 top speed',
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
        alt: 'MotoQuant Pro Simulator — live quarter-mile drag simulation for 796 motorcycles',
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
      '796 motorcycles in catalog',
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
