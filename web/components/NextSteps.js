/**
 * NextSteps — the "What next?" list shown under every result (CLARITY v6).
 *
 *   <NextSteps
 *     items={[
 *       { icon: Wrench, title: 'Find the best parts for my budget',
 *         hint: 'We test every compatible part', href: '/optimize?bike_id=3' },
 *       { icon: Share2, title: 'Save and share this run', onClick: save },
 *     ]}
 *   />
 *
 * Props
 *  - items    : [{ icon?: LucideIcon, title, hint?, href? | onClick?, disabled? }]
 *               href starting with http opens in a new tab; others use next/link.
 *  - heading  : default 'What next?'
 *  - className
 *
 * No 'use client': usable from server pages (pass `icon` as the component
 * reference, e.g. icon: Wrench) and from client pages (onClick works there).
 * Each row is a real <a> or <button> with a >= 56px tap target. Items without
 * href or onClick are skipped (never render a dead row).
 */

import Link from 'next/link';
import { ArrowRight } from 'lucide-react';

const ROW =
  'group flex min-h-[56px] w-full items-center gap-3 rounded-xl border border-white/10 ' +
  'bg-white/[0.03] px-4 py-3 text-left transition-colors hover:border-accent/50 ' +
  'hover:bg-white/[0.06] disabled:cursor-not-allowed disabled:opacity-50';

function Inner({ item }) {
  const Icon = item.icon;
  return (
    <>
      {Icon && (
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent/10 text-accent">
          <Icon size={18} aria-hidden="true" />
        </span>
      )}
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-white">{item.title}</span>
        {item.hint && <span className="mt-0.5 block text-xs text-white/60">{item.hint}</span>}
      </span>
      <ArrowRight
        size={16}
        aria-hidden="true"
        className="shrink-0 text-white/40 transition-transform group-hover:translate-x-0.5 group-hover:text-accent"
      />
    </>
  );
}

export default function NextSteps({ items = [], heading = 'What next?', className = '' }) {
  const rows = items.filter((i) => i && (i.href || i.onClick));
  if (rows.length === 0) return null;
  return (
    <section className={className} aria-label={heading}>
      <h3 className="mb-3 font-display text-base font-semibold text-white">{heading}</h3>
      <ul className="grid gap-2">
        {rows.map((item, idx) => (
          <li key={`${item.title}-${idx}`}>
            {item.href ? (
              /^https?:\/\//.test(item.href) ? (
                <a href={item.href} target="_blank" rel="noopener noreferrer" className={ROW}>
                  <Inner item={item} />
                </a>
              ) : (
                <Link href={item.href} className={ROW}>
                  <Inner item={item} />
                </Link>
              )
            ) : (
              <button type="button" onClick={item.onClick} disabled={item.disabled} className={ROW}>
                <Inner item={item} />
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
