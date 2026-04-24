// BikePicker — fuzzy-search dropdown backed by fuse.js.
//
// Loads ALL bikes once (limit=500) and caches in React Query for 10 min.
// Fuse.js searches across manufacturer + model + year + category on the client
// so "2023 Ninja" and "r15 v3" both resolve correctly without a round-trip.

import { useState, useMemo, useEffect, useRef } from "react";
import Fuse from "fuse.js";
import { Search, X } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { BikeSummary } from "@/types/api";
import clsx from "clsx";

interface Props {
  value: number | null;
  onChange: (id: number | null, summary: BikeSummary | null) => void;
  placeholder?: string;
}

function useAllBikes() {
  return useQuery({
    queryKey: ["bikes", "__all__"],
    queryFn: () => api.listBikes({ limit: 500 }),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  });
}

const FUSE_OPTS = {
  keys: [
    { name: "manufacturer", weight: 0.35 },
    { name: "model", weight: 0.45 },
    { name: "year", weight: 0.1 },
    { name: "category", weight: 0.1 },
  ],
  threshold: 0.35,
  includeScore: true,
  minMatchCharLength: 1,
};

export function BikePicker({ value, onChange, placeholder }: Props) {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [pickedSummary, setPickedSummary] = useState<BikeSummary | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useAllBikes();
  const allBikes = data?.bikes ?? [];

  const fuse = useMemo(() => new Fuse(allBikes, FUSE_OPTS), [allBikes]);

  const results = useMemo<BikeSummary[]>(() => {
    const q = search.trim();
    if (!q) return allBikes.slice(0, 60);
    return fuse.search(q, { limit: 60 }).map((r) => r.item);
  }, [search, fuse, allBikes]);

  useEffect(() => {
    if (value === null) {
      setPickedSummary(null);
      setSearch("");
    }
  }, [value]);

  // Global "/" shortcut fires this event to open the picker.
  useEffect(() => {
    const handler = () => {
      setOpen(true);
      setTimeout(() => inputRef.current?.focus(), 0);
    };
    window.addEventListener("mq:focus-search", handler);
    return () => window.removeEventListener("mq:focus-search", handler);
  }, []);

  const selected = useMemo(() => {
    if (value == null) return null;
    const fresh = allBikes.find((b) => b.id === value);
    if (fresh) return fresh;
    if (pickedSummary && pickedSummary.id === value) return pickedSummary;
    return null;
  }, [allBikes, value, pickedSummary]);

  return (
    <div className="relative">
      <div
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label="Select a bike"
        onClick={() => { setOpen(true); setTimeout(() => inputRef.current?.focus(), 0); }}
        className="input cursor-text flex items-center gap-2"
      >
        <Search className="w-4 h-4 text-carbon-500 shrink-0" aria-hidden="true" />
        {selected && !open ? (
          <div className="flex-1 flex items-center gap-2 min-w-0">
            <span className="font-medium text-carbon-100 truncate">
              {selected.manufacturer} {selected.model}
            </span>
            <span className="text-carbon-500 text-xs shrink-0 hidden sm:block">
              {selected.year} · {selected.displacement_cc}cc · {selected.peak_power_hp} hp
            </span>
            <button
              onClick={(e) => { e.stopPropagation(); onChange(null, null); setPickedSummary(null); setSearch(""); }}
              className="ml-auto text-carbon-500 hover:text-carbon-100 focus-visible:outline-2 focus-visible:outline-signal-500 rounded"
              aria-label="Clear bike selection"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <input
            ref={inputRef}
            autoFocus={open}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onFocus={() => setOpen(true)}
            onKeyDown={(e) => { if (e.key === "Escape") { setOpen(false); setSearch(""); } }}
            placeholder={placeholder ?? `Search ${allBikes.length || 287} bikes…`}
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-carbon-600"
            aria-autocomplete="list"
            aria-controls="bike-picker-list"
          />
        )}
      </div>

      {open && (
        <ul
          id="bike-picker-list"
          role="listbox"
          aria-label="Bike search results"
          className="absolute z-20 left-0 right-0 mt-1 bg-carbon-900 border border-carbon-800 rounded-lg shadow-xl max-h-80 overflow-y-auto"
        >
          {isLoading && (
            <li className="p-4 text-center text-carbon-500 text-sm">Loading catalog…</li>
          )}
          {!isLoading && results.length === 0 && (
            <li className="p-4 text-center text-carbon-500 text-sm">
              No bikes match "{search}" — try manufacturer or model name.
            </li>
          )}
          {results.map((b) => (
            <li
              key={b.id}
              role="option"
              aria-selected={value === b.id}
              onClick={() => { onChange(b.id, b); setPickedSummary(b); setOpen(false); setSearch(""); }}
              className={clsx(
                "w-full text-left px-4 py-2 hover:bg-carbon-800 border-b border-carbon-800/50 last:border-0 text-sm cursor-pointer",
                value === b.id && "bg-carbon-800",
              )}
            >
              <div className="font-medium text-carbon-100">
                {b.manufacturer} {b.model}
              </div>
              <div className="text-xs text-carbon-500 mt-0.5">
                {b.year} · {b.displacement_cc}cc · {b.peak_power_hp} hp · {b.dry_mass_kg} kg · {b.category}
              </div>
            </li>
          ))}
        </ul>
      )}

      {open && (
        <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} aria-hidden="true" />
      )}
    </div>
  );
}
