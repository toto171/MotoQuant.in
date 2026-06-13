import { useState, type ReactNode } from "react";
import {
  Gauge, Play, Loader2, AlertTriangle, MapPin, Cog, Flag, Wind, Droplet,
  ArrowRight, Info,
} from "lucide-react";
import { BikePicker } from "@/components/BikePicker";
import { StatTile } from "@/components/StatTile";
import { OfflineBanner } from "@/components/OfflineBanner";
import { SkeletonStatTile } from "@/components/Skeleton";
import { JobProgressBar } from "@/components/JobProgress";
import { useAutotuneJob } from "@/hooks/useApi";
import type {
  BikeSummary, EcuAutotune, AutotuneGearing, AutotuneLaunchRpm,
  AutotuneTyrePressure, AutotuneFuelTiming,
} from "@/types/api";
import clsx from "clsx";

export function AutotunePage() {
  const [bike, setBike] = useState<BikeSummary | null>(null);
  const [location, setLocation] = useState("");
  // Optional manual environment overrides — left blank → server resolves
  // from location/venue or falls back to ISA.
  const [tempC, setTempC] = useState<string>("");
  const [humidity, setHumidity] = useState<string>("");
  const [altitudeM, setAltitudeM] = useState<string>("");

  // Autotune sweeps gearing + launch RPM on the full sim — slow on a
  // constrained instance, so it runs as a background job with real progress.
  const tune = useAutotuneJob();

  const numOrNull = (s: string): number | null => {
    const t = s.trim();
    if (t === "") return null;
    const n = Number(t);
    return Number.isFinite(n) ? n : null;
  };

  const canRun = bike != null && !tune.isRunning;

  const onRun = () => {
    if (!bike) return;
    tune.run({
      bike_id: bike.id,
      location: location.trim() || undefined,
      ambient_temp_c: numOrNull(tempC) ?? undefined,
      humidity_pct: numOrNull(humidity) ?? undefined,
      altitude_m: numOrNull(altitudeM) ?? undefined,
      rider_weight_kg: 75,
    });
  };

  const result = tune.data;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-semibold flex items-center gap-2">
          <Gauge className="w-5 h-5 text-signal-500" aria-hidden="true" /> Autotune
        </h1>
        <p className="text-sm text-carbon-400 mt-1">
          Get a track-and-weather-aware setup: gearing, launch RPM, tyre
          pressure, and fuel/timing trim for your bike at a given location.
        </p>
      </header>

      <OfflineBanner />

      {/* Inputs */}
      <section className="card p-5 space-y-4">
        <div>
          <label className="block text-xs uppercase tracking-wider text-carbon-500 mb-2">Bike</label>
          <BikePicker value={bike?.id ?? null} onChange={(_, summary) => setBike(summary)} />
        </div>

        <div>
          <label htmlFor="at-location" className="block text-xs uppercase tracking-wider text-carbon-500 mb-2">
            Location
          </label>
          <div className="relative">
            <MapPin className="w-3.5 h-3.5 text-carbon-500 absolute left-3 top-3 pointer-events-none" aria-hidden="true" />
            <input
              id="at-location"
              className="input pl-8"
              placeholder="e.g. Aamby Valley, Pune, or a city name"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
          <p className="text-[10px] text-carbon-600 mt-1.5">
            Optional. Resolves to a matched venue or live weather. Leave the
            manual fields blank to use the resolved conditions.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <NumField id="at-temp" label="Ambient °C" placeholder="auto" value={tempC} onChange={setTempC} />
          <NumField id="at-humidity" label="Humidity %" placeholder="auto" value={humidity} onChange={setHumidity} />
          <NumField id="at-altitude" label="Altitude m" placeholder="auto" value={altitudeM} onChange={setAltitudeM} />
        </div>

        <div className="flex justify-center pt-1">
          <button
            type="button"
            disabled={!canRun}
            onClick={onRun}
            className="btn btn-primary px-8 justify-center focus-visible:outline-2 focus-visible:outline-signal-300"
            title={!bike ? "Select a bike first" : "Get setup"}
          >
            {tune.isRunning ? (
              <><Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" /> Computing setup…</>
            ) : (
              <><Play className="w-4 h-4" aria-hidden="true" /> Get setup</>
            )}
          </button>
        </div>
      </section>

      {/* Error */}
      {tune.error && (
        <div className="card p-4 border-stop-500/40 bg-stop-500/5 flex gap-3" role="alert">
          <AlertTriangle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <div className="font-medium text-stop-500">Autotune failed</div>
            <div className="text-xs text-carbon-400 mt-1">
              {tune.error.message || "Unknown error — is the backend running?"}
            </div>
          </div>
        </div>
      )}

      {/* Live progress (real %, with a Stop button) */}
      {tune.isRunning && !result && (
        <>
          <section className="card p-5">
            <JobProgressBar
              status={tune.status}
              progress={tune.progress}
              stage={tune.stage}
              onStop={tune.stop}
              label="Computing track-aware setup…"
            />
          </section>
          <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {[0, 1, 2, 3, 4].map((i) => <SkeletonStatTile key={i} />)}
          </section>
        </>
      )}

      {result && <AutotuneResult result={result} />}
    </div>
  );
}

