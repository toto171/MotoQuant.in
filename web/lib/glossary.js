/**
 * Glossary — the single source of plain-English definitions (CLARITY v6).
 *
 * Powers <Term k="..."> tooltips and the /docs/glossary page.
 *   { key: { label, short, long } }
 *   - label: how the term reads in running text
 *   - short: one plain sentence, <= 140 chars, no jargon inside it
 *   - long : one or two extra sentences (what a typical / good value looks like)
 *
 * Order here is the order shown on /docs/glossary.
 */

export const GLOSSARY = {
  et: {
    label: 'Quarter-mile time',
    short: 'How long the bike takes to cover a quarter mile (402 metres) from a standing start. Also called "ET" or elapsed time.',
    long: 'Lower is quicker. A 150 cc commuter takes around 18 to 20 seconds, a 400 cc sport bike around 13 to 14 seconds, and a stock Hayabusa about 10 seconds.',
  },
  trap: {
    label: 'Finish-line speed',
    short: 'How fast the bike is going when it crosses the quarter-mile finish line. Racers call it "trap speed".',
    long: 'It mostly shows top-end power; your quarter-mile time also depends on the launch. A stock litre-class sport bike crosses the line at around 215 to 235 km/h.',
  },
  sixty: {
    label: 'First 60 ft (launch)',
    short: 'The time to cover the first 60 feet (about 18 metres). It shows how well the bike gets off the line.',
    long: 'Every extra 0.1 s lost here is roughly 0.07 to 0.1 s lost over the whole quarter mile. A strong launch on a sport bike is about 1.6 to 1.9 seconds.',
  },
  eighth: {
    label: 'Halfway (⅛ mile)',
    short: 'The time and speed at the halfway point of the run: one eighth of a mile (201 metres).',
    long: 'Many strips run eighth-mile races. The quarter-mile time is usually about 1.5 to 1.6 times the eighth-mile time.',
  },
  splits: {
    label: 'Splits',
    short: 'Elapsed times recorded at set distances along the run, such as 60 ft, ⅛ mile and the full quarter mile.',
    long: 'Comparing splits shows where a run was won or lost: a slow first split means a weak launch, a slow final split means a lack of top-end power.',
  },
  launch_rpm: {
    label: 'Launch RPM',
    short: 'The engine speed you hold while you let the clutch out at the start. Too low bogs the bike, too high spins the rear tyre.',
    long: 'The best value depends on the bike, the tyre and the surface. The race-day setup tool suggests one for your conditions.',
  },
  two_step: {
    label: 'Two-step (launch control)',
    short: 'A rev limiter that holds the engine at a fixed speed while you wait on the line, so every launch starts from the same RPM.',
    long: 'You hold the throttle fully open, the limiter keeps the revs steady, and you release the clutch.',
  },
  gearing: {
    label: 'Gearing (sprockets)',
    short: 'How far the bike moves for each turn of the engine, set by the front and rear sprockets and the gearbox.',
    long: 'Shorter gearing (a bigger rear sprocket or smaller front one) accelerates harder but runs out of speed sooner. Taller gearing does the opposite.',
  },
  sprockets: {
    label: 'Sprockets',
    short: 'The toothed wheels that the chain runs over: a small one on the engine and a big one on the rear wheel.',
    long: 'Changing the number of teeth on either one changes the gearing. One extra tooth on the rear sprocket makes the bike pull a little harder and top out a little lower.',
  },
  da: {
    label: 'Air and altitude',
    short: 'Hot, high or humid air is thinner, so the engine gets less oxygen and makes less power. This setting accounts for that.',
    long: 'Engineers call it density altitude. The same bike can be a few tenths of a second slower on a hot day or at a high-altitude strip than on a cool day at sea level.',
  },
  traction: {
    label: 'Traction',
    short: 'How much grip the rear tyre has on the road surface. When the engine asks for more than the grip allows, the tyre spins.',
    long: 'Prepped drag strips have far more grip than ordinary roads. A wet or dusty surface can cost a lot of time because power is wasted as wheelspin.',
  },
  wheelie: {
    label: 'Wheelie',
    short: 'When the front wheel lifts off the ground under hard acceleration. The bike loses time while the front is in the air.',
    long: 'Wheelie bars, a longer swingarm and a lower rider position all help keep the front wheel down so the bike can use its full power.',
  },
  cost_per_tenth: {
    label: 'Cost per tenth of a second',
    short: 'How many rupees you spend for each 0.1 second a part makes your bike quicker. Lower is better value.',
    long: 'It is the price of the part divided by the tenths of a second it gains. A cheap air filter with a small gain can beat an expensive part with a big one.',
  },
  instant_estimate: {
    label: 'Instant estimate',
    short: 'A very fast approximate answer calculated in your browser. It is close to the full simulation but not exact.',
    long: 'Use it for quick what-if checks as you change things. Run the full simulation when you want exact splits, charts and a result you can save.',
  },
  full_sim: {
    label: 'Full simulation',
    short: 'The complete, exact calculation that follows the bike millisecond by millisecond along the whole quarter mile.',
    long: 'It takes a moment longer than the instant estimate and gives you the exact splits and speed-over-time charts. Only full-simulation results can be saved.',
  },
  power_boost: {
    label: 'Engine power change',
    short: 'Make the engine stronger or weaker by a percentage. For example, +10% means 10% more power than stock.',
    long: 'Use it to try a tune, an exhaust or a bigger engine before you buy anything. Negative values model a worn or restricted engine.',
  },
  mass_delta: {
    label: 'Weight added or removed',
    short: 'Change the bike weight in kilograms. Use a negative number to remove weight, such as a lighter battery or exhaust.',
    long: 'A rule of thumb is that 10 kg lighter is worth roughly 0.1 to 0.15 seconds in the quarter mile, depending on the bike.',
  },
  cd_a: {
    label: 'Air resistance (Cd·A)',
    short: 'How much the bike and rider push against the air. It is the drag coefficient (Cd) multiplied by the frontal area (A).',
    long: 'It matters more the faster you go, because air resistance grows with the square of speed. A fairing and a tucked rider reduce it.',
  },
  redline: {
    label: 'Redline',
    short: 'The highest engine speed the bike is allowed to run, in revolutions per minute. The engine changes gear or hits the limiter here.',
    long: 'Most sport bikes shift up just before the redline in a drag race to stay where the engine makes the most power.',
  },
  slip: {
    label: 'Wheelspin (slip)',
    short: 'How much faster the rear tyre is spinning than the bike is moving. A little slip is normal and gives the best grip.',
    long: 'Too much slip burns power as smoke instead of pushing you forward. The simulator tracks it moment by moment.',
  },
  build_profile: {
    label: 'Build type',
    short: 'What kind of parts you are willing to use: street-legal only, drag-strip prep, full race, or anything goes.',
    long: 'Street-legal keeps the bike road-worthy. Drag-strip prep adds track-only parts. Full race and anything-goes allow engine modifications such as nitrous or a turbo.',
  },
  stage_tiers: {
    label: 'Stage 1 / 2 / 3 / 4',
    short: 'A common way to describe how far a bike is modified: a higher stage means bigger changes and a bigger bill.',
    long: 'Stage 1 is bolt-ons (exhaust, filter, tune). Stage 2 adds clutch and gearing work. Stage 3 and 4 go into serious engine work and are usually for track use only.',
  },
  outlaw: {
    label: 'Outlaw (no-limit) build',
    short: 'A build with no rules and no budget cap: every compatible part is on the table, aiming only for the quickest time.',
    long: 'It is the "what is the absolute best this bike can do?" answer. It is usually not street-legal and not cheap.',
  },
  dyno: {
    label: 'Dyno',
    short: 'A machine that measures how much power and twisting force an engine delivers at the rear wheel at each engine speed.',
    long: 'The printed result is a dyno chart. You can upload one to My data so the simulator uses your engine instead of a typical one.',
  },
  dragy: {
    label: 'Dragy',
    short: 'A small GPS device that sits on your bike and records your real quarter-mile times and speeds.',
    long: 'Upload a Dragy run to My data to compare what really happened with what the simulator predicted.',
  },
  top_speed: {
    label: 'Top speed',
    short: 'The fastest the bike can go when it keeps accelerating until the air resistance matches the power.',
    long: 'Some bikes are limited electronically, often to 299 km/h on the big sport bikes. The simulator can show it with or without the limiter.',
  },
};

/** Entries in display order, with the key attached. */
export const GLOSSARY_LIST = Object.entries(GLOSSARY).map(([key, v]) => ({ key, ...v }));

/** Lookup that never throws — unknown keys return null. */
export function getTerm(key) {
  return Object.prototype.hasOwnProperty.call(GLOSSARY, key) ? GLOSSARY[key] : null;
}
