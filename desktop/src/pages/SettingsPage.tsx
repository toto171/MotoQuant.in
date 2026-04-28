// Settings page — real preferences backed by localStorage via SettingsContext.
// Units, theme, default venue, and sim engine mode all persist across sessions.

import { useQuery } from "@tanstack/react-query";
import { Server, Database, Cpu, Info, Gauge, Moon, Sun } from "lucide-react";
import { getResolvedBaseUrl } from "@/lib/api";
import { useSettings } from "@/contexts/SettingsContext";
import { useVenues } from "@/hooks/useApi";
import type { Units, Theme } from "@/contexts/SettingsContext";
import clsx from "clsx";

export function SettingsPage() {
  const url = useQuery({ queryKey: ["backend-url"], queryFn: getResolvedBaseUrl, staleTime: Infinity });
  const {
    units, setUnits,
    theme, setTheme,
    defaultVenueId, setDefaultVenueId,
    useAdaptiveDt, setUseAdaptiveDt,
  } = useSettings();
  const venues = useVenues();

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-carbon-400 mt-1">
          Preferences are saved locally — no account required.
        </p>
      </header>

      {/* Display */}
      <section className="card p-5 space-y-5">
        <div className="text-[10px] uppercase tracking-wider text-carbon-500">Display</div>

        {/* Units */}
        <div className="flex items-start justify-between gap-6">
          <div>
            <div className="text-sm font-medium text-carbon-100">Units</div>
            <div className="text-xs text-carbon-500 mt-0.5">
              Affects trap speed, mass, and torque display. Physics engine always uses SI internally.
            </div>
          </div>
          <div className="flex rounded-md border border-carbon-700 overflow-hidden shrink-0" role="group" aria-label="Units">
            {(["metric", "imperial"] as Units[]).map((u) => (
              <button
                key={u}
                onClick={() => setUnits(u)}
                className={clsx(
                  "px-4 py-1.5 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-signal-500",
                  units === u
                    ? "bg-signal-500 text-carbon-950 font-medium"
                    : "bg-carbon-800 text-carbon-400 hover:text-carbon-100",
                )}
                aria-pressed={units === u}
              >
                {u === "metric" ? "Metric" : "Imperial"}
              </button>
            ))}
          </div>
        </div>

        {units === "metric" && (
          <div className="text-xs text-carbon-600 -mt-2 ml-auto max-w-xs text-right">
            km/h · kg · Nm
          </div>
        )}
        {units === "imperial" && (
          <div className="text-xs text-carbon-600 -mt-2 ml-auto max-w-xs text-right">
            mph · lb · ft·lb
          </div>
        )}

        {/* Theme */}
        <div className="flex items-start justify-between gap-6 pt-4 border-t border-carbon-800">
          <div>
            <div className="text-sm font-medium text-carbon-100">Theme</div>
            <div className="text-xs text-carbon-500 mt-0.5">
              System follows your OS preference. Full light-mode color redesign coming in v0.6.
            </div>
          </div>
          <div className="flex rounded-md border border-carbon-700 overflow-hidden shrink-0" role="group" aria-label="Theme">
            {(["dark", "system"] as Theme[]).map((t) => (
              <button
                key={t}
                onClick={() => setTheme(t)}
                className={clsx(
                  "flex items-center gap-1.5 px-4 py-1.5 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-signal-500",
                  theme === t
                    ? "bg-signal-500 text-carbon-950 font-medium"
                    : "bg-carbon-800 text-carbon-400 hover:text-carbon-100",
                )}
                aria-pressed={theme === t}
              >
                {t === "dark"
                  ? <><Moon className="w-3.5 h-3.5" aria-hidden="true" /> Dark</>
                  : <><Sun className="w-3.5 h-3.5" aria-hidden="true" /> System</>
                }
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Simulation defaults */}
      <section className="card p-5 space-y-5">
        <div className="text-[10px] uppercase tracking-wider text-carbon-500">Simulation defaults</div>

        {/* Default venue */}
        <div className="flex items-start justify-between gap-6">
          <div className="flex-1">
            <div className="text-sm font-medium text-carbon-100">Default venue</div>
            <div className="text-xs text-carbon-500 mt-0.5">
              Pre-selected venue on Simulate and Compare pages.
            </div>
          </div>
          <div className="shrink-0 w-52">
            <select
              className="input text-sm"
              value={defaultVenueId ?? ""}
              onChange={(e) => setDefaultVenueId(e.target.value ? Number(e.target.value) : null)}
              aria-label="Default venue"
            >
              <option value="">ISA default (sea level, 15 °C)</option>
              {venues.data?.venues.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} ({v.country})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Solver */}
        <div className="flex items-start justify-between gap-6 pt-4 border-t border-carbon-800">
          <div>
            <div className="text-sm font-medium text-carbon-100">Solver mode</div>
            <div className="text-xs text-carbon-500 mt-0.5">
              Adaptive RK4 produces smoother timeseries but takes 2–3× longer.
            </div>
          </div>
          <div className="flex rounded-md border border-carbon-700 overflow-hidden shrink-0" role="group" aria-label="Solver mode">
            {[
              { value: false, label: "Fixed 1 ms" },
              { value: true, label: "Adaptive" },
            ].map(({ value, label }) => (
              <button
                key={label}
                onClick={() => setUseAdaptiveDt(value)}
                className={clsx(
                  "px-4 py-1.5 text-sm transition-colors focus-visible:outline-2 focus-visible:outline-signal-500",
                  useAdaptiveDt === value
                    ? "bg-signal-500 text-carbon-950 font-medium"
                    : "bg-carbon-800 text-carbon-400 hover:text-carbon-100",
                )}
                aria-pressed={useAdaptiveDt === value}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* About / runtime */}
      <section className="card p-5 space-y-4">
        <div className="text-[10px] uppercase tracking-wider text-carbon-500">About</div>

        <AboutRow Icon={Gauge} label="App version" value="MotoQuant Pro v0.5.0" hint="Tauri 2 · React 19 · FastAPI sidecar" />
        <AboutRow Icon={Server} label="Backend URL" value={url.data ?? "resolving…"} hint="Python sidecar (ephemeral port)" />
        <AboutRow Icon={Database} label="Database" value="motoquant.db (bundled)" hint="SQLite · WAL-fallback · 290 bikes" />
        <AboutRow Icon={Cpu} label="Physics engine" value="RK4 · 1 ms fixed (or adaptive)" hint="15 sub-models validated" />
        <AboutRow
          Icon={Info}
          label="Reference baselines"
          value="K5 10.033 s · R1 10.286 s · Hayabusa 10.471 s"
          hint="Aamby Valley ISA conditions — ±0.001 s tolerance"
        />
      </section>
    </div>
  );
}

function AboutRow({ Icon, label, value, hint }: {
  Icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="flex items-start gap-4">
      <div className="w-9 h-9 rounded bg-carbon-800 flex items-center justify-center shrink-0" aria-hidden="true">
        <Icon className="w-4 h-4 text-carbon-400" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-carbon-500">{label}</div>
        <div className="font-mono text-sm text-carbon-100 mt-0.5 break-all">{value}</div>
        {hint && <div className="text-xs text-carbon-500 mt-1 leading-relaxed">{hint}</div>}
      </div>
    </div>
  );
}
