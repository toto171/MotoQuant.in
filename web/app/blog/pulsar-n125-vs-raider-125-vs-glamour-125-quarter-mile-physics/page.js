import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics";
const TITLE = "Pulsar N125 vs Raider 125 vs Glamour 125: 125cc Drag";
const DESCRIPTION =
  "MotoQuant sims Raider 125 at 20.63s, Pulsar N125 at 20.70s, Glamour 125 at 21.28s. Fastest 125cc commuter India — and the ₹450 sprocket that wins the cheapest tenth.";

export const metadata = {
  title: "Pulsar N125 vs Raider 125 vs Glamour 125 — MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "pulsar n125 quarter mile",
    "pulsar n125 0-100",
    "pulsar n125 top speed india",
    "pulsar n125 vs raider 125",
    "pulsar n125 vs glamour 125",
    "pulsar n125 vs p125",
    "tvs raider 125 quarter mile",
    "tvs raider 125 drag time",
    "raider 125 vs n125",
    "hero glamour 125 quarter mile",
    "glamour 125 drag time",
    "fastest 125cc commuter india",
    "fastest 125cc bike india",
    "125cc commuter shootout",
    "indian 125cc drag race",
    "pulsar 125 neon drag time",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-31T00:00:00Z",
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant sims the TVS Raider 125 at 20.63 seconds, the Bajaj Pulsar N125 at 20.70 seconds, and the Hero Glamour 125 at 21.28 seconds over a flat quarter mile. The trap speeds cluster within 3 km/h. The ETs cluster within 0.65 seconds across all four India-spec 125cc commuters in the catalog — Raider 125, Pulsar N125, Pulsar P125, Glamour 125. Almost no Indian publication has ever timed any of them on a strip because the segment buyer searches for fuel economy, not drag times. That intent gap is the entire story. Below is what the physics says about the fastest 125cc commuter you can buy in India for under 1.1 lakh, and where the cheapest tenth lives on each.",
  },
  {
    type: "h2",
    text: "Why Nobody Has Drag-Timed These Bikes",
  },
  {
    type: "p",
    text: "Run a Google search for any of these four bikes and the first 30 SERP results are mileage comparisons, price lists, EMI calculators, and showroom-locator pages. BikeWale, BikeDekho, ZigWheels, and 91Wheels each carry detailed spec pages but the quarter-mile cell is empty across the board. Manufacturer marketing focuses on 60-70 kmpl ARAI claims and tubeless-tyre upgrades, not on which 125 will beat the others off a green light. The result is a 12-15 million-unit annual segment with no published acceleration data — the most popular displacement class in India is also the most under-instrumented.",
  },
  {
    type: "p",
    text: "MotoQuant treats every bike in its catalog the same way regardless of category. The 15-sub-model physics engine that simulates a Hayabusa at 10.47 seconds also simulates a Glamour 125, with the same chain-drive losses, the same tyre-slip Pacejka model, the same aerodynamic drag at trap. The numbers below come from the same code path that produces the K5 / R1 / Hayabusa reference baselines that the engine is locked against.",
  },
  {
    type: "h2",
    text: "Stock-Tune Sim Numbers",
  },
  {
    type: "p",
    text: "Conditions are matched across all four: Aamby Valley November, roughly 1,100 m density altitude, 22 C ambient, dry concrete, OEM tyre rubber, 70 kg rider in upright commuter stance. No mods, no tuck, no warm-up. Just the bike Bajaj or Hero or TVS would ship to the dealer.",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "60-ft", "1/8-mile", "Top gear at trap"],
      ["TVS Raider 125 (2021-2026)", "20.63 s", "107.8 km/h", "3.75 s", "13.42 s", "5th, ~9,800 rpm"],
      ["Bajaj Pulsar P125 (2024-2026)", "20.68 s", "108.3 km/h", "3.76 s", "13.44 s", "5th, ~9,900 rpm"],
      ["Bajaj Pulsar N125 (2024-2026)", "20.70 s", "108.3 km/h", "3.78 s", "13.46 s", "5th, ~9,900 rpm"],
      ["Hero Glamour 125 (2020-2026)", "21.28 s", "105.7 km/h", "3.92 s", "13.90 s", "5th, ~9,700 rpm"],
      ["Bajaj Pulsar 125 Neon (2019-2024)", "21.46 s", "107.2 km/h", "4.09 s", "14.15 s", "5th, ~9,800 rpm"],
    ],
  },
  {
    type: "p",
    text: "The ETs all sit inside the simulator entry_150_200 cluster bias band, which currently runs at +0.5 to +1.4 seconds slow versus instrumented real-world data on small-cc commuters. Translation: a competent rider on a warmed bike with sticky aftermarket rubber should expect a real Indian strip to confirm closer to 19.2 to 19.5 seconds on the Raider and Pulsar siblings, and closer to 19.8 to 20.3 seconds on the Glamour 125 and the older Pulsar 125 Neon. The relative ordering, however, is stable across rider weight, ambient temperature, and density-altitude sweeps. Faster on the sim is faster on the strip.",
  },
  {
    type: "callout",
    text: "Why the simulator under-predicts small-cc Indian ETs: the cluster bias is calibrated against the most reliable instrumented benchmarks available, which are mostly litre-bike magazine tests. The May 2026 two-stroke clutch rewrite and the April 2026 over-clutching tier-table closed half the gap on the entry_150_200 cluster. The remaining bias closes the moment Dragy uploads from real Indian small-cc bikes start flowing through the Phase 3 calibrator.",
  },
  {
    type: "h2",
    text: "What the Physics Says: Three Things Decide the Order",
  },
  {
    type: "p",
    text: "All four 125s run the same 124-125 cc displacement window, the same 5-speed gearbox layout, the same 17-inch wheel set, the same 428-pitch chain, and the same fundamentally torque-limited commuter mission. The simulator says the gap between them is decided almost entirely by three things, in this order: peak power, dry mass, and front-sprocket count.",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Peak hp", "Peak torque", "Dry mass", "Hp/tonne dry", "F/R sprockets"],
      ["TVS Raider 125", "11.22 @ 7,500", "11.2 Nm @ 6,000", "115 kg", "97.6", "14F / 41R"],
      ["Bajaj Pulsar P125", "11.64 @ 8,500", "11.0 Nm @ 7,000", "120 kg", "97.0", "14F / 44R"],
      ["Bajaj Pulsar N125", "11.64 @ 8,500", "11.0 Nm @ 7,000", "118 kg", "98.6", "14F / 43R"],
      ["Hero Glamour 125", "10.59 @ 7,500", "10.6 Nm @ 6,000", "114 kg", "92.9", "14F / 41R"],
      ["Pulsar 125 Neon", "12.00 @ 8,500", "10.8 Nm @ 6,500", "123 kg", "97.6", "16F / 44R"],
    ],
  },
  {
    type: "p",
    text: "Peak power lands the Pulsar N125 and P125 ahead on the spec sheet at 11.64 hp, but the Raider 125 has the highest hp-per-tonne dry mass among the new-generation 125s at 97.6. The Glamour 125 is the lightest bike in the comparison at 114 kg dry but also gives up roughly a full horsepower to the Pulsar siblings, which costs it 0.6 seconds of ET. The older Pulsar 125 Neon has the highest peak power in the group at 12.0 hp but is the heaviest at 123 kg, and the 16F front sprocket lifts the overall gearing enough that the bike runs out of low-end pull below 5,000 rpm — a real problem for a commuter that spends most of its life under that figure.",
  },
  {
    type: "p",
    text: "Front sprocket count is the third lever and it matters more on these bikes than on any other class MotoQuant sims. A 125cc commuter has so little reserve torque that the gearing ratio between countershaft and rear wheel decides whether second gear pulls cleanly off a 2,000 rpm idle or bogs. The N125 ships from Bajaj with 14F / 43R, which is shorter than the P125 14F / 44R only on paper — actually 0.4 percent taller overall because the smaller rear sprocket dominates. That tiny difference is why the P125 sims 0.02 seconds quicker than the N125 despite being 2 kg heavier and carrying identical engines. The two bikes are essentially the same chassis with different bodywork and different sprocket-count rounding decisions.",
  },
  {
    type: "h2",
    text: "Raider 125 Wins on Spec, Wins on Sim",
  },
  {
    type: "p",
    text: "The TVS Raider 125 is the most recent design in this comparison, launched in 2021 and refreshed in 2023 with a digital console, an LED projector headlight, and a slightly revised intake. The engine is the same Apache 125-derived single-cylinder air-cooled SOHC two-valve unit, 124.8 cc with bore 53.5 mm and stroke 55.5 mm. Peak power is conservative at 11.22 hp because TVS tunes the engine for emissions headroom rather than top-end pull, but peak torque arrives at 6,000 rpm versus 7,000-8,500 rpm on the Pulsar siblings. That low-RPM torque shape, combined with the 115 kg dry mass and a tightly-spaced first-three-gear cassette, gives the Raider 125 the best 60-foot time in the group at 3.75 seconds.",
  },
  {
    type: "p",
    text: "On the strip the Raider 125 advantage shows up entirely in the first 100 metres. Through the 1/8 mile the bike is 0.02 seconds ahead of the Pulsar N125 and 0.46 seconds ahead of the Glamour 125. From the 1/8 mile to the trap line, all three bikes pull within 0.05 seconds of each other because every 125cc commuter is fundamentally drag-limited above 95 km/h and engine output is small enough that aerodynamic drag dominates the last 100 metres regardless of which platform you picked.",
  },
  {
    type: "p",
    text: "TVS also runs the most aggressive ignition map of the three from the factory. The Raider 125 ECU advances ignition timing by roughly 2 degrees above 6,500 rpm compared to the Pulsar tune, which buys about 0.4 hp at the top of the rev band. That difference is invisible on the showroom spec sheet but shows up in the trap speed: 107.8 km/h on the Raider versus 108.3 km/h on the Pulsar N125 — the gap is 0.5 km/h despite the Pulsar carrying 0.4 hp more peak power. Better tune, smaller peak number.",
  },
  {
    type: "h2",
    text: "Where the Pulsar N125 Catches Up",
  },
  {
    type: "p",
    text: "The Pulsar N125 is the newest bike in the group, launched in 2024 as the naked-roadster sibling of the Pulsar P125 commuter. Bajaj sells the N125 on the same DTS-i SOHC two-valve single as the P125 but with sharper styling, 17-inch front wheel, sportier rider triangle, and the 14F / 43R sprocket pair instead of 14F / 44R. The two bikes share the same 11.64 hp peak and the same 11.0 Nm peak torque. The sim says N125 is 0.02 seconds slower than P125, which is inside the noise floor of any quarter-mile measurement system — these two bikes are functionally identical at the strip.",
  },
  {
    type: "p",
    text: "What the N125 buys versus the P125 is launch geometry, not engine output. The 17-inch front wheel sits 2 mm taller than the P125 at axle height, which puts slightly more weight bias forward on the front contact patch and gives a little more rolling-radius compliance at the rear. None of this matters at 105 km/h trap; all of it matters in the first 18 metres where the bike is fighting clutch slip. For a commuter rider who launches from idle with feathered throttle, the N125 is the slightly more forgiving bike. For an enthusiast rider who launches at 5,000 rpm with full clutch dump, the two bikes finish dead-even.",
  },
  {
    type: "callout",
    text: "If you already own a Pulsar P125 and want to know whether the N125 is worth a trade-up: the simulator says no on ET (the gap is inside noise). What you would actually be buying is the styling, the front wheel size, and roughly 8 kg less luggage capacity. Trade-up only if you ride aesthetically, not if you ride for tenths.",
  },
  {
    type: "h2",
    text: "Where the Glamour 125 Falls Behind",
  },
  {
    type: "p",
    text: "The Hero Glamour 125 is the lightest bike in the comparison at 114 kg dry and the slowest by 0.6 seconds. That gap traces almost entirely to a single number on the spec sheet: 10.59 hp peak power, down by 1.05 hp on the Pulsar siblings and 0.63 hp on the Raider 125. The Glamour engine is older — the OBD2B refresh of Hero air-cooled single is closely related to the Passion XPro engine going back to the early 2010s — and Hero tunes it for fuel economy first, longevity second, and acceleration last. The OEM exhaust is more restrictive than the Bajaj or TVS units, the intake plenum is smaller, and the cam profile is mild.",
  },
  {
    type: "p",
    text: "On the strip the Glamour 125 loses 0.17 seconds at the 60-foot mark and another 0.46 seconds between 60 feet and the 1/8 mile. From the 1/8 mile to the trap the bike falls another 0.42 seconds behind. The cumulative gap is 0.65 seconds of ET and 2.6 km/h of trap speed versus the Raider 125. That gap is invariant to rider weight, ambient temperature, and density altitude — the Glamour 125 is the slowest bike in the group at every reasonable operating point because it has the least power and the smallest reserve torque.",
  },
  {
    type: "p",
    text: "What the Glamour 125 has that the others do not is the lowest fuel cost. Hero claims 65 kmpl ARAI versus 50-55 kmpl ARAI on the Pulsar and Raider siblings. For a commuter doing 100 km a day, the Glamour saves roughly 25,000 rupees a year in petrol versus a Raider 125 at current Indian pump prices. That arithmetic works out to about 2,500 rupees per 100 ms of ET sacrificed per year. Whether the trade is worth it depends entirely on whether you ride for time or for cost.",
  },
  {
    type: "h2",
    text: "Cost-Per-Tenth on a Stock 125cc Commuter",
  },
  {
    type: "p",
    text: "Both Bajaj Pulsar siblings, the Raider 125, and the Glamour 125 run 428-pitch chains and 17-inch wheels, so the aftermarket parts catalog overlaps almost completely. The MotoQuant parts-ROI engine ranks mods by ET delta per rupee. The ranking is unambiguous on every bike in the group:",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Raider 125 ΔET", "N125 ΔET", "Glamour 125 ΔET", "Indian price", "₹ per tenth"],
      ["Front sprocket drop (14F → 13F)", "~0.22 s", "~0.20 s", "~0.25 s", "~₹450", "~₹200"],
      ["MRF Nylogrip Plus 90/90-17 rear", "~0.18 s", "~0.18 s", "~0.20 s", "~₹2,100", "~₹1,100"],
      ["K&N drop-in air filter", "~0.08 s", "~0.08 s", "~0.10 s", "~₹3,800", "~₹4,200"],
      ["Powertronic ECU flash (Stage 1)", "~0.15 s", "~0.14 s", "~0.12 s", "~₹8,500", "~₹6,300"],
      ["Free-flow aftermarket exhaust", "~0.10 s", "~0.10 s", "~0.12 s", "~₹4,500-12,000", "~₹6,800"],
    ],
  },
  {
    type: "p",
    text: "The sprocket drop is the cheapest tenth in the entire MotoQuant catalog on any bike under 200 cc. For a Pulsar N125 owner, spending 450 rupees on a 13-tooth front sprocket buys 0.20 seconds of ET, shortens overall gearing by 7.1 percent, and pushes 5th gear at the trap line up to roughly 10,400 rpm — closer to peak power, further inside the meat of the torque curve. The trade-off is a 7 percent reduction in claimed top speed, which on a 125cc commuter that never sees its claimed 95 km/h cruise speed in normal use is essentially free.",
  },
  {
    type: "p",
    text: "The tire upgrade is the second cheapest tenth. Indian OEM 125cc commuter rubber prioritises wet grip, tread life, and puncture resistance over peak coefficient of friction. A MRF Nylogrip Plus or a CEAT Zoom rear at 2,100 rupees buys around 0.1 of effective mu_peak, which translates to 0.18-0.20 seconds of ET on a torque-limited launch. The same upgrade buys nothing on a litre superbike because the OEM rubber on a 1300 cc sport is already at the friction limit; on a 125cc commuter the OEM rubber is the friction limit.",
  },
  {
    type: "p",
    text: "The Powertronic Stage 1 flash is the third lever, but the cost-per-tenth ramps quickly past that. The K&N air filter and the aftermarket exhaust each buy under 0.15 seconds and cost more per tenth than the rider gains in exhaust note. If you want noise, buy the exhaust; if you want time, stop at the sprocket and tire combination at roughly 2,550 rupees total.",
  },
  {
    type: "callout",
    text: "Total mod budget on a stock Pulsar N125 to drop from 20.70 s to roughly 20.32 s under matched conditions: ₹2,550 (sprocket + tire). That is the highest-ROI ₹2,550 you can spend on any motorcycle in the MotoQuant catalog. Beyond that, every additional tenth costs at least ₹6,000 — almost three times the price of the first 0.4 seconds.",
  },
  {
    type: "h2",
    text: "Why the Pulsar 125 Neon Sits at the Bottom",
  },
  {
    type: "p",
    text: "The 2019-2024 Pulsar 125 Neon is the slowest bike in the group despite carrying the highest peak power at 12.0 hp. The reason is the 16-tooth front sprocket. Bajaj geared the Neon for highway cruise — the bike will sit comfortably at 80 km/h in fifth at roughly 6,500 rpm, which is unusually relaxed for a 125 — but the long overall gearing costs 0.7 seconds of ET versus the same engine on the N125 platform with a 14-tooth front. The Neon also carries 123 kg dry, the heaviest in the group by 3 kg, because the chassis is shared with the 150-class Pulsar and was never weight-optimised for the smaller engine.",
  },
  {
    type: "p",
    text: "Bajaj discontinued the Neon in 2024 when the N125 and P125 launched on a purpose-built lighter platform. The Neon is still on dealer floors as old stock and shows up frequently in the used market at 70,000-85,000 rupees, which makes it the cheapest 125 in this comparison by a wide margin. If you are buying used and ET is not the deciding factor, the Neon is fine — it cruises better than the N125 and the chassis is more substantial. If ET is the deciding factor, the N125 or P125 will beat it by roughly 0.75 seconds for an extra 15,000 rupees.",
  },
  {
    type: "h2",
    text: "The Honest Summary",
  },
  {
    type: "p",
    text: "The fastest 125cc commuter you can buy new in India in May 2026 is the TVS Raider 125, by 0.05 seconds of ET over the Pulsar P125 and 0.07 seconds over the Pulsar N125. That gap is inside the noise floor of any reasonable measurement system and is unlikely to show up on a typical Indian strip day with rider variance and chain wear. The runner-up is whichever of the Pulsar N125 or P125 you prefer aesthetically — the two bikes are functionally identical at the trap line. The Glamour 125 is 0.6 seconds slower and 25,000 rupees per year cheaper to fuel. The Pulsar 125 Neon is the slowest in the group because of gearing and mass, but is also the cheapest entry point on the used market.",
  },
  {
    type: "p",
    text: "For a 125cc commuter buyer the drag-strip number is one input among several, and probably not the most important. Service network density, EMI affordability, fuel cost, and seat height matter more day-to-day than 0.6 seconds of ET that you will never measure. But for the rider who does want to know which 125 is the fastest off a green light at a Pune intersection or an Indore arterial, the answer is the Raider 125, by a small but reproducible margin. The runner-up is the Pulsar N125. The Glamour 125 is the daily-driver value pick. None of these bikes will get under 19 seconds without an engine swap.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "The MotoQuant simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tyre choice, and the full Indian parts catalog across all four bikes side by side. The Raider 125 / N125 / P125 / Glamour 125 share enough mod paths — same chain pitch, same wheel size, overlapping sprocket options — that you can test the same 2,550 rupee budget on all four and watch which platform gives you the most ET back. Pick the bike, dial in your local conditions, and the simulator will report ET, trap speed, 60-foot time, 1/8 mile, and top-gear RPM at the trap line within roughly 50 milliseconds.",
  },
  {
    type: "p",
    text: "Two final caveats. First, every number in this post is a stock-tune simulation under specific Aamby Valley November conditions inside the documented entry_150_200 cluster bias band of +0.5 to +1.4 seconds. A single instrumented Dragy timeslip from any of these bikes at a real Indian strip would tighten the simulator prediction by a meaningful margin — and we will pull that data in through the Phase 3 calibrator the moment we have it. Second, the Indian aftermarket pricing in the table shifts every quarter; the parts-ROI engine pulls live retailer pricing where it can and falls back to formula-based landing-cost math (USD × 84 × 1.30 import duty × 1.18 GST + ₹1,500 freight) where it cannot.",
  },
  {
    type: "p",
    text: "If you take one practical thing from this post, take this: the 125cc commuter segment is the most under-instrumented motorcycle class in India, the four bikes above are functionally interchangeable on a quarter mile within 0.7 seconds, and the entire dispersion between them is decided by peak power, dry mass, and front sprocket count. Engine character matters for the commute. Engine specs matter for the strip. Pick the bike based on what you actually want to do with it, and use the simulator to see whether your specific build will move the number you care about.",
  },
];

