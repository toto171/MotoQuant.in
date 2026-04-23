import { useState } from "react";
import { Play, Loader2, AlertTriangle } from "lucide-react";
import { useSimulate, useVenues } from "@/hooks/useApi";
import { BikePicker } from "@/components/BikePicker";
import { StatTile } from "@/components/StatTile";
import { SimChart, SIM_CHANNELS } from "@/components/SimChart";
import type { BikeSummary } from "@/types/api";

export function SimulatePage() {
  const [bike, setBike] = useState<BikeSummary | null>(null);
  const [venueId, setVenueId] = useState<number | null>(null);
  const [riderMass, setRiderMass] = useState(75);
  const [powerBoost, setPowerBoost] = useState(0);
  const [massDelta, setMassDelta] = useState(0);
  const [adaptive, setAdaptive] = useState(false);

  const venues = useVenues();
  const sim = useSimulate();

  const canRun = bike != null && !sim.isPending;

  const onRun = () => {
    if (!bike) return;
    sim.mutate({
      bike_id: bike.id,
      venue_id: venueId ?? undefined,
      rider_mass_kg: riderMass,
      power_boost_pct: powerBoost,
      mass_delta_kg: massDelta,
      use_adaptive_dt: adaptive,
    });
  };

  const result = sim.data;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Simulate a pass</h1>
        <p className="text-sm text-carbon-400 mt-1">
          Pick a bike, tune the rider and a couple of mods, hit run. Full
          quarter-mile physics (RK4, 15 sub-models) in about a second.
        </p>
      </header>

      <section className="card p-5 space-y-4">
        <div>
          <label className="block text-xs uppercase tracking-wider text-carbon-500 mb-2">
            Bike
          </label>
          <BikePicker
            value={bike?.id ?? null}
            onChange={(_, summary) => setBike(summary)}
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs uppercase tracking-wider text-carbon-500 mb-2">
              Venue
            </label>
            <select
              className="input"
              value={venueId ?? ""}
              onChange={(e) =>
                setVenueId(e.target.value ? Number(e.target.value) : null)
              }
            >
              <option value="">ISA default (sea level, 15 °C)</option>
              {venues.data?.venues.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} — {v.country} ({v.altitude_m ?? 0} m)
                </option>
              ))}
            </select>
          </div>

          <Slider
            label="Rider mass"
            unit="kg"
            min={50}
            max={130}
            step={1}
            value={riderMass}
            onChange={setRiderMass}
          />

          <Slider
            label="Power boost"
            unit="%"
            min={-20}
            max={40}
            step={1}
            value={powerBoost}
            onChange={setPowerBoost}
          />

          <Slider
            label="Mass change"
            unit="kg"
            min={-25}
            max={25}
            step={0.5}
            value={massDelta}
            onChange={setMassDelta}
          />

          <label className="flex items-center gap-2 self-end text-sm text-carbon-300">
            <input
              type="checkbox"
              checked={adaptive}
              onChange={(e) => setAdaptive(e.target.checked)}
              className="accent-signal-500"
            />
            Adaptive RK4 (slower, smoother)
          </label>

          <div className="self-end">
            <button
              disabled={!canRun}
              onClick={onRun}
              className="btn btn-primary w-full justify-center"
            >
              {sim.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Simulating…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" /> Run quarter-mile
                </>
              )}
            </button>
          </div>
        </div>
      </section>

      {sim.isError && (
        <div className="card p-4 border-stop-500/40 bg-stop-500/5 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" />
          <div>
            <div className="font-medium text-stop-500">Simulation failed</div>
            <div className="text-xs text-carbon-400 mt-1">
              {sim.error?.message || "Unknown error"}
            </div>
          </div>
        </div>
      )}

      {result && (
        <>
          <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatTile
              label="Quarter-mile ET"
              value={result.et_quarter_s.toFixed(3)}
              unit="s"
              accent="signal"
            />
            <StatTile
              label="Trap speed"
              value={result.trap_speed_kmh.toFixed(1)}
              unit="km/h"
              hint={`${(result.trap_speed_kmh * 0.6214).toFixed(1)} mph`}
            />
            <StatTile
              label="60 ft"
              value={result.splits["60ft_s"].toFixed(3)}
              unit="s"
            />
            <StatTile
              label="1/8 mile"
              value={result.splits["660ft_s"].toFixed(3)}
              unit="s"
            />
          </section>

          <section className="card p-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-3 text-sm">
              <Detail label="Bike">
                {result.bike.manufacturer} {result.bike.model}
              </Detail>
              <Detail label="Power">
                {result.config.peak_power_hp.toFixed(1)} hp
              </Detail>
              <Detail label="Torque">
                {result.config.peak_torque_nm.toFixed(1)} Nm
              </Detail>
              <Detail label="Mass (total)">
                {result.config.total_mass_kg.toFixed(1)} kg
              </Detail>
              <Detail label="Displacement">
                {result.config.displacement_cc ?? "—"} cc
              </Detail>
              <Detail label="Redline">
                {result.config.redline_rpm?.toLocaleString() ?? "—"} rpm
              </Detail>
              <Detail label="Gears">{result.config.gear_count}</Detail>
              <Detail label="Cd">
                {result.config.cd?.toFixed(3) ?? "—"}
              </Detail>
            </div>
          </section>

          <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {SIM_CHANNELS.map((ch) => (
              <div key={ch} className="card p-4">
                <SimChart
                  channel={ch}
                  timeseries={result.timeseries}
                  etMark={result.et_quarter_s}
                />
              </div>
            ))}
          </section>
        </>
      )}
    </div>
  );
}

function Slider({
  label,
  unit,
  min,
  max,
  step,
  value,
  onChange,
}: {
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (v: number) => void;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <label className="text-xs uppercase tracking-wider text-carbon-500">
          {label}
        </label>
        <span className="text-sm font-medium tabular-nums">
          {value.toFixed(step < 1 ? 1 : 0)} {unit}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-signal-500"
      />
    </div>
  );
}

function Detail({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-carbon-500">
        {label}
      </div>
      <div className="text-carbon-100 mt-0.5">{children}</div>
    </div>
  );
}
