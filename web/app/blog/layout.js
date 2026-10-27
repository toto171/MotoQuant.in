// Auto-generated layout.js — owns the <head> metadata for /blog.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "MotoQuant Blog — Motorcycle Drag Racing Physics, Tuning & Bike Breakdowns";
// ≤160 chars — long-tail terms live on the individual post pages.
const DESCRIPTION = "Long-form deep dives on motorcycle drag racing physics, India-specific venue tuning, and bike-by-bike quarter-mile breakdowns from the MotoQuant engine.";

export const metadata = {
  // absolute: TITLE already carries the brand — skip the '%s · MotoQuant' template
  title: { absolute: TITLE },
  description: DESCRIPTION,
  alternates: { canonical: '/blog' },
  keywords: [
    "motorcycle drag racing blog",
    "india drag tuning guide",
    "aamby valley setup",
    "pulsar ns400z quarter mile",
    "re continental gt 650 drag",
    "pulsar ns200 vs apache rtr 200",
    "hayabusa vs zx-14r",
    "r15 v4 quarter mile",
    "ktm 1390 super duke",
    "2 stroke expansion chamber",
    "motorcycle physics blog india",
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/blog`,
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
      { '@type': 'ListItem', position: 2, name: "Blog", item: `${SITE_URL}/blog` },
    ],
  };
}

export default function BlogLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
