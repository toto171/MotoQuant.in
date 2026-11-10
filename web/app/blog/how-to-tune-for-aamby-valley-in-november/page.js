import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';

export const metadata = {
  title: 'How to tune for Aamby Valley in November | MotoQuant Blog',
  description: 'November at Aamby Valley means 679 m of elevation, about 22°C and a density altitude near 1,100 m on an asphalt strip. What that costs each class of bike, and how to tune for it.',
  keywords: [
    'Aamby Valley drag racing',
    'aamby valley density altitude november',
    'aamby valley weather drag racing',
    'valley run november tuning',
    'indian drag strip weather',
    'drag racing India conditions',
    'density altitude motorcycle',
    'tune for conditions',
  ],
  alternates: { canonical: 'https://motoquant.in/blog/how-to-tune-for-aamby-valley-in-november' },
  openGraph: {
    title: 'How to tune for Aamby Valley in November',
    description: 'Density altitude, temperature, tyres and wind: how Aamby Valley conditions affect your quarter-mile.',
    url: 'https://motoquant.in/blog/how-to-tune-for-aamby-valley-in-november',
    type: 'article',
    publishedTime: '2026-04-24T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'The Aamby Valley airstrip in Maharashtra sits 679 m above sea level. MotoQuant\'s November normals for it are 22°C, 40% humidity and a 26°C track, on asphalt, and each of those numbers changes your quarter-mile time. (Updated 10 November 2026: the venue facts now match the catalog, and every simulated time was re-run on the current engine.)',
  },
  {
    type: 'h2',
    text: 'Density altitude',
  },
  {
    type: 'p',
    text: 'Density altitude (DA) is the altitude at which the standard atmosphere would have the current air density. At Aamby Valley in November (679 m, 22°C, 40% RH) the simulator computes a DA of about 1,120 m, because the air is warmer than the standard atmosphere at that height. Standard sea-level conditions are 0 m DA.',
  },
  {
    type: 'p',
    text: 'As a rule of thumb, every 300 m of density altitude costs about 3% of engine power. The simulator\'s own correction for Aamby in November is 0.895 against its sea-level reference day, a loss of about 10.5% before the run starts. A 178 hp GSX-R 1000 K5 makes about 159 hp there; an 18 hp R15 V3 makes about 16 hp.',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s environmental sub-model uses the SAE J1349 correction: power scales with dry-air pressure and with the inverse square root of intake temperature, anchored so the reference day (sea level, 25°C, 50% humidity) gives exactly 1.0. The Aamby Valley venue entry carries average conditions for every month, so the correction follows the season.',
  },
  {
    type: 'callout',
    text: 'Lower air density also means lower aerodynamic drag, because drag force is proportional to density. On the current engine the drag saving never makes up for the power loss on a stock bike: every bike simulated in this post is slower at Aamby than at sea level, and small bikes lose the most.',
  },
  {
    type: 'h2',
    text: 'Temperature: why November is the best month',
  },
  {
    type: 'p',
    text: 'November opens the dry season in Maharashtra: the monsoon has cleared and humidity drops. It is not the densest month, though. The catalog normals put Aamby\'s DA at about 1,120 m in November, 970 m in December and 920 m in January, against about 1,500 m in May (30°C, 45% RH), where the power loss reaches 13%.',
  },
  {
    type: 'p',
    text: 'Cooler air helps in two ways. It is denser, so volumetric efficiency improves. And a cooler intake charge resists knock a little better, which allows slightly more ignition advance on bikes with DOHC or programmable ignition.',
  },
  {
    type: 'p',
    text: 'Tyre temperature works against you in November. At 20°C ambient your tyres start cold and take longer to reach their working temperature. In a quarter-mile run the first 100 metres may be on tyres 10–15°C below their peak μ window. A warm-up burnout, if the event allows one, or staged staging passes help.',
  },
  {
    type: 'h2',
    text: 'Surface: asphalt'
  },
  {
    type: 'p',
    text: 'The catalog stores Aamby Valley as an asphalt strip with no prep compound, so the simulator applies a surface grip multiplier of 1.00 to the tyre\'s peak friction coefficient. A prepped surface would raise that to 1.18; the event organiser, not the simulator, decides whether there is any.',
  },
  {
    type: 'p',
    text: 'Track temperature matters through the tyre. The November normal for the track is 26°C, so early runs start on cool rubber, and the tyre model loses grip until the tread reaches its operating window.',
  },
  {
    type: 'h2',
    text: 'How to set up your bike for Aamby in November',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s environmental sweep for Aamby Valley in November gives this guidance for three classes of bike.',
  },
  {
    type: 'p',
    text: 'Litre-class superbikes (Hayabusa Gen1, ZX-10R, S 1000 RR) lose about 10.5% of their power, or 17–22 hp. The simulator puts these bikes 0.08 s (S 1000 RR, 2019) to 0.17 s (ZX-10R, 2021) slower at Aamby in November than at sea level; a stock Hayabusa Gen1 goes from 10.11 s to 10.22 s. Most of the launch is traction-limited, so the main concern is the power cut at high speed. Run the most aggressive launch map the tyre can hold.',
  },
  {
    type: 'p',
    text: 'Mid-class bikes (Kawasaki Ninja 650, Triumph Speed 400, Bajaj Dominar 400) lose 4–7 hp. The simulator puts the Ninja 650 0.22 s slower at Aamby than at sea level, and the Dominar 400 and Speed 400 0.34 s and 0.37 s slower. Focus on the launch: a twin or single with an early torque peak spins a cool tyre easily in the morning.',
  },
  {
    type: 'p',
    text: 'Small bikes (R15 V3, Pulsar NS200, Duke 390) lose the most, because they are power-limited for the whole run. A 10% power cut on 18 hp is 1.8 hp, and the lower drag barely helps at 115–150 km/h. The simulator puts the Duke 390 (2017) 0.28 s slower at Aamby than at sea level, and the NS200 and R15 V3 0.42 s and 0.43 s slower. Spend your effort on gearing that keeps the engine in its power band, and on tyre temperature.',
  },
  {
    type: 'callout',
    text: 'The MotoQuant venue database stores Aamby Valley at 679 m on asphalt, with its November normals: 22°C, 40% humidity, 1014 hPa and a 26°C track. Pick it in the simulator and the run uses all of them.',
  },
  {
    type: 'h2',
    text: 'Jetting and fuelling',
  },
  {
    type: 'p',
    text: 'At 1,100 m DA a carburetted bike, or one on an open-loop fuel map, runs rich, because each litre of air carries less oxygen. With a fixed carb jet you are delivering more fuel than the engine can burn. If you are chasing tenths, fit a main jet 1–2 sizes smaller or change the needle clip (raise the needle by 1–2 positions for a leaner full-throttle mixture).',
  },
  {
    type: 'p',
    text: 'Modern EFI bikes (R15 V4, Duke 390, Ninja 400) correct for this on their own through the O2 sensor and closed-loop AFR control, so leave them alone. Bikes with OBD-locked ECUs on open-loop fuel maps (some Dominar variants, older Pulsars) may gain from an ECU piggyback unit that leans out the map at altitude.',
  },
  {
    type: 'h2',
    text: 'Timing your runs',
  },
  {
    type: 'p',
    text: 'Track temperature climbs through the day. A cool morning track keeps the tyre below its grip window for the first part of the run; a hot afternoon track can push some tyres past it. Watch the tyre, not the clock.',
  },
  {
    type: 'p',
    text: 'The catalog\'s November normal for Aamby is a light north-easterly wind averaging 1.2 m/s (about 4 km/h), but gusts on the day can be stronger. In the simulator a steady 10 km/h headwind costs a stock Hayabusa 0.04 s and an R15 V4 0.21 s, because the slower bike spends longer in it with less power to spare. If an event runs several rounds, note the wind for each.',
  },
  {
    type: 'p',
    text: 'You can enter headwind or tailwind speed directly in MotoQuant\'s wind model. If a weather app gives you a reading at the strip, enter it and run the simulation before you stage.',
  },
];

function Prose({ content }) {
  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        if (block.type === 'h2') return <h2 key={i} className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight">{block.text}</h2>;
        if (block.type === 'lead') return <p key={i} className="text-lg text-white/80 leading-relaxed mb-8 font-light">{block.text}</p>;
        if (block.type === 'callout') return (
          <div key={i} className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5">
            <p className="text-sm text-white/80 leading-relaxed italic">{block.text}</p>
          </div>
        );
        return <p key={i} className="text-white/75 text-base leading-relaxed mb-5">{block.text}</p>;
      })}
    </div>
  );
}

export default function PostPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {['venue', 'Aamby Valley', 'weather', 'conditions'].map(t => (
              <span key={t} className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent">{t}</span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            How to tune for Aamby Valley in November
          </h1>
          <div className="text-sm text-white/60 mb-12">
            24 April 2026 · 6 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Set Aamby Valley as your venue</div>
            <div className="text-white/60 text-sm">Pick your bike, open the location picker and choose Aamby Valley City. The November conditions load on their own.</div>
          </div>
          <Link href="/simulator" className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">Open the simulator →</Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
