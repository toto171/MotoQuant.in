// Server-component layout whose only purpose is to own the <head> metadata
// for /optimize. The actual page (page.js) is 'use client' and therefore
// cannot export `metadata` itself — App Router pulls it from the nearest
// server layout instead.
//
// NOTE: do not hard-code catalog counts (bike / parts / venue numbers) in
// the copy below — those are in flux and reconciled separately. Describe
// the feature generically.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE =
  'Motorcycle Build Optimizer India — Budget-Constrained Parts ROI Calculator';
const DESCRIPTION =
  'Free motorcycle build optimizer for Indian riders — enter your bike and budget in INR, and MotoQuant runs a physics-based 0/1 knapsack across every compatible exhaust, ECU, sprocket, and air filter. Returns the build that minimises your quarter-mile ET (or maximises trap speed), with cost-per-tenth, part synergies, and the next-best upgrade highlighted. Built for Hayabusa, R15, Duke 390, NS200, Interceptor 650, and 490+ more.';

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/optimize' },
  keywords: [
    'motorcycle build optimizer india',
    'motorcycle build optimizer',
    'parts roi calculator motorcycle',
    'budget drag build calculator',
    'cost per tenth motorcycle',
    'best mods for ktm rc 390 india',
    'best mods for r15 india',
    'best mods for ns200 india',
    'best mods for interceptor 650 india',
    'best motorcycle mods for quarter mile',
    'motorcycle upgrade path planner',
    'drag bike parts optimizer india',
    'which mods make my bike faster',
    'motorcycle horsepower per rupee',
    'exhaust ecu sprocket roi',
    'ecu flash cost india motorcycle',
    'motorcycle knapsack optimiser',
    'akrapovic vs sc project roi',
    'powertronic vs bazzaz vs dynojet',
    'cost per tenth inr',
    'motorcycle parts roi inr',
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/optimize`,
    type: 'website',
    images: [
      {
        url: `${SITE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: 'MotoQuant Build Optimizer — budget-constrained parts ROI',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: TITLE,
    description: DESCRIPTION,
  },
  robots: { index: true, follow: true },
};

const breadcrumb = {
  '@context': 'https://schema.org',
  '@type': 'BreadcrumbList',
  itemListElement: [
    { '@type': 'ListItem', position: 1, name: 'Home', item: SITE_URL },
    { '@type': 'ListItem', position: 2, name: 'Build Optimizer', item: `${SITE_URL}/optimize` },
  ],
};

export default function OptimizeLayout({ children }) {
  return (
    <>
      <StructuredData data={breadcrumb} />
      {children}
    </>
  );
}
