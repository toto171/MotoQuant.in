'use client';

/**
 * PrintTimeslip — the printed face of /timeslip.
 *
 * Hidden on screen (`hidden print:block`); it becomes the whole page when the
 * visitor chooses "Save as PDF" (window.print()) or presses Ctrl+P. Black on
 * white so it prints cleanly: wordmark, bike, conditions, the quarter-mile
 * time, the splits, what was changed from stock, and an honest footer.
 * No dependencies: the browser's print-to-PDF is the export.
 */

export default function PrintTimeslip({ bikeName, et, trapKmh, splits = [], conditions, changes = [] }) {
  if (et == null) return null;
  const etText = Number(et).toFixed(3);

  return (
    <div className="hidden bg-[rgb(255_255_255)] px-10 py-10 text-[rgb(0_0_0)] print:block">
      <header>
        <div className="flex items-baseline justify-between gap-4">
          <p className="font-display text-2xl font-bold tracking-tight">
            Moto<span className="text-accent">Quant</span>
          </p>
          <p className="text-xs text-neutral-500">motoquant.in</p>
        </div>
        <p className="mt-1 text-xs text-neutral-500">MotoQuant simulated timeslip</p>
      </header>

      <div className="mt-5 border-t border-dashed border-neutral-400" aria-hidden="true" />

      <h1 className="mt-5 font-display text-xl font-bold tracking-tight">{bikeName || 'Motorcycle'}</h1>
      {conditions ? <p className="mt-1 text-sm text-neutral-600">{conditions}</p> : null}

      <div className="mt-8 text-center">
        <p className="text-sm text-neutral-500">Quarter-mile time</p>
        <p className="mt-2 font-mono text-6xl font-bold leading-none tabular-nums">
          {etText}
          <span className="text-2xl font-semibold text-neutral-500"> s</span>
        </p>
        {trapKmh ? (
          <p className="mt-3 font-mono text-sm tabular-nums text-neutral-600">
            Finish-line speed {Number(trapKmh).toFixed(1)} km/h
          </p>
        ) : null}
      </div>

      <div className="mt-8">
        {splits.map((s) => (
          <div
            key={s.label}
            className="flex items-baseline justify-between border-b border-dashed border-neutral-300 py-2 font-mono text-sm tabular-nums"
          >
            <span className="text-sm text-neutral-600">{s.label}</span>
            <span className="font-semibold">{Number(s.value).toFixed(3)} s</span>
          </div>
        ))}
        <div className="flex items-baseline justify-between py-2 font-mono text-sm tabular-nums">
          <span className="text-sm font-semibold">Quarter mile</span>
          <span className="font-bold">{etText} s</span>
        </div>
      </div>

      <div className="mt-6 text-sm">
        <p className="font-semibold">{changes.length ? 'Changed from stock' : 'Stock bike'}</p>
        {changes.length > 0 && (
          <ul className="mt-1 list-disc pl-5 text-neutral-700">
            {changes.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        )}
      </div>

      <div className="mt-10 border-t border-dashed border-neutral-400 pt-3 text-xs text-neutral-500">
        Simulated by MotoQuant from the setup in this slip&apos;s link. Not a stopwatch time.
      </div>
    </div>
  );
}
