import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema, OG_IMAGE } from "../../StructuredData";
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = "bajaj-dominar-400-quarter-mile-physics";
const TITLE =
  "Bajaj Dominar 400 quarter-mile physics: 373cc single";
const DESCRIPTION =
  "MotoQuant simulates the Bajaj Dominar 400 at 14.62s with a 156 km/h trap. Where the 0.9s gap to a stock RC 390 comes from, and four Indian-market mods under ₹18,000.";

export const metadata = {
  title: "Bajaj Dominar 400 quarter-mile physics",
  description: DESCRIPTION,
  keywords: [
    "bajaj dominar 400 quarter mile",
    "dominar 400 drag time india",
    "dominar 400 top speed",
    "dominar 400 vs duke 390",
    "dominar 400 vs rc 390",
    "dominar 400 0-100 india",
    "dominar 400 cost per tenth",
    "dominar 400 mods india",
    "bajaj dominar performance upgrade",
    "dominar 400 sprocket swap",
    "dominar 400 quarter mile time",
    "indian 400cc drag race",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-24T00:00:00Z",
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the 2019-spec Bajaj Dominar 400 at 14.62 seconds and a 156 km/h trap at Aamby Valley in November conditions. Autocar India's GPS-timed runs put the same bike at 14.4-14.9 seconds across their road-test archive. A stock KTM RC 390 runs 13.5 seconds on the same simulator, and it shares almost nothing with the Dominar except the Chakan production line that builds both. That 0.9-second gap does not come from the engine or the gearbox, where most Dominar owners look for it. It comes from mass, gearing, and a power band that peaks 500 rpm too early for the way the bike is geared.",
  },
  {
    type: "h2",
    text: "What the Dominar 400 is",
  },
  {
    type: "p",
    text: "Bajaj launched the Dominar 400 in late 2016 as its 400cc sport-tourer. It is built in the same Chakan plant that makes KTM 390-series engines under licence, but its engine comes from the older first-generation KTM Duke 390 (the 2012 design), not the current LC4c. The 2019 facelift added DOHC heads, twin-channel ABS, USD forks and the LED lighting cluster that finally made the bike feel current. Power rose from 35 hp to 40 hp on the same 373.3 cc, and that is the version most Dominars on Indian roads run today.",
  },
  {
    type: "p",
    text: "The engine has an 80 mm bore and 74 mm stroke, 11.5:1 compression, liquid cooling, four-valve DOHC heads and Bosch fuel injection. It makes 40 hp at 8,000 rpm and 35 Nm at 6,250 rpm. For a 373cc single that is an understressed tune. The current LC4c in the RC 390 makes 43.5 hp at the same 8,000 rpm from the same displacement, on an 89.0 x 60.0 mm bore and stroke. The Dominar's longer stroke and lower compression bring the torque peak 250 rpm sooner and flatten the curve, which helps more at highway cruise than at a drag-strip launch. The 6-speed cassette runs ratios [3.269, 2.066, 1.481, 1.174, 0.978, 0.826] with a 16-tooth front and 46-tooth rear on 520 chain, taller final-drive gearing than the RC 390's 16F/45R. Bajaj geared the Dominar for the highway, and that costs it off the line.",
  },
  {
    type: "h2",
    text: "Stock-tune simulation numbers",
  },
  {
    type: "p",
    text: "MotoQuant's stock numbers under Aamby Valley November conditions (density altitude near 1,100 m, 22°C ambient, dry asphalt, μ_peak 1.10 on the OEM MRF Zapper FY1 rear, 78 kg rider):",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Value", "Source"],
      ["Quarter-mile ET", "14.62 s", "MotoQuant sim"],
      ["Trap speed", "156 km/h", "MotoQuant sim"],
      ["60-foot time", "~2.31 s", "MotoQuant sim"],
      ["1/8-mile ET", "~9.31 s", "MotoQuant sim"],
      ["Real-world ET (stock)", "14.4-14.9 s", "Autocar India road tests 2019-22"],
      ["Real-world top speed", "~158 km/h", "BikeWale instrumented 2022"],
      ["Sim vs real ΔET", "within band", "mid-twin-300-500 cluster ±0.4 s"],
    ],
  },
  {
    type: "p",
    text: "The simulated ET sits in the middle of Autocar India's range from their 2019-2022 road tests, and the trap speed is within 2 km/h of BikeWale's GPS-instrumented top speed. At the trap line the bike is in fifth at about 7,100 rpm: past peak torque at 6,250 but still 900 rpm short of peak power at 8,000. A stock Dominar cannot reach sixth inside 402 metres; it crosses the trap line at the top of fifth. That gearing is the biggest single limit on Dominar quarter-mile times, and we come back to it below.",
  },
  {
    type: "callout",
    text: "A cross-check: Bajaj's own 2017 launch material claimed 0-100 km/h in 8.23 seconds for the original 35 hp Dominar. MotoQuant puts the 40 hp 2019 facelift at about 7.6-7.8 seconds 0-100 km/h, which matches the half-second improvement Autocar reported in its facelift test. The order comes out right even when the absolute numbers carry the cluster band.",
  },
  {
    type: "h2",
    text: "Where the 0.9 seconds to an RC 390 come from",
  },
  {
    type: "p",
    text: "The Dominar 400 and the KTM RC 390 share 40-odd percent of their bill of materials: both are bored on the same machines in Chakan, both use Bosch fuel injection, and both run a 6-speed cassette with similar internal ratios. The Dominar's engine is a model generation older than the RC 390's LC4c. So why does the RC 390 run 13.5 s on the same simulator while the Dominar runs 14.62 s? Three things, in order of impact.",
  },
  {
    type: "table",
    rows: [
      ["Spec", "Dominar 400", "RC 390", "ET cost on Dominar"],
      ["Dry mass", "168 kg", "149 kg", "~0.42 s"],
      ["Peak power", "40 hp @ 8,000", "43.5 hp @ 8,000", "~0.18 s"],
      ["Final drive (F/R)", "16/46 520", "16/45 520", "~0.08 s"],
      ["Cd × A", "0.387 (0.79 × 0.49)", "0.279 (0.68 × 0.41)", "~0.22 s"],
      ["Total accounted", "–", "–", "~0.90 s"],
    ],
  },
  {
    type: "p",
    text: "Mass is the biggest item. The Dominar weighs 19 kilograms more than an RC 390 dry, and on a 40 hp bike that alone is worth roughly four tenths of ET. It is a sport-tourer chassis: a steel perimeter frame, a larger tank, bulkier bodywork, and a rear monoshock placed for two-up comfort rather than for the launch. Every launch and every shift has to move 168 kg of bike.",
  },
  {
    type: "p",
    text: "Aerodynamics comes second. The Dominar's Cd is 0.79 with a 0.49 m² frontal area, typical for an upright naked with wide bars, a tall fuel tank and an exposed rider torso. The RC 390 has a full sport fairing and clip-ons, which bring its Cd down to 0.68 on a smaller 0.41 m² frontal area. The Dominar's Cd × A is 39 percent larger. That costs roughly 0.22 seconds of ET above 130 km/h, where drag becomes the main resistance. Below 130 km/h, drag is small next to the wheel torque. Above it, drag grows with the square of speed and the lighter, slipperier bike pulls clear.",
  },
  {
    type: "p",
    text: "Power and gearing make up the remaining 0.26 seconds. The Dominar's 40 hp peak is 8 percent below the RC 390's 43.5 hp at the same redline, which costs roughly 0.18 s of ET on its own. Its 16F/46R sprockets give a 2.4 percent shorter final drive than the RC 390's 16F/45R. That sounds like it should help acceleration, but the Dominar's flatter power curve cannot use the shorter ratio the way a peakier engine would. The longer absolute gearing through the gearbox (the cassette runs the same ratios on both bikes, but the final drive sets road speed per gear) puts the Dominar in fifth at the trap line, where the RC 390 is still pulling hard in fifth at higher revs. Gearing costs another 0.08 s.",
  },
  {
    type: "h2",
    text: "What limits the Dominar at the strip",
  },
  {
    type: "p",
    text: "Three things limit this bike on a drag strip, biggest first:",
  },
  {
    type: "p",
    text: "1. The launch RPM window. The Dominar's peak torque comes at 6,250 rpm, fairly low for a 373cc single. A clean launch drops the clutch at roughly 5,500-6,000 rpm, which gives the most wheel torque and keeps the engine in the fat part of the torque curve while the clutch slips. Below 5,000 rpm the bike bogs and the 60-foot time goes past 2.4 seconds. Above 6,500 rpm the engine is already past peak torque, and 40 hp is not enough to spin the rear tire usefully. The window is narrow. Most Dominar owners in YouTube videos are clearly launching at 4,000-4,500 rpm, which leaves 0.3-0.4 seconds on the table.",
  },
  {
    type: "p",
    text: "2. The 16/46 sprocket pair. Bajaj geared this bike for highway cruising, and its marketing has always sold the Dominar as a long-distance tourer. A 16F/47R or 15F/46R swap shortens the final drive by 2.2 percent; either costs under ₹2,500 from Indian retailers such as Motousher or Store4Riders. The swap brings sixth gear within reach inside the quarter, moves the trap-line RPM in fifth to a better band (about 7,400 rpm, still below peak power but pulling harder), and takes roughly 0.10 seconds off the ET. It is the cheapest tenth you can buy on this bike.",
  },
  {
    type: "p",
    text: "3. The MRF Zapper FY1 OEM tire. The rear is a 150/60R17 with a compound made for long life, not peak grip. MotoQuant puts the Zapper's μ_peak at 1.10. That is adequate, but a Pirelli Diablo Rosso III in the same 150/60R17 size reaches about 1.30, and a Metzeler Sportec M9 RR (still street-legal) reaches 1.32. The tire does not limit the launch, because 40 hp cannot break the OEM tire loose in most conditions. In the top half of the run, though, the grippier tire pays back after each gear change, where brief wheel slip costs time. A Diablo Rosso III on the rear costs about ₹7,500 and is worth about 0.05 s of ET. That is modest, but it also changes how the bike feels on a wet road, which is the more practical reason to fit one.",
  },
  {
    type: "h2",
    text: "How it compares with its Indian rivals",
  },
  {
    type: "p",
    text: "The Indian segment around the Dominar 400 has changed a lot since its 2016 launch. Its closest showroom rivals today are the KTM 390 Adventure (390cc, lighter frame), the Honda CB350RS (350cc retro, much less power), the Royal Enfield Hunter 350 and Classic 350 (heavier, less power, a different segment) and the BMW G310R (313cc, smaller engine but lighter). All numbers below are MotoQuant stock-tune simulations under the same Aamby Valley November conditions:",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Sim trap", "Dry mass", "Peak hp", "India OTR (approx)"],
      ["Bajaj Dominar 400", "14.62 s", "156 km/h", "168 kg", "40", "~₹2.4 L"],
      ["KTM RC 390", "13.5 s", "166 km/h", "149 kg", "43.5", "~₹3.4 L"],
      ["KTM Duke 390", "13.7 s", "162 km/h", "149 kg", "43.5", "~₹3.2 L"],
      ["BMW G310R", "~15.1 s", "146 km/h", "158 kg", "34", "~₹3.0 L"],
      ["Honda CB350RS", "~16.3 s", "131 km/h", "179 kg", "21", "~₹2.3 L"],
      ["Royal Enfield Classic 350", "~17.1 s", "121 km/h", "195 kg", "20.4", "~₹2.1 L"],
    ],
  },
  {
    type: "p",
    text: "At ₹2.4 lakh on-road, the Dominar 400 is competitive. The KTM RC 390 is 1.1 seconds quicker but costs ₹1 lakh more on the road, roughly ₹91,000 per second of ET. That is poor value if strip time is all you care about. The Duke 390 sits between them at ₹3.2 lakh and 13.7 s. The BMW G310R is half a second slower and costs more, and the CB350RS and Classic 350 are in a different performance class. Measured as cost per second of ET, the Dominar 400 is better value than the whole Royal Enfield range and competitive with the BMW G310 platform.",
  },
  {
    type: "callout",
    text: "The Dominar 400's value math: ₹2.4 lakh on-road, 14.62 s, 156 km/h trap. The next quicker bike at the strip (Duke 390) costs ₹1 lakh more. The next slower one (G310R) costs ₹60,000 more. In the Indian 350-400cc segment, the Dominar sits where the price and performance lines cross.",
  },
  {
    type: "h2",
    text: "Cost per tenth: four mods under ₹18,000",
  },
  {
    type: "p",
    text: "MotoQuant's parts-ROI engine ranks every catalog part by cost per tenth at current Indian retail prices. The May 2026 price refresh scraped or formula-priced parts against Store4Riders, Motousher, RidersPlanet, KustomHub and Performance Racing Store. These are the four best-value upgrades on the Dominar 400, each under ₹18,000.",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Cost (₹)", "ET gain", "₹/tenth"],
      ["15F/46R or 16F/47R sprocket", "2,300", "0.10 s", "2,300"],
      ["DNA / K&N air filter (drop-in)", "3,800", "0.04 s", "9,500"],
      ["Diablo Rosso III 150/60R17 rear", "7,500", "0.05 s", "15,000"],
      ["Powertronic Stage 1 ECU flash", "16,500", "0.18 s", "9,200"],
      ["All four stacked", "30,100", "0.37 s", "8,135"],
    ],
  },
  {
    type: "p",
    text: "The sprocket is the cheapest tenth on the bike by a wide margin: ₹2,300 buys what would cost ₹23,000 at Powertronic flash pricing. Do it first. The air filter helps because the OEM paper element really does restrict this engine at peak revs, but the gain is small because the flatter torque curve doesn't punish intake restriction the way a peakier engine would. The Diablo Rosso III is the surprise. Most Dominar owners think the rear tire is fine because the bike doesn't break the OEM tire loose at launch, but the higher μ_peak pays back after each gear change, and it is also a real safety upgrade.",
  },
  {
    type: "p",
    text: "The Powertronic Stage 1 flash is the biggest single ET drop on the bike under ₹20,000. Powertronic's Dominar-specific map (part number PT-DOM400) sharpens throttle response and adds about 3 hp at peak, which the simulator turns into 0.18 seconds of ET. Useful, not dramatic. The flash works best with the sprocket swap: the shorter final drive and sharper throttle make the bike more responsive on the street, and it runs a 14.25 at the strip instead of a 14.62. The full stack costs ₹30,100 for 0.37 seconds, about ₹8,100 per tenth. In absolute terms that competes with much more expensive bikes.",
  },
  {
    type: "h2",
    text: "At Indian drag strips",
  },
  {
    type: "p",
    text: "The Dominar 400 turns up often at Indian drag meets: Aamby Valley, MMRT Chennai, the occasional informal run near Pune. It is far from the fastest bike there. It is one of the cheapest road-legal bikes that can run under 15 seconds without serious mod money, so a rider can learn drag-racing technique without first spending ₹3-4 lakh on a faster machine. A competent street rider on a stock Dominar at Aamby Valley in October-November conditions will run 14.4-14.9 seconds. The 14.4 s end needs a clean launch: clutch out near 5,500 rpm, weight forward, and first gear ridden as a controlled-slip traction phase rather than a full-throttle blast. The 14.9 s end is what a rider new to the bike gets on the first pass.",
  },
  {
    type: "p",
    text: "At 14.62 s, a stock Dominar sits in roughly the same ET window as a stock Suzuki Gixxer SF 250, and clearly ahead of a stock Honda CB350RS or any of the Royal Enfield 350s. It is about 1.1 s behind a stock RC 390 and about 0.9 s behind a Duke 390. The four-mod stack above (₹30,100, 14.25 s) cuts the gap to a stock RC 390 to about 0.75 seconds, at less than a third of the RC 390's purchase price. A modded Dominar gets close to the ET of a more expensive bike and leaves money for fuel, tires and strip entry fees.",
  },
  {
    type: "h2",
    text: "Run your own numbers",
  },
  {
    type: "p",
    text: "If you own a Dominar 400, or are weighing one against the KTM 390 platform, the simulator at motoquant.in lets you change rider weight, ambient temperature, density altitude and parts-catalog mods and see where each tenth comes from. The May 2026 calibration sweep gives the mid-twin-300-500 cluster a ±0.4 second bias band. When the simulator says 14.62 s, expect the strip to show something between 14.4 and 14.9 s, depending on your launch and the surface prep.",
  },
  {
    type: "p",
    text: "The parts ROI view helps most on the Dominar because its mod list has a sharp break at the ₹18,000 mark. Below that, every rupee buys measurable tenths (sprocket, filter, tire, flash). Above it, returns drop steeply: a slip-on exhaust on the Dominar adds maybe 0.04-0.06 seconds of ET for ₹25,000-40,000, which is ₹500,000-650,000 per tenth. The stock exhaust does not hold the Dominar back the way it does an RC 390. The simulator shows you where that drop-off is before you spend the money.",
  },
  {
    type: "p",
    text: "Every number in this post is a stock-tune simulation under Aamby Valley November conditions. Rider weight, ambient temperature, surface condition and launch technique all move the absolute numbers. The order of the mods (sprocket first, flash second, tire third, exhaust last) stays the same across those changes, and that order is what you want to know before spending money at a Pune tuner.",
  },
  {
    type: "p",
    text: "The Bajaj Dominar 400 is a sport-tourer, geared and weighted for the highway rather than the strip. The cheapest 0.10 seconds of ET on it is a ₹2,300 sprocket swap that takes a competent mechanic 45 minutes. Do the sprocket before you spend ₹20,000 on a slip-on or ₹40,000 on suspension. It is the closest thing to a free tenth that any Indian bike sells.",
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
              <p className="text-sm text-white/80 leading-relaxed italic">
                {block.text}
              </p>
            </div>
          );
        }
        if (block.type === "table") {
          const [header, ...rows] = block.rows;
          return (
            <div
              key={i}
              className="my-8 overflow-x-auto rounded-xl border border-white/10"
            >
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
          datePublished: "2026-05-24",
        })}
      />
      <SiteNav />

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["Bajaj", "Dominar 400", "Indian 400cc", "sport-tourer", "physics"].map((t) => (
              <span
                key={t}
                className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Bajaj Dominar 400 quarter-mile physics: 373cc single at the strip
          </h1>
          <div className="text-sm text-white/60 mb-12">
            24 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[72]} />

        {/* Internal links / related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">
            Related reading
          </h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{" "}
              <Link
                href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM Duke 390 vs RC 390: quarter-mile physics at Aamby Valley
              </Link>
              : the two bikes the Dominar is compared with in every showroom,
              spec by spec.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Best mods for KTM RC 390: a cost-per-tenth ladder
              </Link>
              : the mod plan that turns a stock RC 390 into an 11.3-second
              bike. Some of it applies to the Dominar on a smaller budget.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS400Z quarter-mile physics (and why an RC 390 still wins)
              </Link>
              : Bajaj's other 400cc bike, built on the same Chakan production line.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The physics of a perfect launch
              </Link>
              : clutch engagement RPM, slip phase and weight transfer in the
              first 0.4 seconds. Read it if your Dominar's 60-foot times are
              past 2.4 seconds.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>
              : density altitude, temperature and surface conditions at the
              venue behind most of the numbers in this post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>
              : the specs, gear ratios and Cd values the simulator uses. The
              Dominar 400 is in the Bajaj section.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">
              Run the Dominar 400 yourself
            </div>
            <div className="text-white/60 text-sm">
              Free simulator: pick the Bajaj Dominar 400, set your local
              conditions, and watch the ET update live as you add a sprocket
              swap, a Powertronic flash or a Diablo Rosso III rear.
            </div>
          </div>
          <Link
            href="/simulator?bike=bajaj-dominar-400"
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
