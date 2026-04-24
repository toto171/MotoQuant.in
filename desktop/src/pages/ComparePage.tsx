import { useState, useMemo } from "react";
import { Play, Loader2, AlertTriangle, GitCompare, ArrowRight } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend, CartesianGrid,
} from "recharts";
import { useCompare, useVenues } from "@/hooks/useApi";
import { BikePicker } from "@/components/BikePicker";
import { StatTile } from "@/components/StatTile";
import { OfflineBanner } from "@/components/OfflineBanner";
import { SkeletonBuildCards, Skeleton } from "@/components/Skeleton";
import type {
  BikeSummary, CompareBuildSummary, CompareTimeseries,
} from "@/types/api";

interface SideState {
  bike: BikeSummary | null;
  riderMass: number;
  powerBoost: number;
  massDelta: number;
}

const INITIAL_A: SideState = { bike: null, riderMass: 75, powerBoost: 0, massDelta: 0 };
const INITIAL_B: SideState = { bike: null, riderMass: 75, powerBoost: 10, massDelta: -5 };

export function ComparePage() {
  const [a, setA] = useState<SideState>(INITIAL_A);
  const [b, setB] = useState<SideState>(INITIAL_B);
  const [venueId, setVenueId] = useState<number | null>(null);

  const venues = useVenues();
  const cmp = useCompare();

  const canRun = a.bike != null && b.bike != null && !cmp.isPending;

  const onRun = () => {
    if (!a.bike || !b.bike) return;
    cmp.mutate({
      a_bike_id: a.bike.id,
      a_rider_mass_kg: a.riderMass,
      a_power_boost_pct: a.powerBoost,
      a_mass_delta_kg: a.massDelta,
      b_bike_id: b.bike.id,
      b_rider_mass_kg: b.riderMass,
      b_power_boost_pct: b.powerBoost,
      b_mass_delta_kg: b.massDelta,
      venue_id: venueId ?? undefined,
    });
  };

  const result = cmp.data;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-signal-500" aria-hidden="true" /> Compare two builds
        </h1>
        <p className="text-sm text-carbon-400 mt-1">
          Run two bikes on the same track under identical conditions. Delta is B − A — negative ET means B is faster.
        </p>
      </header>

      <OfflineBanner />

      <section className="card p-4">
        <label className="block text-xs uppercase tracking-wider text-carbon-500 mb-2" htmlFor="venue-cmp">
          Shared venue + conditions
        </label>
        <select
          id="venue-cmp"
          className="input w-full"
          value={venueId ?? ""}
          onChange={(e) => setVenueId(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">ISA default (sea level, 15 °C)</option>
          {venues.data?.venues.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name} — {v.country} ({v.altitude_m ?? 0} m)
            </option>
          ))}
        </select>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BuildColumn label="A" accent="carbon" state={a} onChange={setA} />
        <BuildColumn label="B" accent="signal" state={b} onChange={setB} />
      </section>

      <div className="flex justify-center">
        <button
          disabled={!canRun}
          onClick={onRun}
          className="btn btn-primary px-8 justify-center focus-visible:outline-2 focus-visible:outline-signal-300"
          aria-label="Run comparison"
          title={!a.bike || !b.bike ? "Select a bike for both A and B first" : "Run compare"}
        >
          {cmp.isPending ? (
            <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Running A vs B…</>
          ) : (
            <><Play className="w-4 h-4" aria-hidden="true" /> Run compare</>
          )}
        </button>
      </div>

      {/* Error */}
      {cmp.isError && (
        <div className="card p-4 border-stop-500/40 bg-stop-500/5 flex gap-3" role="alert">
          <AlertTriangle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <div className="font-medium text-stop-500">Compare failed</div>
            <div className="text-xs text-carbon-400 mt-1">
              {cmp.error?.message || "Unknown error — is the backend running?"}
            </div>
          </div>
        </div>
      )}

      {/* Loading skeleton */}
      {cmp.isPending && !result && (
        <>
          <div className="card p-5">
            <div className="flex items-center justify-between gap-6 flex-wrap">
              <Skeleton className="h-6 w-40" />
              <div className="flex gap-6">
                <Skeleton className="h-10 w-24" />
                <Skeleton className="h-10 w-24" />
                <Skeleton className="h-10 w-24" />
              </div>
            </div>
          </div>
          <SkeletonBuildCards />
        </>
      )}

      {result && <Results result={result} />}
    </div>
  );
}

