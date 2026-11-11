// Every timeslip is computed from its link, so there is nothing for a search
// engine to index; shared previews use the site-wide card.
export const metadata = {
  title: 'Timeslip',
  description:
    'A simulated quarter-mile timeslip. The link holds the bike, its changes and the conditions; the page runs them through the physics when it opens.',
  // Its own canonical, so the page never inherits another page's.
  alternates: { canonical: '/timeslip' },
  robots: { index: false, follow: true },
};

export default function TimeslipLayout({ children }) {
  return children;
}
