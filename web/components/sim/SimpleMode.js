'use client';

import { BarChart3, Layers, Settings2, Share2, Wrench, Zap } from 'lucide-react';
import LocationPicker from '../LocationPicker';
import NextSteps from '../NextSteps';
import BikeChooser from './BikeChooser';
import ResultCard from './ResultCard';
import { SimSlider } from './controls';
import AskPanel from './AskPanel';

/**
 * SimpleMode — two steps and an answer. Stacked on phones with the result
 * directly under the bike picker; two columns from lg with a sticky result.
 */
export default function SimpleMode({ sim }) {
  const {
    bike, bikes, changeBike, defaultBikeVariant, riderKg, setRiderKg, location, applyLocation,
    resetEnv, goAdvanced, saveAndShare, headline, saveTask, fullSimTask, shareBuild, shareCopied,
  } = sim;

  const bikeId = bike?.id;
  const busy = saveTask.active || fullSimTask.active;
  const steps = [
    {
      icon: Wrench,
      title: 'Add parts and mods',
      hint: 'Pick an exhaust, tyres or tuning and see the new time',
      onClick: () => goAdvanced('quarter', 'parts'),
    },
    bikeId && {
      icon: Zap,
      title: 'Find the best parts for my budget',
      hint: 'We test every compatible part for you',
      href: `/optimize?bike_id=${bikeId}`,
    },
    bikeId && {
      icon: Settings2,
      title: 'Get a race-day setup',
      hint: 'Gearing, launch RPM and tyre pressure for today’s air',
      href: `/autotune?bike_id=${bikeId}`,
    },
    {
      icon: Layers,
      title: 'Compare with another bike',
      hint: 'Put two bikes side by side',
      onClick: () => goAdvanced('compare'),
    },
    {
      icon: BarChart3,
      title: 'See charts and splits',
      hint: 'Runs the full simulation',
      onClick: () => { goAdvanced('charts'); sim.startFullSim(); },
    },
    headline && {
      icon: Share2,
      title: shareCopied ? 'Link copied' : 'Save and share this run',
      hint: 'Saves an exact result and copies a link to your timeslip',
      onClick: busy ? undefined : saveAndShare,
      disabled: busy,
    },
  ].filter(Boolean);

  // Phones: one column in answer-first order — bike, result, then the rest.
  // From lg: the two step cards are a plain vertical stack on the left (no
  // grid rows, so their heights never follow the result card) and the result
  // is a sticky right column. `contents` lets the left column's children take
  // part in the phone ordering.
  return (
    <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 lg:items-start">
      <div className="contents lg:flex lg:min-w-0 lg:flex-col lg:gap-5">
        {/* Step 1 */}
        <section className="card card-pad order-1 min-w-0" aria-labelledby="sim-step-1">
          <h2 id="sim-step-1" className="mb-4 flex items-center gap-2.5 font-display text-xl font-semibold text-white">
            <span className="step-badge" aria-hidden="true">1</span> Choose your bike
          </h2>
          <BikeChooser bike={bike} bikes={bikes} onSelect={changeBike} variant={defaultBikeVariant} />
        </section>

        {/* Step 2 */}
        <section className="card card-pad order-3 min-w-0" aria-labelledby="sim-step-2">
          <h2 id="sim-step-2" className="mb-4 flex items-center gap-2.5 font-display text-xl font-semibold text-white">
            <span className="step-badge" aria-hidden="true">2</span> You and the conditions
          </h2>
          <div className="space-y-6">
            <SimSlider
              label="Rider weight with gear"
              value={riderKg}
              onChange={setRiderKg}
              min={50}
              max={130}
              unit=" kg"
              hint="Include your helmet, jacket and boots."
            />
            <div id="sim-location">
              <p className="field-label">Where are you racing? (optional)</p>
              <LocationPicker value={location} onResolved={applyLocation} onCleared={resetEnv} compact />
              <p className="field-hint">Adjusts for altitude and weather. Leave blank to use the default conditions.</p>
            </div>
          </div>
        </section>
      </div>

      {/* Result — directly under the picker on phones, sticky on the right from lg */}
      <div className="order-2 min-w-0 space-y-5 lg:sticky lg:top-24">
        <ResultCard sim={sim} />
        <div className="card card-pad">
          <NextSteps items={steps} />
        </div>
      </div>

      {/* Phones only: the plain-English chat sits below the answer (on desktop it is under the page header) */}
      <div className="order-4 min-w-0 lg:hidden">
        <AskPanel />
      </div>
    </div>
  );
}
