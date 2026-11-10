// Auto-generated layout.js — owns the <head> metadata for /features.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "What you can do with MotoQuant: free quarter-mile simulator for motorcycles";
const DESCRIPTION = "Pick a bike from the 534-bike catalog and see its quarter-mile time, find the best parts for your budget, get a race-day setup for your strip, compare two bikes, check your own timeslips and save and share runs. Free and open source.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/features' },
  keywords: [
    "drag racing features",
    "motorcycle build optimiser india",
    "motorcycle build optimizer india",
    "motorcycle ecu autotune india",
    "density altitude motorcycle drag racing",
    "parts ROI calculator",
    "cost per tenth calculator",
    "cost per tenth inr",
    "dragy import software",
    "motorcycle physics simulator features",
    "budget aware build optimiser",
    "knapsack drag bike parts",
    "a vs b motorcycle compare",
    "motorcycle quarter mile compare tool",
    "indian motorcycle drag tool features",
    "cfmoto 800nk simulator",
    "yamaha mt-125 quarter mile",
    "yamaha xsr125 drag",
    "drag racing parts knapsack optimiser",
    "hornet 2.0 vs ns200 drag",
    "kawasaki ninja zx-4r quarter mile india",
    "kawasaki ninja 400 india drag",
    "ecu flash cost india motorcycle",
    "motorcycle 60 ft calculator",
    "yamaha mt-15 v1 simulator",
    "altitude correction motorcycle power",
    "aamby valley density altitude",
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/features`,
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
      { '@type': 'ListItem', position: 2, name: "Features", item: `${SITE_URL}/features` },
    ],
  };
}

export default function FeaturesLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
