'use client';

/**
 * AdvancedWorkbench — the full workbench: Setup | Parts and mods | Results.
 * On phones the order is Setup, Results, Parts so the answer stays near the
 * controls; from lg it is three columns.
 */

import { useId } from 'react';
import { Check, RotateCcw, Share2 } from 'lucide-react';
import SimProgress from '../SimProgress';
import ResultCard from './ResultCard';
import PartsCatalog from './PartsCatalog';
import { EnvironmentPanel, TuningPanel, TyresPanel } from './SetupPanels';
import TopSpeedTab from './TopSpeedTab';
import { ChartsTab, SplitsTab } from './ChartsSplitsTabs';
import CompareTab from './CompareTab';
import MyDataTab from './MyDataTab';
import SpecsTab from './SpecsTab';

const TABS = [
  ['quarter', 'Quarter mile'],
  ['topspeed', 'Top speed'],
  ['charts', 'Charts'],
  ['splits', 'Splits'],
  ['compare', 'Compare'],
  ['data', 'My data'],
  ['specs', 'Specs'],
];

export default function AdvancedWorkbench({ sim }) {
  const uid = useId();
  const {
    bike, bikes, defaultBikeVariant, changeBike, riderKg, setRiderKg, powerBoost, setPowerBoost,
    massChange, setMassChange, showEnv, setShowEnv, location, venue, venues, applyLocation, resetEnv,
    pickVenue, ambientTemp, trackTemp, humidity, headwind, setAmbientTemp, setTrackTemp, setHumidity,
    setHeadwind, tiresStatus, allTires, frontTire, rearTire, setFrontTire, setRearTire, retryAdvanced,
    categories, allParts, partsStatus, partsError, partsBikeId, selectedParts, buildCost,
    categoryNameById, togglePart, removePart, retryParts, focusRequest, clearFocusRequest,
    activeTab, setActiveTab, liveSim, setLiveSim, activeOp, shareBuild, shareCopied, resetAll,
  } = sim;

  const toggleEnv = () => setShowEnv(!showEnv);

  return (
    <div>
      {/* Toolbar */}
      <div className="mb-5 flex flex-wrap items-center gap-x-5 gap-y-3 rounded-2xl border border-white/10 bg-asphalt-2 px-4 py-3">
        <label className="flex min-h-11 cursor-pointer items-center gap-2.5 text-sm text-white/85">
          <input
            type="checkbox"
            checked={liveSim}
            onChange={(e) => setLiveSim(e.target.checked)}
            className="h-5 w-5 accent-accent"
          />
          Update as I change things
        </label>
        {activeOp && (
          <SimProgress active compact progress={activeOp.task.progress} label={activeOp.label} onStop={activeOp.task.stop} />
        )}
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <button type="button" onClick={shareBuild} disabled={!bike} className="btn-ghost btn-sm">
            {shareCopied ? <Check size={14} aria-hidden="true" className="text-signal-go" /> : <Share2 size={14} aria-hidden="true" />}
            {shareCopied ? 'Link copied' : 'Share this setup'}
          </button>
          <button type="button" onClick={resetAll} className="btn-ghost btn-sm">
            <RotateCcw size={14} aria-hidden="true" /> Reset
          </button>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-12 lg:items-start">
        {/* Setup */}
        <div className="order-1 space-y-5 lg:col-span-3">
          <h2 className="sr-only">Setup</h2>
          <TuningPanel
            bike={bike}
            bikes={bikes}
            variant={defaultBikeVariant}
            onSelectBike={changeBike}
            riderKg={riderKg}
            setRiderKg={setRiderKg}
            powerBoost={powerBoost}
            setPowerBoost={setPowerBoost}
            massChange={massChange}
            setMassChange={setMassChange}
          />
          <EnvironmentPanel
            open={showEnv}
            onToggle={toggleEnv}
            location={location}
            venue={venue}
            venues={venues}
            onResolved={applyLocation}
            onCleared={resetEnv}
            onPickVenue={pickVenue}
            ambientTemp={ambientTemp}
            trackTemp={trackTemp}
            humidity={humidity}
            headwind={headwind}
            setAmbientTemp={setAmbientTemp}
            setTrackTemp={setTrackTemp}
            setHumidity={setHumidity}
            setHeadwind={setHeadwind}
          />
          <TyresPanel
            status={tiresStatus === 'idle' ? 'loading' : tiresStatus}
            tires={allTires}
            frontTire={frontTire}
            rearTire={rearTire}
            setFrontTire={setFrontTire}
            setRearTire={setRearTire}
            onRetry={retryAdvanced}
          />
        </div>

        {/* Parts */}
        <div className="order-3 lg:order-2 lg:col-span-4">
          <PartsCatalog
            bikeId={bike?.id ?? null}
            categories={categories}
            allParts={allParts}
            partsStatus={partsStatus}
            partsError={partsError}
            partsBikeId={partsBikeId}
            selectedParts={selectedParts}
            buildCost={buildCost}
            categoryNameById={categoryNameById}
            onToggle={togglePart}
            onRemove={removePart}
            onRetry={retryParts}
            focusRequest={focusRequest}
            onFocusDone={clearFocusRequest}
          />
        </div>

        {/* Results */}
        <div className="order-2 space-y-4 lg:order-3 lg:col-span-5">
          <h2 className="sr-only">Results</h2>
          <div
            role="tablist"
            aria-label="Result views"
            className="flex flex-wrap gap-1.5"
          >
            {TABS.map(([id, label]) => (
              <button
                key={id}
                id={`${uid}-tab-${id}`}
                type="button"
                role="tab"
                aria-selected={activeTab === id}
                aria-controls={`${uid}-panel`}
                onClick={() => setActiveTab(id)}
                className={`inline-flex min-h-11 shrink-0 items-center rounded-xl border px-4 text-sm font-semibold transition-colors ${
                  activeTab === id
                    ? 'border-accent bg-accent/10 text-accent'
                    : 'border-white/12 text-white/70 hover:border-white/30 hover:text-white'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div id={`${uid}-panel`} role="tabpanel" aria-labelledby={`${uid}-tab-${activeTab}`}>
            {activeTab === 'quarter' && <ResultCard sim={sim} advanced />}
            {activeTab !== 'quarter' && (
              <div className="card card-pad">
                {activeTab === 'topspeed' && <TopSpeedTab sim={sim} />}
                {activeTab === 'charts' && <ChartsTab sim={sim} />}
                {activeTab === 'splits' && <SplitsTab sim={sim} />}
                {activeTab === 'compare' && <CompareTab sim={sim} />}
                {activeTab === 'data' && <MyDataTab sim={sim} />}
                {activeTab === 'specs' && <SpecsTab sim={sim} />}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
