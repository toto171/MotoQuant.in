'use client';

/**
 * Small shared controls for the /simulator page: SimSlider, SimDropdown,
 * ErrorTile, PartChip. Memoised — the page re-renders on every slider tick,
 * these must not (F9). Accessibility (F13): every control has a visible label
 * wired by id, dropdowns are labelled via aria-labelledby, close on Escape,
 * and icon-only buttons carry a name.
 */

import { memo, useEffect, useId, useMemo, useRef, useState } from 'react';
import { AlertCircle, ChevronDown, Search, X } from 'lucide-react';
import { partLabel } from '../../lib/api';

// ─── Slider ──────────────────────────────────────────────────────────────────
// `good` says which direction is "better" so the value can be coloured:
//   'up'   (more is good: power), 'down' (less is good: weight), null (neutral)
export const SimSlider = memo(function SimSlider({
  label, hint, value, onChange, min, max, step = 1, unit = '', signed = false, good = null,
}) {
  const id = useId();
  const tone =
    good === 'up' ? (value > 0 ? 'text-signal-go' : value < 0 ? 'text-signal-foul' : 'text-white')
    : good === 'down' ? (value < 0 ? 'text-signal-go' : value > 0 ? 'text-signal-foul' : 'text-white')
    : 'text-white';
  const shown = `${signed && value > 0 ? '+' : ''}${value}${unit}`;
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="field-label !mb-0">{label}</label>
        <output htmlFor={id} className={`font-mono text-sm font-medium tabular-nums ${tone}`}>{shown}</output>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuetext={shown}
        className="mt-1 h-11 w-full cursor-pointer accent-accent"
      />
      {hint && <p className="field-hint !mt-0">{hint}</p>}
    </div>
  );
});

