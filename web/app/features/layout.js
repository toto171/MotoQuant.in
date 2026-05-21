// Auto-generated layout.js — owns the <head> metadata for /features.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "Features — Physics Drag Sim, Parts ROI, Dragy Import, Build Optimiser (India)";
const DESCRIPTION = "What you get inside MotoQuant Pro: 15 first-principles physics sub-models (Pacejka tires, RK4 solver, weight transfer, two-stroke expansion-chamber), 637-bike catalog covering Hayabusa to R15 V4 to NS400Z, parts ROI with cost-per-tenth in INR, Bayesian build optimiser, Dragy GPS calibration, A vs B compare, and the smart recommendations engine.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/features' },
  keywords: [
    "drag racing features",
    "motorcycle build optimiser india",
    "parts ROI calculator",
    "cost per tenth calculator",
    "dragy import software",
    "pacejka tire model motorcycle",
    "motorcycle physics simulator features",
    "bayesian build optimiser",
    "a vs b motorcycle compare",
    "motorcycle quarter mile compare tool",
    "indian motorcycle drag tool features",
    "cfmoto 800nk simulator",
    "yamaha mt-125 quarter mile",
    "yamaha xsr125 drag",
    "drag racing parts knapsack optimiser",
    "hornet 2.0 vs ns200 drag",
    "kawasaki ninja 400 india drag",
    "ecu flash cost india motorcycle",
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
