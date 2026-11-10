'use client';

/**
 * PrintTimeslip — print-only layout for the public /r/[id] run page.
 *
 * Hidden on screen (`hidden print:block`); becomes the whole page when the
 * user hits "Download PDF" (window.print()) or Ctrl+P. Deliberately
 * light-on-white — the screen keeps the dark cockpit, but dark backgrounds
 * waste ink and most browsers strip them when printing anyway, so the print
 * face is a clean black-on-white timing-booth slip: wordmark + masthead,
 * bike, venue + date, the big ET, the ruled splits table, honest footer.
 *
 * Zero deps by design (no jsPDF) — the browser's print-to-PDF is the export.
 */

export default function PrintTimeslip({ run, id }) {
  if (!run) return null;

  const bikeName = [run.manufacturer, run.model].filter(Boolean).join(' ') || 'Motorcycle';
  const et = Number(run.et_quarter_s).toFixed(3);
  const splits = [
    { label: 'First 60 ft (launch)', value: run.time_60ft_s },
    { label: '330 ft', value: run.time_330ft_s },
    { label: 'Halfway — ⅛ mile', value: run.et_eighth_s },
    { label: '1000 ft', value: run.time_1000ft_s },
  ].filter((s) => s.value != null);

  return (
    <div className="hidden print:block bg-[rgb(255_255_255)] text-[rgb(0_0_0)] px-10 py-10">
      {/* masthead — wordmark + site, then the timing-assoc letterhead line */}
      <header>
        <div className="flex items-baseline justify-between gap-4">
          <p className="font-display font-bold text-2xl tracking-tight">
            Moto<span className="text-accent">Quant</span>
          </p>
          <p className="text-xs text-neutral-500">motoquant.in</p>
        </div>
        <p className="mt-1 text-xs text-neutral-500">
          MotoQuant simulated timeslip · run #{id || '—'}
        </p>
      </header>

      <div className="mt-5 border-t border-dashed border-neutral-400" aria-hidden="true" />

      {/* bike + venue + date */}
      <h1 className="mt-5 font-display font-bold text-xl tracking-tight">
        {bikeName}
        {run.year ? <span className="text-neutral-500"> · {run.year}</span> : null}
      </h1>
      <p className="mt-1 text-sm text-neutral-600">
        {run.venue ? `Conditions: ${run.venue}` : 'Conditions were not recorded for this run'}
        {run.created_at ? ` · ${String(run.created_at).slice(0, 10)}` : ''}
      </p>

      {/* headline ET + trap */}
      <div className="mt-8 text-center">
        <p className="text-sm text-neutral-500">Quarter-mile time</p>
        <p className="mt-2 font-mono font-bold text-6xl leading-none tabular-nums">
          {et}
          <span className="text-2xl font-semibold text-neutral-500"> s</span>
        </p>
        {run.trap_speed_kmh ? (
          <p className="mt-3 font-mono text-sm text-neutral-600 tabular-nums">
            Finish-line speed {Number(run.trap_speed_kmh).toFixed(1)} km/h
          </p>
        ) : null}
      </div>

      {/* splits — the ruled slip body */}
      <div className="mt-8">
        {splits.map((s) => (
          <div
            key={s.label}
            className="flex items-baseline justify-between border-b border-dashed border-neutral-300 py-2 font-mono text-sm tabular-nums"
          >
            <span className="text-sm text-neutral-600">{s.label}</span>
            <span className="font-semibold">{Number(s.value).toFixed(3)}s</span>
          </div>
        ))}
        <div className="flex items-baseline justify-between py-2 font-mono text-sm tabular-nums">
          <span className="text-sm font-semibold">Quarter mile</span>
          <span className="font-bold">{et}s</span>
        </div>
      </div>

      {/* honest footer */}
      <div className="mt-10 flex items-baseline justify-between gap-4 border-t border-dashed border-neutral-400 pt-3 text-xs text-neutral-500">
        <span>Simulated by MotoQuant. Not a stopwatch time.</span>
        <span>motoquant.in/r/{id || ''}</span>
      </div>
    </div>
  );
}
