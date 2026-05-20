import { useEffect, useMemo, useState } from "react";
import {
  Plus, Trash2, Loader2, Filter, AlertCircle, IndianRupee, ArrowLeftRight, Wrench, Zap,
} from "lucide-react";
import { BikePicker } from "@/components/BikePicker";
import { StatTile } from "@/components/StatTile";
import { OfflineBanner } from "@/components/OfflineBanner";
import { SkeletonPartRows } from "@/components/Skeleton";
import { useToastStore } from "@/store/toastStore";
import {
  useParts, usePartsCategories, useQuickSimulate, useSurrogatePredict,
} from "@/hooks/useApi";
import type { BikeSummary, Part } from "@/types/api";
import clsx from "clsx";

const EXCLUSIVE_PREFIXES = [
  "exhaust", "air-filter", "air_filter", "ecu", "piggyback",
  "fuel-system", "fuel_system", "battery", "chain",
  "front-sprocket", "front_sprocket", "rear-sprocket", "rear_sprocket",
  "slipper", "clutch", "quickshifter", "boost", "turbo", "supercharger",
  "nitrous", "wheelie",
] as const;

export function isExclusiveCategory(name: string | null | undefined): boolean {
  if (!name) return false;
  const n = name.toLowerCase();
  return EXCLUSIVE_PREFIXES.some((p) => n.startsWith(p) || n.includes(p));
}

