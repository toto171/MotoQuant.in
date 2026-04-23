import { History } from "lucide-react";

export function HistoryPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Run history</h1>
        <p className="text-sm text-carbon-400 mt-1">
          Saved sim runs and leaderboard — wired to /api/leaderboard on the
          desktop build (coming up next).
        </p>
      </header>
      <div className="card p-10 text-center text-carbon-500 flex flex-col items-center gap-3">
        <History className="w-8 h-8 text-carbon-600" />
        <div>No saved runs yet.</div>
        <div className="text-xs text-carbon-600">
          Run a sim on the Simulate tab and save it — it'll show up here.
        </div>
      </div>
    </div>
  );
}
