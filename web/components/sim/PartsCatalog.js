'use client';

/**
 * PartsCatalog — "Parts and mods": a search field, the selected-parts summary
 * with total cost pinned at the top, and a collapsible list per category.
 * Incompatible parts are greyed out (not hidden) with a plain reason, and
 * picking a part in a one-per-bike slot (exhaust, ECU, …) replaces the other.
 * Rows are memoised so toggling one part re-renders one row (F9).
 */

import { memo, useEffect, useMemo, useRef, useState } from 'react';
import { Check, ChevronRight, Search } from 'lucide-react';
import { partLabel } from '../../lib/api';
import { ErrorTile, PartChip } from './controls';
import { partSlot, inr } from './format';

const humanKey = (k) => k.split('.').pop().replace(/_/g, ' ');

const PartRow = memo(function PartRow({ part, selected, replaces, onToggle }) {
  const compat = part.compatible !== false;
  const disabled = !compat && !selected;
  const name = partLabel(part.brand, part.model_name);
  const deltas = part.param_deltas && typeof part.param_deltas === 'object' ? Object.entries(part.param_deltas) : [];
  const mults = part.param_multipliers && typeof part.param_multipliers === 'object' ? Object.entries(part.param_multipliers) : [];
  return (
    <button
      type="button"
      onClick={() => { if (!disabled) onToggle(part); }}
      disabled={disabled}
      aria-pressed={selected}
      title={compat ? undefined : `Does not fit this bike: ${part.fitment_reason || 'incompatible'}`}
      className={`w-full rounded-xl border p-3 text-left transition-colors ${
        selected
          ? 'border-accent/50 bg-accent/[0.08] text-white'
          : disabled
            ? 'cursor-not-allowed border-white/[0.06] text-white/45 opacity-60'
            : 'border-white/10 text-white/80 hover:border-white/30 hover:text-white'
      }`}
    >
      <span className="flex items-start justify-between gap-3">
        <span className="min-w-0">
          <span className="block text-sm font-medium">{name}</span>
          {!compat && <span className="mt-0.5 block text-xs text-signal-foul">Does not fit this bike</span>}
          {replaces && !selected && <span className="mt-0.5 block text-xs text-white/60">Replaces {replaces}</span>}
          {part.fitment_notes && <span className="mt-0.5 block text-xs text-white/55">{part.fitment_notes}</span>}
        </span>
        <span className="shrink-0 text-right text-sm">
          {part.price_inr > 0 && <span className="block text-white/70">{inr(part.price_inr)}</span>}
          {selected && (
            <span className="mt-0.5 inline-flex items-center gap-1 text-xs font-medium text-accent">
              <Check size={12} aria-hidden="true" /> Added
            </span>
          )}
        </span>
      </span>
      {(deltas.length > 0 || mults.length > 0) && (
        <span className="mt-2 flex flex-wrap gap-1.5">
          {deltas.map(([k, v]) => (
            <span key={k} className={`rounded px-1.5 py-0.5 text-xs ${v > 0 ? 'bg-signal-go/10 text-signal-go' : 'bg-signal-foul/10 text-signal-foul'}`}>
              {humanKey(k)} {v > 0 ? '+' : ''}{v}
            </span>
          ))}
          {mults.map(([k, v]) => (
            <span key={k} className={`rounded px-1.5 py-0.5 text-xs ${v > 1 ? 'bg-signal-go/10 text-signal-go' : 'bg-signal-foul/10 text-signal-foul'}`}>
              {humanKey(k)} ×{v}
            </span>
          ))}
        </span>
      )}
    </button>
  );
});

