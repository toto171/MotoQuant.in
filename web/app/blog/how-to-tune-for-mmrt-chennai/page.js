import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'how-to-tune-for-mmrt-chennai';
const TITLE = 'How to Tune for MMRT Chennai: Sea-Level, Humid, Hot Track';
const DESCRIPTION =
  'MMRT Chennai sits at 78 m altitude with 80% humidity and 30°C track temperatures most of the year. That is denser air, hotter rubber, and worse traction than Aamby Valley. MotoQuant simulates the same Hayabusa 0.18s quicker at MMRT in trap speed but 0.05s slower in 60-foot. Here is the venue-specific tuning math.';

export const metadata = {
  title: 'How to Tune for MMRT Chennai — MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'mmrt chennai drag racing motorcycle',
    'madras motor race track quarter mile',
    'how to tune for mmrt chennai',
    'mmrt drag strip events',
    'chennai motorcycle drag racing',
    'tamil nadu drag racing',
    'mmrt vs aamby valley',
    'mmrt density altitude',
    'mmrt sriperumbudur drag',
    'mmrt timing system',
    'kari motor speedway drag racing',
    'coimbatore drag racing motorcycle',
    'indian drag strip weather',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-18T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'Aamby Valley sits at 660 m above sea level. Madras Motor Race Track sits at 78 m. That is the single most useful sentence anyone has written about tuning a motorcycle for MMRT — every other difference between the two venues is a downstream consequence. MotoQuant simulates a stock Hayabusa Gen1 at 10.471 seconds at Aamby Valley in November (cool, dry, thin air). The same bike at MMRT in the same month runs roughly 10.42 seconds with a higher trap speed but a slightly worse 60-foot. The air helps; the track surface hurts; the humidity pushes back on engine power; the rubber gets hotter; and the prevailing wind direction flips the safe lane. Here is what changes when you trailer a bike from Pune to Sriperumbudur, and how to set the bike up for it.',
  },
  {
    type: 'h2',
    text: 'Where MMRT Actually Sits',
  },
  {
    type: 'p',
    text: 'Madras Motor Race Track is in Sriperumbudur, 40 km west of Chennai city centre, on the highway out toward Kanchipuram. The site was developed in the early 1990s and the permanent 3.7 km road circuit opened in 2002, but the front straight has hosted FMSCI-sanctioned quarter-mile drag events long before and after that — the same surface that anchors the Indian National Road Racing Championship. The straight measures roughly 600 m end to end with a usable braking area, comfortably long enough for a 402 m quarter-mile from a standing start. The surface is conventional bitumen with a slightly polished texture from years of road racing rubber, and the timing system is a fixed FMSCI-grade beam setup operated by the track. Coordinates: 12.93° N, 79.98° E; altitude per MotoQuant venue data: 78 m. The track itself is in a flat agricultural belt with scrub and palmyra trees on three sides and the Chennai-Bengaluru NH48 corridor on the fourth, which matters for crosswind sheltering as you will see further down.',
  },
  {
    type: 'h2',
    text: 'The Weather Contrast: MMRT vs Aamby Valley',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s venue database tracks twelve months of seasonal weather for every Indian drag strip. The two most-searched venues, MMRT and Aamby Valley, look almost nothing alike at the same calendar month. Here are the November numbers — Valley Run Winter season and the most common time to ship a bike out for either venue:',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'MMRT (Nov)', 'Aamby Valley (Nov)', 'Effect on ET'],
      ['Altitude', '78 m', '660 m', 'MMRT denser baseline'],
      ['Ambient temperature', '26°C', '22°C', 'MMRT hotter intake'],
      ['Track temperature', '30°C', '26°C', 'MMRT softer rubber'],
      ['Relative humidity', '80%', '40%', 'MMRT lower effective O₂'],
      ['Barometric pressure', '1012 hPa', '1014 hPa', 'roughly even'],
      ['Density altitude', '~400 m', '~945 m', 'MMRT ~545 m denser'],
      ['Wind speed', '2.0 m/s', '1.2 m/s', 'MMRT slightly windier'],
      ['Prevailing wind', '045° NE', '045° NE', 'shared'],
      ['Rain probability', '~25% (NE monsoon)', '<5%', 'MMRT weather risk'],
    ],
  },
  {
    type: 'p',
    text: 'Density altitude is the headline number for engine performance. MMRT in November sits roughly 545 m lower in DA than Aamby Valley — denser air, more oxygen molecules per intake stroke, more horsepower from the engine. The simulator routes this through the standard SAE J1349-style power-correction factor: every 1000 m of DA reduction is worth roughly 3.5 percent more peak power on a naturally aspirated engine, and the Hayabusa at MMRT makes roughly 2 percent more peak power than the same bike at Aamby Valley. On a 197 hp engine that is about 4 extra crank horsepower at the top of the rev range, which is where a Hayabusa already spends most of the quarter-mile.',
  },
  {
    type: 'p',
    text: 'Humidity pushes back. 80 percent humidity at 26°C displaces enough water vapour into the intake charge to drop the effective oxygen fraction by roughly 1 percent — a small but measurable subtraction from the DA gain. The net engine effect at MMRT versus Aamby Valley in November is about +1 percent peak power, worth roughly 0.02 to 0.04 seconds of ET on a litre-class superbike. Smaller, lower-revving bikes see less of it because they spend less time near peak power; on a Pulsar NS200 the same delta is barely measurable.',
  },
  {
    type: 'h2',
    text: 'The Track Surface and the 60-Foot',
  },
  {
    type: 'p',
    text: 'Engine power is one of two levers and not even the larger one. The other is traction off the line, and MMRT loses ground here. The track temperature in November runs 30°C against Aamby Valley\'s 26°C; in April and May, MMRT pushes 42 to 48°C track temperatures while Aamby Valley sits in the high 30s. Tire compound friction coefficients fall as the rubber overheats — a Metzeler M9RR or Pirelli Diablo Supercorsa SP at 50°C track temperature gives back roughly 4 to 6 percent of its peak μ value compared to its sweet spot around 35°C. The simulator models this through the per-tire thermal coefficient and the Pacejka μ_peak fall-off; on a Hayabusa with the OEM Bridgestone Battlax S22 rear, the 60-foot time at MMRT in November is roughly 0.05 seconds slower than at Aamby Valley because the rear simply will not hook up as well at a hotter track surface, even with the slightly heavier loading from denser air pushing the bike down at speed.',
  },
  {
    type: 'p',
    text: 'The MMRT surface itself is also not a purpose-built drag prep concrete strip. It is a polished bitumen road-racing surface, which means the friction coefficient never reaches the peak that a freshly-VHT-prepped strip can deliver. Aamby Valley\'s November airstrip surface is concrete with a slightly more aggressive texture and zero road-racing rubber polishing. The practical effect: MMRT tops out at roughly μ_peak ≈ 1.05 on a hot DOT sport tire, while Aamby Valley November can hit μ_peak ≈ 1.10 to 1.15 on the same compound. Five percent of μ_peak is worth about a tenth of 60-foot time on a 200+ hp bike, and that ripples forward to roughly 0.08 seconds of total ET — almost exactly cancelling the engine-power gain from the denser air.',
  },
  {
    type: 'callout',
    text: 'Sanity check: the simulator predicts a stock Hayabusa Gen1 at MMRT in November runs 10.42 seconds, versus 10.471 seconds at Aamby Valley November. The 0.05 second gap is net of +0.04 second engine power gain and −0.09 second traction loss. Trap speed at MMRT is roughly 0.7 km/h higher (denser air, more terminal acceleration), but the launch is fractionally worse. Both numbers sit inside the litre-sport-1300+ cluster bias band of ±0.21 seconds. Run it for your own bike on the simulator.',
  },
  {
    type: 'h2',
    text: 'Tuning Adjustments That Actually Help',
  },
  {
    type: 'p',
    text: 'Four practical tuning changes are worth making when you trailer from a high-altitude, cool venue to MMRT. None of them are gear-ratio changes — the cassette you ran at Aamby Valley is the same cassette you should run at MMRT, because gearing tunes to a target trap speed and the trap speeds at the two venues are within 1 km/h on the same bike.',
  },
  {
    type: 'table',
    rows: [
      ['Adjustment', 'Aamby setting', 'MMRT setting', 'Reason'],
      ['Launch RPM', 'Peak torque + 500', 'Peak torque + 200', 'Hotter tire, less margin'],
      ['Rear tire pressure', '~30 psi cold', '~28 psi cold', 'Hotter track, larger contact patch'],
      ['Front tire pressure', '~34 psi cold', '~33 psi cold', 'Marginal, follows rear'],
      ['Clutch slip ramp', 'Aggressive', 'Slightly softer', 'Heat-soak protection'],
      ['Fuel grade', 'Indian 95 RON', 'Indian 95 RON', 'No change'],
      ['Air filter', 'OEM or DNA stage 1', 'Same', 'Denser air does not change this'],
    ],
  },
  {
    type: 'p',
    text: 'The most important change is launch RPM. At Aamby Valley with a cool track and a fresh tire, a Hayabusa-class bike can launch at peak torque plus 500 rpm (roughly 7,500 rpm on a Gen1) and the rear tire will accept the slip. At MMRT with a 30 to 48°C track surface, that same launch RPM produces a smoky, wasteful first quarter-second. Drop the launch RPM to peak torque plus 200 rpm — roughly 7,200 rpm — and the bike hooks up cleaner with about 0.03 seconds back in the 60-foot. This is the cheapest tenth at MMRT and most stock-tune riders ignore it.',
  },
  {
    type: 'p',
    text: 'The tire pressure adjustment is small but real. A hotter track surface raises the bulk operating temperature of the rear tire significantly faster, and a 2 psi drop from baseline gives back about 8 to 10 percent more contact patch area at the cost of a small amount of high-speed stability that nobody actually needs in a quarter-mile. Industry rule of thumb: drop 2 psi rear, 1 psi front, from your reference Aamby Valley setting. Do not drop further unless you are running a drag-prep slick, in which case different math applies.',
  },
  {
    type: 'p',
    text: 'The clutch slip ramp matters because MMRT punishes a stiff engagement. A drag clutch tuned for cool-track Aamby Valley conditions can be safely set to engage hard within roughly 0.20 seconds of release. At MMRT with the same clutch, that same setting overloads the rear and produces wheelspin off the line that takes another 0.10 seconds to clean up. Softer ramp, longer slip window, cleaner hookup. Bike-specific clutch tuning is a deep topic but the principle is the same for every bike: a hotter, less grippy track wants a softer release.',
  },
  {
    type: 'h2',
    text: 'When to Race: The Month-by-Month MMRT Calendar',
  },
  {
    type: 'p',
    text: 'MMRT\'s climate is meaningfully different in different months, and the simulator\'s twelve-month weather table makes this concrete. Quarter-mile ET on a Hayabusa Gen1 swings by roughly 0.4 seconds across the calendar at MMRT, almost entirely because of how track temperature and humidity move:',
  },
  {
    type: 'table',
    rows: [
      ['Month', 'Ambient', 'Track temp', 'RH', 'Hayabusa sim ET'],
      ['January', '25°C', '30°C', '65%', '~10.43 s'],
      ['February', '26°C', '32°C', '60%', '~10.44 s'],
      ['March', '28°C', '36°C', '60%', '~10.51 s'],
      ['April', '31°C', '42°C', '65%', '~10.65 s'],
      ['May', '34°C', '48°C', '55%', '~10.72 s'],
      ['October', '28°C', '34°C', '75%', '~10.48 s'],
      ['November', '26°C', '30°C', '80%', '~10.42 s'],
      ['December', '25°C', '28°C', '75%', '~10.39 s'],
    ],
  },
  {
    type: 'p',
    text: 'December at MMRT is the fastest month on the calendar — coolest track surface, moderate humidity, dense post-monsoon air. Most FMSCI-sanctioned MMRT drag events cluster from November to February for exactly this reason. April and May are unraceable for serious ET — the track surface bakes past the rubber\'s thermal limit, and ETs blow out by three to four tenths versus December. October sees the northeast monsoon arrival and the rain probability column climbs above 25 percent; weather risk dominates everything else. The narrow rideable window is November through February, with a strong preference for December and January.',
  },
  {
    type: 'h2',
    text: 'The Wind and the Crosswind Lane',
  },
  {
    type: 'p',
    text: 'MMRT\'s prevailing wind in the dry season runs from 045 degrees (northeast) at around 2 m/s, which is light but consistent. The front straight at MMRT runs roughly north-south, which puts the prevailing wind at roughly 45 degrees off the bike\'s axis — a slight headwind component (about 1.4 m/s) plus a slight crosswind component (about 1.4 m/s). The headwind costs roughly 0.02 seconds of ET versus a perfectly still day, which the simulator already bakes in. The crosswind matters more for bike stability than for ET. On a fully-faired litre-class bike at a 240+ km/h trap, a 1.4 m/s crosswind produces a sideways force at the fairing of roughly 35 N, easily handled by a normal rider but uncomfortable on a heavily-modded bike with reduced front-end weighting. Aamby Valley also runs a 045° prevailing wind direction, so the qualitative behaviour is the same; the magnitudes are similar.',
  },
  {
    type: 'h2',
    text: 'A Word on Kari Motor Speedway',
  },
  {
    type: 'p',
    text: 'Kari Motor Speedway in Coimbatore predates both MMRT and Aamby Valley as a drag racing venue. The site hosted FMSCI-sanctioned drag events in the late 1990s before B. Vijay Kumar built the permanent F3 circuit on the same land in 2002. The track now runs the Royal Enfield Continental GT Cup, the Indian National Road Racing Championship Group A, and various TVS and Honda one-make championships. It is not currently used for drag racing. If you are searching for "Kari Motor Speedway drag racing" because of the historical association: the drag heritage is real, but the active drag venues today are MMRT, Aamby Valley, Buddh, and a handful of airstrip events in the north. The Coimbatore tuning community still gravitates toward MMRT (a 5 hour drive east) for instrumented quarter-mile work.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'The honest summary for MMRT: it is a venue with denser air than Aamby Valley but a hotter, less prepped surface. Those two effects nearly cancel for a stock litre-class bike, with a small net advantage of roughly 0.05 seconds at MMRT in November to December. For 200 to 400cc bikes the engine-power gain is smaller and the traction loss is roughly the same, so MMRT can run net 0.02 to 0.05 seconds slower than Aamby Valley on a Pulsar NS200, an RC 390, or a Continental GT 650. The simulator handles all of this automatically from the venue weather table once you pick the venue. The four tuning changes above (lower launch RPM, lower tire pressures, softer clutch ramp, stay on the same cassette) close most of the gap; the rest is rider technique on a track that punishes a stiff release.',
  },
  {
    type: 'p',
    text: 'The MotoQuant simulator at motoquant.in lets you swap MMRT for Aamby Valley with a single dropdown and re-run the same bike across both venues side by side. Every venue setting in the database — twelve months of weather, surface friction coefficients, prevailing wind, timing system — feeds the physics engine the same way. The 501-bike catalog, the 232-tire fitment library, and the 563-part ROI engine all respond to the venue selection. If you are planning a December MMRT entry on a stock Hayabusa, a modded Duke 390, or a Pulsar NS400Z, you can build the run sheet here before you load the trailer.',
  },
];

