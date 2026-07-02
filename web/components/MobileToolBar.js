'use client';

/**
 * MobileToolBar — app-style fixed bottom tab bar for the five product tools
 * (Cockpit v3 flagship nav). Rendered only below lg and only on tool routes,
 * where the hamburger drawer buried the product two taps deep. Mounted once
 * from SiteNav so every page gets it without per-page wiring.
 *
 * Translucent blur so overlapping the page tail stays readable; safe-area
 * inset respected for gesture-nav phones.
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
      className="fixed inset-x-0 bottom-0 z-50 border-t border-white/10 bg-black/85 backdrop-blur-xl lg:hidden"
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
              className={`flex min-w-[56px] flex-col items-center gap-1 px-3 pb-2 pt-2.5 transition-colors ${
                active ? 'text-brand-orange' : 'text-white/50 hover:text-white/80'
              }`}
            >
              <Icon size={18} aria-hidden="true" />
              <span className="font-mono text-[9px] uppercase tracking-[0.18em]">{t.label}</span>
              <span
                aria-hidden="true"
                className={`h-0.5 w-6 rounded-full ${active ? 'bg-brand-orange' : 'bg-transparent'}`}
              />
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
