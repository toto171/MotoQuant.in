// Auto-generated layout.js — owns the <head> metadata for /signup.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "Create Account — MotoQuant";
const DESCRIPTION = "Create a free, optional MotoQuant account in seconds to save runs to your garage.";

export const metadata = {
  // absolute: TITLE already carries the brand — skip the '%s · MotoQuant' template
  title: { absolute: TITLE },
  description: DESCRIPTION,
  alternates: { canonical: '/signup' },
  keywords: ["motoquant signup"],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/signup`,
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
      { '@type': 'ListItem', position: 2, name: "Sign up", item: `${SITE_URL}/signup` },
    ],
  };
}

export default function SignupLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
