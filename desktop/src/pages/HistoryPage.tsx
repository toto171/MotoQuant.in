import { History, Loader2, AlertTriangle, Trophy } from "lucide-react";
import { useLeaderboard } from "@/hooks/useApi";
import type { LeaderboardEntry } from "@/types/api";

export function HistoryPage() {
  const lb = useLeaderboard(50);

  const entries = lb.data?.leaderboard ?? [];
  const hasEntries = entries.length > 0;

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Run history</h1>
          <p className="text-sm text-carbon-400 mt-1">
            Top saved simulation runs from the local{" "}
            <code className="font-mono text-carbon-300">sim_runs</code> table.
            Save a run on the Simulate tab and it'll show up here, ranked by
            quarter-mile ET.
          </p>
        </div>
        {hasEntries && (
          <div className="shrink-0 text-right">
            <div className="text-[10px] uppercase tracking-wider text-carbon-500">
              Total runs
            </div>
            <div className="text-xl font-semibold tabular-nums">
              {lb.data?.total ?? entries.length}
            </div>
          </div>
        )}
      </header>

      {lb.isPending && (
        <div className="card p-10 flex items-center justify-center gap-3 text-carbon-400">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading leaderboard…</span>
        </div>
      )}

      {lb.isError && (
        <div className="card p-4 border-stop-500/40 bg-stop-500/5 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" />
          <div>
            <div className="font-medium text-stop-500">
              Couldn't load leaderboard
            </div>
            <div className="text-xs text-carbon-400 mt-1">
              {lb.error?.message || "Unknown error"}
            </div>
          </div>
        </div>
      )}

      {!lb.isPending && !lb.isError && !hasEntries && (
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
                <th className="text-left px-4 py-3 w-12">#</th>
                <th className="text-left px-4 py-3">Bike</th>
                <th className="text-right px-4 py-3 tabular-nums">ET</th>
                <th className="text-right px-4 py-3 tabular-nums">Trap</th>
                <th className="text-left px-4 py-3 w-40">Saved</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((run, i) => (
                <Row key={run.id} run={run} rank={i + 1} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Row({ run, rank }: { run: LeaderboardEntry; rank: number }) {
  const bikeLabel = [run.manufacturer, run.model, run.year && `(${run.year})`]
    .filter(Boolean)
    .join(" ") || "Unknown bike";

  return (
    <tr className="border-t border-carbon-800/60 hover:bg-carbon-800/30 transition-colors">
      <td className="px-4 py-3">
        <RankBadge rank={rank} />
      </td>
      <td className="px-4 py-3 text-carbon-100">{bikeLabel}</td>
      <td className="px-4 py-3 text-right tabular-nums font-mono">
        {run.et_quarter_s.toFixed(3)} s
      </td>
      <td className="px-4 py-3 text-right tabular-nums font-mono text-carbon-300">
        {run.trap_speed_kmh.toFixed(1)} km/h
      </td>
      <td className="px-4 py-3 text-carbon-500 text-xs">
        {formatDate(run.created_at)}
      </td>
    </tr>
  );
}

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) {
    return (
      <div
        className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-signal-600/20 text-signal-400"
        title="Fastest"
      >
        <Trophy className="w-3.5 h-3.5" />
      </div>
    );
  }
  return (
    <div className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-carbon-800 text-carbon-400 text-xs font-medium tabular-nums">
      {rank}
    </div>
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