// ─── Searchable dropdown ─────────────────────────────────────────────────────
export const SimDropdown = memo(function SimDropdown({
  label, hint, items, selected, onSelect, getKey, renderItem, renderSelected, searchKey, groupKey,
  emptyMsg = 'No results', placeholder = 'Select…',
}) {
  const uid = useId();
  const labelId = `${uid}-label`;
  const btnId = `${uid}-btn`;
  const listId = `${uid}-list`;
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [hi, setHi] = useState(-1);
  const ref = useRef(null);
  const btnRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const h = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, [open]);

  const flat = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const filtered = needle ? items.filter((i) => searchKey(i).toLowerCase().includes(needle)) : items;
    if (!groupKey) return filtered.map((i) => ({ item: i }));
    const groups = {};
    for (const i of filtered) (groups[groupKey(i)] ||= []).push(i);
    const out = [];
    for (const g of Object.keys(groups).sort()) {
      out.push({ header: g });
      for (const i of groups[g]) out.push({ item: i });
    }
    return out;
  }, [items, q, searchKey, groupKey]);

  const options = useMemo(() => flat.filter((r) => r.item), [flat]);

  const close = (refocus) => {
    setOpen(false);
    setQ('');
    setHi(-1);
    if (refocus) btnRef.current?.focus();
  };
  const pick = (item) => { onSelect(item); close(true); };

  const onKey = (e) => {
    if (e.key === 'Escape') { e.preventDefault(); close(true); return; }
    if (!options.length) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setHi((i) => Math.min(options.length - 1, i + 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setHi((i) => Math.max(0, i - 1)); }
    else if (e.key === 'Enter' && hi >= 0) { e.preventDefault(); pick(options[hi].item); }
  };

  let optIdx = -1;
  return (
    <div className="relative" ref={ref}>
      <span id={labelId} className="field-label">{label}</span>
      <button
        ref={btnRef}
        id={btnId}
        type="button"
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => { if (e.key === 'Escape' && open) close(true); }}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={open ? listId : undefined}
        aria-labelledby={`${labelId} ${btnId}`}
        className="input-base flex items-center justify-between gap-2 text-left hover:border-white/25"
      >
        <span className="min-w-0 flex-1 truncate">
          {selected ? renderSelected(selected) : <span className="text-white/45">{placeholder}</span>}
        </span>
        <ChevronDown size={16} aria-hidden="true" className={`shrink-0 text-white/50 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {hint && <p className="field-hint">{hint}</p>}
      {open && (
        <div className="absolute z-50 mt-1.5 w-full overflow-hidden rounded-xl border border-white/[0.14] bg-asphalt-1 shadow-2xl">
          <div className="border-b border-white/10 p-2">
            <div className="relative">
              <Search size={14} aria-hidden="true" className="absolute left-3 top-1/2 -translate-y-1/2 text-white/45" />
              <input
                autoFocus
                type="text"
                role="combobox"
                aria-expanded="true"
                aria-controls={listId}
                aria-activedescendant={hi >= 0 ? `${uid}-opt-${hi}` : undefined}
                aria-label={`Search ${label.toLowerCase()}`}
                value={q}
                onChange={(e) => { setQ(e.target.value); setHi(-1); }}
                onKeyDown={onKey}
                placeholder="Search…"
                className="input-base h-11 pl-9"
              />
            </div>
          </div>
          <div id={listId} role="listbox" aria-labelledby={labelId} className="max-h-64 overflow-y-auto">
            {flat.map((row, idx) => {
              if (row.header) {
                return (
                  <div key={`h-${row.header}`} role="presentation" className="sticky top-0 bg-asphalt-1 px-3 py-1.5 text-xs font-semibold text-white/60">
                    {row.header}
                  </div>
                );
              }
              optIdx += 1;
              const my = optIdx;
              const key = getKey ? getKey(row.item) : idx;
              return (
                <button
                  key={key}
                  id={`${uid}-opt-${my}`}
                  type="button"
                  role="option"
                  aria-selected={selected === row.item || (getKey && selected && getKey(selected) === key)}
                  onClick={() => pick(row.item)}
                  onMouseEnter={() => setHi(my)}
                  className={`flex min-h-11 w-full items-center border-l-2 px-3 py-2 text-left text-sm text-white/85 hover:text-white ${
                    my === hi ? 'border-accent bg-white/[0.06]' : 'border-transparent hover:bg-white/[0.06]'
                  }`}
                >
                  {renderItem(row.item)}
                </button>
              );
            })}
            {options.length === 0 && <p className="px-3 py-4 text-sm text-white/55">{emptyMsg}</p>}
          </div>
        </div>
      )}
    </div>
  );
});

// ─── Error tile with Retry ───────────────────────────────────────────────────
export function ErrorTile({ message, onRetry, retryLabel = 'Try again', className = '' }) {
  return (
    <div role="alert" className={`flex items-center justify-between gap-3 rounded-xl border border-signal-foul/30 bg-signal-foul/[0.06] p-3 text-sm text-signal-foul ${className}`}>
      <span className="flex min-w-0 items-start gap-2">
        <AlertCircle size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
        <span className="break-words">{message}</span>
      </span>
      {onRetry && (
        <button type="button" onClick={onRetry} className="btn-ghost btn-sm shrink-0">{retryLabel}</button>
      )}
    </div>
  );
}

// ─── Selected part chip ──────────────────────────────────────────────────────
export const PartChip = memo(function PartChip({ part, onRemove }) {
  const name = partLabel(part.brand, part.model_name);
  return (
    <span className="inline-flex min-h-8 items-center gap-1.5 rounded-lg border border-white/[0.14] bg-white/[0.04] py-1 pl-2.5 pr-1 text-xs text-white/80">
      <span className="font-medium">{name}</span>
      {part.price_inr > 0 && <span className="text-white/55">₹{(part.price_inr / 1000).toFixed(1)}k</span>}
      <button
        type="button"
        onClick={() => onRemove(part.id)}
        aria-label={`Remove ${name}`}
        className="flex h-7 w-7 items-center justify-center rounded-md text-white/55 hover:bg-white/10 hover:text-white"
      >
        <X size={13} aria-hidden="true" />
      </button>
    </span>
  );
});

/** Tinted sub-panel used inside result tabs. */
export const PANEL = 'rounded-xl border border-white/10 bg-white/[0.03] p-4';
