'use client';

/**
 * SiteNav — single source of truth for the top navigation across every
 * marketing/page surface. Lives in <body> at fixed top, blurs the
 * background on scroll, exposes the mobile drawer.
 *
 * One component used by:
 *   /, /features, /about, /pricing, /blog, /blog/*, /docs/*, /bikes,
 *   /bikes/[id], /whitepaper, /optimize, /autotune, /login, /signup,
 *   /account, /terms, /privacy
 *
 * The /docs sub-tree previously had its own copy — replaced by this
 * to keep visual rhythm + nav state in lock-step site-wide.
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { useAuth } from './AuthProvider';

const NAV_LINKS = [
  { href: '/simulator',                 label: 'Simulator' },
  { href: '/optimize',                  label: 'Optimize' },
  { href: '/autotune',                  label: 'Tune' },
  { href: '/bikes',                     label: 'Bikes' },
  { href: '/features',                  label: 'Features' },
  { href: '/whitepaper',                label: 'Whitepaper' },
  { href: '/docs/getting-started',      label: 'Docs',     match: '/docs' },
  { href: '/blog',                      label: 'Blog' },
  { href: '/about',                     label: 'About' },
  { href: '/pricing',                   label: 'Pricing' },
];

function isActive(pathname, link) {
  if (!pathname) return false;
  const target = link.match || link.href;
  if (target === '/') return pathname === '/';
  return pathname === target || pathname.startsWith(target + '/');
}

export default function SiteNav() {
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => { setOpen(false); }, [pathname]);

  return (
    <header
      className={[
        'fixed top-0 inset-x-0 z-50 h-16 border-b transition-colors duration-300',
        scrolled
          ? 'bg-black/80 backdrop-blur-xl border-brand-orange/15'
          : 'bg-black/40 backdrop-blur-md border-white/5',
      ].join(' ')}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <span className="text-xl font-display font-bold tracking-tight">
            <span className="text-gradient-orange">Moto</span>
            <span className="text-white">Quant</span>
          </span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold text-brand-accent border border-brand-accent/30 bg-brand-accent/5 tracking-widest">
            PRO
          </span>
        </Link>

        <nav className="hidden lg:flex gap-7 items-center text-sm font-mono">
          {NAV_LINKS.map(link => {
            const active = isActive(pathname, link);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={[
                  'transition-colors duration-200',
                  active ? 'text-brand-orange' : 'text-white/60 hover:text-white',
                ].join(' ')}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          {isAuthenticated ? (
            <Link
              href="/account"
              title="Your account"
              className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-white/10 hover:border-brand-orange/50 transition-colors"
            >
              <span className="w-5 h-5 rounded-full bg-brand-orange/20 text-brand-orange text-[10px] font-bold flex items-center justify-center uppercase">
                {user?.email?.[0] ?? 'U'}
              </span>
              <span className="text-xs font-mono text-white/70 max-w-[9rem] truncate">
                {user?.email?.split('@')[0]}
              </span>
              {user?.tier && user.tier !== 'free' && (
                <span className="text-[9px] font-mono uppercase tracking-wider text-brand-accent">
                  {user.tier}
                </span>
              )}
            </Link>
          ) : (
            <Link
              href="/login"
              className="hidden sm:block text-sm font-mono text-white/60 hover:text-white transition-colors whitespace-nowrap"
            >
              Sign in
            </Link>
          )}
          <Link
            href="/simulator"
            className="px-3 sm:px-4 py-2 bg-brand-orange hover:bg-brand-orangeLight text-black font-display font-bold rounded-md text-xs sm:text-sm transition-colors whitespace-nowrap shadow-orange-soft"
          >
            Launch <span className="hidden sm:inline">Simulator</span>
          </Link>
          <button
            type="button"
            onClick={() => setOpen(v => !v)}
            aria-label={open ? 'Close menu' : 'Open menu'}
            aria-expanded={open}
            aria-controls="site-nav-mobile"
            className="lg:hidden p-2 rounded-md border border-white/10 text-white/80 hover:text-white hover:border-brand-orange/50 transition-colors"
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div
            id="site-nav-mobile"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18 }}
            className="lg:hidden absolute top-16 left-0 right-0 bg-black/95 backdrop-blur-xl border-b border-brand-orange/20"
          >
            <nav className="max-w-6xl mx-auto px-4 py-4 grid gap-1 font-mono text-sm">
              {NAV_LINKS.map(link => {
                const active = isActive(pathname, link);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={[
                      'px-4 py-3 rounded-md transition-colors',
                      active
                        ? 'text-brand-orange bg-brand-orange/10'
                        : 'text-white/70 hover:text-white hover:bg-white/5',
                    ].join(' ')}
                  >
                    {link.label}
                  </Link>
                );
              })}
              <div className="my-1 border-t border-white/10" />
              <Link
                href={isAuthenticated ? '/account' : '/login'}
                className={[
                  'px-4 py-3 rounded-md transition-colors',
                  isActive(pathname, { href: isAuthenticated ? '/account' : '/login' })
                    ? 'text-brand-orange bg-brand-orange/10'
                    : 'text-white/70 hover:text-white hover:bg-white/5',
                ].join(' ')}
              >
                {isAuthenticated
                  ? `Account — ${user?.email?.split('@')[0] ?? ''}`
                  : 'Sign in / Create account'}
              </Link>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
