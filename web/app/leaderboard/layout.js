// Server-component layout that owns /leaderboard metadata.
export const metadata = {
  title: 'Leaderboard — every catalog bike ranked by quarter-mile time | MotoQuant',
  description:
    'Every motorcycle in the MotoQuant catalog ranked by its simulated stock quarter-mile time, all in the same conditions. Filter by type and engine size, then open any bike in the simulator.',
  alternates: { canonical: '/leaderboard' },
};

export default function LeaderboardLayout({ children }) {
  return children;
}
