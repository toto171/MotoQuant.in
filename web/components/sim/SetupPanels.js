'use client';

/**
 * Advanced "Setup" column: bike, the three tuning sliders, "Air and altitude"
 * and "Tyres". All memoised and fed stable callbacks from useSimulatorState.
 */

import { memo, useMemo } from 'react';
import { ChevronDown } from 'lucide-react';
import LocationPicker from '../LocationPicker';
import Term from '../Term';
import { DEFAULT_ALTITUDE_M } from '../ConditionsLine';
import BikeChooser from './BikeChooser';
import { ErrorTile, SimDropdown, SimSlider } from './controls';
import { tyreFitsWheel } from './format';

// Module-level render fns keep SimDropdown's memo effective.
const venueKey = (v) => v.id ?? 'default';
const venueSearch = (v) => `${v.name} ${v.country || ''}`;
const venueGroup = (v) => v.country || 'Default';
const venueItem = (v) => (
  <span className="flex w-full items-center justify-between gap-3">
    <span>{v.name}</span>
    {v.altitude_m != null && <span className="text-xs text-white/55">{Math.round(v.altitude_m)} m</span>}
  </span>
);
const venueSelected = (v) => <span>{v.name}</span>;
const NO_VENUE = { id: null, name: 'Default conditions (no venue)', country: 'Default', altitude_m: DEFAULT_ALTITUDE_M };

const tireKey = (t) => t.id ?? 'stock';
const tireSearch = (t) => `${t.manufacturer} ${t.model} ${t.size_designation || ''} ${t.compound_type || ''}`;
const tireGroup = (t) => t.manufacturer || 'Stock';
// Size is part of the label: several tyres ship under one model name in
// multiple sizes and would otherwise read as duplicate entries.
const tireItem = (t) => (
  <span className="flex w-full items-center justify-between gap-3">
    <span>
      {t.model}
      {t.size_designation ? <span className="text-white/55"> · {t.size_designation}</span> : null}
    </span>
    <span className="shrink-0 text-xs text-white/55">{t.compound_type || ''}</span>
  </span>
);
const tireSelected = (t) => (
  <span>{t.id == null ? 'Original tyre (stock)' : `${t.manufacturer} ${t.model}${t.size_designation ? ` · ${t.size_designation}` : ''}`}</span>
);
const STOCK_TIRE = { id: null, manufacturer: 'Stock', model: 'Original tyre' };

