// Auto-generated layout.js — owns the <head> metadata for /about.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL, OG_IMAGE } from '../StructuredData';

const TITLE =
  'About MotoQuant: open-source simulator from Pune';
const DESCRIPTION =
  'MotoQuant is a free, open-source (Apache-2.0) quarter-mile simulator for motorcycles, built in Pune for Indian riders and drag strips. Why we built it and how.';

export const metadata = {
  title: { absolute: TITLE }, // already names MotoQuant: no suffix
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
