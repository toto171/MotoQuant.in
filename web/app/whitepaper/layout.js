// Auto-generated layout.js — owns the <head> metadata for /whitepaper.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "Whitepaper — The Physics Behind MotoQuant Pro";
const DESCRIPTION = "Complete technical whitepaper: RK4 integrator, Pacejka tire model, dyno SAE J1349 correction, weighted-benchmark validation methodology, 15 sub-model architecture. Read before you trust the numbers.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/whitepaper' },
  keywords: ["drag simulator whitepaper", "motorcycle physics paper", "pacejka tire model india"],
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
