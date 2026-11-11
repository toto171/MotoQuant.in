// Per-bike metadata and structured data for /bikes/[id].
//
// Everything here comes from the catalog files committed with the build
// (lib/stockCatalog.js), never from the backend API. The API runs on a free
// host that sleeps; when metadata waited on it, a cold start gave hundreds of
// bike pages the same fallback title and no crawlable heading. Now every page
// has its own title, description and JSON-LD whether or not the API is up.
// The page itself still fetches the full spec sheet in the browser.

import { notFound } from 'next/navigation';
import StructuredData, { SITE_URL, OG_IMAGE, OG_IMAGE_URL, breadcrumbSchema } from '../../StructuredData';
import {
  getStockBike,
  stockBikeName,
  STOCK_RIDER_KG,
  STOCK_CONDITIONS,
} from '../../../lib/stockCatalog';

function describe(bike) {
  const alt = Math.round(STOCK_CONDITIONS.altitude_m);
  const lead =
    `Simulated stock quarter mile: ${bike.et_s.toFixed(3)} s at ${bike.trap_kmh.toFixed(1)} km/h` +
    ` with a ${STOCK_RIDER_KG} kg rider at ${alt} m. ${Math.round(bike.displacement_cc)} cc.`;
  const full = `${lead} Add parts or change the strip in the free simulator.`;
  return full.length <= 160 ? full : `${lead} Try it in the free simulator.`;
}

export async function generateMetadata({ params }) {
  const { id } = await params;
  const bike = getStockBike(id);
  if (!bike) notFound();

  const name = stockBikeName(bike);
  const title = `${name} quarter-mile time`;
  const description = describe(bike);
  const path = `/bikes/${bike.id}`;

  return {
    title,
    description,
    alternates: { canonical: path },
    openGraph: {
      title,
      description,
      url: `${SITE_URL}${path}`,
      type: 'website',
      images: [OG_IMAGE],
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
      images: [OG_IMAGE],
    },
  };
}

function vehicleSchema(bike) {
  const name = stockBikeName(bike);
  return {
    '@context': 'https://schema.org',
    '@type': 'Vehicle',
    '@id': `${SITE_URL}/bikes/${bike.id}#vehicle`,
    name,
    url: `${SITE_URL}/bikes/${bike.id}`,
    image: OG_IMAGE_URL,
    description: describe(bike),
    brand: { '@type': 'Brand', name: bike.manufacturer },
    manufacturer: { '@type': 'Organization', name: bike.manufacturer },
    model: bike.model,
    vehicleModelDate: String(bike.year_from),
    category: bike.category.replace(/_/g, ' '),
    bodyType: 'Motorcycle',
    vehicleEngine: {
      '@type': 'EngineSpecification',
      engineDisplacement: {
        '@type': 'QuantitativeValue',
        value: Math.round(bike.displacement_cc),
        unitCode: 'CMQ', // cubic centimetre
      },
    },
  };
}

export default async function BikeDetailLayout({ children, params }) {
  const { id } = await params;
  const bike = getStockBike(id);
  if (!bike) notFound();

  return (
    <>
      <StructuredData data={vehicleSchema(bike)} />
      <StructuredData
        data={breadcrumbSchema([
          ['Bikes', '/bikes'],
          [stockBikeName(bike), `/bikes/${bike.id}`],
        ])}
      />
      {children}
    </>
  );
}