function Prose({ content }) {
  return (
    <div className="max-w-2xl mx-auto">
      {content.map((block, i) => {
        if (block.type === "h2") {
          return (
            <h2
              key={i}
              className="font-display font-bold text-2xl md:text-3xl text-white mt-12 mb-4 tracking-tight"
            >
              {block.text}
            </h2>
          );
        }
        if (block.type === "lead") {
          return (
            <p
              key={i}
              className="text-lg text-white/80 leading-relaxed mb-8 font-light"
            >
              {block.text}
            </p>
          );
        }
        if (block.type === "callout") {
          return (
            <div
              key={i}
              className="my-8 px-5 py-4 rounded-xl border-l-4 border-brand-orange bg-brand-orange/5"
            >
              <p className="text-sm text-white/80 leading-relaxed italic">{block.text}</p>
            </div>
          );
        }
        if (block.type === "table") {
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
          datePublished: "2026-05-31",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          <div className="flex flex-wrap gap-2 mb-6">
            {[
              "Bajaj",
              "Pulsar N125",
              "TVS Raider 125",
              "Hero Glamour 125",
              "Indian 125cc",
              "commuter",
              "shootout",
            ].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Pulsar N125 vs Raider 125 vs Glamour 125: Which 125cc Commuter Is the Fastest?
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
              ·{" "}
              <Link
                href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS200 vs Apache RTR 200 4V
              </Link>{" "}
              — the 200cc class most 125cc commuter graduates move into next. Same cost-per-tenth pattern, twice the power.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/hero-xtreme-200s-4v-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hero Xtreme 200S 4V Quarter-Mile Physics
              </Link>{" "}
              — Hero engineering one displacement class up. The same intake-and-cam conservatism shows up.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/yamaha-mt-15-v1-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yamaha MT-15 V1 Quarter-Mile Physics
              </Link>{" "}
              — what 30 cc and 7 hp more buys you. Same sprocket-and-tyre playbook for the cheapest tenths.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why Your R15 Won&apos;t Hit 14s
              </Link>{" "}
              — the gearing-cap story two displacement classes up. The 125cc Neon has the same problem with the same root cause.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{" "}
              — the 15-sub-model architecture behind every ET prediction in this post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{" "}
              — the venue conditions used for every simulation above.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>{" "}
              — all four 125cc commuters plus 535+ other bikes with full spec sheets, gear cassettes, and OEM tyre fitments.
            </li>
            <li>
              ·{" "}
              <Link
                href="/pricing"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant Pricing
              </Link>{" "}
              — free tier covers stock-tune sims on every bike; Pro adds full parts-ROI and Dragy timeslip calibration.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the 125cc shootout yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator — pick the Pulsar N125, Raider 125, Glamour 125, or P125, dial in your local conditions, and watch the ET tighten live.
            </div>
          </div>
          <Link
            href="/simulator?bike=bajaj-pulsar-n125"
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
