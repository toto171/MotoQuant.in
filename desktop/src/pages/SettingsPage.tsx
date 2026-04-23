import { useQuery } from "@tanstack/react-query";
import { Server, Database, Cpu, Info } from "lucide-react";
import { getResolvedBaseUrl } from "@/lib/api";

export function SettingsPage() {
  const url = useQuery({
    queryKey: ["backend-url"],
    queryFn: getResolvedBaseUrl,
    staleTime: Infinity,
  });

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <header>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-carbon-400 mt-1">
          Runtime info and app preferences.
        </p>
      </header>

      <section className="card p-5 space-y-4">
        <Row
          Icon={Server}
          label="Backend URL"
          value={url.data ?? "resolving…"}
          hint="Python sidecar bound to this ephemeral port."
        />
        <Row
          Icon={Database}
          label="Database"
          value="motoquant.db (bundled)"
          hint="SQLite, read-only for catalog; user runs written to app-data."
        />
        <Row
          Icon={Cpu}
          label="Physics engine"
          value="RK4 · 1 ms fixed (or adaptive)"
          hint="15 sub-models · validated K5 10.033 s / R1 10.286 s / Hayabusa 10.471 s."
        />
        <Row
          Icon={Info}
          label="Version"
          value="MotoQuant Pro v0.5.0"
          hint="Tauri 2.0 shell · React 19 · FastAPI sidecar."
        />
      </section>
    </div>
  );
}

function Row({
  Icon,
  label,
  value,
  hint,
}: {
  Icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="flex items-start gap-4">
      <div className="w-9 h-9 rounded bg-carbon-800 flex items-center justify-center shrink-0">
        <Icon className="w-4 h-4 text-carbon-400" />
      </div>
      <div className="flex-1">
        <div className="text-[10px] uppercase tracking-wider text-carbon-500">
          {label}
        </div>
        <div className="font-mono text-sm text-carbon-100 mt-0.5">{value}</div>
        {hint && (
          <div className="text-xs text-carbon-500 mt-1 leading-relaxed">
            {hint}
          </div>
        )}
      </div>
    </div>
  );
}
