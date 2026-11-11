// /bikes — server page. Owns the metadata and the JSON-LD for the catalog
// index (they used to sit in bikes/layout.js, which every /bikes/[id] page
// inherited). Renders the interactive catalog (BikesCatalogClient, which
// loads cards from the API) and, below it, a plain list of every bike built
// from the catalog committed with the build, so each bike page has a link a
// crawler can follow without running JavaScript or waking the API.

import Link from 'next/link';
import StructuredData, { SITE_URL, OG_IMAGE, breadcrumbSchema } from '../StructuredData';
import { stockBikes } from '../../lib/stockCatalog';
import BikesCatalogClient from './BikesCatalogClient';

const TITLE = '534 motorcycles: specs and quarter-mile times';
const DESCRIPTION =
  'Specs and simulated quarter-mile times for 534 motorcycles, from the Pulsar NS200 and R15 V4 to the Hayabusa. Open any bike in the free simulator.';

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/bikes' },
  keywords: [
    'motorcycle spec database india',
    'motorcycle catalog',
    'bike specifications database',
    'motorcycle dyno database',
    'motorcycle aero database',
    'motorcycle gear ratios',
    'hayabusa specs',
    'gsxr 1000 specs',
    'r1 specifications',
    'zx-10r specs',
    'ktm duke 390 specifications',
    'rc 390 specs',
    'bajaj pulsar ns200 specs',
    'apache rtr 200 specs',
    'yamaha r15 v4 specifications',
    'royal enfield interceptor 650 specs',
    'yezdi roadster 334 specs',
    'yezdi adventure 334 specs',
    'hero glamour 125 specs',
    'cfmoto 800nk specs',
    'hayabusa 2026 gen 3 specs',
    'pulsar n250 specifications',
    'ktm 890 duke specs',
    'ktm 890 duke r india',
    'suzuki gsx-s750 specs',
    'gsx-s750 quarter mile',
    'honda cb500x adventure specs',
    'honda cb500x india',
    'yamaha mt-15 v1 specs',
    'yamaha mt-15 2019 specifications',
    'bajaj pulsar 125 neon specs',
    'suzuki gsx-r600 k8 specs',
    'gsxr 600 k8 quarter mile',
    'indian motorcycle database',
    'indian bike specifications',
    'valley run bikes',
    'harley nightster rh975 quarter mile',
    'harley davidson nightster drag time',
    'nightster rh975 vs sportster s drag',
    'husqvarna svartpilen 250 quarter mile',
    'svartpilen 250 drag time india',
    'husqvarna svartpilen 250 india price',
    'honda cb125r quarter mile',
    'honda cb125r drag time',
    'honda cb125r india',
    'ktm 1390 super duke r evo quarter mile india',
    'ktm 1390 evo drag time',
    'ktm 1390 india price',
    'kawasaki ninja h2 sx vs hayabusa india',
    'triumph street triple 765 rs quarter mile india',
    'street triple 765 rs vs 765 r',
    'hayabusa 2026 launch control 2.6 seconds',
  ],
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/bikes`,
    type: 'website',
    images: [OG_IMAGE],
  },
  twitter: {
    card: 'summary_large_image',
    title: TITLE,
    description: DESCRIPTION,
    images: [OG_IMAGE],
  },
};

// CollectionPage tells search engines this is a browsable list, so they can
// send people straight to the right bike page.
function collectionSchema() {
  return {
    '@context': 'https://schema.org',
    '@type': 'CollectionPage',
    name: 'Motorcycle catalog',
    description: DESCRIPTION,
    url: `${SITE_URL}/bikes`,
    isPartOf: { '@id': `${SITE_URL}/#website` },
    about: {
      '@type': 'Thing',
      name: 'Motorcycle specifications and simulated quarter-mile times',
    },
    numberOfItems: 534,
    inLanguage: 'en-IN',
  };
}

const byText = (a, b) => a.localeCompare(b, 'en', { sensitivity: 'base', numeric: true });

function groupByMaker(bikes) {
  const makers = new Map();
  for (const b of bikes) {
    if (!makers.has(b.manufacturer)) makers.set(b.manufacturer, []);
    makers.get(b.manufacturer).push(b);
  }
  return [...makers.entries()]
    .sort(([a], [b]) => byText(a, b))
    .map(([maker, list]) => [maker, list.sort((a, b) => byText(a.model, b.model))]);
}

/** Every catalog bike, grouped by maker: plain server-rendered links. */
function AllBikesByMaker() {
  const groups = groupByMaker(stockBikes());
  return (
    <section aria-labelledby="all-bikes-heading" className="mt-14 border-t border-white/10 pt-10">
      <h2 id="all-bikes-heading" className="font-display text-xl font-semibold text-white">
        All bikes by maker
      </h2>
      <p className="mt-1 text-sm text-white/65">
        Simulated stock quarter-mile time next to each bike. Open a maker to see its bikes.
      </p>
      <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 items-start">
        {groups.map(([maker, list]) => (
          <details key={maker} className="card group px-4 py-1">
            <summary className="flex min-h-[44px] cursor-pointer list-none items-center justify-between gap-3 [&::-webkit-details-marker]:hidden">
              <span className="font-display text-base font-semibold text-white">{maker}</span>
              <span className="flex items-center gap-3 text-sm text-white/60 tabular-nums">
                {list.length}
                <span aria-hidden="true" className="text-lg transition-transform duration-200 group-open:rotate-45">
                  +
                </span>
              </span>
            </summary>
            <ul className="pb-3 pt-1 text-sm">
              {list.map((b) => (
                <li key={b.id} className="flex items-baseline justify-between gap-3 py-1">
                  <Link
                    href={`/bikes/${b.id}`}
                    className="text-white/80 underline-offset-2 hover:text-accent hover:underline"
                  >
                    {b.model}
                  </Link>
                  <span className="shrink-0 font-mono text-white/55 tabular-nums">{b.et_s.toFixed(3)} s</span>
                </li>
              ))}
            </ul>
          </details>
        ))}
      </div>
    </section>
  );
}

export default function BikesPage() {
  return (
    <>
      <StructuredData data={breadcrumbSchema([['Bikes', '/bikes']])} />
      <StructuredData data={collectionSchema()} />
      <BikesCatalogClient>
        <AllBikesByMaker />
      </BikesCatalogClient>
    </>
  );
}
