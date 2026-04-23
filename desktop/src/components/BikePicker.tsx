import { useState, useMemo, useEffect } from "react";
import { Search, X } from "lucide-react";
import { useBikes } from "@/hooks/useApi";
import type { BikeSummary } from "@/types/api";
import clsx from "clsx";

interface Props {
  value: number | null;
  onChange: (id: number | null, summary: BikeSummary | null) => void;
}

export function BikePicker({ value, onChange }: Props) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  // Sticky copy of the last-picked summary — prevents the display from
  // losing its label when search clears after a pick. Without this, picking
  // e.g. "Suzuki Hayabusa" would select id=114 correctly, but then
  // `setSearch("")` causes the next /api/bikes fetch to return the first 60
  // bikes alphabetically (Aprilia, BMW, ...) which doesn't contain Hayabusa
  // — so the `selected` lookup returned null and the picker fell back to
  // the empty-search input state even though `value` was still set.
  // Bug only manifested for bikes past the first 60 alphabetically
  // (Harley, Suzuki, Triumph, Yamaha, etc.).
  const [pickedSummary, setPickedSummary] = useState<BikeSummary | null>(null);

  const { data, isLoading } = useBikes({ search, limit: 60 });

  // Mirror external clears (e.g. parent resets the form).
  useEffect(() => {
    if (value === null) setPickedSummary(null);
  }, [value]);

  const selected = useMemo(() => {
    if (value == null) return null;
    // Prefer a fresh match from the current search fetch (keeps data up to
    // date if the catalog ever changes); fall back to the sticky local copy.
    const fresh = data?.bikes.find((b) => b.id === value);
    if (fresh) return fresh;
    if (pickedSummary && pickedSummary.id === value) return pickedSummary;
    return null;
  }, [data, value, pickedSummary]);

  return (
    <div className="relative">
      <div
        onClick={() => setOpen(true)}
        className="input cursor-text flex items-center gap-2"
      >
        <Search className="w-4 h-4 text-carbon-500 shrink-0" />
        {selected && !open ? (
          <div className="flex-1 flex items-center gap-2">
            <span className="font-medium text-carbon-100">
              {selected.manufacturer} {selected.model}
            </span>
            <span className="text-carbon-500 text-xs">
              {selected.year} · {selected.displacement_cc}cc ·{" "}
              {selected.peak_power_hp} hp
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onChange(null, null);
                setPickedSummary(null);
                setSearch("");
              }}
              className="ml-auto text-carbon-500 hover:text-carbon-100"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <input
            autoFocus={open}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setOpen(true)}
            placeholder="Search 287 bikes…"
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-carbon-600"
          />
        )}
      </div>

      {open && (
        <div className="absolute z-20 left-0 right-0 mt-1 bg-carbon-900 border border-carbon-800 rounded-lg shadow-xl max-h-80 overflow-y-auto">
          {isLoading && (
            <div className="p-4 text-center text-carbon-500 text-sm">
              Loading…
            </div>
          )}
          {!isLoading && (!data || data.bikes.length === 0) && (
            <div className="p-4 text-center text-carbon-500 text-sm">
              No bikes match.
            </div>
          )}
          {data?.bikes.map((b) => (
            <button
              key={b.id}
              onClick={() => {
                onChange(b.id, b);
                setPickedSummary(b); // sticky for display (see comment above)
                setOpen(false);
                setSearch("");
              }}
              className={clsx(
                "w-full text-left px-4 py-2 hover:bg-carbon-800 border-b border-carbon-800/50 last:border-0 text-sm",
                value === b.id && "bg-carbon-800",
              )}
            >
              <div className="font-medium text-carbon-100">
                {b.manufacturer} {b.model}
              </div>
              <div className="text-xs text-carbon-500 mt-0.5">
                {b.year} · {b.displacement_cc}cc · {b.peak_power_hp} hp ·{" "}
                {b.dry_mass_kg} kg · {b.category}
              </div>
            </button>
          ))}
        </div>
      )}
      {open && (
        <div
          className="fixed inset-0 z-10"
          onClick={() => setOpen(false)}
        />
      )}
    </div>
  );
}
