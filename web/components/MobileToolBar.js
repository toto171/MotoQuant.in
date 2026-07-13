'use client';

/**
 * MobileToolBar — app-style fixed bottom tab bar for the five product tools
 * (STAGED v4 skin). Rendered only below lg and only on tool routes, where
 * the hamburger drawer buried the product two taps deep. Mounted once from
 * SiteNav so every page gets it without per-page wiring.
 *
 * Translucent blur so overlapping the page tail stays readable; safe-area
 * inset respected for gesture-nav phones. Active tab = volt text + volt
 * tint pill (the one accent detail in this viewport strip).
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bike, Gauge, Trophy, Wrench, Zap } from 'lucide-react';

const TOOLS = [
  { href: '/simulator', label: 'Simulate', icon: Gauge },
  { href: '/optimize', label: 'Optimize', icon: Wrench },
  { href: '/autotune', label: 'Tune', icon: Zap },
  { href: '/bikes', label: 'Bikes', icon: Bike },
  { href: '/leaderboard', label: 'Board', icon: Trophy },
];

const TOOL_PREFIXES = ['/simulator', '/optimize', '/autotune', '/bikes', '/leaderboard'];

export default function MobileToolBar() {
  const pathname = usePathname() || '';
  const onToolRoute = TOOL_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(p + '/')
  );
  if (!onToolRoute) return null;

  return (
    <nav
      aria-label="Tools"
      className="fixed inset-x-0 bottom-0 z-50 border-t border-white/[0.08] bg-asphalt-0/95 backdrop-blur-xl lg:hidden"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      <div className="mx-auto flex max-w-md items-stretch justify-around">
        {TOOLS.map((t) => {
          const active = pathname === t.href || pathname.startsWith(t.href + '/');
          const Icon = t.icon;
          return (
            <Link
              key={t.href}
              href={t.href}
              aria-current={active ? 'page' : undefined}
              className={`flex min-w-[56px] flex-col items-center gap-1 px-2 pb-2 pt-2 transition-colors ${
                active ? 'text-accent' : 'text-white/45 hover:text-white/80'
              }`}
            >
              <span
                className={`flex h-7 w-12 items-center justify-center rounded-full transition-colors ${
                  active ? 'bg-accent/10' : 'bg-transparent'
                }`}
              >
                <Icon size={18} aria-hidden="true" />
              </span>
              <span className="font-mono text-[9px] uppercase tracking-[0.18em]">{t.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
