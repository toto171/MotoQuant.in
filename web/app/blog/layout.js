// Auto-generated layout.js — owns the <head> metadata for /blog.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "MotoQuant Blog — Motorcycle Drag Racing Physics, Tuning & Bike Breakdowns";
const DESCRIPTION = "Long-form deep dives on motorcycle drag racing physics, India-specific tuning, and bike-by-bike quarter-mile breakdowns: Hayabusa vs ZX-14R, Pulsar NS200 vs Apache RTR 200, KTM 1390 Super Duke R EVO, Hero Xtreme 200S 4V, how a 2-stroke expansion chamber actually works, why your R15 will not hit 14s, and Aamby Valley November tuning.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/blog' },
  keywords: [
    "motorcycle drag racing blog",
    "india drag tuning guide",
    "aamby valley setup",
    "hayabusa vs zx-14r",
    "pulsar ns200 vs apache rtr 200",
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