function BuildColumn({ label, accent, state, onChange }: {
  label: "A" | "B"; accent: "carbon" | "signal";
  state: SideState; onChange: (next: SideState) => void;
}) {
  const pillClass = accent === "signal"
    ? "bg-signal-600/20 text-signal-400"
    : "bg-carbon-800 text-carbon-300";
  const patch = (p: Partial<SideState>) => onChange({ ...state, ...p });

  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-2">
        <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-semibold ${pillClass}`}
          aria-label={`Build ${label}`}
        >{label}</span>
        <span className="text-xs uppercase tracking-wider text-carbon-500">
          {label === "A" ? "Baseline" : "Modified"}
        </span>
      </div>
      <div>
        <label className="block text-xs uppercase tracking-wider text-carbon-500 mb-2">Bike</label>
        <BikePicker value={state.bike?.id ?? null} onChange={(_, summary) => patch({ bike: summary })} />
      </div>
      <Slider label="Rider mass" unit="kg" min={50} max={130} step={1} value={state.riderMass} onChange={(v) => patch({ riderMass: v })} />
      <Slider label="Power boost" unit="%" min={-20} max={40} step={1} value={state.powerBoost} onChange={(v) => patch({ powerBoost: v })} />
      <Slider label="Mass change" unit="kg" min={-25} max={25} step={0.5} value={state.massDelta} onChange={(v) => patch({ massDelta: v })} />
    </div>
  );
}

function Results({ result }: {
  result: { a: CompareBuildSummary; b: CompareBuildSummary; delta: { et_s: number; trap_kmh: number; faster: "A" | "B" | "tie"; cost_diff_inr: number } };
}) {
  const { a, b, delta } = result;
  const chartData = useMemo(() => buildChart(a.timeseries, b.timeseries), [a.timeseries, b.timeseries]);

  return (
    <>
      <section className="card p-5 flex items-center justify-between gap-6 flex-wrap" role="status" aria-live="polite">
        <div className="flex items-center gap-3">
          <span className="text-xs uppercase tracking-wider text-carbon-500">Winner</span>
          {delta.faster === "tie" ? (
            <span className="text-lg font-semibold">Tie</span>
          ) : (
            <span className="inline-flex items-center gap-2 text-lg font-semibold">
              <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full ${
                delta.faster === "B" ? "bg-signal-600/20 text-signal-400" : "bg-carbon-800 text-carbon-300"
              }`}>
                {delta.faster}
              </span>
              <ArrowRight className="w-4 h-4 text-carbon-600" aria-hidden="true" />
              <span className="tabular-nums text-signal-400">
                {Math.abs(delta.et_s).toFixed(3)} s faster
              </span>
            </span>
          )}
        </div>
        <div className="flex gap-6 text-sm">
          <Delta label="ΔET" value={fmtSigned(delta.et_s, 3)} unit="s" />
          <Delta label="ΔTrap" value={fmtSigned(delta.trap_kmh, 1)} unit="km/h" />
          <Delta label="ΔCost" value={fmtSigned(delta.cost_diff_inr, 0)} unit="₹" />
        </div>
      </section>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BuildCard build={a} />
        <BuildCard build={b} accent="signal" />
      </section>

      {chartData.length > 0 && (
        <section className="card p-5">
          <div className="text-xs uppercase tracking-wider text-carbon-500 mb-3">Velocity vs. time (overlay)</div>
          <div style={{ width: "100%", height: 280 }} role="img" aria-label="Velocity comparison chart">
            <ResponsiveContainer>
              <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 20, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="t" type="number" domain={["dataMin", "dataMax"]}
                  tick={{ fill: "#8a8a8a", fontSize: 11 }}
                  label={{ value: "Time (s)", position: "insideBottom", offset: -5, fill: "#8a8a8a", fontSize: 11 }}
                />
                <YAxis tick={{ fill: "#8a8a8a", fontSize: 11 }}
                  label={{ value: "km/h", angle: -90, position: "insideLeft", fill: "#8a8a8a", fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ background: "#161616", border: "1px solid #2a2a2a", fontSize: 12 }}
                  labelFormatter={(v) => `${Number(v).toFixed(2)} s`}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line type="monotone" dataKey="A" stroke="#9ca3af" dot={false} strokeWidth={1.8} isAnimationActive={false} />
                <Line type="monotone" dataKey="B" stroke="#f97316" dot={false} strokeWidth={2} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}
    </>
  );
}

