// Auto-generated layout.js — owns the <head> metadata for /about.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "About MotoQuant — Built in Pune for the Indian Drag Strip";
const DESCRIPTION = "MotoQuant is a free, open-source, first-principles drag-racing simulator built in Pune for the Indian motorcycle community — Aamby Valley regulars, MMRT track-day riders, and Narhe tuning shops. Founder story, roadmap, design philosophy, and how the project differs from generic power-to-weight quarter-mile calculators.";

export const metadata = {
  // absolute: TITLE already carries the brand — skip the '%s · MotoQuant' template
  title: { absolute: TITLE },
  description: DESCRIPTION,
  alternates: { canonical: '/about' },
  keywords: [
    "motoquant about",
    "indian drag racing simulator",
    "pune motorcycle physics tool",
    "aamby valley drag racing software",
    "narhe motorcycle tuning",
    "indian motorcycle simulator team",
    "drag racing software india",
    "physics based motorcycle calculator india",
    "valley run technology",
    "mmrt drag simulator",
    "buddh international circuit track day",
    "bic motorcycle track day",
    "indian motorcycle dyno tuning",
    "motorcycle 60 ft time launch technique",
    "pune dyno tuning shop",
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/about`,
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
      { '@type': 'ListItem', position: 2, name: "About", item: `${SITE_URL}/about` },
    ],
  };
}

export default function AboutLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
