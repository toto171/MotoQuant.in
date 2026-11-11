// Server-component layout that owns /leaderboard metadata. The count and the
// conditions come from the same stock_times.json the board renders.
import { SITE_URL, OG_IMAGE } from '../StructuredData';
import data from './stock_times.json';

const TITLE = `${data.bikes.length} bikes ranked by quarter-mile time`;
const DESCRIPTION =
  `Every bike in the catalog ranked by its simulated stock quarter-mile time, with a ${data.rider_kg} kg rider at ` +
  `${Math.round(data.conditions.altitude_m)} m. Filter by type and engine size.`;

export const metadata = {
  title: TITLE,
  description: DESCRIPTION,
  alternates: { canonical: '/leaderboard' },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `${SITE_URL}/leaderboard`,
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

export default function LeaderboardLayout({ children }) {
  return children;
}
