import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "pulsar-n125-vs-raider-125-vs-glamour-125-quarter-mile-physics";
const TITLE = "Pulsar N125 vs Raider 125 vs Glamour 125: 125cc drag";
const DESCRIPTION =
  "The fastest 125cc commuter in India, by simulation: Raider 125 at 20.63s, Pulsar N125 at 20.70s, Glamour 125 at 21.28s. Plus the ₹450 sprocket that buys the cheapest tenth.";

export const metadata = {
  title: "Pulsar N125 vs Raider 125 vs Glamour 125 | MotoQuant",
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
    text: "MotoQuant sims the TVS Raider 125 at 20.63 seconds, the Bajaj Pulsar N125 at 20.70 seconds and the Hero Glamour 125 at 21.28 seconds over a flat quarter mile. Across all four India-spec 125cc commuters in the catalog (Raider 125, Pulsar N125, Pulsar P125, Glamour 125), trap speeds sit within 3 km/h of each other and ETs within 0.65 seconds. Almost no Indian publication has ever timed any of them on a strip, because people shopping for these bikes search for fuel economy, not drag times. The physics can still say which is the fastest 125cc commuter you can buy in India for under 1.1 lakh, and where the cheapest tenth is on each.",
  },
  {
    type: "h2",
    text: "Why nobody has drag-timed these bikes",
  },
  {
    type: "p",
    text: "Search Google for any of these four bikes and the first 30 results are mileage comparisons, price lists, EMI calculators and showroom-locator pages. BikeWale, BikeDekho, ZigWheels and 91Wheels all carry detailed spec pages, and the quarter-mile cell is empty on every one. Manufacturer marketing talks about 60-70 kmpl ARAI claims and tubeless-tyre upgrades, not about which 125 beats the others off a green light. So a segment that sells 12-15 million units a year has no published acceleration data. India's most popular displacement class is also its least measured.",
  },
  {
    type: "p",
    text: "MotoQuant treats every bike in its catalog the same way. The 15-sub-model physics engine that simulates the reference Hayabusa at 10.11 seconds also simulates the Glamour 125, with the same chain-drive losses, tyre grip model and aerodynamic drag at trap. The numbers below come from the same code path as the K5, R1 and Hayabusa reference baselines that the engine is locked against.",
  },
  {
    type: "h2",
    text: "Stock-tune sim numbers",
  },
  {
    type: "p",
    text: "All four run under the same conditions: Aamby Valley in November, roughly 1,100 m density altitude, 22 C ambient, dry asphalt, OEM tyres and a 70 kg rider in an upright commuter stance. No mods, no tuck, no warm-up: the bike as Bajaj, Hero or TVS ships it to the dealer.",
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
    text: "All of these ETs fall inside the simulator's entry_150_200 cluster bias band, which currently reads +0.5 to +1.4 seconds slow against instrumented real-world data on small-cc commuters. So a real Indian strip should confirm something closer to 19.2 to 19.5 seconds on the Raider and the Pulsar siblings, and 19.8 to 20.3 seconds on the Glamour 125 and the older Pulsar 125 Neon. That assumes a competent rider on a warmed bike with sticky aftermarket rubber. The order does not change when you sweep rider weight, ambient temperature or density altitude, so the bike that is faster on the sim is faster on the strip.",
  },
  {
    type: "callout",
    text: "Why the simulator under-predicts small-cc Indian ETs: the cluster bias is calibrated against the most reliable instrumented benchmarks available, and most of those are litre-bike magazine tests. The May 2026 two-stroke clutch rewrite and the April 2026 over-clutching tier-table closed half the gap on the entry_150_200 cluster. The rest of the bias closes as instrumented timeslips from real Indian small-cc bikes join the benchmark set.",
  },
  {
    type: "h2",
    text: "Three things decide the order",
  },
  {
    type: "p",
    text: "All four 125s share the 124-125 cc displacement window, a 5-speed gearbox, 17-inch wheels, a 428-pitch chain and a torque-limited commuter job. In the simulator, almost the whole gap between them comes from three things, in this order: peak power, dry mass and front-sprocket count.",
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
    text: "On the spec sheet the Pulsar N125 and P125 lead on peak power at 11.64 hp, but the Raider 125 has the highest hp per tonne of dry mass among the new-generation 125s at 97.6. The Glamour 125 is the lightest bike here at 114 kg dry, but it gives up roughly a full horsepower to the Pulsar siblings, and that costs it 0.6 seconds of ET. The older Pulsar 125 Neon makes the most peak power in the group at 12.0 hp but is also the heaviest at 123 kg. Its 16F front sprocket lifts the overall gearing so much that the bike runs out of low-end pull below 5,000 rpm, a real problem for a commuter that spends most of its life under that figure.",
  },
  {
    type: "p",
    text: "Front sprocket count is the third lever, and it matters more on these bikes than on any other class MotoQuant sims. A 125cc commuter has so little reserve torque that the ratio between countershaft and rear wheel decides whether second gear pulls cleanly off a 2,000 rpm idle or bogs. The N125 ships from Bajaj with 14F / 43R, which is shorter than the P125's 14F / 44R only on paper; it is actually 0.4 percent taller overall because the smaller rear sprocket dominates. That small difference is why the P125 sims 0.02 seconds quicker than the N125 despite being 2 kg heavier with an identical engine. The two are close to the same chassis with different bodywork and different sprocket choices.",
  },
  {
    type: "h2",
    text: "The Raider 125 wins on spec and on the sim",
  },
  {
    type: "p",
    text: "The TVS Raider 125 is the most recent design in this comparison: launched in 2021, then refreshed in 2023 with a digital console, an LED projector headlight and a slightly revised intake. The engine is the same Apache 125-derived air-cooled SOHC two-valve single, 124.8 cc, with a 53.5 mm bore and 55.5 mm stroke. Peak power is a conservative 11.22 hp because TVS tunes for emissions headroom rather than top-end pull, but peak torque arrives at 6,000 rpm against 7,000-8,500 rpm on the Pulsar siblings. That low-rpm torque, the 115 kg dry mass and closely spaced first three gears give the Raider 125 the best 60-foot time in the group at 3.75 seconds.",
  },
  {
    type: "p",
    text: "On the strip the Raider's whole advantage comes in the first 100 metres. At the 1/8 mile it is 0.02 seconds ahead of the Pulsar N125 and 0.46 seconds ahead of the Glamour 125. From the 1/8 mile to the trap line all three pull within 0.05 seconds of each other. Above 95 km/h every 125cc commuter is drag-limited: the engine makes so little power that aerodynamic drag decides the last 100 metres, whichever bike you picked.",
  },
  {
    type: "p",
    text: "TVS also ships the most aggressive factory ignition map of the three. The Raider 125 ECU runs roughly 2 degrees more advance above 6,500 rpm than the Pulsar tune, which buys about 0.4 hp at the top of the rev band. You will not see that on the showroom spec sheet. It shows in the trap speed: 107.8 km/h on the Raider against 108.3 km/h on the Pulsar N125. The gap is only 0.5 km/h, even though the Pulsar carries 0.4 hp more peak power.",
  },
  {
    type: "h2",
    text: "Where the Pulsar N125 catches up",
  },
  {
    type: "p",
    text: "The Pulsar N125 is the newest bike in the group, launched in 2024 as the naked-roadster sibling of the Pulsar P125 commuter. Bajaj builds it on the same DTS-i SOHC two-valve single as the P125, with sharper styling, a 17-inch front wheel, a sportier rider triangle and a 14F / 43R sprocket pair instead of 14F / 44R. Both make 11.64 hp and 11.0 Nm at peak. The sim has the N125 0.02 seconds slower than the P125, which is inside the noise floor of any quarter-mile measurement system. At the strip the two bikes are functionally identical.",
  },
  {
    type: "p",
    text: "What the N125 changes against the P125 is launch geometry. Its 17-inch front wheel sits 2 mm taller than the P125's at axle height, which puts slightly more weight on the front contact patch and gives a little more rolling-radius compliance at the rear. None of this matters at a 105 km/h trap. All of it matters in the first 18 metres, while the bike is fighting clutch slip. A commuter who launches from idle with a feathered throttle will find the N125 slightly more forgiving. An enthusiast who launches at 5,000 rpm with a full clutch dump will finish dead even on either.",
  },
  {
    type: "callout",
    text: "Own a Pulsar P125 and wondering whether to trade up to the N125? On ET the simulator says no; the gap is inside the noise. You would be paying for the styling, the front wheel size and roughly 8 kg less luggage capacity. Trade up for the looks, not for tenths.",
  },
  {
    type: "h2",
    text: "Where the Glamour 125 falls behind",
  },
  {
    type: "p",
    text: "The Hero Glamour 125 is the lightest bike in the comparison at 114 kg dry, and the slowest by 0.6 seconds. Almost all of that gap comes from one number on the spec sheet: 10.59 hp peak power, 1.05 hp down on the Pulsar siblings and 0.63 hp down on the Raider 125. The Glamour's engine is older; the OBD2B refresh of Hero's air-cooled single is closely related to the Passion XPro engine going back to the early 2010s. Hero tunes it for fuel economy first, longevity second and acceleration last. The OEM exhaust is more restrictive than the Bajaj or TVS units, the intake plenum is smaller and the cam profile is mild.",
  },
  {
    type: "p",
    text: "On the strip the Glamour 125 loses 0.17 seconds by the 60-foot mark and another 0.46 seconds between 60 feet and the 1/8 mile. From the 1/8 mile to the trap it falls another 0.42 seconds behind. The cumulative gap to the Raider 125 is 0.65 seconds of ET and 2.6 km/h of trap speed. Rider weight, ambient temperature and density altitude do not change it. With the least power and the smallest reserve torque, the Glamour 125 is the slowest bike in the group at every reasonable operating point.",
  },
  {
    type: "p",
    text: "What the Glamour 125 does have is the lowest fuel cost. Hero claims 65 kmpl ARAI, against 50-55 kmpl ARAI for the Pulsar and Raider siblings. A commuter doing 100 km a day saves roughly 25,000 rupees a year in petrol over a Raider 125 at current Indian pump prices. That works out to about 2,500 rupees a year for every 100 ms of ET you give up. Whether that trade is worth it depends on whether you ride for time or for cost.",
  },
  {
    type: "h2",
    text: "Cost per tenth on a stock 125cc commuter",
  },
  {
    type: "p",
    text: "Both Bajaj Pulsar siblings, the Raider 125 and the Glamour 125 run 428-pitch chains and 17-inch wheels, so their aftermarket parts overlap almost completely. MotoQuant's parts-ROI engine ranks mods by ET gained per rupee, and the order is clear on every bike in the group:",
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
    text: "The sprocket drop is the cheapest tenth in the MotoQuant catalog on any bike under 200 cc. On a Pulsar N125, 450 rupees for a 13-tooth front sprocket buys 0.20 seconds of ET. It shortens overall gearing by 7.1 percent and lifts 5th gear at the trap line to roughly 10,400 rpm, closer to peak power and deeper into the torque curve. You give up 7 percent of claimed top speed, which costs almost nothing on a 125cc commuter that never sees its claimed 95 km/h cruise speed in normal use.",
  },
  {
    type: "p",
    text: "The tyre upgrade is the second-cheapest tenth. OEM rubber on Indian 125cc commuters puts wet grip, tread life and puncture resistance ahead of peak friction. An MRF Nylogrip Plus or CEAT Zoom rear at 2,100 rupees adds around 0.1 to effective mu_peak, which is worth 0.18-0.20 seconds of ET on a torque-limited launch. The same upgrade buys nothing on a litre superbike, because the OEM rubber on a 1300 cc sport bike is already at the friction limit. On a 125cc commuter, the OEM rubber is the friction limit.",
  },
  {
    type: "p",
    text: "The Powertronic Stage 1 flash is the third lever, and the cost per tenth climbs fast after that. The K&N air filter and the aftermarket exhaust each buy under 0.15 seconds, at a cost per tenth that the louder exhaust note does not make up for. If you want noise, buy the exhaust. If you want time, stop at the sprocket and tyre, roughly 2,550 rupees in all.",
  },
  {
    type: "callout",
    text: "To take a stock Pulsar N125 from 20.70 s to roughly 20.32 s under matched conditions: ₹2,550 (sprocket + tyre). No ₹2,550 spent on any motorcycle in the MotoQuant catalog buys more. After that, every extra tenth costs at least ₹6,000, almost three times what the first 0.4 seconds cost.",
  },
  {
    type: "h2",
    text: "Why the Pulsar 125 Neon sits at the bottom",
  },
  {
    type: "p",
    text: "The 2019-2024 Pulsar 125 Neon is the slowest bike in the group even though it makes the most peak power, 12.0 hp. The 16-tooth front sprocket is why. Bajaj geared the Neon for highway cruising: it sits comfortably at 80 km/h in fifth at roughly 6,500 rpm, which is unusually relaxed for a 125. That long overall gearing costs 0.7 seconds of ET against the same engine on the N125 platform with a 14-tooth front. The Neon also carries 123 kg dry, the heaviest in the group by 3 kg, because it shares its chassis with the 150-class Pulsar and was never lightened for the smaller engine.",
  },
  {
    type: "p",
    text: "Bajaj discontinued the Neon in 2024, when the N125 and P125 launched on a lighter, purpose-built platform. It is still on dealer floors as old stock and turns up often on the used market at 70,000-85,000 rupees, which makes it the cheapest 125 in this comparison by a wide margin. If you are buying used and ET is not the deciding factor, the Neon is fine: it cruises better than the N125 and its chassis is more substantial. If ET does decide it, the N125 or P125 will beat it by roughly 0.75 seconds for an extra 15,000 rupees.",
  },
  {
    type: "h2",
    text: "The short answer",
  },
  {
    type: "p",
    text: "The fastest 125cc commuter you can buy new in India in May 2026 is the TVS Raider 125, by 0.05 seconds of ET over the Pulsar P125 and 0.07 seconds over the Pulsar N125. That gap is inside the noise floor of any reasonable measurement system, and rider variance and chain wear will probably hide it on a typical Indian strip day. Second place goes to whichever of the Pulsar N125 or P125 you like the look of; at the trap line the two are functionally identical. The Glamour 125 is 0.6 seconds slower and 25,000 rupees a year cheaper to fuel. The Pulsar 125 Neon is the slowest in the group because of its gearing and mass, and it is also the cheapest way in on the used market.",
  },
  {
    type: "p",
    text: "For a 125cc commuter buyer the drag-strip number is one input among several, and probably not the most important. Service network density, EMI affordability, fuel cost and seat height matter more day to day than 0.6 seconds of ET you will never measure. If you do want to know which 125 is quickest off a green light at a Pune intersection or on an Indore arterial road, it is the Raider 125, by a small but reproducible margin. The Glamour 125 is the value pick for daily riding. None of these bikes will get under 19 seconds without an engine swap.",
  },
  {
    type: "h2",
    text: "Run your own numbers",
  },
  {
    type: "p",
    text: "The MotoQuant simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, tyre choice and the full Indian parts catalog across all four bikes side by side. The Raider 125, N125, P125 and Glamour 125 share enough mod paths (same chain pitch, same wheel size, overlapping sprocket options) to try the same 2,550 rupee budget on all four. See which platform gives back the most ET. Pick the bike, set your local conditions, and the simulator reports ET, trap speed, 60-foot time, 1/8 mile and top-gear rpm at the trap line within roughly 50 milliseconds.",
  },
  {
    type: "p",
    text: "Two caveats. First, every number in this post is a stock-tune simulation under Aamby Valley November conditions, inside the documented entry_150_200 cluster bias band of +0.5 to +1.4 seconds. One instrumented Dragy timeslip from any of these bikes at a real Indian strip would tighten the prediction noticeably; the “Submit a timeslip” form is how to send one. Second, the Indian aftermarket prices in the table shift every quarter. The parts catalog uses retailer prices where it has them and falls back to formula-based landing-cost math (USD × 84 × 1.30 import duty × 1.18 GST + ₹1,500 freight) where it does not.",
  },
  {
    type: "p",
    text: "Pick the bike for what you actually want to do with it, and use the simulator to check whether your build moves the number you care about.",
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
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Pulsar N125 vs Raider 125 vs Glamour 125: which 125cc commuter is the fastest?
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
              ·{" "}
              <Link
                href="/blog/pulsar-ns200-vs-apache-rtr-200-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS200 vs Apache RTR 200 4V
              </Link>
              : the 200cc class most 125cc commuter graduates move into next. Same cost-per-tenth pattern, twice the power.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/hero-xtreme-200s-4v-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Hero Xtreme 200S 4V quarter-mile physics
              </Link>
              : Hero engineering one displacement class up. The same intake-and-cam conservatism shows up.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/yamaha-mt-15-v1-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Yamaha MT-15 V1 quarter-mile physics
              </Link>
              : what 30 cc and 7 hp more buys you. Same sprocket-and-tyre playbook for the cheapest tenths.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why your R15 won&apos;t hit 14s
              </Link>
              : the gearing-cap story two displacement classes up. The 125cc Neon has the same problem with the same root cause.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>
              : the 15-sub-model architecture behind every ET prediction in this post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>
              : the venue conditions used for every simulation above.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>
              : all four 125cc commuters plus 535+ other bikes with full spec sheets, gear cassettes, and OEM tyre fitments.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">Run the 125cc shootout yourself</div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the Pulsar N125, Raider 125, Glamour 125 or P125, set your local conditions and watch the ET change live.
            </div>
          </div>
          <Link
            href="/simulator?bike=bajaj-pulsar-n125"
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
