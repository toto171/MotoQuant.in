// Auto-generated layout.js — owns the <head> metadata for /pricing.
// The page is "use client" so it cannot export `metadata` itself; App Router
// pulls it from the nearest server layout instead.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = "Pricing — Free, Pro & Studio Plans for Motorcycle Drag Simulator";
const DESCRIPTION = "Simple, honest INR pricing for MotoQuant Pro. Free tier with 10 sims/day, Pro at Rs.499/mo for unlimited sims plus ROI engine, Studio at Rs.2,999/mo for Dragy import plus dyno calibration. GST-compliant, Razorpay-secured.";

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/pricing' },
  keywords: ["motoquant pricing", "drag simulator subscription", "motorcycle simulator india price", "razorpay drag racing tool"],
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
