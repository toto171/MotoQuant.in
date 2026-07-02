'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

/**
 * DocsMobileNav — collapsible section list for <md viewports, where the
 * desktop sidebar is hidden and phones previously had NO docs navigation.
 *
 * Native <details>/<summary> keeps this dependency-free, keyboard/screen-
 * reader accessible, and reduced-motion safe (no animation at all). A tiny
 * client leaf (usePathname only — SSG-safe, no Suspense needed) so the
 * summary row can name the page you are on.
 */
export default function DocsMobileNav({ pages }) {
  const pathname = usePathname();
  const current = pages.find((p) => p.href === pathname);

  return (
    <details className="md:hidden card mb-8 overflow-hidden group">
      <summary className="flex items-center justify-between gap-3 px-4 py-3 cursor-pointer select-none list-none [&::-webkit-details-marker]:hidden min-h-[44px]">
        <span className="flex items-baseline gap-3 min-w-0">
          <span className="label-mono text-brand-orange shrink-0">Docs</span>
          <span className="font-mono text-sm text-white/85 truncate">
            {current ? current.label : 'Documentation'}
          </span>
        </span>
        <span
          aria-hidden="true"
          className="shrink-0 text-white/45 transition-transform duration-200 motion-reduce:transition-none group-open:rotate-180"
        >
          ▾
        </span>
      </summary>
      <nav className="border-t border-white/10 py-2" aria-label="Documentation pages">
        {pages.map((p) => {
          const active = pathname === p.href;
          return (
            <Link
              key={p.href}
              href={p.href}
              aria-current={active ? 'page' : undefined}
              className={[
                'block px-4 py-2.5 text-sm font-mono border-l-2 transition-colors min-h-[40px]',
                active
                  ? 'border-brand-orange text-white bg-white/5'
                  : 'border-transparent text-white/65 hover:text-white hover:bg-white/5',
              ].join(' ')}
            >
              {p.label}
            </Link>
          );
        })}
      </nav>
    </details>
  );
}
