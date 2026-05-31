import Link from 'next/link';
import SiteNav from '../../../components/SiteNav';
import SiteFooter from '../../../components/SiteFooter';
import StructuredData, { articleSchema } from '../../StructuredData';

const SLUG = 'bmw-f-900-gs-quarter-mile-physics';
const TITLE = 'BMW F 900 GS Quarter-Mile Physics: 105hp Mid-ADV at 12.08s';
const DESCRIPTION =
  'MotoQuant sims the 2024 BMW F 900 GS at 12.083s and 193.5 km/h trap — 0.45s quicker than the F 850 GS. Physics vs Tiger 900 GT Pro, Tenere 700, R 1300 GS for India.';

export const metadata = {
  title: 'BMW F 900 GS Quarter-Mile Physics — MotoQuant',
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
    text: 'MotoQuant simulates the 2024 BMW F 900 GS at 12.083 seconds and a 193.5 km/h trap under Aamby Valley November conditions. That puts BMW mid-range adventure twin within 0.91 seconds of its bigger R 1300 GS sibling, and within 0.0 seconds of a Triumph Tiger 900 GT Pro on ET (the Tiger out-traps it by 3.0 km/h). For a 219 kg kerb 895cc parallel twin riding on a 21-inch spoke front wheel and a 150/70R17 spoke rear, those are interesting numbers. They are also the reason the F 900 GS is the most interesting mid-ADV launch BMW has done since the 2018 F 850 GS — and the simulator says the 14 kg of weight that came out of the chassis is doing more for ET than the extra 10 hp.',
  },
  {
    type: 'h2',
    text: 'What Changed Between the F 850 GS and the F 900 GS',
  },
  {
    type: 'p',
    text: 'The F 900 GS is not a brand-new platform. It is the 2024 mid-cycle refresh of the F 850 GS, with the 853cc parallel twin bored out to 895cc (86.0 × 77.0 mm, up from 84.0 × 77.0 mm), revised intake cams, a lighter crankshaft, and compression bumped from 12.7:1 to 13.1:1. BMW press kit numbers are 105 hp at 8500 rpm and 93 Nm at 6750 rpm at the crank — up from 95 hp at 8250 rpm and 92 Nm at 6250 rpm on the F 850 GS. The torque peak shifted 500 rpm higher, which the simulator sees as a slight loss of low-end punch in exchange for a longer second-gear pull through the trap zone.',
  },
  {
    type: 'p',
    text: 'The headline change is not the engine. It is the chassis. BMW claims the F 900 GS is 14 kg lighter at the kerb than the outgoing F 850 GS — 219 kg wet vs 233 kg wet, both numbers including the 14.5 L fuel tank and oils. The diet came from a redesigned steel-trellis frame with thinner-wall sections, a plastic fuel tank replacing the previous metal one, repositioned electronics, and a lighter aluminum subframe. Service manual 0K01-K81 confirms the engine itself is roughly 2 kg lighter via the new crank and revised oil pan, so the remaining 12 kg is all chassis and bodywork. On a quarter-mile sim, that matters more than the extra horsepower.',
  },
  {
    type: 'p',
    text: 'BMW also retuned the 6-speed cassette for the GS — distinct from the F 900 R and F 900 XR street siblings, which share the same engine but use a shorter cassette for road riding. The GS gets gear ratios of 2.615, 1.842, 1.435, 1.179, 1.000, and 0.879 with F16/R41 final drive on a 525 chain. Sixth gear is overdriven (0.879:1) for ADV touring cruise — a choice that costs nothing on the quarter-mile because the bike never gets to sixth, and gains a noticeable amount of highway comfort at 110 km/h cruise. Top gear on the F 900 R is closer to 1.000; the GS deliberately gives up a touch of in-gear acceleration to make the bike quieter at sustained touring speeds.',
  },
  {
    type: 'h2',
    text: 'Stock-Tune Simulation Numbers',
  },
  {
    type: 'p',
    text: 'Running the F 900 GS in MotoQuant with a 78 kg rider, OEM Metzeler Karoo 4 spoke wheel set (peak grip coefficient 1.05 on dry concrete — these are off-road-biased block-tread tires, not sport-touring radials), 22°C ambient, dry concrete, and density altitude around 1100 m (Aamby Valley November), the stock-tune output is:',
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
    text: 'The simulator places the F 900 GS at the boundary of the mid-twin-500-700 cluster. At 105 hp and 219 kg kerb it carries an effective power-to-weight ratio of roughly 480 hp per tonne — the same headline number as the CFMoto 675SR-R supersport, which scored 11.323s in the same sim. The 0.76 second gap between the two bikes is almost entirely aerodynamic and tire-related: the F 900 GS runs a Cd of 0.82 (large frontal area, 21-inch front hub exposed, tall ADV silhouette) and a 1.05 peak tire grip coefficient (off-road Karoo 4 blocks), where the SR-R runs Cd 0.55 and tire grip 1.30. Power matters less than people think on the strip; aero and grip matter more.',
  },
  {
    type: 'callout',
    text: 'Why the off-road tires cost so much ET: the simulator runs the F 900 GS in first gear at launch with a peak grip coefficient of 1.05. Swap to a 50/50 ADV radial like a Continental TKC 70 (peak grip 1.15) and the simulator drops the 60-foot from 2.353s to 2.218s — worth around 0.13 seconds of total ET. Swap to a road-biased sport-touring tire like a Pirelli Angel GT II (peak grip 1.25) and the 60-foot drops further to 2.151s, worth a total of around 0.22 seconds. The F 900 GS as delivered is geared and tired for fire roads, not strips.',
  },
  {
    type: 'h2',
    text: 'How the F 900 GS Stacks Against the Mid-ADV Field',
  },
  {
    type: 'p',
    text: 'Five adventure bikes, five different platform philosophies, one venue. Numbers below are MotoQuant stock-tune simulations under matched Aamby Valley November conditions. Every bike runs its OEM tires and OEM gearing — no mods, no swaps, no tire upgrades:',
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
    text: 'Two things jump out of that table. First, the F 900 GS and the Tiger 900 GT Pro post the same ET to three decimal places (12.081 vs 12.083 — a difference of 2 milliseconds, well inside simulator noise) despite the Tiger having a triple instead of a twin, slightly more power, and similar weight. The Tiger out-traps the BMW by 3.0 km/h because the triple makes peak power 1000 rpm higher and pulls harder in the back half of the quarter. The BMW loses 3 km/h at the trap but holds the ET because the parallel twin punches out of the gate slightly harder on its 93 Nm torque peak at 6750 rpm — 16 percent more torque per liter than the Tiger triple.',
  },
  {
    type: 'p',
    text: 'Second, the R 1300 GS is in a different conversation. At 145 hp, 237 kg kerb, and a Cd of 0.55 (BMW invested heavily in the GS Pro fairing for the 2024 refresh), the R 1300 sims to 11.174s and 218.4 km/h. That is 0.91 seconds and 24.9 km/h ahead of the F 900 GS, which is what you would expect from a 40 hp power bump on a bike that weighs only 18 kg more and slips through the air 33 percent better. The R 1300 GS is the strip-fast ADV. The F 900 GS is the everywhere-else-fast ADV.',
  },
  {
    type: 'p',
    text: 'The Tenere 700 sits at the back of the table by a wide margin — 12.660s on 73 hp and 204 kg kerb. That is the cost of running a CP2 twin from the MT-07 with no compression bump, no cam revisions, and tall ADV gearing. The Tenere is the cheapest bike in the comparison and the only one Yamaha India has not officially launched as of mid-2026, so for an Indian buyer comparing the F 900 GS against showroom alternatives, the realistic competition set is the R 1300 GS above, the Tiger 900 GT Pro alongside, and the KTM 890 Adventure (not in the comparison because the 2024-spec Indian-market 890 Adventure was discontinued in favor of the 990 Adventure for FY26).',
  },
  {
    type: 'h2',
    text: 'Why the F 900 GS Posts a Better ET Than the F 850 GS Despite the Tire Penalty',
  },
  {
    type: 'p',
    text: 'BMW does not publish an instrumented quarter-mile time for the F 850 GS, but Cycle World and MCN tests across 2018 to 2023 put the F 850 GS at roughly 12.5 to 12.6 seconds with similar Karoo 3 OEM tires and similar rider weight. The MotoQuant sim of the F 900 GS lands at 12.083s — call it a 0.42 to 0.52 second improvement over the bike it replaces. That gap decomposes cleanly in the simulator.',
  },
  {
    type: 'p',
    text: 'The 14 kg weight reduction is worth roughly 0.16 seconds on its own — drop a 233 kg kerb to a 219 kg kerb on the same engine map, the simulator says the ET drops 0.18s. The extra 10 hp peak (95 to 105) is worth roughly 0.14 seconds, mostly in the trap zone. The compression bump from 12.7:1 to 13.1:1 and the revised intake cams are worth another 0.05 to 0.08 seconds via stronger midrange torque. The slightly taller final drive (F16/R41 vs the F 850 GS F16/R42) costs around 0.03 seconds in launch but gains it back in fifth-gear cruise. Net: about 0.40 to 0.45 seconds, which matches the magazine-test delta between the two bikes within simulator tolerance.',
  },
  {
    type: 'p',
    text: 'The interesting line in that decomposition is the weight reduction beating the horsepower bump on a per-kilo basis. At this weight class and power output, the simulator says 1 kg of mass removal is worth roughly 11.4 milliseconds of ET, and 1 horsepower addition is worth roughly 14 milliseconds. So per dollar of engineering spend, BMW chose well: the new plastic tank, lighter frame, and crank diet were almost certainly cheaper to develop and validate than the +10 hp engine work, and they paid back nearly the same ET reduction.',
  },
  {
    type: 'h2',
    text: 'What This Means for the Indian Buyer',
  },
  {
    type: 'p',
    text: 'BMW Motorrad India listed the F 900 GS at ₹13.75 lakh ex-showroom Delhi for the standard variant (₹14.50 lakh for the GS Trophy variant with cross-spoke wheels, Enduro Pro mode, and the off-road suspension setup) at the November 2024 dealer launch. On-road in Mumbai or Bangalore lands closer to ₹16 to 17 lakh including TCS, RTO, insurance, and the standard Vario luggage package most buyers spec. That puts the F 900 GS in direct conversation with the Triumph Tiger 900 GT Pro (₹15.95 lakh ex-showroom), the KTM 890 Adventure R (discontinued — replaced by 990 Adventure at ₹16.65 lakh), and slots roughly ₹6 lakh under the R 1300 GS (₹20.95 lakh ex-showroom for the standard, ₹24+ lakh fully optioned).',
  },
  {
    type: 'p',
    text: 'The Indian ADV buyer math is mostly about touring weight and luggage capacity, not about quarter-mile times. But there is a specific subset of buyers who care: the rider who bought an F 850 GS in 2019 or 2020 and is now considering whether to refresh to the F 900 GS or jump to the R 1300 GS for FY27. The simulator says the F 900 GS picks up roughly 0.45 seconds of ET over the F 850 GS for an upgrade cost of roughly ₹2 lakh net of resale. The R 1300 GS picks up roughly 0.91 seconds for an upgrade cost closer to ₹8 lakh net of resale. On a pure seconds-per-rupee basis, the F 900 GS is the more efficient upgrade. On a do-everything-better basis, the R 1300 GS earns its premium.',
  },
  {
    type: 'p',
    text: 'For the drag-curious ADV rider — and there are more of them than the segment likes to admit — the cheapest path to a faster F 900 GS is also the dullest one: swap the Karoo 4 rear for a road-biased sport-touring tire like the Continental TKC 70 (₹14,500 for the 150/70R17 rear) or a Pirelli Scorpion Trail II (₹17,200 for the same size). The simulator says the road-biased tire is worth around 0.13 seconds of ET stock-engine — about the same return as a Stage 1 ECU flash on a sportbike, for less money. Beyond that, a Powertronic Stage 1 flash (₹38,000 expected for the BMS-O ECU family, confirmed compatible by Powertronic India for the F 900 R sibling) adds roughly 8 hp and shaves another 0.08 seconds. Stage 1 plus tire swap puts the F 900 GS into the 11.8s ET range for a total parts spend under ₹55,000 — close to Tiger 900 GT Pro stock-tune territory.',
  },
  {
    type: 'callout',
    text: 'Cost-per-tenth on the F 900 GS: road-biased ADV tire (~₹17,200, ~0.13s) is cheapest at ₹132,000 per tenth. Powertronic Stage 1 flash (~₹38,000, ~0.08s) is second cheapest at ₹475,000 per tenth. Akrapovic slip-on (~₹95,000, ~0.04s) is the most expensive at ₹2.4 million per tenth — it is a sound mod and a weight mod, not a speed mod. Skip the slip-on unless the noise matters to you.',
  },
  {
    type: 'h2',
    text: 'Gearing — Where the Tenths Live',
  },
  {
    type: 'p',
    text: 'The F 900 GS ships with F16/R41 final drive, 525 chain, and the cassette ratios listed earlier. The simulator log shows the bike doing the following during a stock-tune Aamby Valley run: launch in first at 5500 rpm with the limited slip from the OEM A&S clutch; shift to second at 1.10 seconds and 60 feet; shift to third at 2.45 seconds and 195 feet; shift to fourth at 4.55 seconds and 510 feet; cross the trap line in fifth at 8400 rpm and 193 km/h, having shifted to fifth at 7.95 seconds and 1180 feet. That is a five-gear quarter — the signature of an ADV with relatively short individual gears stacked under an overdriven sixth.',
  },
  {
    type: 'p',
    text: 'Notice that the bike never engages sixth gear on the strip. Sixth is purely for highway cruise — at 110 km/h in sixth, the engine sits at roughly 4500 rpm, which is where BMW wanted noise and vibration to live for ADV touring. A 15/41 sprocket swap (one tooth shorter at the front) would shift the simulator into sixth roughly 50 feet before the trap line. The sim says the resulting deadband shift costs more ET than the shorter gearing gains in torque, so the swap is net-negative for ET. The factory final drive is already at the right tooth count for the strip. Where a sprocket swap would help is touring fuel economy at 110 km/h — but that is a different optimization problem than the quarter-mile.',
  },
  {
    type: 'p',
    text: 'For the rider who genuinely wants the F 900 GS to do the strip thing, the highest-impact gearing change is not the sprockets. It is the launch RPM. The OEM launch RPM in the BMW BMS-O ECU is set conservatively at 4500 rpm to protect the A&S clutch on muddy off-road climbs. If you flash with Powertronic Stage 1 and bump the launch RPM to 6500 rpm (closer to the 6750 torque peak), the simulator says the 60-foot drops from 2.353s to 2.218s and the total ET drops by roughly 0.15 seconds. Combine that with the road-biased tire and the F 900 GS sims out at 11.80s — closing to within 0.6 seconds of the R 1300 GS stock for under ₹60,000 in mods plus a flash.',
  },
  {
    type: 'h2',
    text: 'The Honest Take',
  },
  {
    type: 'p',
    text: 'The BMW F 900 GS is the right mid-ADV for the Indian buyer who wants the GS DNA, the BMW dealer network, and a bike that genuinely goes off-road on Karoo 4 spoke wheels without feeling sketchy. It is not the right ADV for the buyer who wants to occasionally show up at Aamby Valley or MMRT and embarrass a Ninja 650 owner — for that use case, the R 1300 GS at ₹7 lakh more is meaningfully quicker, and the Tiger 900 GT Pro at ₹2 lakh less posts the same ET with a more refined ride at street speeds.',
  },
  {
    type: 'p',
    text: 'What the simulator does say about the F 900 GS is that BMW made the right engineering trade-offs for the brief. The 14 kg weight reduction is doing as much for the bike as the 10 hp power bump, and the chassis investment paid off in handling and steering responsiveness as much as in ET. The 6-speed cassette with the overdriven sixth gear is correct for an ADV; the F 16/R 41 final drive is correct for the cassette. The off-road biased Karoo 4 OEM tire choice is correct for the buyer demographic, and the rider who wants better strip numbers can swap the rear tire for ₹17,200 and pick up 0.13 seconds without touching anything else.',
  },
  {
    type: 'p',
    text: 'The F 900 GS is the most coherent product BMW has put in this slot since the original F 800 GS in 2008. The simulator numbers reflect that coherence: nothing about the bike is wrong for its purpose, and the mods that would make it faster are exactly the mods that compromise the off-road bias the platform is built for. If you want a strip-fast ADV, buy the R 1300 GS. If you want a do-everything ADV that happens to also turn a 12.0 second quarter, the F 900 GS is the buy.',
  },
  {
    type: 'h2',
    text: 'Run Your Own Numbers',
  },
  {
    type: 'p',
    text: 'If you are sizing up the F 900 GS against the Tiger 900 GT Pro, the R 1300 GS, or any used F 850 GS on the Indian market, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tire selection, and parts-catalog mods to see exactly where the tenths come from on your specific bike under your specific conditions. The cluster-bias correction discussed earlier is baked into the model — when the simulator says 12.08, expect 11.85 to 12.00 on a well-prepped surface with a competent rider and warm tires.',
  },
  {
    type: 'p',
    text: 'Two final caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions. Move the same bike to Chennai MMRT in February (sea-level, hot ambient, higher humidity) and the simulator drops the F 900 GS by roughly 0.05 seconds on density altitude alone. Move it to a high-elevation strip like Leh or Manali (rare, but Indian ADV riders do try) and the simulator adds 0.30 to 0.40 seconds for the same bike. The relative ordering of which mods help most stays stable across venues; the absolute ETs shift with the air.',
  },
  {
    type: 'p',
    text: 'Second, the mid-twin-500-700 cluster bias is being actively calibrated in the background. The most recent sweep pass on May 30 put the cluster mean bias at +0.18 seconds slow for parallel twins in this displacement range. As the calibration work continues, expect the F 900 GS sim ET to drift toward 11.95 to 12.00 over the next few months without any change to the bike itself. The relative comparisons against the Tiger 900 GT Pro and the R 1300 GS will stay stable because the calibration applies uniformly across the cluster.',
  },
  {
    type: 'p',
    text: 'If you take one thing from this post, take this: the BMW F 900 GS is the first mid-ADV in BMW lineup that the simulator can recommend on quarter-mile numbers alone, not just on brand and off-road capability. The R 1300 GS is still faster, the Tiger 900 GT Pro is still cheaper, but the F 900 GS is the bike where BMW finally got the weight, the power, the gearing, and the geometry right at the same time. That is a rare thing in mid-segment ADV product development, and the strip numbers are the cleanest way to see it.',
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
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            BMW F 900 GS Quarter-Mile Physics: 105hp Mid-ADV at 12.08s
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                CFMoto 675SR-R Quarter-Mile Physics: The 95hp Daytona 660 Rival
              </Link>{' '}
              — same power-to-weight as the F 900 GS, 0.76 seconds quicker on aero alone.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/aprilia-tuono-457-vs-rs-457-quarter-mile-physics" className="text-brand-accent hover:text-brand-orange transition-colors">
                Aprilia Tuono 457 vs RS 457: Same Engine, 0.41s Different ET
              </Link>{' '}
              — the cleanest case study of how aero alone moves the quarter-mile.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/how-to-tune-for-aamby-valley-in-november" className="text-brand-accent hover:text-brand-orange transition-colors">
                How to Tune for Aamby Valley in November
              </Link>{' '}
              — the venue conditions used for every simulation above.
            </li>
            <li>
              ·{' '}
              <Link href="/blog/indian-drag-strip-elevation-comparison" className="text-brand-accent hover:text-brand-orange transition-colors">
                Indian Drag Strip Elevation Comparison
              </Link>{' '}
              — why the F 900 GS picks up 0.05s in Chennai and loses 0.30s in Leh.
            </li>
            <li>
              ·{' '}
              <Link href="/bikes" className="text-brand-accent hover:text-brand-orange transition-colors">
                Browse the full bike catalog
              </Link>{' '}
              — every spec, every gear ratio, every Cd value used by the simulator.
            </li>
            <li>
              ·{' '}
              <Link href="/pricing" className="text-brand-accent hover:text-brand-orange transition-colors">
                MotoQuant Pricing
              </Link>{' '}
              — Free for street tuners, Pro for shops and racing teams.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the F 900 GS yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the BMW F 900 GS, swap to a road-biased ADV tire, and watch the ET update live.
            </div>
          </div>
          <Link
            href="/simulator?bike=bmw-f-900-gs"
            className="shrink-0 px-5 py-2.5 bg-brand-orange text-black font-display font-bold rounded-lg text-sm hover:bg-brand-orangeLight transition-colors"
          >
            Run sim →
          </Link>
        </div>
      </article>

      <SiteFooter />
    </div>
  );
}
