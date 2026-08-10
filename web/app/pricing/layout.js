// Auto-generated layout.js — owns the <head> metadata for /pricing.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "Pricing — Free, Pro & Studio Plans for MotoQuant Drag Simulator (India)";
const DESCRIPTION = "Transparent INR pricing for MotoQuant Pro motorcycle drag simulator — free during the open beta. Free tier covers 541 bikes; Pro at Rs.499/mo adds unlimited sims and the parts ROI cost-per-tenth engine; Studio at Rs.1,999/mo adds Dragy GPS import and dyno calibration. No GST added, Razorpay + Stripe secured, monthly or yearly.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/pricing' },
  keywords: [
    "motoquant pricing",
    "motoquant pro price",
    "drag simulator subscription india",
    "motorcycle simulator india price",
    "razorpay drag racing tool",
    "parts roi calculator subscription",
    "dragy software subscription india",
    "quarter mile calculator pro",
    "motoquant studio plan",
    "motoquant free plan",
    "motorcycle drag tool pricing india",
    "indian motorcycle simulator subscription",
    "drag racing app monthly plan india",
    "free quarter mile simulator india",
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/pricing`,
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
      { '@type': 'ListItem', position: 2, name: "Pricing", item: `${SITE_URL}/pricing` },
    ],
  };
}

export default function PricingLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumbs()} />
      {children}
    </>
  );
}
