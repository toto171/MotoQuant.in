// Auto-generated layout.js — owns the <head> metadata for /whitepaper.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL, OG_IMAGE } from '../StructuredData';

const TITLE =
  'Whitepaper: the physics behind MotoQuant';
const DESCRIPTION =
  'How the MotoQuant quarter-mile simulator works: 15 sub-models, RK4 integration at 1 ms, and validation against 250 published tests weighted by source quality.';

export const metadata = {
  title: { absolute: TITLE }, // already names MotoQuant: no suffix
  description: DESCRIPTION,
  alternates: { canonical: '/whitepaper' },
  keywords: [
    "drag simulator whitepaper",
    "motorcycle physics paper",
    "rk4 motorcycle simulator",
    "first principles motorcycle drag simulation",
    "motorcycle quarter mile physics whitepaper",
    "sae j1349 dyno correction",
    "weighted benchmark validation methodology",
    "motorcycle physics simulation accuracy",
    "physics based bike ET predictor",
    "motorcycle 60 ft time physics",
    "drag racing launch rpm modelling",
    "motorcycle clutch slip phase simulation",
    "indian dyno chart rear wheel power",
    "motorcycle drag racing wheelie physics",
    "density altitude motorcycle drag racing",
    "density altitude correction formula motorcycle",
    "rk4 1ms integrator motorcycle physics",
    "weighted benchmark validation 74 timeslips",
    "ktm 1390 super duke r evo physics",
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/whitepaper`,
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
      { '@type': 'ListItem', position: 2, name: "Whitepaper", item: `${SITE_URL}/whitepaper` },
    ],
  };
}

export default function WhitepaperLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
