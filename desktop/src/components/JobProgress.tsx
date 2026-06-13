import { Loader2, X } from "lucide-react";
import clsx from "clsx";
import type { JobProgress as JobProgressState } from "@/types/api";

// Determinate progress bar for background jobs (full sim / optimise / autotune).
// Replaces the indeterminate spinner so the user sees real % + a Stop button.
// When `progress` is null (connecting / pre-tick) it renders an indeterminate
// shimmer instead of a 0% bar so the UI never looks stuck.
export function JobProgressBar({
  status,
  progress,
  stage,
  onStop,
  label,
  className,
}: {
  status: JobProgressState["status"] | "idle";
  progress: number | null;
  stage: string;
  onStop?: () => void;
  label?: string;
  className?: string;
}) {
  const pct = progress != null ? Math.round(Math.max(0, Math.min(1, progress)) * 100) : null;
  const connecting = status === "connecting" || progress == null;
  const headline = stage || (connecting ? "Waking the simulation engine…" : label || "Running…");

  return (
    <div
      className={clsx("space-y-2", className)}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="flex items-center justify-between gap-3 text-xs">
        <span className="flex items-center gap-1.5 text-carbon-300 min-w-0">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-signal-500 shrink-0" aria-hidden="true" />
          <span className="truncate">{headline}</span>
        </span>
        <span className="flex items-center gap-2 shrink-0">
          {pct != null && <span className="tabular-nums text-carbon-400">{pct}%</span>}
          {onStop && (
            <button
              type="button"
              onClick={onStop}
              className="inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] px-2 py-0.5 rounded border border-carbon-700 text-carbon-400 hover:border-stop-500 hover:text-stop-500 transition-colors focus-visible:outline-2 focus-visible:outline-signal-500"
              aria-label="Stop the running simulation"
            >
              <X className="w-3 h-3" aria-hidden="true" /> Stop
            </button>
          )}
        </span>
      </div>
      <div
        className="h-1.5 w-full rounded-full bg-carbon-800 overflow-hidden"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct ?? undefined}
      >
        {pct != null ? (
          <div
            className="h-full bg-signal-500 transition-[width] duration-300 ease-out shadow-glow"
            style={{ width: `${pct}%` }}
          />
        ) : (
          <div className="h-full w-1/3 bg-signal-500/70 animate-job-indeterminate rounded-full" />
        )}
      </div>
    </div>
  );
}
