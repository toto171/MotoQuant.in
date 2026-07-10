'use client';

/**
 * Skeleton primitives (STAGED v4) — shaped loading states for every
 * on-mount fetch. A skeleton must approximate the layout it replaces so the
 * page doesn't jump when data lands. Never a bare "Loading…" text line.
 *
 * All variants are reduced-motion-safe: the shimmer is a CSS animation that
 * @media (prefers-reduced-motion) freezes into a static tinted block
 * (see .skeleton in globals.css).
 */

export function Skeleton({ className = '' }) {
  return <div aria-hidden="true" className={`skeleton ${className}`} />;
}

export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div aria-hidden="true" className={`space-y-2.5 ${className}`}>
      {Array.from({ length: lines }, (_, i) => (
        <div
          key={i}
          className="skeleton h-3.5"
          style={{ width: `${i === lines - 1 ? 55 : 85 + ((i * 7) % 12)}%` }}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ rows = 3, className = '' }) {
  return (
    <div aria-hidden="true" className={`card p-5 ${className}`}>
      <div className="skeleton h-4 w-1/3 mb-4" />
      <SkeletonText lines={rows} />
    </div>
  );
}

export function SkeletonTable({ rows = 6, cols = 4, className = '' }) {
  return (
    <div aria-hidden="true" className={`card overflow-hidden ${className}`}>
      <div className="flex gap-4 px-4 py-3 border-b border-white/10">
        {Array.from({ length: cols }, (_, i) => (
          <div key={i} className="skeleton h-3 flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }, (_, r) => (
        <div key={r} className="flex gap-4 px-4 py-3.5 border-b border-white/5 last:border-0">
          {Array.from({ length: cols }, (_, c) => (
            <div key={c} className="skeleton h-3.5 flex-1" style={{ opacity: 1 - r * 0.09 }} />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Card-grid skeleton for catalog pages (bikes grid, blog index).
 */
export function SkeletonCards({ count = 6, className = '' }) {
  return (
    <div aria-hidden="true" className={`grid gap-4 sm:grid-cols-2 lg:grid-cols-3 ${className}`}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="card p-5">
          <div className="skeleton h-3 w-1/4 mb-3" />
          <div className="skeleton h-5 w-3/4 mb-4" />
          <div className="flex gap-3">
            <div className="skeleton h-3 w-16" />
            <div className="skeleton h-3 w-16" />
            <div className="skeleton h-3 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}