function NumField({ id, label, placeholder, value, onChange }: {
  id: string; label: string; placeholder?: string;
  value: string; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-[10px] uppercase tracking-wider text-carbon-500 mb-1.5">
        {label}
      </label>
      <input
        id={id}
        type="number"
        className="input tabular-nums"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}

function AutotuneResult({ result }: { result: EcuAutotune }) {
  const env = result.environment;
  return (
    <div className="space-y-5">
      {/* Header + combined net */}
      <section className="card p-5 flex flex-wrap items-center justify-between gap-4" role="status" aria-live="polite">
        <div>
          <div className="text-xs uppercase tracking-wider text-carbon-500">Setup for</div>
          <div className="text-lg font-semibold text-carbon-100">{result.bike_name}</div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-carbon-500">Stock ET</div>
            <div className="font-mono tabular-nums text-carbon-300">{result.stock.et_s.toFixed(3)} s</div>
          </div>
          <ArrowRight className="w-4 h-4 text-carbon-600" aria-hidden="true" />
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-carbon-500">Tuned ET</div>
            <div className="font-mono tabular-nums text-signal-400 text-lg font-semibold">
              {result.combined.et_s.toFixed(3)} s
            </div>
            <div
              className={clsx(
                "text-[10px] tabular-nums",
                result.combined.delta_et_s < 0 ? "text-go-500" : "text-carbon-500",
              )}
            >
              {result.combined.delta_et_s >= 0 ? "+" : ""}{result.combined.delta_et_s.toFixed(3)} s
            </div>
          </div>
        </div>
      </section>

      {/* Environment tiles */}
      <section>
        <div className="text-[10px] uppercase tracking-wider text-carbon-500 mb-2">Conditions</div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <StatTile label="Temp" value={env.temperature_c.toFixed(1)} unit="°C" />
          <StatTile label="Humidity" value={env.humidity_pct.toFixed(0)} unit="%" />
          <StatTile label="Density alt" value={Math.round(env.density_altitude_ft).toLocaleString()} unit="ft" />
          <StatTile label="Air density" value={env.air_density_kgm3.toFixed(3)} unit="kg/m³" />
          <StatTile
            label="Power corr"
            value={`${env.power_correction_pct >= 0 ? "+" : ""}${env.power_correction_pct.toFixed(1)}`}
            unit="%"
            accent={env.power_correction_pct < 0 ? "warn" : "plain"}
          />
        </div>
      </section>

      {/* Recommendation cards */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <GearingCard gearing={result.gearing} />
        <LaunchRpmCard launch={result.launch_rpm} />
        <TyrePressureCard tyre={result.tyre_pressure} />
        <FuelTimingCard fuel={result.fuel_timing} />
      </section>

      {/* Overall rationale */}
      <section className="card p-5">
        <div className="text-[10px] uppercase tracking-wider text-carbon-500 mb-2 flex items-center gap-1">
          <Info className="w-3 h-3" aria-hidden="true" /> Rationale
        </div>
        <p className="text-sm text-carbon-300 leading-relaxed">{result.rationale}</p>
        <div className="text-[10px] text-carbon-600 mt-3 pt-3 border-t border-carbon-800 flex flex-wrap gap-x-4 gap-y-1">
          <span>Source: {result.environment_source}</span>
          <span>Scoring: {result.scoring_method}</span>
          {env.location && <span>Location: {env.location}</span>}
        </div>
      </section>
    </div>
  );
}

function GuidelineBadge() {
  return (
    <span
      className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded border border-warn-500/40 text-warn-500"
      title="Advisory guideline, not a simulated optimum"
    >
      Guideline
    </span>
  );
}

function CardShell({ icon, title, badge, children }: {
  icon: ReactNode; title: string; badge?: ReactNode; children: ReactNode;
}) {
  return (
    <div className="card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-signal-500">{icon}</span>
          <div className="text-xs uppercase tracking-wider text-carbon-400">{title}</div>
        </div>
        {badge}
      </div>
      {children}
    </div>
  );
}

function GearingCard({ gearing }: { gearing: AutotuneGearing }) {
  return (
    <CardShell icon={<Cog className="w-4 h-4" aria-hidden="true" />} title="Gearing">
      {gearing.adjustable ? (
        <>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-semibold tabular-nums text-carbon-100">
              {gearing.recommended_front ?? gearing.stock_front}
              <span className="text-carbon-600 mx-1">/</span>
              {gearing.recommended_rear ?? gearing.stock_rear}
            </span>
            <span className="text-xs text-carbon-500">F/R teeth</span>
          </div>
          <div className="text-[11px] text-carbon-500 flex flex-wrap items-center gap-x-3 gap-y-0.5 tabular-nums">
            <span>Final drive {gearing.recommended_final_drive.toFixed(2)}</span>
            {(gearing.stock_front != null && gearing.stock_rear != null) && (
              <span className="text-carbon-600">stock {gearing.stock_front}/{gearing.stock_rear}</span>
            )}
            <span className={clsx(gearing.delta_et_s < 0 ? "text-go-500" : "text-carbon-500")}>
              {gearing.delta_et_s >= 0 ? "+" : ""}{gearing.delta_et_s.toFixed(3)} s
            </span>
          </div>
          <p className="text-[11px] text-carbon-400 leading-relaxed">{gearing.recommendation}</p>
        </>
      ) : (
        <>
          <div className="text-sm font-medium text-carbon-300">
            Fixed ({gearing.drive} drive)
          </div>
          <p className="text-[11px] text-carbon-500 leading-relaxed">
            {gearing.recommendation || `Final drive ${gearing.recommended_final_drive.toFixed(2)} is not user-adjustable on a ${gearing.drive}-drive bike.`}
          </p>
        </>
      )}
    </CardShell>
  );
}

function LaunchRpmCard({ launch }: { launch: AutotuneLaunchRpm }) {
  return (
    <CardShell icon={<Flag className="w-4 h-4" aria-hidden="true" />} title="Launch RPM">
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular-nums text-carbon-100">
          {Math.round(launch.recommended_rpm).toLocaleString()}
        </span>
        <span className="text-xs text-carbon-500">rpm</span>
      </div>
      <div className="text-[11px] text-carbon-500 flex flex-wrap items-center gap-x-3 gap-y-0.5 tabular-nums">
        <span className="text-carbon-600">stock {Math.round(launch.stock_rpm).toLocaleString()}</span>
        <span className={clsx(launch.delta_et_s < 0 ? "text-go-500" : "text-carbon-500")}>
          {launch.delta_et_s >= 0 ? "+" : ""}{launch.delta_et_s.toFixed(3)} s
        </span>
      </div>
      <p className="text-[11px] text-carbon-400 leading-relaxed">{launch.rationale}</p>
    </CardShell>
  );
}

function TyrePressureCard({ tyre }: { tyre: AutotuneTyrePressure }) {
  return (
    <CardShell
      icon={<Wind className="w-4 h-4" aria-hidden="true" />}
      title="Tyre pressure"
      badge={tyre.is_guideline ? <GuidelineBadge /> : undefined}
    >
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold tabular-nums text-carbon-100">
          {tyre.rear_psi.toFixed(1)}
          <span className="text-carbon-600 mx-1">/</span>
          {tyre.front_psi.toFixed(1)}
        </span>
        <span className="text-xs text-carbon-500">R/F psi</span>
      </div>
      <div className="text-[11px] text-carbon-600 tabular-nums">
        stock {tyre.stock_rear_psi.toFixed(1)}/{tyre.stock_front_psi.toFixed(1)} psi
      </div>
      <p className="text-[11px] text-carbon-400 leading-relaxed">{tyre.rationale}</p>
    </CardShell>
  );
}

function FuelTimingCard({ fuel }: { fuel: AutotuneFuelTiming }) {
  return (
    <CardShell
      icon={<Droplet className="w-4 h-4" aria-hidden="true" />}
      title="Fuel / timing"
      badge={fuel.is_guideline ? <GuidelineBadge /> : undefined}
    >
      {fuel.applicable ? (
        <>
          <div className="flex items-baseline gap-3 flex-wrap">
            <span className="text-lg font-semibold tabular-nums text-carbon-100">
              {fuel.fuel_trim_pct >= 0 ? "+" : ""}{fuel.fuel_trim_pct.toFixed(1)}%
              <span className="text-xs text-carbon-500 font-normal ml-1">fuel</span>
            </span>
            <span className="text-lg font-semibold tabular-nums text-carbon-100">
              {fuel.timing_advance_deg >= 0 ? "+" : ""}{fuel.timing_advance_deg.toFixed(1)}°
              <span className="text-xs text-carbon-500 font-normal ml-1">timing</span>
            </span>
          </div>
          <p className="text-[11px] text-carbon-400 leading-relaxed">{fuel.rationale}</p>
        </>
      ) : (
        <p className="text-[11px] text-carbon-500 leading-relaxed">
          {fuel.rationale || "Fuel/timing trim not applicable for this bike's fuelling."}
        </p>
      )}
    </CardShell>
  );
}