function BuildCard({ build, accent }: { build: CompareBuildSummary; accent?: "signal" }) {
  const border = accent === "signal" ? "border-signal-600/40" : "border-carbon-700";
  return (
    <div className={`card p-5 border ${border}`}>
      <div className="flex items-center justify-between mb-3">
        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold ${
          accent === "signal" ? "bg-signal-600/20 text-signal-400" : "bg-carbon-800 text-carbon-300"
        }`}>{build.label}</span>
        <span className="text-sm text-carbon-200 truncate">{build.bike_name}</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <StatTile label="ET" value={build.et_quarter_s.toFixed(3)} unit="s" accent={accent} />
        <StatTile label="Trap" value={build.trap_speed_kmh.toFixed(1)} unit="km/h" />
        <StatTile label="60 ft" value={build.et_60ft_s.toFixed(3)} unit="s" />
        <StatTile label="1/8 mile" value={build.et_eighth_s.toFixed(3)} unit="s" />
      </div>
      <div className="mt-3 text-xs text-carbon-500 flex justify-between">
        <span>{build.peak_power_hp.toFixed(1)} hp · {build.total_mass_kg.toFixed(1)} kg</span>
        {build.build_cost_inr > 0 && <span>₹{Math.round(build.build_cost_inr).toLocaleString()}</span>}
      </div>
    </div>
  );
}

function Delta({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div className="text-right">
      <div className="text-[10px] uppercase tracking-wider text-carbon-500">{label}</div>
      <div className="font-mono tabular-nums">{value} <span className="text-carbon-500">{unit}</span></div>
    </div>
  );
}

function fmtSigned(n: number, decimals: number): string {
  if (!Number.isFinite(n)) return "—";
  const sign = n > 0 ? "+" : "";
  return decimals === 0
    ? `${sign}${Math.round(n).toLocaleString()}`
    : `${sign}${n.toFixed(decimals)}`;
}

function buildChart(aTs: CompareTimeseries | undefined, bTs: CompareTimeseries | undefined) {
  if (!aTs && !bTs) return [];
  const tMax = Math.max(
    aTs?.t_s?.[aTs.t_s.length - 1] ?? 0,
    bTs?.t_s?.[bTs.t_s.length - 1] ?? 0,
  );
  if (tMax <= 0) return [];
  return Array.from({ length: 161 }, (_, i) => {
    const t = (i / 160) * tMax;
    return { t, A: aTs ? interp(aTs.t_s, aTs.v_kmh, t) : undefined, B: bTs ? interp(bTs.t_s, bTs.v_kmh, t) : undefined };
  });
}

function interp(xs: number[], ys: number[], x: number): number | undefined {
  if (!xs.length || !ys.length) return undefined;
  if (x <= xs[0]) return ys[0];
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1];
  for (let i = 1; i < xs.length; i++) {
    if (xs[i] >= x) {
      const t = (x - xs[i - 1]) / (xs[i] - xs[i - 1]);
      return ys[i - 1] + t * (ys[i] - ys[i - 1]);
    }
  }
  return ys[ys.length - 1];
}

function Slider({ label, unit, min, max, step, value, onChange }: {
  label: string; unit: string; min: number; max: number; step: number;
  value: number; onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <label className="text-xs uppercase tracking-wider text-carbon-500">{label}</label>
        <span className="text-sm font-medium tabular-nums">{value.toFixed(step < 1 ? 1 : 0)} {unit}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-signal-500 focus-visible:outline-2 focus-visible:outline-signal-500"
        aria-label={`${label}: ${value} ${unit}`}
      />
    </div>
  );
}
