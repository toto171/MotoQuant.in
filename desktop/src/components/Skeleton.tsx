// Shimmer skeleton primitives — animate-pulse gray blocks that match the
// shape of the real content, eliminating the empty-then-populated flash.

import clsx from "clsx";

interface SkeletonProps {
  className?: string;
}

/** Generic shimmer block — pass width/height via className. */
export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={clsx(
        "rounded bg-carbon-700/60 animate-pulse",
        className,
      )}
      aria-hidden="true"
    />
  );
}

/** Skeleton for a single StatTile card. */
export function SkeletonStatTile() {
  return (
    <div className="card py-4 px-5 space-y-2" aria-hidden="true">
      <Skeleton className="h-2.5 w-20" />
      <Skeleton className="h-9 w-28" />
    </div>
  );
}

/** Skeleton for a 4-channel chart grid (2×2). */
export function SkeletonChartGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4" aria-hidden="true">
      {[0, 1, 2, 3].map((i) => (
        <div key={i} className="card p-4">
          <div className="flex justify-between mb-2">
            <Skeleton className="h-2.5 w-20" />
            <Skeleton className="h-2.5 w-8" />
          </div>
          <Skeleton className="h-48 w-full" />
        </div>
      ))}
    </div>
  );
}

/** Skeleton rows for the BikesPage table. */
export function SkeletonTableRows({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i} className="border-t border-carbon-800" aria-hidden="true">
          {Array.from({ length: cols }).map((_, j) => (
            <td key={j} className="px-4 py-3">
              <Skeleton
                className={clsx(
                  "h-3",
                  j === 0 ? "w-40" : j === cols - 1 ? "w-16" : "w-20",
                )}
              />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

/** Skeleton rows for the parts catalog list. */
export function SkeletonPartRows({ rows = 6 }: { rows?: number }) {
  return (
    <ul className="divide-y divide-carbon-800" aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <li key={i} className="flex items-center gap-3 px-4 py-3">
          <Skeleton className="w-7 h-7 rounded" />
          <div className="flex-1 space-y-1.5">
            <Skeleton className="h-3 w-48" />
            <Skeleton className="h-2.5 w-28" />
          </div>
          <Skeleton className="h-3 w-16 shrink-0" />
        </li>
      ))}
    </ul>
  );
}

/** Skeleton for two side-by-side build cards (ComparePage). */
export function SkeletonBuildCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4" aria-hidden="true">
      {[0, 1].map((i) => (
        <div key={i} className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <Skeleton className="w-8 h-8 rounded-full" />
            <Skeleton className="h-3 w-32" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[0, 1, 2, 3].map((j) => (
              <div key={j} className="card py-4 px-5 space-y-2">
                <Skeleton className="h-2.5 w-12" />
                <Skeleton className="h-8 w-20" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
