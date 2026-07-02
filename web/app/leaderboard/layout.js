// Server-component layout that owns /leaderboard metadata.
export const metadata = {
  title: 'Leaderboard — Fastest Simulated Quarter-Mile Runs | MotoQuant',
  description:
    'The fastest saved quarter-mile simulations on MotoQuant, filterable by venue. Real physics, real conditions — Aamby Valley to Santa Pod.',
  alternates: { canonical: '/leaderboard' },
};

export default function LeaderboardLayout({ children }) {
  return children;
}
