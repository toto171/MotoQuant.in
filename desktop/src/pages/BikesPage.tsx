import { useState } from "react";
import { Link } from "react-router-dom";
import { Search, ChevronLeft, ChevronRight, Bike } from "lucide-react";
import { useBikes } from "@/hooks/useApi";

const PAGE = 40;

export function BikesPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<string>("");
  const [offset, setOffset] = useState(0);

  const { data, isLoading } = useBikes({
    search: search || undefined,
    category: category || undefined,
    limit: PAGE,
    offset,
  });

  const total = data?.total ?? 0;
  const page = Math.floor(offset / PAGE) + 1;
  const pages = Math.max(1, Math.ceil(total / PAGE));

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">Bike library</h1>
        <p className="text-sm text-carbon-400 mt-1">
          287 curated motorcycles — first-principles aero, gear ratios, tire
          fitments. Click through for the full spec sheet.
        </p>
      </header>

      <section className="flex flex-col md:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-carbon-500 absolute left-3 top-3.5 pointer-events-none" />
          <input
            className="input pl-9"
            placeholder="Search manufacturer or model…"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOffset(0);
            }}
          />
        </div>
        <select
          className="input md:w-52"
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setOffset(0);
          }}
        >
          <option value="">All categories</option>
          <option value="sport">Sport</option>
          <option value="naked">Naked</option>
          <option value="cruiser">Cruiser</option>
          <option value="adventure">Adventure</option>
          <option value="touring">Touring</option>
          <option value="commuter">Commuter</option>
          <option value="scooter">Scooter</option>
        </select>
      </section>

      <section className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-carbon-900 text-carbon-500 text-[10px] uppercase tracking-wider">
            <tr>
              <th className="text-left px-4 py-2.5">Bike</th>
              <th className="text-left px-4 py-2.5">Year</th>
              <th className="text-left px-4 py-2.5">Displacement</th>
              <th className="text-left px-4 py-2.5">Power</th>
              <th className="text-left px-4 py-2.5">Dry mass</th>
              <th className="text-left px-4 py-2.5">Category</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="p-8 text-center text-carbon-500">
                  Loading…
                </td>
              </tr>
            )}
            {!isLoading && data?.bikes.length === 0 && (
              <tr>
                <td colSpan={6} className="p-8 text-center text-carbon-500">
                  No bikes match.
                </td>
              </tr>
            )}
            {data?.bikes.map((b) => (
              <tr
                key={b.id}
                className="border-t border-carbon-800 hover:bg-carbon-800/40"
              >
                <td className="px-4 py-2.5">
                  <Link
                    to={`/simulate?bike=${b.id}`}
                    className="flex items-center gap-2 text-carbon-100 hover:text-signal-500"
                  >
                    <Bike className="w-3.5 h-3.5 text-carbon-500" />
                    <span className="font-medium">
                      {b.manufacturer} {b.model}
                    </span>
                  </Link>
                </td>
                <td className="px-4 py-2.5 text-carbon-400">{b.year ?? "—"}</td>
                <td className="px-4 py-2.5 text-carbon-400">
                  {b.displacement_cc ? `${b.displacement_cc} cc` : "—"}
                </td>
                <td className="px-4 py-2.5 text-carbon-400">
                  {b.peak_power_hp ? `${b.peak_power_hp} hp` : "—"}
                </td>
                <td className="px-4 py-2.5 text-carbon-400">
                  {b.dry_mass_kg ? `${b.dry_mass_kg} kg` : "—"}
                </td>
                <td className="px-4 py-2.5">
                  <span className="chip text-carbon-300">{b.category ?? "—"}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <div className="flex items-center justify-between text-xs text-carbon-500">
        <div>
          {total} bikes · page {page} of {pages}
        </div>
        <div className="flex gap-2">
          <button
            className="btn btn-ghost"
            disabled={offset === 0}
            onClick={() => setOffset(Math.max(0, offset - PAGE))}
          >
            <ChevronLeft className="w-4 h-4" />
            Prev
          </button>
          <button
            className="btn btn-ghost"
            disabled={offset + PAGE >= total}
            onClick={() => setOffset(offset + PAGE)}
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
