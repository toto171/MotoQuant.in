import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, ChevronLeft, ChevronRight, Bike, AlertTriangle, SlidersHorizontal, X } from "lucide-react";
import { useBikes } from "@/hooks/useApi";
import { OfflineBanner } from "@/components/OfflineBanner";
import { Skeleton, SkeletonTableRows } from "@/components/Skeleton";

const PAGE = 40;
const CATEGORIES = ["sport", "naked", "cruiser", "adventure", "touring", "commuter", "scooter"];

export function BikesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("");
  const [offset, setOffset] = useState(0);

  const { data, isLoading, isError, error } = useBikes({
    search: search || undefined,
    category: category || undefined,
    limit: PAGE,
    offset,
  });

  const total = data?.total ?? 0;
  const page = Math.floor(offset / PAGE) + 1;
  const pages = Math.max(1, Math.ceil(total / PAGE));
  const hasFilters = search !== "" || category !== "";
  const hasResults = (data?.bikes.length ?? 0) > 0;

  const clearFilters = () => { setSearch(""); setCategory(""); setOffset(0); };

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      <header>
        <h1 className="text-2xl font-semibold">Bike library</h1>
        <p className="text-sm text-carbon-400 mt-1">
          501 curated motorcycles — first-principles aero, gear ratios, tire fitments.
        </p>
      </header>

      <OfflineBanner />

      {/* Filters */}
      <section className="flex flex-col sm:flex-row gap-3" role="search" aria-label="Filter bikes">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-carbon-500 absolute left-3 top-3.5 pointer-events-none" aria-hidden="true" />
          <input
            className="input pl-9"
            placeholder="Search manufacturer or model…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOffset(0); }}
            aria-label="Search bikes"
          />
        </div>
        <div className="relative">
          <SlidersHorizontal className="w-3.5 h-3.5 text-carbon-500 absolute left-3 top-3 pointer-events-none" aria-hidden="true" />
          <select
            className="input sm:w-52 pl-8"
            value={category}
            onChange={(e) => { setCategory(e.target.value); setOffset(0); }}
            aria-label="Filter by category"
          >
            <option value="">All categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>
        </div>
        {hasFilters && (
          <button onClick={clearFilters} className="btn btn-ghost text-sm gap-1.5" aria-label="Clear filters">
            <X className="w-3.5 h-3.5" /> Clear
          </button>
        )}
      </section>

      {/* Error state */}
      {isError && (
        <div className="card p-4 border-stop-500/40 bg-stop-500/5 flex gap-3" role="alert">
          <AlertTriangle className="w-5 h-5 text-stop-500 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <div className="font-medium text-stop-500">Couldn't load bike catalog</div>
            <div className="text-xs text-carbon-400 mt-1">
              {(error as Error)?.message || "Unknown error — is the backend running?"}
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <section className="card overflow-hidden">
        <table className="w-full text-sm" role="table" aria-label="Bike catalog">
          <thead className="bg-carbon-900 text-carbon-500 text-[10px] uppercase tracking-wider">
            <tr>
              <th scope="col" className="text-left px-4 py-2.5">Bike</th>
              <th scope="col" className="text-left px-4 py-2.5">Year</th>
              <th scope="col" className="text-left px-4 py-2.5 hidden md:table-cell">Displacement</th>
              <th scope="col" className="text-left px-4 py-2.5">Power</th>
              <th scope="col" className="text-left px-4 py-2.5 hidden sm:table-cell">Dry mass</th>
              <th scope="col" className="text-left px-4 py-2.5">Category</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && <SkeletonTableRows rows={PAGE} cols={6} />}
            {!isLoading && !isError && !hasResults && (
              <tr>
                <td colSpan={6} className="p-12 text-center">
                  <div className="flex flex-col items-center gap-3 text-carbon-500">
                    <Bike className="w-8 h-8 text-carbon-700" aria-hidden="true" />
                    <div className="font-medium">
                      {hasFilters
                        ? `No bikes match "${search || category}"`
                        : "No bikes found"}
                    </div>
                    {hasFilters && (
                      <button onClick={clearFilters} className="btn btn-ghost text-sm">
                        Clear filters
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            )}
            {data?.bikes.map((b) => (
              <tr
                key={b.id}
                className="border-t border-carbon-800 hover:bg-carbon-800/40 focus-within:bg-carbon-800/20 transition-colors"
              >
                <td className="px-4 py-2.5">
                  <Link
                    to={`/simulate?bike=${b.id}`}
                    className="flex items-center gap-2 text-carbon-100 hover:text-signal-500 focus-visible:outline-2 focus-visible:outline-signal-500 rounded"
                  >
                    <Bike className="w-3.5 h-3.5 text-carbon-500 shrink-0" aria-hidden="true" />
                    <span className="font-medium">{b.manufacturer} {b.model}</span>
                  </Link>
                </td>
                <td className="px-4 py-2.5 text-carbon-400">{b.year ?? "—"}</td>
                <td className="px-4 py-2.5 text-carbon-400 hidden md:table-cell">
                  {b.displacement_cc ? `${b.displacement_cc} cc` : "—"}
                </td>
                <td className="px-4 py-2.5 text-carbon-400">
                  {b.peak_power_hp ? `${b.peak_power_hp} hp` : "—"}
                </td>
                <td className="px-4 py-2.5 text-carbon-400 hidden sm:table-cell">
                  {b.dry_mass_kg ? `${b.dry_mass_kg} kg` : "—"}
                </td>
                <td className="px-4 py-2.5">
                  {b.category ? (
                    <span className="chip text-carbon-300 capitalize">{b.category}</span>
                  ) : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Pagination */}
      {!isLoading && hasResults && (
        <div className="flex items-center justify-between text-xs text-carbon-500">
          <div>
            {total} bikes · page {page} of {pages}
          </div>
          <div className="flex gap-2" role="navigation" aria-label="Pagination">
            <button
              className="btn btn-ghost"
              disabled={offset === 0}
              onClick={() => setOffset(Math.max(0, offset - PAGE))}
              aria-label="Previous page"
            >
              <ChevronLeft className="w-4 h-4" aria-hidden="true" />
              Prev
            </button>
            <button
              className="btn btn-ghost"
              disabled={offset + PAGE >= total}
              onClick={() => setOffset(offset + PAGE)}
              aria-label="Next page"
            >
              Next
              <ChevronRight className="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      )}

      {/* Loading pagination placeholder */}
      {isLoading && (
        <div className="flex items-center justify-between">
          <Skeleton className="h-3 w-32" />
          <div className="flex gap-2">
            <Skeleton className="h-8 w-16 rounded-md" />
            <Skeleton className="h-8 w-16 rounded-md" />
          </div>
        </div>
      )}
    </div>
  );
}
