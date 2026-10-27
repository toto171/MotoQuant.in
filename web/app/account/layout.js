// Auto-generated layout.js — owns the <head> metadata for /account.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "Account — your MotoQuant garage";
const DESCRIPTION = "Your saved runs and sign-in settings.";

export const metadata = {
  // absolute: TITLE already carries the brand — skip the '%s · MotoQuant' template
  title: { absolute: TITLE },
  description: DESCRIPTION,
  alternates: { canonical: '/account' },
  keywords: ["motoquant account"],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/account`,
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
  robots: { index: false, follow: false },
};

function breadcrumbs() {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
      { '@type': 'ListItem', position: 2, name: "Account", item: `${SITE_URL}/account` },
    ],
  };
}

export default function AccountLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
