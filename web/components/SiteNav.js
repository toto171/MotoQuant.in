'use client';

/**
 * SiteNav — single source of truth for the top navigation across every
 * surface (IGNITION v5 skin). Fixed top, blurs over the page, exposes the
 * mobile drawer and mounts CommandPalette + MobileToolBar once sitewide.
 *
 * Brand lockup: GaugeMark (the redline Q) + the sentence-case wordmark —
 * Moto white / Quant signal-orange, per the identity kit.
 *
 * Structure (July 2026): the five product tools stay first-class links;
 * the five content pages fold into a Resources dropdown so the bar reads
 * as product-first instead of a ten-link strip.
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Menu, Search, X } from 'lucide-react';
import { useAuth } from './AuthProvider';
import CommandPalette from './CommandPalette';
import GaugeMark from './GaugeMark';
import MobileToolBar from './MobileToolBar';

const TOOL_LINKS = [
  { href: '/simulator',   label: 'Simulator' },
  { href: '/optimize',    label: 'Optimize' },
  { href: '/autotune',    label: 'Tune' },
  { href: '/bikes',       label: 'Bikes' },
  { href: '/leaderboard', label: 'Leaderboard' },
];

const RESOURCE_LINKS = [
  { href: '/features',             label: 'Features' },
  { href: '/docs/getting-started', label: 'Docs', match: '/docs' },
  { href: '/whitepaper',           label: 'Whitepaper' },
  { href: '/blog',                 label: 'Blog' },
  { href: '/about',                label: 'About' },
];

const PRICING_LINK = { href: '/pricing', label: 'Pricing' };

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
  const [resOpen, setResOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const resRef = useRef(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Global ⌘K / Ctrl+K — the flagship jump-anywhere affordance.
  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  // Close menus on route change
  useEffect(() => {
    setOpen(false);
    setResOpen(false);
  }, [pathname]);

  // Resources dropdown: outside click + Escape close
  useEffect(() => {
    if (!resOpen) return undefined;
    const onDown = (e) => {
      if (resRef.current && !resRef.current.contains(e.target)) setResOpen(false);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') setResOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [resOpen]);

  const resourcesActive = RESOURCE_LINKS.some((l) => isActive(pathname, l));

  // Active link = white with a 2px signal-orange underline; inactive = quiet white.
  const linkCls = (active) =>
    [
      'transition-colors duration-200',
      active
        ? 'text-white underline decoration-accent decoration-2 underline-offset-[10px]'
        : 'text-white/60 hover:text-white',
    ].join(' ');

  const drawerLinkCls = (active) =>
    [
      'px-4 py-3 rounded-md border-l-2 transition-colors',
      active
        ? 'border-accent bg-white/[0.06] text-white'
        : 'border-transparent text-white/70 hover:text-white hover:bg-white/5',
    ].join(' ');

  return (
    <header
      className={[
        'fixed top-0 inset-x-0 z-50 h-16 border-b border-white/[0.08] transition-colors duration-300',
        scrolled
          ? 'bg-asphalt-0/90 backdrop-blur-xl'
          : 'bg-asphalt-0/85 backdrop-blur',
      ].join(' ')}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-full flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <GaugeMark size={26} />
          <span className="font-display font-bold text-xl tracking-tight">
            <span className="text-white">Moto</span>
            <span className="text-accent">Quant</span>
          </span>
        </Link>

        {/* gap-4 until xl: at 1024-1100px the full cluster (5 tools + Pricing
            + Resources + search + auth + CTA) was overflowing the viewport by
            ~60px and clipping the CTA (field-reported). */}
        <nav className="hidden lg:flex gap-4 xl:gap-6 items-center text-sm font-mono">
          {TOOL_LINKS.map((link) => (
            <Link key={link.href} href={link.href} className={linkCls(isActive(pathname, link))}>
              {link.label}
            </Link>
          ))}
          <span aria-hidden="true" className="h-4 w-px bg-white/15" />
          <Link
            href={PRICING_LINK.href}
            className={linkCls(isActive(pathname, PRICING_LINK))}
          >
            {PRICING_LINK.label}
          </Link>
          <div className="relative" ref={resRef}>
            <button
              type="button"
              onClick={() => setResOpen((v) => !v)}
              aria-expanded={resOpen}
              aria-haspopup="menu"
              className={[
                'flex items-center gap-1 transition-colors duration-200',
                resourcesActive || resOpen
                  ? 'text-white'
                  : 'text-white/60 hover:text-white',
              ].join(' ')}
            >
              Resources
              <ChevronDown
                size={13}
                aria-hidden="true"
                className={`transition-transform ${resOpen ? 'rotate-180' : ''}`}
              />
            </button>
            <AnimatePresence>
              {resOpen && (
                <motion.div
                  role="menu"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.15 }}
                  className="absolute right-0 top-full mt-3 w-44 overflow-hidden rounded-xl border border-white/10 bg-asphalt-1/95 backdrop-blur-xl shadow-2xl"
                >
                  {RESOURCE_LINKS.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      role="menuitem"
                      className={[
                        'block px-4 py-2.5 text-sm transition-colors',
                        isActive(pathname, link)
                          ? 'text-white bg-white/[0.06]'
                          : 'text-white/70 hover:text-white hover:bg-white/5',
                      ].join(' ')}
                    >
                      {link.label}
                    </Link>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </nav>

        <div className="flex items-center gap-2 sm:gap-3">
          <button
            type="button"
            onClick={() => setPaletteOpen(true)}
            aria-label="Search — Ctrl+K"
            title="Search bikes, pages, actions (Ctrl+K)"
            className="flex items-center gap-2 rounded-md border border-white/10 px-2.5 py-2 text-white/60 transition-colors hover:border-white/30 hover:text-white"
          >
            <Search size={15} aria-hidden="true" />
            <kbd className="label-mono hidden md:max-lg:inline xl:inline">⌘K</kbd>
          </button>
          {isAuthenticated ? (
            <Link
              href="/account"
              title="Your account"
              className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-md border border-white/10 hover:border-white/30 transition-colors"
            >
              <span className="w-5 h-5 rounded-full bg-white/10 text-white/80 text-[10px] font-bold flex items-center justify-center uppercase">
                {user?.email?.[0] ?? 'U'}
              </span>
              <span className="text-xs font-mono text-white/70 max-w-[9rem] truncate">
                {user?.email?.split('@')[0]}
              </span>
              {user?.tier && user.tier !== 'free' && (
                <span className="text-[9px] font-mono uppercase tracking-wider text-mint">
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
          <Link href="/simulator" className="btn-primary btn-sm whitespace-nowrap">
            {/* Full label only where it fits: below lg and at xl+ the CTA reads
                "Run a sim"; in the tight lg..xl band it shortens to "Run" so
                the cluster never clips. */}
            <span>
              Run
              <span className="hidden sm:max-lg:inline xl:inline"> a sim</span>
            </span>
          </Link>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? 'Close menu' : 'Open menu'}
            aria-expanded={open}
            aria-controls="site-nav-mobile"
            className="lg:hidden p-2 rounded-md border border-white/10 text-white/80 hover:text-white hover:border-white/30 transition-colors"
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
            className="lg:hidden absolute top-16 left-0 right-0 bg-asphalt-0/95 backdrop-blur-xl border-b border-white/[0.08] max-h-[calc(100vh-4rem)] overflow-y-auto"
          >
            <nav className="max-w-6xl mx-auto px-4 py-4 grid gap-1 font-mono text-sm">
              <span className="label-mono px-4 pt-1 pb-1.5">Tools</span>
              {TOOL_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={drawerLinkCls(isActive(pathname, link))}
                >
                  {link.label}
                </Link>
              ))}
              <span className="label-mono px-4 pt-3 pb-1.5">Resources</span>
              {[...RESOURCE_LINKS, PRICING_LINK].map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className={drawerLinkCls(isActive(pathname, link))}
                >
                  {link.label}
                </Link>
              ))}
              <div className="my-1 border-t border-white/10" />
              <Link
                href={isAuthenticated ? '/account' : '/login'}
                className={drawerLinkCls(
                  isActive(pathname, { href: isAuthenticated ? '/account' : '/login' })
                )}
              >
                {isAuthenticated
                  ? `Account — ${user?.email?.split('@')[0] ?? ''}`
                  : 'Sign in / Create account'}
              </Link>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      <MobileToolBar />
    </header>
  );
}
