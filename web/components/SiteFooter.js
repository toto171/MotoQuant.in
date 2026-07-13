'use client';

/**
 * SiteFooter — quiet 4-column footer on asphalt (STAGED v4 skin).
 * Secondary nav, contact, legal, the brand wordmark and the pinned
 * reference-baselines line. Replaces every per-page <footer> across
 * the marketing site. No glows — the footer is the quietest surface
 * on the slip.
 */

import Link from 'next/link';
import StageDots from './StageDots';

const COLS = [
  {
    title: 'Product',
    links: [
      { href: '/simulator',            label: 'Simulator' },
      { href: '/features',             label: 'Features' },
      { href: '/pricing',              label: 'Pricing' },
      { href: '/leaderboard',          label: 'Leaderboard' },
      { href: '/login',                label: 'Sign in / Account' },
      { href: '/bikes',                label: 'Bikes catalog' },
    ],
  },
  {
    title: 'Data',
    links: [
      { href: '/docs/getting-started', label: 'Getting started' },
      { href: '/docs/physics',         label: 'Physics docs' },
      { href: '/docs/validation',      label: 'Validation data' },
      { href: '/whitepaper',           label: 'Whitepaper' },
    ],
  },
  {
    title: 'Company',
    links: [
      { href: '/about',                label: 'About' },
      { href: '/blog',                 label: 'Blog' },
      { href: 'mailto:motoquant@gmail.com', label: 'Contact' },
    ],
  },
  {
    title: 'Legal',
    links: [
      { href: '/terms',                label: 'Terms' },
      { href: '/privacy',              label: 'Privacy' },
    ],
  },
];

export default function SiteFooter() {
  return (
    <footer className="relative border-t border-white/[0.08] bg-asphalt-0 mt-24">
      <div className="max-w-6xl mx-auto px-6 pt-16 pb-10">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(4,1fr)]">
          {/* Brand block */}
          <div>
            <Link href="/" className="inline-flex items-center gap-2.5 group mb-4">
              <StageDots size={5} />
              <span className="font-display font-bold uppercase text-xl tracking-[0.04em] text-white">
                MotoQuant
              </span>
            </Link>
            <p className="text-sm text-white/50 leading-relaxed max-w-sm">
              First-principles physics for motorcycle drag racing.
              Built in Pune for the Indian racing community —
              made for the strip and the salt.
            </p>
            <p className="mt-4 label-mono">
              motoquant.in &middot; Built in India &middot; Free during beta
            </p>
          </div>

          {COLS.map(col => (
            <div key={col.title}>
              <div className="label-mono mb-3">
                {col.title}
              </div>
              <ul className="space-y-2">
                {col.links.map(l => (
                  <li key={l.href}>
                    <Link
                      href={l.href}
                      className="text-sm text-white/65 hover:text-white transition-colors"
                    >
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 pt-8 border-t border-white/[0.08] flex flex-col md:flex-row md:items-center md:justify-between gap-4 text-xs font-mono tabular-nums text-white/40">
          <p>
            &copy; {new Date().getFullYear()} MotoQuant Pro. Not affiliated with
            any motorcycle manufacturer.
          </p>
          <p className="flex flex-wrap gap-x-4 gap-y-1">
            <span>K5 · 9.9331s</span>
            <span className="text-white/20">·</span>
            <span>R1 · 10.1436s</span>
            <span className="text-white/20">·</span>
            <span>Hayabusa · 10.3633s</span>
            <span className="text-white/20">·</span>
            <span>±0.0000 since Jul 13, 2026</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
