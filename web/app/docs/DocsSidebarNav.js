'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

/**
 * DocsSidebarNav — active-aware rail for the docs sidebar.
 *
 * Client leaf so the server layout stays fully static. usePathname is
 * SSG-safe (unlike useSearchParams it needs no Suspense boundary): the
 * build prerenders the neutral state and the active orange rail
 * hydrates client-side.
 */
export default function DocsSidebarNav({ pages }) {
  const pathname = usePathname();
  return (
    <nav className="space-y-1">
      {pages.map((p) => {
        const active = pathname === p.href;
        return (
          <Link
            key={p.href}
            href={p.href}
            aria-current={active ? 'page' : undefined}
            className={[
              'block py-2 pr-3 pl-3 rounded-md text-sm font-mono transition-colors border-l-2',
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
  );
}
