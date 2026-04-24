// Shown at the top of each page when the Python backend is unreachable.
// Reads the cached health query — no extra HTTP call.

import { WifiOff } from "lucide-react";
import { useEngineStatus } from "@/hooks/useEngineStatus";

export function OfflineBanner() {
  const { offline } = useEngineStatus();
  if (!offline) return null;

  return (
    <div
      className="flex items-center gap-3 rounded-lg border border-stop-500/40 bg-stop-500/5 px-4 py-3 text-sm text-stop-400"
      role="alert"
    >
      <WifiOff className="w-4 h-4 shrink-0" aria-hidden="true" />
      <div>
        <span className="font-medium">Engine offline.</span>{" "}
        The MotoQuant backend isn't responding. Start it with{" "}
        <code className="font-mono text-xs bg-carbon-800 px-1 py-0.5 rounded">
          uvicorn motoquant.api:app --port 8000
        </code>{" "}
        or restart the desktop app.
      </div>
    </div>
  );
}
