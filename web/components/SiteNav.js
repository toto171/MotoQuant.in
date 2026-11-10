'use client';

/**
 * SiteNav — single source of truth for the top navigation (CLARITY v6).
 * Fixed top bar; also mounts CommandPalette + MobileToolBar once sitewide
 * (rendered OUTSIDE <header> because backdrop-filter on the header would
 * otherwise become the containing block of their position:fixed boxes).
 *
 * Desktop (>= lg): Simulator · Upgrades · Race-day setup · Bikes ·
 *   Leaderboard · Learn ▾ | search · GitHub · theme · Your runs · Open simulator
 * Below lg: logo, search, theme toggle, (sm+) CTA, hamburger drawer.
 * Paths are unchanged from earlier versions; only labels were renamed.
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Github, Menu, Search, X } from 'lucide-react';
import CommandPalette from './CommandPalette';
import GaugeMark from './GaugeMark';
import MobileToolBar from './MobileToolBar';
import ThemeToggle from './ThemeToggle';

const TOOL_LINKS = [
  { href: '/simulator',   label: 'Simulator' },
  { href: '/optimize',    label: 'Upgrades' },
  { href: '/autotune',    label: 'Race-day setup' },
  { href: '/bikes',       label: 'Bikes' },
  { href: '/leaderboard', label: 'Leaderboard' },
];

const LEARN_LINKS = [
  { href: '/docs/getting-started', label: 'Getting started',        desc: 'A 5-minute walkthrough of the simulator' },
  { href: '/docs/glossary',        label: 'Glossary',               desc: 'Drag-racing terms in plain English' },
  { href: '/docs/physics',         label: 'How the physics works',  desc: 'What the simulator calculates, step by step' },
  { href: '/validation',           label: 'Accuracy',               desc: 'How close the predictions are to real timeslips' },
  { href: '/blog',                 label: 'Blog',                   desc: 'Guides and explainers' },
  { href: '/about',                label: 'About',                  desc: 'Who builds this, and why it is open source' },
];

const GITHUB_URL = 'https://github.com/toto171/MotoQuant.in';

function isActive(pathname, link) {
  if (!pathname) return false;
  const target = link.match || link.href;
  if (target === '/') return pathname === '/';
  return pathname === target || pathname.startsWith(target + '/');
}

export default function SiteNav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [learnOpen, setLearnOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const learnRef = useRef(null);
  const learnBtnRef = useRef(null);

  // Global ⌘K / Ctrl+K — jump anywhere.
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
    setLearnOpen(false);
  }, [pathname]);

  // Learn dropdown: outside click + Escape close
  useEffect(() => {
    if (!learnOpen) return undefined;
    const onDown = (e) => {
      if (learnRef.current && !learnRef.current.contains(e.target)) setLearnOpen(false);
    };
    const onKey = (e) => {
      if (e.key === 'Escape') {
        setLearnOpen(false);
        learnBtnRef.current?.focus();
      }
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [learnOpen]);

  const learnActive = LEARN_LINKS.some((l) => isActive(pathname, l));

  // Active = full-strength ink with an accent underline; inactive = secondary ink.
  const linkCls = (active) =>
    [
      'whitespace-nowrap rounded-md px-1 py-2 transition-colors duration-200',
      active
        ? 'text-white underline decoration-accent decoration-2 underline-offset-[10px]'
        : 'text-white/70 hover:text-white',
    ].join(' ');

  const drawerLinkCls = (active) =>
    [
      'block min-h-[44px] rounded-lg border-l-2 px-4 py-2.5 transition-colors',
      active
        ? 'border-accent bg-white/[0.06] text-white'
        : 'border-transparent text-white/75 hover:bg-white/5 hover:text-white',
    ].join(' ');

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 h-16 border-b border-white/10 bg-asphalt-0/90 backdrop-blur-xl">
        <div className="mx-auto flex h-full max-w-7xl items-center justify-between gap-3 px-4 sm:px-6">
          <Link href="/" className="flex shrink-0 items-center gap-2.5" aria-label="MotoQuant home">
            <GaugeMark size={26} />
            <span className="font-display text-xl font-bold tracking-tight">
              <span className="text-white">Moto</span>
              <span className="text-accent">Quant</span>
            </span>
          </Link>

          <nav
            aria-label="Main"
            className="hidden items-center gap-3 text-sm font-medium lg:flex xl:gap-5"
          >
            {TOOL_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                aria-current={isActive(pathname, link) ? 'page' : undefined}
                className={linkCls(isActive(pathname, link))}
              >
                {link.label}
              </Link>
            ))}
            <div className="relative" ref={learnRef}>
              <button
                ref={learnBtnRef}
                type="button"
                onClick={() => setLearnOpen((v) => !v)}
                aria-expanded={learnOpen}
                aria-controls="nav-learn-menu"
                className={[
                  'flex items-center gap-1 rounded-md px-1 py-2 transition-colors duration-200',
                  learnActive || learnOpen ? 'text-white' : 'text-white/70 hover:text-white',
                ].join(' ')}
              >
                Learn
                <ChevronDown
                  size={14}
                  aria-hidden="true"
                  className={`transition-transform ${learnOpen ? 'rotate-180' : ''}`}
                />
              </button>
              <AnimatePresence>
                {learnOpen && (
                  <motion.ul
                    id="nav-learn-menu"
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-full mt-3 w-80 overflow-hidden rounded-xl border border-white/10 bg-asphalt-1 p-1.5 shadow-[var(--overlay-shadow)]"
                  >
                    {LEARN_LINKS.map((link) => (
                      <li key={link.href}>
                        <Link
                          href={link.href}
                          aria-current={isActive(pathname, link) ? 'page' : undefined}
                          className={[
                            'block rounded-lg px-3.5 py-2.5 transition-colors',
                            isActive(pathname, link) ? 'bg-white/[0.06]' : 'hover:bg-white/5',
                          ].join(' ')}
                        >
                          <span className="block text-sm font-semibold text-white">{link.label}</span>
                          <span className="mt-0.5 block text-xs font-normal text-white/60">{link.desc}</span>
                        </Link>
                      </li>
                    ))}
                    {/* Below xl the bar has no room for these two, so they live here. */}
                    <li className="mt-1 border-t border-white/10 pt-1 xl:hidden">
                      <a
                        href={GITHUB_URL}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 rounded-lg px-3.5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-white/5"
                      >
                        <Github size={15} aria-hidden="true" /> Source code on GitHub
                      </a>
                      <Link
                        href="/runs"
                        className="block rounded-lg px-3.5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-white/5"
                      >
                        Your runs
                      </Link>
                    </li>
                  </motion.ul>
                )}
              </AnimatePresence>
            </div>
          </nav>

          <div className="flex items-center gap-1.5 sm:gap-2">
            <button
              type="button"
              onClick={() => setPaletteOpen(true)}
              aria-label="Search bikes and pages (Ctrl+K)"
              title="Search bikes, pages, actions (Ctrl+K)"
              className="inline-flex h-11 min-w-[44px] items-center justify-center gap-2 rounded-xl border border-white/[0.12] px-3 text-white/70 transition-colors hover:border-white/30 hover:text-white"
            >
              <Search size={18} aria-hidden="true" />
              <kbd className="hidden font-sans text-xs text-white/55 2xl:inline">Ctrl K</kbd>
            </button>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="MotoQuant on GitHub"
              title="Source code on GitHub"
              className="hidden h-11 w-11 items-center justify-center rounded-xl border border-white/[0.12] text-white/70 transition-colors hover:border-white/30 hover:text-white xl:inline-flex"
            >
              <Github size={18} aria-hidden="true" />
            </a>
            <ThemeToggle />
            <Link
              href="/runs"
              title="Runs you saved in this browser"
              className="hidden h-11 items-center whitespace-nowrap rounded-xl px-2 text-sm font-medium text-white/70 transition-colors hover:text-white xl:inline-flex"
            >
              Your runs
            </Link>
            <Link href="/simulator" className="btn-primary btn-sm hidden whitespace-nowrap sm:inline-flex">
              Open simulator
            </Link>
            <button
              type="button"
              onClick={() => setOpen((v) => !v)}
              aria-label={open ? 'Close menu' : 'Open menu'}
              aria-expanded={open}
              aria-controls="site-nav-mobile"
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-white/[0.12] text-white/80 transition-colors hover:border-white/30 hover:text-white lg:hidden"
            >
              {open ? <X size={18} aria-hidden="true" /> : <Menu size={18} aria-hidden="true" />}
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
              className="absolute left-0 right-0 top-16 max-h-[calc(100dvh-4rem)] overflow-y-auto border-b border-white/10 bg-asphalt-0 lg:hidden"
            >
              <nav aria-label="Mobile" className="mx-auto grid max-w-6xl gap-1 px-4 pb-24 pt-3 text-base">
                <p className="px-4 pb-1 pt-1 text-xs font-semibold uppercase tracking-wider text-white/55">Tools</p>
                {TOOL_LINKS.map((link) => (
                  <Link key={link.href} href={link.href} className={drawerLinkCls(isActive(pathname, link))}>
                    {link.label}
                  </Link>
                ))}
                <p className="px-4 pb-1 pt-4 text-xs font-semibold uppercase tracking-wider text-white/55">Learn</p>
                {LEARN_LINKS.map((link) => (
                  <Link key={link.href} href={link.href} className={drawerLinkCls(isActive(pathname, link))}>
                    {link.label}
                    <span className="block text-xs font-normal text-white/55">{link.desc}</span>
                  </Link>
                ))}
                <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className={`${drawerLinkCls(false)} mt-2 flex items-center gap-2`}>
                  <Github size={16} aria-hidden="true" /> Source code on GitHub
                </a>
                <div className="my-1 border-t border-white/10" />
                <Link href="/runs" className={drawerLinkCls(isActive(pathname, { href: '/runs' }))}>
                  Your runs
                </Link>
                <Link href="/simulator" className="btn-primary mt-2">
                  Open simulator
                </Link>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
      <MobileToolBar />
    </>
  );
}
