import { useEffect, useMemo, useState } from "react";
import {
  Plus,
  Trash2,
  Loader2,
  Filter,
  AlertCircle,
  IndianRupee,
} from "lucide-react";
import { BikePicker } from "@/components/BikePicker";
import { StatTile } from "@/components/StatTile";
import {
  useParts,
  usePartsCategories,
  useQuickSimulate,
} from "@/hooks/useApi";
import type { BikeSummary, Part } from "@/types/api";
import clsx from "clsx";

export function BuildPage() {
  const [bike, setBike] = useState<BikeSummary | null>(null);
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  // Selected parts are kept as a full Map keyed by id so a filter change on
  // the catalog doesn't cause them to vanish from the build summary.
  const [selectedMap, setSelectedMap] = useState<Map<number, Part>>(new Map());
  const selectedIds = useMemo(
    () => Array.from(selectedMap.keys()),
    [selectedMap],
  );

  const categories = usePartsCategories();
  const parts = useParts({
    bike_id: bike?.id,
    category: categoryFilter || undefined,
    search: search || undefined,
    compatible_only: true,
    limit: 500,
  });

  const sim = useQuickSimulate();

  // Re-run whenever bike or selection changes — ~50 ms per run server-side.
  useEffect(() => {
    if (!bike) return;
    sim.mutate({
      bike_id: bike.id,
      part_ids: selectedIds,
      rider_mass_kg: 75,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bike?.id, selectedIds.join(",")]);

  const selectedParts = useMemo(
    () => Array.from(selectedMap.values()),
    [selectedMap],
  );
  const buildCost = selectedParts.reduce(
    (sum, p) => sum + (p.price_inr ?? 0),
    0,
  );

  const toggle = (part: Part) =>
    setSelectedMap((prev) => {
      const next = new Map(prev);
      if (next.has(part.id)) next.delete(part.id);
      else next.set(part.id, part);
      return next;
    });

  return (
    <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">
      <section className="space-y-5">
        <header>
          <h1 className="text-2xl font-semibold">Build-a-bike</h1>
          <p className="text-sm text-carbon-400 mt-1">
            Pick a base. Add parts. See the ET and trap speed update live —
            every pick runs the physics engine end to end.
          </p>
        </header>

        <div className="card p-5 space-y-4">
          <div>
            <label className="block text-xs uppercase tracking-wider text-carbon-500 mb-2">
              Base bike
            </label>
            <BikePicker
              value={bike?.id ?? null}
              onChange={(_, summary) => {
                setBike(summary);
                setSelectedMap(new Map());
              }}
            />
          </div>

          {bike && (
            <div className="flex flex-wrap gap-3">
              <div className="relative flex-1 min-w-[200px]">
                <Filter className="w-3.5 h-3.5 text-carbon-500 absolute left-3 top-3 pointer-events-none" />
                <select
                  className="input pl-8"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                >
                  <option value="">All categories</option>
                  {categories.data?.categories.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.display_name}
                    </option>
                  ))}
                </select>
              </div>
              <input
                className="input flex-1 min-w-[200px]"
                placeholder="Search brand or model…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          )}
        </div>

        {!bike && (
          <div className="card p-8 text-center text-carbon-500 text-sm">
            Pick a base bike to start browsing the parts catalog.
          </div>
        )}

        {bike && (
          <div className="card overflow-hidden">
            {parts.isLoading && (
              <div className="p-8 text-center text-carbon-500 text-sm">
                <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                Loading catalog…
              </div>
            )}
            {parts.isError && (
              <div className="p-6 border-l-4 border-stop-500 flex items-start gap-3 text-sm">
                <AlertCircle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" />
                <div>
                  <div className="font-medium text-stop-500">
                    Parts failed to load
                  </div>
                  <div className="text-carbon-400 mt-1">
                    {parts.error?.message || "Unknown error"}
                  </div>
                </div>
              </div>
            )}
            {parts.data && parts.data.parts.length === 0 && (
              <div className="p-8 text-center text-carbon-500 text-sm">
                No compatible parts for this bike + filter combo.
              </div>
            )}
            <ul className="divide-y divide-carbon-800">
              {parts.data?.parts.map((p) => (
                <PartRow
                  key={p.id}
                  part={p}
                  selected={selectedMap.has(p.id)}
                  onToggle={() => toggle(p)}
                />
              ))}
            </ul>
          </div>
        )}
      </section>

      <aside className="space-y-4 lg:sticky lg:top-6 lg:self-start">
        <div className="card p-5">
          <div className="text-xs uppercase tracking-wider text-carbon-500 mb-3">
            Your build
          </div>
          {!bike && (
            <div className="text-sm text-carbon-500">No bike selected.</div>
          )}
          {bike && sim.isPending && !sim.data && (
            <div className="flex items-center gap-2 text-sm text-carbon-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              Simulating baseline…
            </div>
          )}
          {sim.data && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <StatTile
                  label="ET"
                  value={sim.data.et_quarter_s.toFixed(3)}
                  unit="s"
                  accent="signal"
                />
                <StatTile
                  label="Trap"
                  value={sim.data.trap_speed_kmh.toFixed(1)}
                  unit="km/h"
                />
                <StatTile
                  label="60 ft"
                  value={sim.data.et_60ft_s.toFixed(3)}
                  unit="s"
                />
                <StatTile
                  label="1/8 mi"
                  value={sim.data.et_eighth_s.toFixed(3)}
                  unit="s"
                />
              </div>
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
                  <IndianRupee className="w-3 h-3" />
                  {buildCost > 0 ? buildCost.toLocaleString("en-IN") : "—"}
                </div>
                <div>
                  {selectedIds.length} part
                  {selectedIds.length === 1 ? "" : "s"}
                </div>
              </div>
            </div>
          )}
        </div>

        {selectedParts.length > 0 && (
          <div className="card p-4">
            <div className="text-xs uppercase tracking-wider text-carbon-500 mb-2">
              Selected
            </div>
            <ul className="space-y-2">
              {selectedParts.map((p) => (
                <li
                  key={p.id}
                  className="flex items-start justify-between gap-2 text-sm"
                >
                  <div className="min-w-0">
                    <div className="font-medium text-carbon-100 truncate">
                      {p.brand} {p.model_name}
                    </div>
                    <div className="text-[10px] text-carbon-500 uppercase tracking-wider">
                      {p.category_display}
                      {p.price_inr
                        ? ` · ₹${p.price_inr.toLocaleString("en-IN")}`
                        : ""}
                    </div>
                  </div>
                  <button
                    onClick={() => toggle(p)}
                    className="text-carbon-500 hover:text-stop-500 shrink-0"
                    title="Remove"
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

function PartRow({
  part,
  selected,
  onToggle,
}: {
  part: Part;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <li
      className={clsx(
        "flex items-center gap-3 px-4 py-3 hover:bg-carbon-800/40 cursor-pointer",
        selected && "bg-signal-500/5",
      )}
      onClick={onToggle}
    >
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggle();
        }}
        className={clsx(
          "w-7 h-7 rounded border shrink-0 flex items-center justify-center",
          selected
            ? "border-signal-500 bg-signal-500 text-carbon-950"
            : "border-carbon-700 text-carbon-500 hover:border-signal-500",
        )}
      >
        <Plus
          className={clsx(
            "w-3.5 h-3.5 transition-transform",
            selected && "rotate-45",
          )}
        />
      </button>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline gap-2">
          <span className="font-medium text-carbon-100 truncate">
            {part.brand}
          </span>
          <span className="text-sm text-carbon-400 truncate">
            {part.model_name}
          </span>
        </div>
        <div className="text-[10px] uppercase tracking-wider text-carbon-500 mt-0.5">
          {part.category_display}
          {typeof part.power_delta_hp === "number" &&
            ` · +${part.power_delta_hp} hp`}
          {typeof part.mass_delta_kg === "number" &&
            ` · ${part.mass_delta_kg > 0 ? "+" : ""}${part.mass_delta_kg} kg`}
        </div>
      </div>
      <div className="text-right text-sm shrink-0">
        {part.price_inr ? (
          <div className="tabular-nums text-carbon-200">
            ₹{part.price_inr.toLocaleString("en-IN")}
          </div>
        ) : (
          <div className="text-carbon-600 text-xs">no price</div>
        )}
      </div>
    </li>
  );
}
