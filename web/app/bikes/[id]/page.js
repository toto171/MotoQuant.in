// /bikes/[id] — server page. Reads the bike from the catalog committed with
// the build (lib/stockCatalog.js), so the heading and the simulated time are
// in the HTML whether or not the backend API is awake, and an id that is not
// in the catalog is a real 404. BikeDetailClient renders the page and fetches
// the full spec sheet in the browser.

import { notFound } from 'next/navigation';
import BikeDetailClient from './BikeDetailClient';
import {
  BIKE_PAGE_IDS,
  getStockBike,
  STOCK_RIDER_KG,
  STOCK_CONDITIONS,
} from '../../../lib/stockCatalog';

// Every catalog bike is known at build time; any other id is a 404.
export const dynamicParams = false;

export function generateStaticParams() {
  return BIKE_PAGE_IDS.map((id) => ({ id: String(id) }));
}

export default async function BikeDetailPage({ params }) {
  const { id } = await params;
  const stock = getStockBike(id);
  if (!stock) notFound();

  return <BikeDetailClient stock={stock} riderKg={STOCK_RIDER_KG} conditions={STOCK_CONDITIONS} />;
}
