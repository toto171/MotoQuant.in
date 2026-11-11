'use client';

import { memo, useMemo } from 'react';
import BikePicker from '../BikePicker';
import { popularChips } from '../../lib/popularBikes';

/**
 * BikeChooser — the shared bike picker + one-tap popular bikes + a one-line
 * fact summary. `data-exp` attributes keep the GROWTH_EXP_003 default-bike
 * A/B attribution working.
 */
const BikeChooser = memo(function BikeChooser({ bike, bikes, onSelect, variant }) {
  const chips = useMemo(
    () => popularChips(bikes).map(({ label, bike: match }) => ({ label, match })),
    [bikes],
  );

  return (
    <div data-exp="EXP-003" data-variant={variant}>
      <BikePicker value={bike} onSelect={onSelect} label="Your bike" />

      {chips.length > 0 && (
        <div className="mt-3">
          <p className="field-hint !mt-0 mb-1.5">Popular bikes</p>
          <div className="flex flex-wrap gap-2">
            {chips.map(({ label, match }) => {
              const active = bike?.id === match.id;
              return (
                <button
                  key={label}
                  type="button"
                  aria-pressed={active}
                  onClick={() => onSelect(match)}
                  className={`inline-flex min-h-11 items-center rounded-lg border px-3.5 text-sm font-medium transition-colors ${
                    active
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-white/15 text-white/75 hover:border-white/35 hover:text-white'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Always rendered, one line tall, so the line appearing when the
          default bike loads does not push the result card down (CLS). */}
      <p className="mt-3 min-h-[1.25rem] text-sm text-white/65">
        {bike
          ? [
              bike.category,
              bike.peak_power_hp ? `${Math.round(bike.peak_power_hp)} hp` : null,
              bike.dry_mass_kg ? `${Math.round(bike.dry_mass_kg)} kg` : null,
              bike.year ? String(bike.year) : null,
            ].filter(Boolean).join(' · ')
          : null}
      </p>
    </div>
  );
});

export default BikeChooser;