export const EnvironmentPanel = memo(function EnvironmentPanel({
  open, onToggle, location, venue, venues, onResolved, onCleared, onPickVenue,
  ambientTemp, trackTemp, humidity, headwind, setAmbientTemp, setTrackTemp, setHumidity, setHeadwind,
}) {
  const venueItems = useMemo(() => [NO_VENUE, ...venues], [venues]);
  return (
    <section id="sim-env" className="card card-pad" aria-label="Air and altitude">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex min-h-11 w-full items-center justify-between gap-3 text-left"
      >
        <span className="font-display text-lg font-semibold text-white">
          <Term k="da">Air and altitude</Term>
        </span>
        <ChevronDown size={18} aria-hidden="true" className={`text-white/55 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {!open && (
        <p className="text-sm text-white/60">
          {venue ? `${venue.name}${venue.altitude_m != null ? ` · ${Math.round(venue.altitude_m)} m` : ''}` : `Default conditions · ${DEFAULT_ALTITUDE_M} m`} · {ambientTemp} °C
        </p>
      )}
      {open && (
        <div className="mt-4 space-y-5">
          <div>
            <p className="field-label">Where are you racing?</p>
            <LocationPicker value={location} onResolved={onResolved} onCleared={onCleared} compact />
          </div>
          {venues.length > 0 && (
            <SimDropdown
              label="Or choose a venue from the full list"
              items={venueItems}
              selected={venue || NO_VENUE}
              onSelect={onPickVenue}
              getKey={venueKey}
              searchKey={venueSearch}
              groupKey={venueGroup}
              renderItem={venueItem}
              renderSelected={venueSelected}
            />
          )}
          <SimSlider label="Air temperature" value={ambientTemp} onChange={setAmbientTemp} min={-30} max={60} unit=" °C" />
          <SimSlider label="Track temperature" value={trackTemp} onChange={setTrackTemp} min={10} max={65} unit=" °C" />
          <SimSlider label="Humidity" value={humidity} onChange={setHumidity} min={0} max={100} unit=" %" />
          <SimSlider
            label="Headwind"
            hint="Use a negative number for a tailwind."
            value={headwind}
            onChange={setHeadwind}
            min={-30}
            max={30}
            unit=" km/h"
            signed
          />
        </div>
      )}
    </section>
  );
});

export const TyresPanel = memo(function TyresPanel({
  status, tires, frontTire, rearTire, setFrontTire, setRearTire, onRetry,
}) {
  // Each picker lists only tyres made for that wheel (or for either wheel);
  // the server refuses a front tyre at the rear and the reverse.
  const frontItems = useMemo(
    () => [STOCK_TIRE, ...tires.filter((t) => tyreFitsWheel(t, 'front'))],
    [tires],
  );
  const rearItems = useMemo(
    () => [STOCK_TIRE, ...tires.filter((t) => tyreFitsWheel(t, 'rear'))],
    [tires],
  );
  return (
    <section className="card card-pad" aria-label="Tyres">
      <h2 className="mb-4 font-display text-lg font-semibold text-white">Tyres</h2>
      {status === 'error' ? (
        <ErrorTile message="We could not load the tyre list." onRetry={onRetry} />
      ) : status !== 'ready' ? (
        <div aria-busy="true" aria-label="Loading tyres" className="space-y-4">
          <div className="skeleton h-12 w-full" />
          <div className="skeleton h-12 w-full" />
        </div>
      ) : (
        <div className="space-y-4">
          <SimDropdown
            label="Front tyre"
            items={frontItems}
            selected={frontTire || STOCK_TIRE}
            onSelect={setFrontTire}
            getKey={tireKey}
            searchKey={tireSearch}
            groupKey={tireGroup}
            renderItem={tireItem}
            renderSelected={tireSelected}
          />
          <SimDropdown
            label="Rear tyre"
            hint="The rear tyre sets how hard the bike can launch."
            items={rearItems}
            selected={rearTire || STOCK_TIRE}
            onSelect={setRearTire}
            getKey={tireKey}
            searchKey={tireSearch}
            groupKey={tireGroup}
            renderItem={tireItem}
            renderSelected={tireSelected}
          />
        </div>
      )}
    </section>
  );
});

export const TuningPanel = memo(function TuningPanel({
  bike, bikes, variant, onSelectBike, riderKg, setRiderKg, powerBoost, setPowerBoost, massChange, setMassChange,
}) {
  return (
    <section className="card card-pad" aria-label="Bike and tuning">
      <h2 className="mb-4 font-display text-lg font-semibold text-white">Your bike</h2>
      <BikeChooser bike={bike} bikes={bikes} onSelect={onSelectBike} variant={variant} />
      <div className="mt-6 space-y-5">
        <SimSlider label="Rider weight" hint="With helmet, jacket and boots." value={riderKg} onChange={setRiderKg} min={50} max={130} unit=" kg" />
        <SimSlider
          label="Engine power change"
          value={powerBoost}
          onChange={setPowerBoost}
          min={-20}
          max={50}
          unit=" %"
          signed
          good="up"
          hint="Extra power or lost power compared with stock."
        />
        <SimSlider
          label="Weight added or removed"
          value={massChange}
          onChange={setMassChange}
          min={-30}
          max={30}
          unit=" kg"
          signed
          good="down"
          hint="Negative means you made the bike lighter."
        />
      </div>
    </section>
  );
});
