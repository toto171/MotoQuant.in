import { History, Loader2, AlertTriangle } from "lucide-react";
import { useLeaderboard, useMyRuns } from "@/hooks/useApi";
import { LOCAL_LAB } from "@/lib/api";
import type { MyRun } from "@/types/api";

export function HistoryPage() {
  // Hosted builds show the signed-in user's personal runs (/api/me/runs,
  // auth-gated). Local Lab has no accounts — the local DB's saved runs ARE
  // this machine's history, surfaced via the public leaderboard route.
  // LOCAL_LAB is a build-time constant, so exactly one query is ever live.
  const myRuns = useMyRuns(50, !LOCAL_LAB);
  const board = useLeaderboard(50, LOCAL_LAB);

  const entries: MyRun[] = LOCAL_LAB
    ? (board.data?.leaderboard ?? []).map((e) => ({
        ...e,
        et_eighth_s: null,
        time_60ft_s: null,
        notes: null,
        venue: null,
      }))
    : (myRuns.data?.runs ?? []);
  const count = LOCAL_LAB
    ? (board.data?.total ?? entries.length)
    : (myRuns.data?.count ?? entries.length);
  const isPending = LOCAL_LAB ? board.isPending : myRuns.isPending;
  const isError = LOCAL_LAB ? board.isError : myRuns.isError;
  const errorMessage = LOCAL_LAB ? board.error?.message : myRuns.error?.message;
  const hasEntries = entries.length > 0;

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Run history</h1>
          <p className="text-sm text-carbon-400 mt-1">
            {LOCAL_LAB
              ? "Runs saved on this machine, fastest first. Save a run on the Simulate tab and it'll show up here."
              : "Your saved simulation runs, newest first. Save a run on the Simulate tab and it'll show up here."}
          </p>
        </div>
        {hasEntries && (
          <div className="shrink-0 text-right">
            <div className="text-[10px] uppercase tracking-wider text-carbon-500">
              Saved runs
            </div>
            <div className="text-xl font-semibold tabular-nums">{count}</div>
          </div>
        )}
      </header>

      {isPending && (
        <div className="card p-10 flex items-center justify-center gap-3 text-carbon-400">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading your runs…</span>
        </div>
      )}

      {isError && (
        <div className="card p-4 border-stop-500/40 bg-stop-500/5 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" />
          <div>
            <div className="font-medium text-stop-500">
              Couldn't load your runs
            </div>
            <div className="text-xs text-carbon-400 mt-1">
              {errorMessage || "Unknown error"}
            </div>
          </div>
        </div>
      )}

      {!isPending && !isError && !hasEntries && (
        <div className="card p-10 text-center text-carbon-500 flex flex-col items-center gap-3">
          <History className="w-8 h-8 text-carbon-600" />
          <div>No saved runs yet.</div>
          <div className="text-xs text-carbon-600">
            Run a sim on the Simulate tab and save it — it'll show up here.
          </div>
        </div>
      )}

      {hasEntries && (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-carbon-900 text-[10px] uppercase tracking-wider text-carbon-500">
              <tr>
                <th className="text-left px-4 py-3">Bike</th>
                <th className="text-right px-4 py-3 tabular-nums">ET</th>
                <th className="text-right px-4 py-3 tabular-nums">Trap</th>
                <th className="text-right px-4 py-3 tabular-nums">60 ft</th>
                <th className="text-left px-4 py-3">Venue</th>
                <th className="text-left px-4 py-3 w-40">Saved</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((run) => (
                <Row key={run.id} run={run} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Row({ run }: { run: MyRun }) {
  const bikeLabel =
    [run.manufacturer, run.model, run.year && `(${run.year})`]
      .filter(Boolean)
      .join(" ") || "Unknown bike";

  return (
    <tr className="border-t border-carbon-800/60 hover:bg-carbon-800/30 transition-colors">
      <td className="px-4 py-3 text-carbon-100">{bikeLabel}</td>
      <td className="px-4 py-3 text-right tabular-nums font-mono">
        {run.et_quarter_s.toFixed(3)} s
      </td>
      <td className="px-4 py-3 text-right tabular-nums font-mono text-carbon-300">
        {run.trap_speed_kmh.toFixed(1)} km/h
      </td>
      <td className="px-4 py-3 text-right tabular-nums font-mono text-carbon-400">
        {run.time_60ft_s != null ? `${run.time_60ft_s.toFixed(3)} s` : "—"}
      </td>
      <td className="px-4 py-3 text-carbon-400">{run.venue || "—"}</td>
      <td className="px-4 py-3 text-carbon-500 text-xs">
        {formatDate(run.created_at)}
      </td>
    </tr>
  );
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
