'use client';

/**
 * ActionButton — the one run/stop button pattern (STAGED v4).
 *
 * Pairs with useAsyncTask: idle it's the volt primary button; while the task
 * runs it flips to the amber .btn-running "■ Stop — NN%" state with live
 * progress — real percentage when the backend reports it (job-backed sims),
 * an animated sweep strip otherwise (plain fetches, cold starts). The button
 * IS the progress bar, so no async action ships with a dead "Working…" label.
 *
 *   const task = useAsyncTask((signal, onProgress) => simulateJob(body, onProgress, signal));
 *   <ActionButton task={task} onRun={() => task.run()} label="Run full sim" />
 *
 * Props
 *  - task        : useAsyncTask return value (required)
 *  - onRun       : click handler when idle (usually () => task.run(...))
 *  - label       : idle label
 *  - runningLabel: verb shown while active (default = label)
 *  - disabled    : disables the idle button only (Stop always works)
 *  - variant     : 'primary' | 'ghost' (idle style)
 *  - stoppable   : set false for actions that can't be meaningfully aborted
 *  - className
 */

import SimProgress from './SimProgress';

export default function ActionButton({
  task,
  onRun,
  label,
  runningLabel = null,
  disabled = false,
  variant = 'primary',
  stoppable = true,
  className = '',
}) {
  const active = !!task?.active;
  const pct =
    typeof task?.progress === 'number' && task.progress > 0
      ? Math.min(100, Math.round(task.progress * 100))
      : null;

  if (!active) {
    return (
      <button
        type="button"
        onClick={onRun}
        disabled={disabled}
        className={`${variant === 'ghost' ? 'btn-ghost' : 'btn-primary'} ${className}`}
      >
        {label}
      </button>
    );
  }

  const verb = runningLabel || label;
  return (
    <button
      type="button"
      onClick={stoppable ? task.stop : undefined}
      aria-label={stoppable ? `Stop — ${verb}` : verb}
      className={`btn-running relative overflow-hidden ${className}`}
    >
      <span className="relative z-10 flex items-center gap-2 font-mono text-sm">
        {stoppable && <span aria-hidden="true">■</span>}
        <span>
          {stoppable ? 'Stop' : verb}
          {pct != null ? ` — ${pct}%` : '…'}
        </span>
      </span>
      {/* live progress strip pinned to the button's bottom edge */}
      <SimProgress
        active
        edge
        progress={task.progress}
        className="absolute inset-x-0 bottom-0 z-10"
      />
    </button>
  );
}
