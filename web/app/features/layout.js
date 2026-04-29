// Auto-generated layout.js — owns the <head> metadata for /features.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "Features — Drag Sim, ROI Engine, Dragy Import, Build Optimiser";
const DESCRIPTION = "Complete feature breakdown: 15 physics sub-models, 334-bike catalog, parts ROI with cost-per-tenth, Bayesian build optimiser, Dragy GPS calibration, A vs B compare, smart recommendations engine.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/features' },
  keywords: ["drag racing features", "motorcycle build optimiser", "parts ROI calculator", "dragy import software"],
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
