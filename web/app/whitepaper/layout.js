// Auto-generated layout.js — owns the <head> metadata for /whitepaper.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "Whitepaper — The Physics Behind MotoQuant Pro";
const DESCRIPTION = "Complete technical whitepaper for the MotoQuant Pro motorcycle drag simulator: RK4 integrator at 1 ms step, Pacejka magic-formula tire model with thermal evolution, SAE J1349 dyno correction, weighted-benchmark validation methodology against 74 published timeslips, 15 sub-model architecture, and the K5/R1/Hayabusa reference baselines. Read this before you trust the predicted quarter-mile numbers.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/whitepaper' },
  keywords: [
    "drag simulator whitepaper",
    "motorcycle physics paper",
    "pacejka tire model india",
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
    "pacejka magic formula motorcycle thermal",
    "weighted benchmark validation 74 timeslips",
    "ktm 1390 super duke r evo physics",
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/whitepaper`,
    type: 'website',
    images: [{
      url: `${SITE_URL}/og-image.png`,
      width: 1200,
      height: 630,
      alt: TITLE,
    }],
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
