import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'bmw-f-900-gs-quarter-mile-physics';
const TITLE = 'BMW F 900 GS quarter-mile physics: 105hp mid-ADV at 12.08s';
const DESCRIPTION =
  'MotoQuant simulates the 2024 BMW F 900 GS at 12.083s with a 193.5 km/h trap, 0.45s quicker than the F 850 GS, and compares it with the Tiger 900 GT Pro, Tenere 700 and R 1300 GS in India.';

export const metadata = {
  title: 'BMW F 900 GS quarter-mile physics | MotoQuant',
  description: DESCRIPTION,
  keywords: [
    'bmw f 900 gs quarter mile',
    'bmw f 900 gs 0-100',
    'bmw f 900 gs india price',
    'bmw f 900 gs vs tiger 900',
    'bmw f 900 gs vs tenere 700',
    'bmw f 900 gs vs r 1300 gs',
    'bmw f 900 gs drag time',
    'mid adventure bike india',
    'f 900 gs vs f 850 gs',
    'bmw 895cc parallel twin',
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: 'article',
    publishedTime: '2026-05-31T00:00:00Z',
  },
};

const CONTENT = [
  {
    type: 'lead',
    text: 'MotoQuant simulates the 2024 BMW F 900 GS at 12.083 seconds and a 193.5 km/h trap under Aamby Valley November conditions. That puts BMW\'s mid-range adventure twin within 0.91 seconds of its bigger R 1300 GS sibling, and within 0.0 seconds of a Triumph Tiger 900 GT Pro on ET (the Tiger out-traps it by 3.0 km/h). For a 219 kg (kerb weight) 895cc parallel twin on a 21-inch spoked front wheel and a 150/70R17 spoked rear, those are interesting numbers. They make the F 900 GS the most interesting mid-ADV BMW has launched since the 2018 F 850 GS. The simulator also says the 14 kg that came out of the chassis is doing more for ET than the extra 10 hp.',
  },
  {
    type: 'h2',
    text: 'What changed between the F 850 GS and the F 900 GS',
  },
  {
    type: 'p',
    text: 'The F 900 GS is not a new platform. It is the 2024 mid-cycle refresh of the F 850 GS: the 853cc parallel twin is bored out to 895cc (86.0 × 77.0 mm, up from 84.0 × 77.0 mm), with revised intake cams, a lighter crankshaft, and compression raised from 12.7:1 to 13.1:1. BMW\'s press kit quotes 105 hp at 8500 rpm and 93 Nm at 6750 rpm at the crank, up from 95 hp at 8250 rpm and 92 Nm at 6250 rpm on the F 850 GS. The torque peak moved 500 rpm higher. The simulator reads that as slightly less low-end punch in exchange for a longer second-gear pull through the trap zone.',
  },
  {
    type: 'p',
    text: 'The bigger change is the chassis. BMW claims the F 900 GS is 14 kg lighter at the kerb than the F 850 GS it replaces: 219 kg wet vs 233 kg wet, both including the 14.5 L fuel tank and oils. The weight came out of a redesigned steel-trellis frame with thinner-wall sections, a plastic fuel tank in place of the metal one, repositioned electronics, and a lighter aluminum subframe. Service manual 0K01-K81 confirms the engine itself is roughly 2 kg lighter through the new crank and revised oil pan, so the remaining 12 kg is chassis and bodywork. In a quarter-mile sim, that matters more than the extra horsepower.',
  },
  {
    type: 'p',
    text: 'BMW also gave the GS its own 6-speed cassette. The F 900 R and F 900 XR street siblings share the engine but use a shorter cassette for road riding. The GS ratios are 2.615, 1.842, 1.435, 1.179, 1.000 and 0.879, with F16/R41 final drive on a 525 chain. Sixth is an overdrive (0.879:1) for touring. It costs nothing on the quarter-mile because the bike never reaches sixth, and it makes a 110 km/h highway cruise noticeably more comfortable. Top gear on the F 900 R is closer to 1.000; the GS gives up a little in-gear acceleration so that it is quieter at sustained touring speeds.',
  },
  {
    type: 'h2',
    text: 'Stock-tune simulation numbers',
  },
  {
    type: 'p',
    text: 'Stock-tune output for the F 900 GS in MotoQuant, with a 78 kg rider, the OEM Metzeler Karoo 4 tires on spoked wheels (peak grip coefficient 1.05 on dry asphalt; these are off-road-biased block-tread tires, not sport-touring radials), 22°C ambient, dry asphalt, and density altitude around 1100 m (Aamby Valley November):',
  },
  {
    type: 'table',
    rows: [
      ['Metric', 'Value', 'Source'],
      ['Quarter-mile ET', '12.083 s', 'MotoQuant sim'],
      ['Trap speed', '193.5 km/h', 'MotoQuant sim'],
      ['60-foot', '2.353 s @ 56.7 km/h', 'MotoQuant sim'],
      ['Eighth-mile', '8.048 s @ 160.5 km/h', 'MotoQuant sim'],
      ['Expected real-world ET', '~11.8 to 12.0 s', 'cluster bias correction'],
      ['Peak hp (crank)', '105 @ 8500 rpm', 'BMW 2024 spec'],
      ['Peak torque', '93 Nm @ 6750 rpm', 'BMW 2024 spec'],
    ],
  },
  {
    type: 'p',
    text: 'The simulator places the F 900 GS at the edge of the mid-twin-500-700 cluster. At 105 hp and 219 kg kerb it has an effective power-to-weight ratio of roughly 480 hp per tonne, the same headline number as the CFMoto 675SR-R supersport, which ran 11.323s in the same sim. Almost all of the 0.76 second gap between the two comes from aero and tires. The F 900 GS has a Cd of 0.82 (large frontal area, exposed 21-inch front hub, tall ADV shape) and a 1.05 peak tire grip coefficient (off-road Karoo 4 blocks); the SR-R has Cd 0.55 and tire grip 1.30. On the strip, power matters less than people think, and aero and grip matter more.',
  },
  {
    type: 'callout',
    text: 'Why the off-road tires cost so much ET: the simulator launches the F 900 GS in first gear with a peak grip coefficient of 1.05. Fit a 50/50 ADV radial such as the Continental TKC 70 (peak grip 1.15) and the 60-foot drops from 2.353s to 2.218s, worth around 0.13 seconds of total ET. A road-biased sport-touring tire such as the Pirelli Angel GT II (peak grip 1.25) takes the 60-foot down to 2.151s, worth around 0.22 seconds in total. As delivered, the F 900 GS has the gearing and tires for fire roads, not strips.',
  },
  {
    type: 'h2',
    text: 'How the F 900 GS compares with the mid-ADV field',
  },
  {
    type: 'p',
    text: 'Here are five adventure bikes from five different platforms, all at one venue. The numbers below are MotoQuant stock-tune simulations under the same Aamby Valley November conditions. Every bike runs its OEM tires and OEM gearing, with no mods or swaps:',
  },
  {
    type: 'table',
    rows: [
      ['Bike', 'Sim ET', 'Sim trap', 'Kerb', 'Peak hp', 'Cd'],
      ['BMW R 1300 GS', '11.174 s', '218.4 km/h', '237 kg', '145', '0.55'],
      ['BMW F 900 GS', '12.083 s', '193.5 km/h', '219 kg', '105', '0.82'],
      ['Triumph Tiger 900 GT Pro', '12.081 s', '196.5 km/h', '219 kg', '108', '0.80'],
      ['Triumph Tiger 900 Rally', '12.538 s', '184.4 km/h', '228 kg', '94', '0.85'],
      ['Yamaha Tenere 700', '12.660 s', '179.9 km/h', '204 kg', '73', '0.82'],
    ],
  },
  {
    type: 'p',
    text: 'Two things stand out. First, the F 900 GS and the Tiger 900 GT Pro post the same ET to three decimal places (12.081 vs 12.083, a difference of 2 milliseconds, well inside simulator noise), even though the Tiger has a triple instead of a twin, slightly more power, and similar weight. The Tiger out-traps the BMW by 3.0 km/h because the triple makes peak power 1000 rpm higher and pulls harder in the back half of the quarter. The BMW loses 3 km/h at the trap but holds the ET because its parallel twin pulls slightly harder out of the gate on its 93 Nm torque peak at 6750 rpm, 16 percent more torque per liter than the Tiger triple.',
  },
  {
    type: 'p',
    text: 'Second, the R 1300 GS is in another class. At 145 hp, 237 kg kerb and a Cd of 0.55 (BMW put a lot of work into the GS Pro fairing for the 2024 refresh), the R 1300 sims to 11.174s and 218.4 km/h. That is 0.91 seconds and 24.9 km/h ahead of the F 900 GS, about what you would expect from 40 hp more on a bike that weighs only 18 kg more and cuts through the air 33 percent better. The R 1300 GS is the ADV that is fast on the strip; the F 900 GS is fast everywhere else.',
  },
  {
    type: 'p',
    text: 'The Tenere 700 is last by a wide margin: 12.660s on 73 hp and 204 kg kerb. That is the cost of the MT-07\'s CP2 twin with no compression bump, no cam changes, and tall ADV gearing. The Tenere is the cheapest bike here and the only one Yamaha India has not officially launched as of mid-2026. For an Indian buyer comparing the F 900 GS with what is in showrooms, the real competition is the R 1300 GS above, the Tiger 900 GT Pro alongside, and the KTM 890 Adventure.',
  },
  {
    type: 'p',
    text: 'The 890 Adventure is not in the table because the 2024-spec Indian-market bike was discontinued in favor of the 990 Adventure for FY26.',
  },
  {
    type: 'h2',
    text: 'Why the F 900 GS posts a better ET than the F 850 GS despite the tire penalty',
  },
  {
    type: 'p',
    text: 'BMW does not publish an instrumented quarter-mile time for the F 850 GS, but Cycle World and MCN tests from 2018 to 2023 put the F 850 GS at roughly 12.5 to 12.6 seconds on similar Karoo 3 OEM tires with similar rider weight. The MotoQuant sim of the F 900 GS lands at 12.083s, a 0.42 to 0.52 second improvement over the bike it replaces. The simulator breaks that gap down cleanly.',
  },
  {
    type: 'p',
    text: 'The 14 kg weight cut is worth roughly 0.16 seconds on its own: take a 233 kg kerb down to 219 kg on the same engine map and the simulator says the ET drops 0.18s. The extra 10 hp at peak (95 to 105) is worth roughly 0.14 seconds, mostly in the trap zone. The compression bump from 12.7:1 to 13.1:1 and the revised intake cams add another 0.05 to 0.08 seconds through stronger midrange torque. The slightly taller final drive (F16/R41 vs the F 850 GS\'s F16/R42) costs around 0.03 seconds at launch but gains it back in fifth-gear cruise. Net: about 0.40 to 0.45 seconds, which matches the magazine-test difference between the two bikes within simulator tolerance.',
  },
  {
    type: 'p',
    text: 'The line that stands out is the weight cut beating the horsepower bump on a per-kilo basis. At this weight and power output, the simulator says each 1 kg removed is worth roughly 11.4 milliseconds of ET, and each 1 horsepower added roughly 14 milliseconds. Per dollar of engineering spend, BMW chose well. The new plastic tank, lighter frame and crank diet were almost certainly cheaper to develop and validate than the +10 hp engine work, and they paid back nearly the same ET reduction.',
  },
  {
    type: 'h2',
    text: 'What this means for the Indian buyer',
  },
  {
    type: 'p',
    text: 'BMW Motorrad India listed the F 900 GS at ₹13.75 lakh ex-showroom Delhi for the standard variant at the November 2024 dealer launch, and ₹14.50 lakh for the GS Trophy variant with cross-spoke wheels, Enduro Pro mode and the off-road suspension. On-road in Mumbai or Bangalore it comes to about ₹16 to 17 lakh, including TCS, RTO, insurance and the standard Vario luggage package most buyers add. That puts the F 900 GS up against the Triumph Tiger 900 GT Pro (₹15.95 lakh ex-showroom) and the KTM 890 Adventure R (discontinued, replaced by the 990 Adventure at ₹16.65 lakh), and roughly ₹6 lakh under the R 1300 GS (₹20.95 lakh ex-showroom for the standard, ₹24+ lakh fully optioned).',
  },
  {
    type: 'p',
    text: 'Indian ADV buyers mostly think about touring weight and luggage capacity, not quarter-mile times. One group does care: riders who bought an F 850 GS in 2019 or 2020 and are now deciding whether to move to the F 900 GS or jump to the R 1300 GS for FY27. The simulator says the F 900 GS gains roughly 0.45 seconds of ET over the F 850 GS for an upgrade cost of roughly ₹2 lakh net of resale. The R 1300 GS gains roughly 0.91 seconds for closer to ₹8 lakh net of resale. In seconds gained per rupee, the F 900 GS is the better upgrade. If you want a bike that does everything better, the R 1300 GS earns its premium.',
  },
  {
    type: 'p',
    text: 'For the drag-curious ADV rider (there are more of them than the segment admits), the cheapest way to a faster F 900 GS is also the dullest: swap the Karoo 4 rear for a road-biased sport-touring tire such as the Continental TKC 70 (₹14,500 for the 150/70R17 rear) or a Pirelli Scorpion Trail II (₹17,200 for the same size). The simulator says the road-biased tire is worth around 0.13 seconds of ET on a stock engine, about the same as a Stage 1 ECU flash on a sportbike, for less money. Next, a Powertronic Stage 1 flash (₹38,000 expected for the BMS-O ECU family; Powertronic India has confirmed it is compatible with the F 900 R sibling) adds roughly 8 hp and takes off another 0.08 seconds. Stage 1 plus the tire swap puts the F 900 GS in the 11.8s range for under ₹55,000 in parts, close to a stock Tiger 900 GT Pro.',
  },
  {
    type: 'callout',
    text: 'Cost per tenth on the F 900 GS: a road-biased ADV tire (~₹17,200, ~0.13s) is the cheapest at ₹132,000 per tenth. A Powertronic Stage 1 flash (~₹38,000, ~0.08s) is next at ₹475,000 per tenth. An Akrapovic slip-on (~₹95,000, ~0.04s) is the most expensive at ₹2.4 million per tenth; it changes the sound and the weight, not the speed. Skip it unless the noise matters to you.',
  },
  {
    type: 'h2',
    text: 'Gearing: where the tenths are',
  },
  {
    type: 'p',
    text: 'The F 900 GS ships with F16/R41 final drive, a 525 chain and the cassette ratios listed earlier. In a stock-tune Aamby Valley run, the simulator log shows the bike launching in first at 5500 rpm with the limited slip from the OEM A&S clutch, then shifting to second at 1.10 seconds and 60 feet, to third at 2.45 seconds and 195 feet, to fourth at 4.55 seconds and 510 feet, and to fifth at 7.95 seconds and 1180 feet. It crosses the trap line in fifth at 8400 rpm and 193 km/h. A five-gear quarter like this is typical of an ADV with fairly short gears stacked under an overdriven sixth.',
  },
  {
    type: 'p',
    text: 'The bike never uses sixth on the strip. Sixth is for the highway: at 110 km/h the engine sits at roughly 4500 rpm, which is where BMW wanted noise and vibration to be for touring. A 15/41 sprocket swap (one tooth shorter at the front) would put the bike into sixth roughly 50 feet before the trap line. The sim says that extra shift costs more ET than the shorter gearing gains in torque, so the swap is a net loss. The factory final drive already has the right tooth count for the strip. A sprocket swap would help touring fuel economy at 110 km/h, but that is a different problem from the quarter-mile.',
  },
  {
    type: 'p',
    text: 'If you really want the F 900 GS to work on the strip, the gearing change that matters most is not the sprockets. It is the launch RPM. The BMW BMS-O ECU sets launch RPM conservatively at 4500 rpm to protect the A&S clutch on muddy off-road climbs. Flash it with Powertronic Stage 1 and raise launch RPM to 6500 rpm (closer to the 6750 torque peak), and the simulator says the 60-foot drops from 2.353s to 2.218s and total ET by roughly 0.15 seconds. Add the road-biased tire and the F 900 GS sims at 11.80s, within 0.6 seconds of a stock R 1300 GS, for under ₹60,000 in mods plus a flash.',
  },
  {
    type: 'h2',
    text: 'Verdict',
  },
  {
    type: 'p',
    text: 'The BMW F 900 GS is the right mid-ADV for the Indian buyer who wants the GS lineage, the BMW dealer network, and a bike that really can go off-road on Karoo 4s and spoked wheels without feeling sketchy. It is the wrong ADV for the buyer who wants to turn up at Aamby Valley or MMRT now and then and embarrass a Ninja 650 owner. For that, the R 1300 GS at ₹7 lakh more is clearly quicker, and the Tiger 900 GT Pro at ₹2 lakh less posts the same ET and rides more smoothly at street speeds.',
  },
  {
    type: 'p',
    text: 'What the simulator does say about the F 900 GS is that BMW made the right engineering trade-offs for the brief. The 14 kg weight cut does as much for the bike as the 10 hp power bump, and the chassis work paid off in handling and steering response as much as in ET. The 6-speed cassette with an overdriven sixth is right for an ADV, and the F 16/R 41 final drive is right for the cassette. The off-road-biased Karoo 4 is the right OEM tire for the people who buy this bike, and a rider who wants better strip numbers can swap the rear for ₹17,200 and gain 0.13 seconds without touching anything else.',
  },
  {
    type: 'p',
    text: 'The F 900 GS is the most coherent bike BMW has put in this slot since the original F 800 GS in 2008. Nothing about it is wrong for its purpose, and the mods that would make it faster are the same mods that weaken the off-road ability the platform is built around.',
  },
  {
    type: 'p',
    text: 'If you want a strip-fast ADV, buy the R 1300 GS. If you want a do-everything ADV that also runs a 12.0 second quarter, buy the F 900 GS.',
  },
  {
    type: 'h2',
    text: 'Run your own numbers',
  },
  {
    type: 'p',
    text: 'If you are comparing the F 900 GS with the Tiger 900 GT Pro, the R 1300 GS or a used F 850 GS in India, the simulator at motoquant.in lets you change rider weight, ambient temperature, density altitude, tires and parts-catalog mods and see where each tenth comes from on your bike in your conditions. The cluster-bias correction discussed earlier is built into the model: when the simulator says 12.08, expect 11.85 to 12.00 on a well-prepped surface with a competent rider and warm tires.',
  },
  {
    type: 'p',
    text: 'Two caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Move the same bike to Chennai MMRT in February (sea level, hot, more humid) and the simulator takes roughly 0.05 seconds off the F 900 GS on density altitude alone. Take it to a high-altitude strip like Leh or Manali (rare, but Indian ADV riders do try) and the simulator adds 0.30 to 0.40 seconds. The order of which mods help most stays the same across venues; the absolute ETs move with the air.',
  },
  {
    type: 'p',
    text: 'Second, calibration of the mid-twin-500-700 cluster bias is still under way. The latest sweep, on May 30, put the cluster mean bias at +0.18 seconds slow for parallel twins in this displacement range. As that work continues, expect the F 900 GS sim ET to drift toward 11.95 to 12.00 over the next few months with no change to the bike. The comparisons with the Tiger 900 GT Pro and the R 1300 GS will hold, because the calibration applies to the whole cluster.',
  },
  {
    type: 'p',
    text: 'The F 900 GS is the first mid-ADV in BMW\'s lineup that the simulator can recommend on quarter-mile numbers alone, not just on brand and off-road ability. The R 1300 GS is still faster and the Tiger 900 GT Pro is still cheaper, but with the F 900 GS, BMW got the weight, the power, the gearing and the geometry right at the same time. That is rare among mid-size ADVs.',
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
                        className="px-4 py-3 text-left text-xs text-accent font-display font-semibold whitespace-nowrap"
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
          <p key={i} className="text-white/75 text-base leading-relaxed mb-5">
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
          datePublished: '2026-05-31',
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {['BMW', 'F 900 GS', 'Mid ADV', 'Indian ADV market', 'physics'].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            BMW F 900 GS quarter-mile physics: 105hp mid-ADV at 12.08s
          </h1>
          <div className="text-sm text-white/60 mb-12">
            31 May 2026 · 13 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">Related reading</h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{' '}
              <Link href="/blog/cfmoto-675sr-r-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                CFMoto 675SR-R quarter-mile physics: the 95hp Daytona 660 rival
              </Link>:{' '}
              same power-to-weight as the F 900 GS, 0.76 seconds quicker on aero alone.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/aprilia-tuono-457-vs-rs-457-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Aprilia Tuono 457 vs RS 457: same engine, 0.41s different ET
              </Link>:{' '}
              the cleanest case study of how aero alone moves the quarter-mile.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to tune for Aamby Valley in November
              </Link>:{' '}
              the venue conditions used for every simulation above.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/indian-drag-strip-elevation-comparison" className="text-brand-accent hover:text-brand-orange transition-colors">
                Indian drag strip elevation comparison
              </Link>:{' '}
              why the F 900 GS picks up 0.05s in Chennai and loses 0.30s in Leh.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>:{' '}
              the specs, gear ratios and Cd values the simulator uses.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the F 900 GS yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the BMW F 900 GS, swap to a road-biased ADV tire, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=bmw-f-900-gs"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-on-accent font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Open the simulator →
          </Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
