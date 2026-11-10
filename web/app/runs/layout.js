// Saved runs live in the visitor's browser, so there is nothing to index.
export const metadata = {
  title: 'Your runs | MotoQuant',
  description:
    'Runs you saved in the MotoQuant simulator. They are stored in this browser only; nothing is uploaded.',
  alternates: { canonical: '/runs' },
  robots: { index: false, follow: true },
};

export default function RunsLayout({ children }) {
  return children;
}