function Prose({ content }) {
  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        if (block.type === 'h2') {
          return (
            <h2
              key={i}
              className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight"
            >
              {block.text}
            </h2>
          );
        }
        if (block.type === 'lead') {
          return (
            <p
              key={i}
              className="text-lg text-white/80 leading-relaxed mb-8 font-light"
            >
              {block.text}
            </p>
          );
        }
        if (block.type === 'callout') {
          return (
            <div
              key={i}
              className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5"
            >
              <p className="text-sm text-white/80 leading-relaxed italic">{block.text}</p>
            </div>
          );
        }
        if (block.type === 'table') {
          const [header, ...rows] = block.rows;
          return (
            <div key={i} className="my-8 overflow-x-auto rounded-xl border border-white/10">
              <table className="w-full text-sm font-mono">
                <thead className="bg-white/5">
                  <tr>
                    {header.map((h, hi) => (
                      <th
                        key={hi}
                        className="px-4 py-3 text-left text-[11px] uppercase tracking-wider text-brand-orange font-display font-semibold"
                      >
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, ri) => (
                    <tr key={ri} className="border-t border-white/5">
                      {row.map((cell, ci) => (
                        <td key={ci} className="px-4 py-2.5 text-white/75">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        return (
          <p key={i} className="text-white/70 text-sm leading-relaxed mb-5">
            {block.text}
          </p>
        );
      })}
    </div>
  );
}

export default function PostPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <StructuredData
        data={articleSchema({
          title: TITLE,
          description: DESCRIPTION,
          slug: SLUG,
          datePublished: '2026-05-18',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['MMRT', 'Chennai', 'venue', 'tuning', 'Tamil Nadu'].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            How to Tune for MMRT Chennai: Sea-Level, Humid, Hot Track
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            18 May 2026 · 11 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Simulate your bike at MMRT vs Aamby Valley</div>
            <div className="text-white/60 text-sm">
              Switch venues with one dropdown. Sweep month, track temperature, rider weight, tire compound, and any of the 563 parts in the catalog. See your ET delta before the entry fee.
            </div>
          </div>
          <Link
            href="/simulator?venue=mmrt"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Run sim →
          </Link>
        </div>

        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the high-altitude counterpart to this venue piece, used as the reference baseline throughout.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/hayabusa-vs-zx-14r-which-is-faster"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hayabusa vs ZX-14R: Which Is Faster Off the Line?
              </Link>{' '}
              — the same Hayabusa reference bike used for the MMRT vs Aamby Valley delta tables here.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The Physics of a Perfect Launch
              </Link>{' '}
              — the underlying physics of the launch-RPM and clutch-ramp adjustments recommended above.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM Duke 390 vs RC 390: Quarter-Mile Physics at Aamby Valley
              </Link>{' '}
              — the same venue framing applied to a 400-class single, including a quick MMRT delta estimate.
            </li>
            <li>
              ·{' '}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{' '}
              — what is inside the simulator that produced these numbers, and what the cluster bias bands mean.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — 501 bikes with full spec sheets, OEM tire fitments, and venue-aware quarter-mile predictions for every Indian drag strip in the database.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                Pricing
              </Link>{' '}
              — free tier covers stock-tune sims at every venue; Pro unlocks the full parts-ROI engine and Dragy timeslip calibration against your own MMRT runs.
            </li>
          </ul>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
