/**
 * PostBikeLinks — "Bikes in this post" on a blog post: one plain link per
 * catalog bike the post is about, to its /bikes/[id] page. No time is shown
 * here: posts quote times under their own venue conditions, and the stock
 * catalog time (default conditions) would read as a contradiction.
 *
 * Server component. Names and times come from the catalog committed with the
 * build (lib/stockCatalog.js), so a link never points at an id that is not in
 * the catalog: an unknown id is dropped, not rendered. Only list a bike when
 * the catalog entry is the same bike the post discusses (name AND years).
 */

import Link from 'next/link';
import { getStockBike, stockBikeName } from '../lib/stockCatalog';

export default function PostBikeLinks({ ids = [] }) {
  const bikes = ids.map((id) => getStockBike(id)).filter(Boolean);
  if (bikes.length === 0) return null;
  return (
    <div className="max-w-2xl mx-auto mt-12">
      <h2 className="font-display font-bold text-lg text-white mb-3">
        {bikes.length === 1 ? 'The bike in this post' : 'Bikes in this post'}
      </h2>
      <ul className="text-sm text-white/70 space-y-2">
        {bikes.map((b) => (
          <li key={b.id}>
            <Link
              href={`/bikes/${b.id}`}
              className="font-medium text-accent underline-offset-2 hover:text-accent-bright hover:underline"
            >
              {stockBikeName(b)}
            </Link>
            : specs and the simulated stock quarter-mile time.
          </li>
        ))}
      </ul>
    </div>
  );
}
