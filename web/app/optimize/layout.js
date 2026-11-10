// Server-component layout whose only purpose is to own the <head> metadata
// for /optimize (page.js composes the page chrome and the client tool).
//
// NOTE: do not hard-code catalog counts (bike / parts / venue numbers) in
// the copy below — those are in flux and reconciled separately. Describe
// the feature generically.

import StructuredData, { SITE_URL } from '../StructuredData';

const TITLE = 'Best parts for your budget: motorcycle upgrade planner for India';
const DESCRIPTION =
  'Free motorcycle upgrade planner for Indian riders. Enter your bike and a budget in rupees and MotoQuant tests every compatible exhaust, ECU, sprocket and air filter, then shows the combination that makes your quarter-mile quickest (or your finish-line speed highest), with the cost per tenth of a second, parts that work well together and the best next upgrade.';

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
        alt: 'MotoQuant: best parts for your budget',
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
    { '@type': 'ListItem', position: 2, name: 'Best parts for your budget', item: `${SITE_URL}/optimize` },
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
