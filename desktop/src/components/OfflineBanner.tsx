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
        <span className="font-medium">MotoQuant servers unreachable.</span>{" "}
        Couldn't reach the hosted simulation engine. Check your internet
        connection — results will load once the connection is restored.
      </div>
    </div>
  );
}
