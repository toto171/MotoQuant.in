/**
 * SiteFooter — tidy four-column footer (CLARITY v6). Product / Learn /
 * Project / Legal, the brand lockup, and the open-source line. Replaces every
 * per-page <footer>. Server-component safe.
 */

import Link from 'next/link';
import GaugeMark from './GaugeMark';

const REPO = 'https://github.com/toto171/MotoQuant.in';

const COLS = [
  {
    title: 'Product',
    links: [
      { href: '/simulator',   label: 'Simulator' },
      { href: '/optimize',    label: 'Upgrades' },
      { href: '/autotune',    label: 'Race-day setup' },
      { href: '/bikes',       label: 'Bikes' },
      { href: '/leaderboard', label: 'Leaderboard' },
    ],
  },
  {
    title: 'Learn',
    links: [
      { href: '/docs/getting-started', label: 'Getting started' },
      { href: '/docs/glossary',        label: 'Glossary' },
      { href: '/docs/physics',         label: 'How the physics works' },
      { href: '/validation',           label: 'Accuracy' },
      { href: '/whitepaper',           label: 'Whitepaper' },
      { href: '/blog',                 label: 'Blog' },
    ],
  },
  {
    title: 'Project',
    links: [
      { href: '/about',    label: 'About' },
      { href: '/features', label: 'Features' },
      { href: REPO,        label: 'Source code on GitHub', external: true },
      { href: `${REPO}/issues`, label: 'Report a problem', external: true },
      { href: `${REPO}/blob/main/CONTRIBUTING.md`, label: 'Contribute', external: true },
      { href: '/contact',  label: 'Contact' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { href: '/terms',   label: 'Terms' },
      { href: '/privacy', label: 'Privacy' },
      { href: `${REPO}/blob/main/LICENSE`, label: 'MIT License', external: true },
    ],
  },
];

const LINK_CLS = 'inline-flex min-h-[32px] items-center text-sm text-white/70 transition-colors hover:text-white';

export default function SiteFooter() {
  return (
    <footer className="relative mt-20 border-t border-white/10 bg-asphalt-0">
      <div className="mx-auto max-w-6xl px-6 pb-10 pt-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div className="sm:col-span-2 lg:col-span-1">
            <Link href="/" className="mb-4 inline-flex items-center gap-2.5" aria-label="MotoQuant home">
              <GaugeMark size={30} />
              <span className="font-display text-xl font-bold tracking-tight">
                <span className="text-white">Moto</span>
                <span className="text-accent">Quant</span>
              </span>
            </Link>
            <p className="max-w-sm text-sm leading-relaxed text-white/65">
              A free motorcycle quarter-mile simulator. Pick a bike, see how fast it
              should run, and find out what makes it quicker. Built in India for
              the drag-racing community.
            </p>
          </div>

          {COLS.map((col) => (
            <div key={col.title}>
              <h2 className="mb-2 font-display text-sm font-semibold text-white">{col.title}</h2>
              <ul>
                {col.links.map((l) => (
                  <li key={l.href}>
                    {l.external ? (
                      <a href={l.href} target="_blank" rel="noopener noreferrer" className={LINK_CLS}>
                        {l.label}
                      </a>
                    ) : (
                      <Link href={l.href} className={LINK_CLS}>
                        {l.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col gap-2 border-t border-white/10 pt-6 text-sm text-white/60 md:flex-row md:items-center md:justify-between">
          <p>Free and open source &middot; MIT License</p>
          <p>
            &copy; {new Date().getFullYear()} MotoQuant. Not affiliated with any motorcycle manufacturer.
          </p>
        </div>
      </div>
    </footer>
  );
}