export function BuildPage() {
  const pushToast = useToastStore((s) => s.push);
  const [bike, setBike] = useState<BikeSummary | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [selectedMap, setSelectedMap] = useState<Map<number, Part>>(new Map());
  // Fast-preview = surrogate model (~1-3 ms inference). Falls back to the
  // full quick-sim (~50 ms) automatically when the surrogate reports the
  // build is outside its training envelope, or when the surrogate route
  // is unavailable (503 — model pickle not loaded on the backend).
  const [fastPreview, setFastPreview] = useState(true);

  const selectedIds = useMemo(() => Array.from(selectedMap.keys()), [selectedMap]);
  const selectedParts = useMemo(() => Array.from(selectedMap.values()), [selectedMap]);
  const buildCost = selectedParts.reduce((sum, p) => sum + (p.price_inr ?? 0), 0);

  // Aggregate part deltas for the surrogate preview. The full sim path
  // re-applies parts server-side; the surrogate path takes raw deltas.
  const previewDeltas = useMemo(() => {
    let powerBoost = 0;
    let massDelta = 0;
    for (const p of selectedParts) {
      // power_delta_hp on a stock 100 hp bike → +1% per hp gain (rough);
      // a real recompute happens on the server when fastPreview is OFF.
      if (typeof p.power_delta_hp === "number") {
        powerBoost += p.power_delta_hp;
      }
      if (typeof p.mass_delta_kg === "number") massDelta += p.mass_delta_kg;
    }
    return { powerBoost, massDelta };
  }, [selectedParts]);

  const categories = usePartsCategories();
  const parts = useParts({
    bike_id: bike?.id,
    category: categoryFilter || undefined,
    search: search || undefined,
    compatible_only: true,
    limit: 500,
  });
  const sim = useQuickSimulate();
  const surrogate = useSurrogatePredict();

  useEffect(() => {
    if (!bike) return;

    if (fastPreview) {
      // Power boost % from absolute hp delta — assumes stock peak is in
      // the bike summary; if not present, treat 1 hp delta as ~1 % which
      // is the right order of magnitude across the catalog. `BikeSummary`
      // declares `peak_power_hp: number | null`, so a direct read with
      // `?? 100` fallback is correctly typed without an assertion.
      const stockHp = bike.peak_power_hp ?? 100;
      const powerBoostPct = stockHp > 0 ? (previewDeltas.powerBoost / stockHp) * 100 : 0;
      surrogate.mutate(
        {
          bike_id: bike.id,
          power_boost_pct: powerBoostPct,
          mass_delta_kg: previewDeltas.massDelta,
          rider_weight_kg: 75,
        },
        {
          onSuccess: (resp) => {
            if (!resp.within_training_envelope) {
              // Out-of-distribution → escalate to the real sim.
              sim.mutate({ bike_id: bike.id, part_ids: selectedIds, rider_mass_kg: 75 });
            }
          },
          onError: () => {
            // Surrogate unavailable (503 → no model) → fall back to real sim.
            sim.mutate({ bike_id: bike.id, part_ids: selectedIds, rider_mass_kg: 75 });
          },
        },
      );
    } else {
      sim.mutate({ bike_id: bike.id, part_ids: selectedIds, rider_mass_kg: 75 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bike?.id, selectedIds.join(","), fastPreview, previewDeltas.powerBoost, previewDeltas.massDelta]);

  const visibleParts = useMemo(
    () => (parts.data?.parts ?? []).filter((p) => p.compatible !== false),
    [parts.data],
  );

  const selectedByExclusiveCategory = useMemo(() => {
    const m = new Map<number, Part>();
    for (const p of selectedParts) {
      if (isExclusiveCategory(p.category_name)) m.set(p.category_id, p);
    }
    return m;
  }, [selectedParts]);

  const toggle = (part: Part) =>
    setSelectedMap((prev) => {
      const next = new Map(prev);
      if (next.has(part.id)) { next.delete(part.id); return next; }

      // Exclusive category: evict the incumbent and fire a toast.
      if (isExclusiveCategory(part.category_name)) {
        for (const [otherId, otherPart] of next) {
          if (otherPart.category_id === part.category_id) {
            next.delete(otherId);
            pushToast({
              message: `Replaced ${otherPart.brand} ${otherPart.model_name} with ${part.brand} ${part.model_name}`,
              variant: "info",
            });
          }
        }
      }
      next.set(part.id, part);
      return next;
    });

  return (
    <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">
      {/* Left: catalog */}
      <section className="space-y-5 min-w-0">
        <header>
          <h1 className="text-2xl font-semibold">Build-a-bike</h1>
          <p className="text-sm text-carbon-400 mt-1">
            Pick a base. Add parts. Every pick runs the physics engine live.
            Exclusive categories (exhaust, ECU, chain…) swap rather than stack.
          </p>
        </header>

        <OfflineBanner />

        <div className="card p-5 space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-wider text-carbon-500 mb-2">Base bike</label>
            <BikePicker
              value={bike?.id ?? null}
              onChange={(_, summary) => { setBike(summary); setSelectedMap(new Map()); }}
            />
          </div>

          {bike && (
            <div className="flex flex-wrap gap-3">
              <div className="relative flex-1 min-w-[180px]">
                <Filter className="w-3.5 h-3.5 text-carbon-500 absolute left-3 top-3 pointer-events-none" aria-hidden="true" />
                <select
                  className="input pl-8"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  aria-label="Filter parts by category"
                >
                  <option value="">All categories</option>
                  {categories.data?.categories.map((c) => (
                    <option key={c.id} value={c.name}>{c.display_name}</option>
                  ))}
                </select>
              </div>
              <input
                className="input flex-1 min-w-[180px]"
                placeholder="Search brand or model…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                aria-label="Search parts"
              />
            </div>
          )}
        </div>

        {/* Empty state — no bike selected */}
        {!bike && (
          <div className="card p-12 text-center flex flex-col items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-carbon-800 flex items-center justify-center">
              <Wrench className="w-7 h-7 text-carbon-600" aria-hidden="true" />
            </div>
            <div>
              <div className="font-medium text-carbon-200">No bike selected</div>
              <div className="text-sm text-carbon-500 mt-1">
                Choose a base bike above to browse the compatible parts catalog.
              </div>
            </div>
          </div>
        )}

        {bike && (
          <div className="card overflow-hidden">
            {/* Loading skeleton */}
            {parts.isLoading && <SkeletonPartRows rows={8} />}

            {/* Error */}
            {parts.isError && (
              <div className="p-6 border-l-4 border-stop-500 flex items-start gap-3 text-sm" role="alert">
                <AlertCircle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" aria-hidden="true" />
                <div>
                  <div className="font-medium text-stop-500">Parts failed to load</div>
                  <div className="text-carbon-400 mt-1">{parts.error?.message || "Unknown error"}</div>
                </div>
              </div>
            )}

            {/* Empty state — filters produced no results */}
            {!parts.isLoading && !parts.isError && visibleParts.length === 0 && (
              <div className="p-10 text-center text-carbon-500 text-sm flex flex-col items-center gap-2">
                <div className="font-medium">No compatible parts found</div>
                <div className="text-xs text-carbon-600">
                  {categoryFilter || search
                    ? "Try clearing the category or search filter."
                    : `No parts are catalogued for ${bike.manufacturer} ${bike.model} yet.`}
                </div>
              </div>
            )}

            {visibleParts.length > 0 && (
              <>
                <div className="px-4 py-2 text-[10px] uppercase tracking-wider text-carbon-500 bg-carbon-900/40 border-b border-carbon-800">
                  {visibleParts.length} compatible part{visibleParts.length === 1 ? "" : "s"} for{" "}
                  <span className="text-carbon-300">{bike.manufacturer} {bike.model}</span>
                </div>
                <ul className="divide-y divide-carbon-800" role="list" aria-label="Compatible parts">
                  {visibleParts.map((p) => {
                    const exclusiveSwap =
                      isExclusiveCategory(p.category_name) &&
                      !selectedMap.has(p.id) &&
                      selectedByExclusiveCategory.has(p.category_id)
                        ? selectedByExclusiveCategory.get(p.category_id) || null
                        : null;
                    return (
                      <PartRow
                        key={p.id}
                        part={p}
                        selected={selectedMap.has(p.id)}
                        swapsOut={exclusiveSwap}
                        onToggle={() => toggle(p)}
                      />
                    );
                  })}
                </ul>
              </>
            )}
          </div>
        )}
      </section>

      {/* Right: build summary */}
      <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs uppercase tracking-wider text-carbon-500">Your build</div>
            <button
              onClick={() => setFastPreview((v) => !v)}
              className={clsx(
                "text-[10px] uppercase tracking-wider px-2 py-1 rounded border transition-colors flex items-center gap-1 focus-visible:outline-2 focus-visible:outline-signal-500",
                fastPreview
                  ? "border-signal-500/40 bg-signal-500/10 text-signal-500"
                  : "border-carbon-700 text-carbon-400 hover:border-carbon-600",
              )}
              title={fastPreview ? "Surrogate model preview (~1-3 ms). Click for full sim." : "Full physics sim (~50 ms). Click for fast preview."}
              aria-pressed={fastPreview}
            >
              <Zap className="w-3 h-3" aria-hidden="true" />
              {fastPreview ? "Fast preview" : "Full sim"}
            </button>
          </div>

          {!bike && (
            <div className="text-sm text-carbon-500">No bike selected.</div>
          )}

          {bike && (sim.isPending || surrogate.isPending) && !sim.data && !surrogate.data && (
            <div className="flex items-center gap-2 text-sm text-carbon-400">
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
              {fastPreview ? "Inferring…" : "Simulating baseline…"}
            </div>
          )}

          {sim.isError && !surrogate.data && (
            <div className="text-xs text-stop-400 flex items-center gap-1.5" role="alert">
              <AlertCircle className="w-3.5 h-3.5" aria-hidden="true" />
              {sim.error?.message || "Simulation failed"}
            </div>
          )}

          {/* Surrogate-only display: when fastPreview is on AND surrogate is
              within envelope AND we don't have a full sim escalation yet. */}
          {fastPreview && surrogate.data?.within_training_envelope && !sim.data && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <StatTile label="ET" value={surrogate.data.et_s.toFixed(3)} unit="s" accent="signal" />
                <StatTile label="Trap" value={surrogate.data.trap_kmh.toFixed(1)} unit="km/h" />
              </div>
              <div className="text-[10px] text-carbon-500 uppercase tracking-wider flex items-center justify-between border-t border-carbon-800 pt-2">
                <span>Surrogate · {surrogate.data.source}</span>
                <span className="tabular-nums">{surrogate.data.inference_ms.toFixed(1)} ms</span>
              </div>
            </div>
          )}

          {sim.data && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <StatTile label="ET" value={sim.data.et_quarter_s.toFixed(3)} unit="s" accent="signal" />
                <StatTile label="Trap" value={sim.data.trap_speed_kmh.toFixed(1)} unit="km/h" />
                <StatTile label="60 ft" value={sim.data.et_60ft_s.toFixed(3)} unit="s" />
                <StatTile label="1/8 mi" value={sim.data.et_eighth_s.toFixed(3)} unit="s" />
              </div>

              {/* Out-of-envelope chip — surrogate triggered fallback to full sim */}
              {fastPreview && surrogate.data && !surrogate.data.within_training_envelope && (
                <div className="text-[10px] text-warn-500 flex items-start gap-1.5 px-2.5 py-1.5 rounded-md border border-warn-500/30 bg-warn-500/5">
                  <AlertCircle className="w-3 h-3 mt-0.5 shrink-0" aria-hidden="true" />
                  Build is outside the surrogate's training envelope ({surrogate.data.envelope_violations.join(", ")}). Used full sim instead.
                </div>
              )}

              {sim.data.stock_et_s != null && sim.data.et_delta_s != null && (
                <div
                  className={clsx(
                    "text-xs p-2.5 rounded-md border",
                    sim.data.et_delta_s < 0
                      ? "border-go-500/40 bg-go-500/5 text-go-500"
                      : sim.data.et_delta_s > 0
                        ? "border-warn-500/40 bg-warn-500/5 text-warn-500"
                        : "border-carbon-700 text-carbon-400",
                  )}
                  role="status"
                  aria-live="polite"
                >
                  Parts delta{" "}
                  <strong className="tabular-nums">
                    {sim.data.et_delta_s >= 0 ? "+" : ""}
                    {sim.data.et_delta_s.toFixed(3)} s
                  </strong>{" "}
                  vs stock {sim.data.stock_et_s.toFixed(3)} s
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-carbon-400 pt-2 border-t border-carbon-800">
                <div className="flex items-center gap-1">
                  <IndianRupee className="w-3 h-3" aria-hidden="true" />
                  {buildCost > 0 ? buildCost.toLocaleString("en-IN") : "—"}
                </div>
                <div>{selectedIds.length} part{selectedIds.length === 1 ? "" : "s"}</div>
              </div>
            </div>
          )}

          {/* Empty state — bike selected but nothing added yet */}
          {bike && !sim.isPending && sim.data && selectedParts.length === 0 && (
            <div className="mt-4 pt-4 border-t border-carbon-800 text-center text-carbon-500 text-xs">
              Pick parts from the catalog to see their impact.
            </div>
          )}
        </div>

        {selectedParts.length > 0 && (
          <div className="card p-4">
            <div className="text-xs uppercase tracking-wider text-carbon-500 mb-2">Selected</div>
            <ul className="space-y-2" role="list" aria-label="Selected parts">
              {selectedParts.map((p) => (
                <li key={p.id} className="flex items-start justify-between gap-2 text-sm">
                  <div className="min-w-0">
                    <div className="font-medium text-carbon-100 truncate">{p.brand} {p.model_name}</div>
                    <div className="text-[10px] text-carbon-500 uppercase tracking-wider">
                      {p.category_display}
                      {p.price_inr ? ` · ₹${p.price_inr.toLocaleString("en-IN")}` : ""}
                    </div>
                  </div>
                  <button
                    onClick={() => toggle(p)}
                    className="text-carbon-500 hover:text-stop-500 shrink-0 focus-visible:outline-2 focus-visible:outline-signal-500 rounded"
                    aria-label={`Remove ${p.brand} ${p.model_name}`}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </aside>
    </div>
  );
}

function PartRow({ part, selected, swapsOut, onToggle }: {
  part: Part; selected: boolean; swapsOut: Part | null; onToggle: () => void;
}) {
  return (
    <li
      className={clsx(
        "flex items-center gap-3 px-4 py-3 hover:bg-carbon-800/40 cursor-pointer transition-colors",
        selected && "bg-signal-500/5",
      )}
      onClick={onToggle}
      role="option"
      aria-selected={selected}
    >
      <button
        onClick={(e) => { e.stopPropagation(); onToggle(); }}
        className={clsx(
          "w-7 h-7 rounded border shrink-0 flex items-center justify-center transition-colors focus-visible:outline-2 focus-visible:outline-signal-500",
          selected
            ? "border-signal-500 bg-signal-500 text-carbon-950"
            : "border-carbon-700 text-carbon-500 hover:border-signal-500",
        )}
        aria-label={selected ? `Remove ${part.brand} ${part.model_name}` : `Add ${part.brand} ${part.model_name}`}
      >
        <Plus className={clsx("w-3.5 h-3.5 transition-transform", selected && "rotate-45")} aria-hidden="true" />
      </button>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="font-medium text-carbon-100 truncate">{part.brand}</span>
          <span className="text-sm text-carbon-400 truncate">{part.model_name}</span>
        </div>
        <div className="text-[10px] uppercase tracking-wider text-carbon-500 mt-0.5 flex flex-wrap items-center gap-2">
          <span>{part.category_display}</span>
          {typeof part.power_delta_hp === "number" && <span>· +{part.power_delta_hp} hp</span>}
          {typeof part.mass_delta_kg === "number" && (
            <span>· {part.mass_delta_kg > 0 ? "+" : ""}{part.mass_delta_kg} kg</span>
          )}
          {swapsOut && (
            <span className="inline-flex items-center gap-1 text-warn-500">
              <ArrowLeftRight className="w-3 h-3" aria-hidden="true" />
              replaces {swapsOut.brand}
            </span>
          )}
        </div>
      </div>
      <div className="text-right text-sm shrink-0">
        {part.price_inr ? (
          <div className="tabular-nums text-carbon-200">₹{part.price_inr.toLocaleString("en-IN")}</div>
        ) : (
          <div className="text-carbon-600 text-xs">no price</div>
        )}
      </div>
    </li>
  );
}
