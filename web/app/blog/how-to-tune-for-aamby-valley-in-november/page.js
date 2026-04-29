import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';

export const metadata = {
  title: 'How to Tune for Aamby Valley in November — MotoQuant Blog',
  description: 'November at Aamby Valley means density altitude around 1100 m, 18–24°C, and concrete with a good grip coefficient. Every number changes your optimal tune.',
  keywords: ['Aamby Valley drag racing', 'drag racing India conditions', 'density altitude motorcycle', 'tune for conditions'],
  alternates: { canonical: 'https://motoquant.in/blog/how-to-tune-for-aamby-valley-in-november' },
  openGraph: {
    title: 'How to Tune for Aamby Valley in November',
    description: 'Density altitude, temperature, and surface grip — how Aamby Valley conditions affect your quarter-mile.',
    url: 'https://motoquant.in/blog/how-to-tune-for-aamby-valley-in-november',
    type: 'article',
    publishedTime: '2026-04-24T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'Aamby Valley City in Maharashtra sits at approximately 1,050 m above sea level. In November, temperatures run 18–24°C during the day with low humidity (20–40%). The drag surface is concrete — well-maintained, consistent, and with a grip coefficient higher than typical asphalt. All of these numbers have direct physics implications for your quarter-mile time. Here is how to use them.',
  },
  {
    type: 'h2',
    text: 'Density Altitude: The Number That Governs Everything',
  },
  {
    type: 'p',
    text: 'Density altitude (DA) is the altitude at which the current air density matches the standard atmosphere. At Aamby Valley in November — 1,050 m elevation, 21°C, 30% RH — the density altitude is approximately 1,080–1,120 m. Standard sea-level conditions are 0 m DA.',
  },
  {
    type: 'p',
    text: 'Every 300 m of density altitude costs approximately 3% of engine power. At 1,100 m DA, you are losing roughly 11% of your rated power before the run even starts. A 178 hp GSX-R 1000 K5 effectively makes ~158 hp at Aamby Valley in November. A 18 hp R15 V3 makes ~16 hp.',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s environmental sub-model computes this using the standard ICAO atmosphere model: power correction factor = (P_standard / P_actual) × √(T_standard / T_actual), where P is ambient pressure and T is temperature in Kelvin. The Aamby Valley venue entry in the database carries average November conditions including pressure at elevation.',
  },
  {
    type: 'callout',
    text: 'The good news: lower air density also means lower aerodynamic drag. The drag force is proportional to air density — so at Aamby Valley you are fighting roughly 11% less aero drag than at sea level. For high-powered bikes where drag is the dominant resistance force at trap speed, the lower drag partially offsets the power loss. For small-cc bikes where drag is less dominant, the power loss hurts more than the drag reduction helps.',
  },
  {
    type: 'h2',
    text: 'Temperature: Why November is the Best Month',
  },
  {
    type: 'p',
    text: 'November is arguably the best month for drag racing in Maharashtra. The monsoon has cleared, temperatures are in the 18–24°C range, and humidity is low. Compare this to May (38–42°C, 60–70% RH) where density altitude can exceed 2,200 m and power losses exceed 18%.',
  },
  {
    type: 'p',
    text: 'Lower temperature helps in two ways. First, cooler air is denser, so engine volumetric efficiency improves. Second, the intake charge temperature drops, which marginally increases knock resistance and allows slightly more aggressive ignition advance on bikes with DOHC or programmable ignition.',
  },
  {
    type: 'p',
    text: 'Tyre temperature is the other side of the November equation. At 20°C ambient, your tyres start cold and take longer to reach optimal operating temperature. For a short quarter-mile run, the first 100 metres may be on tyres that are 10–15°C below their peak μ window. A warm-up burnout (if allowed at the event) or staged staging passes help here.',
  },
  {
    type: 'h2',
    text: 'Surface: Concrete vs Asphalt',
  },
  {
    type: 'p',
    text: 'Aamby Valley\'s drag surface is concrete, and the strip has been well-maintained. Concrete in good condition has a surface grip coefficient of 0.80–0.90 (scaling factor relative to ideal asphalt), versus 0.75–0.85 for mid-grade asphalt. MotoQuant uses a surface grip multiplier that scales μ_peak — so on Aamby Valley concrete with a sticky tyre, you can realistically push μ_effective up to 1.1–1.2 for a well-prepped slick.',
  },
  {
    type: 'p',
    text: 'The concrete surface also has a different thermal conductivity profile. It warms up more slowly than asphalt, so early-in-the-day runs (7–9 AM) will have lower surface grip and higher risk of tyre spin at launch. By mid-morning (10–11 AM) the surface has typically reached 35–45°C even in November, and grip is near its daily peak.',
  },
  {
    type: 'h2',
    text: 'How to Set Up Your Bike for Aamby in November',
  },
  {
    type: 'p',
    text: 'Here is the practical tuning guidance that MotoQuant\'s environmental sweep gives for Aamby Valley in November, applied to three representative bike classes:',
  },
  {
    type: 'p',
    text: 'Litre-class superbike (Hayabusa Gen1, ZX-10R, S1000RR): The power penalty from density altitude is approximately 19–23 hp. The drag reduction is approximately the same in absolute terms. Net ET change from Aamby November vs sea-level ISA: roughly +0.10–0.15s for the litre class. These bikes are gearing-limited on the top end anyway, so the main concern is not losing too much from the power cut at high speed. Run the bike in its most aggressive launch map — the concrete surface supports it.',
  },
  {
    type: 'p',
    text: 'Mid-class sport (Kawasaki Ninja 650, Triumph Speed 400, Bajaj Dominar 400): Power penalty 4–7 hp, drag reduction proportional. These bikes benefit more from the drag reduction since they are power-limited at top speed. ET change vs sea-level: approximately +0.20–0.30s. Focus on launch — the mid-class parallel twin has a reasonable power-to-weight but a torque curve that peaks early. At Aamby, that early torque peak means more slip risk on cold concrete in the morning.',
  },
  {
    type: 'p',
    text: 'Small-cc (R15 V3, Pulsar NS200, Duke 390): The power penalty hurts proportionally more because these bikes have less absolute power margin. A 10% power cut on 18 hp is 1.8 hp — meaningful. The drag reduction barely compensates because the trap speeds (120–150 km/h) are in a regime where drag is not yet dominant. ET change: +0.30–0.50s vs sea-level. For small-cc bikes at Aamby, prioritise gearing (shorter top-end ratio to keep the engine in its power band despite the altitude cut) and tyre temperature management.',
  },
  {
    type: 'callout',
    text: 'The MotoQuant venue database stores Aamby Valley with its November seasonal data: elevation 1,050 m, mean temp 21°C, mean RH 28%, surface type concrete, grip_multiplier 0.88. Select it in the Location Picker and your simulation instantly accounts for all of this.',
  },
  {
    type: 'h2',
    text: 'The Jetting / Fueling Question',
  },
  {
    type: 'p',
    text: 'For carburetted bikes or bikes with open-loop fuel maps: at 1,100 m DA, the air-fuel mixture goes rich because there is less oxygen per unit of air volume. On a bike with a fixed carb jet, this means you are delivering more fuel than the engine can burn. A jet drop (main jet 1–2 sizes smaller) or needle clip change (raise the needle by 1–2 positions for a leaner full-throttle mixture) is warranted if you are chasing tenths.',
  },
  {
    type: 'p',
    text: 'Modern EFI bikes (R15 V4, Duke 390, Ninja 400) compensate automatically via the O2 sensor and closed-loop AFR control — no action needed. But bikes with OBD-locked ECUs on open-loop fuel maps (some Dominar variants, older Pulsars) may benefit from an ECU piggyback unit that leans out the map at altitude.',
  },
  {
    type: 'h2',
    text: 'Timing Your Runs',
  },
  {
    type: 'p',
    text: 'The best November Aamby runs typically happen between 9:30 AM and 12:00 PM. By 9:30 the surface has warmed enough for consistent traction. After noon, track temperature can climb into the high 40s°C, which does not affect grip much on concrete but does raise tyre operating temperature into a zone where some tyres begin to drop off the peak μ curve.',
  },
  {
    type: 'p',
    text: 'Wind is a factor. November at Aamby Valley can see 8–15 km/h northeast winds. A headwind raises effective aerodynamic drag — at 10 km/h headwind, the Cd×A term sees an extra ~6% drag at 150 km/h trap. A tailwind reduces drag. If the event does multiple rounds, pay attention to which direction the wind shifted and adjust your top-end expectations accordingly.',
  },
  {
    type: 'p',
    text: 'MotoQuant\'s wind model lets you input headwind or tailwind speed directly. If you have a weather app reading at the strip, plug it in and run the simulation before you stage. It is one of those variables that most racers ignore but that consistently separates the analysts from the guessers.',
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
        return <p key={i} className="text-white/70 text-sm leading-relaxed mb-5">{block.text}</p>;
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
              <span key={t} className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide">{t}</span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            How to Tune for Aamby Valley in November
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            24 April 2026 · 6 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <div className="max-w-2xl mx-auto mt-16 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Set Aamby Valley as your venue</div>
            <div className="text-white/60 text-sm">Select your bike, open the Location Picker, choose Aamby Valley City, and the November conditions load automatically.</div>
          </div>
          <Link href="/simulator" className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors">Run sim →</Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
