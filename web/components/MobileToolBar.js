'use client';

/**
 * MobileToolBar — app-style fixed bottom tab bar for the five tools
 * (CLARITY v6). Rendered only below lg and only on tool routes, where the
 * hamburger drawer would bury the product two taps deep. Mounted once from
 * SiteNav. Labels (paths unchanged): Simulate / Upgrades / Setup / Bikes / Board.
 *
 * Adds the `mq-toolbar` class; globals.css pads <body> while it is mounted so
 * it never covers page content. Safe-area inset respected.
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bike, Gauge, Trophy, Wrench, Zap } from 'lucide-react';

const TOOLS = [
  { href: '/simulator', label: 'Simulate', icon: Gauge },
  { href: '/optimize', label: 'Upgrades', icon: Wrench },
  { href: '/autotune', label: 'Setup', icon: Zap },
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
      className="mq-toolbar fixed inset-x-0 bottom-0 z-50 border-t border-white/10 bg-asphalt-0/95 backdrop-blur-xl lg:hidden"
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
              className={`flex min-h-[56px] min-w-[56px] flex-1 flex-col items-center justify-center gap-0.5 px-1 py-1.5 transition-colors ${
                active ? 'text-accent' : 'text-white/60 hover:text-white'
              }`}
            >
              <span
                className={`flex h-7 w-12 items-center justify-center rounded-full transition-colors ${
                  active ? 'bg-accent/15' : 'bg-transparent'
                }`}
              >
                <Icon size={18} aria-hidden="true" />
              </span>
              <span className="text-xs font-medium">{t.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
