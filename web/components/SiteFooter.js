'use client';

/**
 * SiteFooter — unified footer with secondary nav, contact, legal,
 * and the brand wordmark. Replaces every per-page <footer> across
 * the marketing site.
 */

import Link from 'next/link';

const COLS = [
  {
    title: 'Product',
    links: [
      { href: '/simulator',            label: 'Simulator' },
      { href: '/features',             label: 'Features' },
      { href: '/pricing',              label: 'Pricing' },
      { href: '/login',                label: 'Sign in / Account' },
      { href: '/bikes',                label: 'Bikes catalog' },
    ],
  },
  {
    title: 'Documentation',
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
      { href: 'mailto:dhisetu@gmail.com', label: 'Contact' },
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
    <footer className="relative border-t border-brand-orange/15 bg-black mt-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-16 pb-10">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(4,1fr)]">
          {/* Brand block */}
          <div>
            <Link href="/" className="inline-flex items-center gap-2 group mb-4">
              <span className="text-2xl font-display font-bold tracking-tight">
                <span className="text-gradient-orange">Moto</span>
                <span className="text-white">Quant</span>
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold text-brand-accent border border-brand-accent/30 bg-brand-accent/5 tracking-widest">
                PRO
              </span>
            </Link>
            <p className="text-sm text-white/55 leading-relaxed max-w-sm">
              First-principles physics for motorcycle drag racing.
              Built in Pune for the Indian racing community —
              made for the strip and the salt.
            </p>
            <p className="mt-4 text-[10px] font-mono uppercase tracking-widest text-white/35">
              motoquant.in &middot; Made in India
            </p>
          </div>

          {COLS.map(col => (
            <div key={col.title}>
              <div className="text-[10px] font-mono uppercase tracking-widest text-brand-orange mb-3">
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

        <div className="mt-14 pt-8 border-t border-white/5 flex flex-col md:flex-row md:items-center md:justify-between gap-4 text-xs font-mono text-white/40">
          <p>
            &copy; {new Date().getFullYear()} MotoQuant Pro. Not affiliated with
            any motorcycle manufacturer.
          </p>
          <p className="flex flex-wrap gap-x-4 gap-y-1">
            <span>K5 · 10.0334s</span>
            <span className="text-white/20">·</span>
            <span>R1 · 10.2859s</span>
            <span className="text-white/20">·</span>
            <span>Hayabusa · 10.4712s</span>
            <span className="text-white/20">·</span>
            <span className="text-brand-accent">±0.0000 since Apr 30, 2026</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
