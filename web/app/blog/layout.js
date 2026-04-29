// Auto-generated layout.js — owns the <head> metadata for /blog.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "MotoQuant Blog — Drag Racing Physics, Tuning, and Validation Notes";
const DESCRIPTION = "Long-form posts on the physics of the perfect launch, why your R15 will not hit 14s, how to tune for Aamby Valley in November, and other deep-dives from the MotoQuant team.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/blog' },
  keywords: ["motorcycle drag racing blog", "india drag tuning guide", "aamby valley setup"],
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