const PartsCatalog = memo(function PartsCatalog({
  bikeId, categories, allParts, partsStatus, partsError, partsBikeId, selectedParts, buildCost,
  categoryNameById, onToggle, onRemove, onRetry, focusRequest, onFocusDone,
}) {
  const [query, setQuery] = useState('');
  const [openCat, setOpenCat] = useState(null);
  const searchRef = useRef(null);
  const rootRef = useRef(null);

  const ready = partsStatus === 'ready' && partsBikeId === bikeId;

  useEffect(() => {
    if (focusRequest !== 'parts' || !ready) return;
    rootRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    searchRef.current?.focus({ preventScroll: true });
    onFocusDone();
  }, [focusRequest, onFocusDone, ready]);

  const byCat = useMemo(() => {
    const m = new Map();
    for (const p of allParts) {
      if (!m.has(p.category_id)) m.set(p.category_id, []);
      m.get(p.category_id).push(p);
    }
    return m;
  }, [allParts]);

  const needle = query.trim().toLowerCase();
  const visible = useMemo(() => {
    const out = [];
    for (const cat of categories) {
      let list = byCat.get(cat.id) || [];
      if (needle) list = list.filter((p) => `${p.brand} ${p.model_name}`.toLowerCase().includes(needle));
      if (needle && list.length === 0) continue;
      out.push({ cat, list });
    }
    return out;
  }, [categories, byCat, needle]);

  const selectedIds = useMemo(() => new Set(selectedParts.map((p) => p.id)), [selectedParts]);
  // exclusivity group -> selected part label (for the "Replaces …" hint)
  const takenGroups = useMemo(() => {
    const m = new Map();
    for (const p of selectedParts) {
      const g = partSlot(p, categoryNameById[p.category_id]);
      if (g) m.set(g, { id: p.id, label: partLabel(p.brand, p.model_name) });
    }
    return m;
  }, [selectedParts, categoryNameById]);

  return (
    <section ref={rootRef} id="sim-parts" className="card card-pad" aria-label="Parts and mods">
      <h2 className="font-display text-lg font-semibold text-white">Parts and mods</h2>
      <p className="field-hint !mt-0.5">Parts that do not fit your bike are greyed out.</p>

      {selectedParts.length > 0 && (
        <div className="mt-3 rounded-xl border border-accent/30 bg-accent/[0.06] p-3">
          <p className="text-sm font-medium text-white">
            {selectedParts.length} {selectedParts.length === 1 ? 'part' : 'parts'} · {inr(buildCost)}
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {selectedParts.map((p) => <PartChip key={p.id} part={p} onRemove={onRemove} />)}
          </div>
        </div>
      )}

      <div className="mt-4">
        <label htmlFor="sim-parts-search" className="field-label">Search parts</label>
        <div className="relative">
          <Search size={16} aria-hidden="true" className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/45" />
          <input
            ref={searchRef}
            id="sim-parts-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Brand or name, e.g. Akrapovic"
            className="input-base pl-10"
            disabled={!ready}
          />
        </div>
      </div>

      <div className="mt-4">
        {partsStatus === 'error' ? (
          <ErrorTile message={partsError || 'We could not load the parts list.'} onRetry={onRetry} />
        ) : !ready ? (
          <div aria-busy="true" aria-label="Loading parts" className="space-y-2">
            {Array.from({ length: 8 }, (_, i) => <div key={i} className="skeleton h-11 w-full" />)}
          </div>
        ) : visible.length === 0 ? (
          <p className="py-6 text-center text-sm text-white/60">No parts match “{query}”.</p>
        ) : (
          <ul className="space-y-1.5">
            {visible.map(({ cat, list }) => {
              const isOpen = needle ? true : openCat === cat.id;
              const fits = list.filter((p) => p.compatible !== false).length;
              const chosen = list.filter((p) => selectedIds.has(p.id)).length;
              return (
                <li key={cat.id}>
                  <button
                    type="button"
                    onClick={() => setOpenCat(openCat === cat.id ? null : cat.id)}
                    aria-expanded={isOpen}
                    className={`flex min-h-11 w-full items-center justify-between gap-3 rounded-xl border px-3 text-left text-sm transition-colors ${
                      isOpen ? 'border-white/20 bg-white/[0.06] text-white' : 'border-transparent text-white/75 hover:bg-white/[0.04]'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <ChevronRight size={14} aria-hidden="true" className={`transition-transform ${isOpen ? 'rotate-90' : ''}`} />
                      <span className="font-medium">{cat.display_name || cat.name}</span>
                      <span className="text-xs text-white/55">
                        {fits}{list.length !== fits ? ` of ${list.length}` : ''} fit
                      </span>
                    </span>
                    {chosen > 0 && (
                      <span className="rounded bg-accent px-1.5 py-0.5 text-xs font-bold text-on-accent">{chosen}</span>
                    )}
                  </button>
                  {isOpen && (
                    <div className="mb-2 ml-3 mt-1.5 space-y-1.5 border-l border-white/10 pl-3">
                      {list.length === 0 ? (
                        <p className="py-2 text-sm text-white/55">No parts in this category.</p>
                      ) : (
                        list.map((part) => (
                          <PartRow
                            key={part.id}
                            part={part}
                            selected={selectedIds.has(part.id)}
                            replaces={(() => { const g = partSlot(part, cat.name); return g && takenGroups.has(g) && takenGroups.get(g).id !== part.id ? takenGroups.get(g).label : null; })()}
                            onToggle={onToggle}
                          />
                        ))
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
});

export default PartsCatalog;
