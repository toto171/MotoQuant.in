import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";
import { REPO_URL } from "../../../lib/site";

const SLUG = "bajaj-dominar-400-quarter-mile-physics";
const TITLE =
  "Bajaj Dominar 400 Quarter-Mile Physics: 373cc Single";
const DESCRIPTION =
  "MotoQuant simulates the Bajaj Dominar 400 at 14.62s and 156 km/h trap. Where the 0.9s gap to a stock RC 390 lives, plus four India mods under ₹18,000.";

export const metadata = {
  title: "Bajaj Dominar 400 Quarter-Mile Physics — MotoQuant",
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
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "MotoQuant simulates the 2019-spec Bajaj Dominar 400 at 14.62 seconds and a 156 km/h trap at Aamby Valley in November conditions. Autocar India's GPS-timed runs put the same bike at 14.4-14.9 seconds across their road-test archive. A stock KTM RC 390 — the bike that shares almost nothing with the Dominar except the Chakan production line that builds both — runs 13.5 seconds on the same simulator. That 0.9-second gap is not where most Dominar owners assume it lives. It is not the engine. It is not the gearbox. It is mass, gearing, and a power band that peaks 500 rpm too early for the way the bike is geared.",
  },
  {
    type: "h2",
    text: "What the Dominar 400 Actually Is",
  },
  {
    type: "p",
    text: "The Dominar 400 launched in late 2016 as Bajaj's attempt at a sport-tourer in the 400cc segment — built around the same Chakan plant infrastructure that produces KTM 390 series engines under licence, but with an engine derived from the older first-generation KTM Duke 390 (the 2012 design) rather than the current LC4c. The 2019 facelift added DOHC heads, twin-channel ABS, USD forks, and the LED lighting cluster that finally made the bike feel like a current product. The engine pulled from 35 hp to 40 hp on the same 373.3 cc displacement, which is the version most Dominars on Indian roads today run.",
  },
  {
    type: "p",
    text: "The engine architecture is 80 mm bore by 74 mm stroke, 11.5:1 compression, liquid-cooled, four-valve DOHC, Bosch fuel injection, 40 hp at 8,000 rpm and 35 Nm at 6,250 rpm. That is a noticeably understressed tune for a 373cc single — the current LC4c on the RC 390 makes 43.5 hp at the same 8,000 rpm from the same displacement on a tighter 89.0 x 60.0 mm bore-and-stroke. The Dominar's longer stroke and lower compression produce a torque peak 250 rpm sooner and a flatter curve that is more useful at highway cruise than at a drag strip launch. The 6-speed cassette runs ratios [3.269, 2.066, 1.481, 1.174, 0.978, 0.826] with a 16-tooth front and 46-tooth rear on 520 chain. That is taller final-drive gearing than the RC 390's 16F/45R — Bajaj geared the Dominar for highway use, which costs the bike off the line.",
  },
  {
    type: "h2",
    text: "Stock-Tune Simulation Numbers",
  },
  {
    type: "p",
    text: "Running the Dominar 400 in MotoQuant under Aamby Valley November conditions — density altitude near 1,100 m, 22°C ambient, dry concrete, μ_peak 1.10 on the OEM MRF Zapper FY1 rear, 78 kg rider — produces these stock numbers:",
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
    text: "The simulator number sits squarely in the middle of Autocar India's published range across their 2019-2022 road tests, and the trap speed matches BikeWale's GPS-instrumented top speed to within 2 km/h. The bike is geared so that fifth gear at the trap line is running about 7,100 rpm — past peak torque at 6,250 but still 900 rpm short of peak power at 8,000. Sixth gear is unreachable inside 402 metres on a stock Dominar; the bike trips the trap line at the top of fifth. That gearing choice is the single biggest constraint on Dominar quarter-mile times, and we will get to it.",
  },
  {
    type: "callout",
    text: "A useful sanity check: Bajaj's own 2017 launch material claimed 0-100 km/h in 8.23 seconds for the original 35 hp Dominar. MotoQuant simulates the 40 hp 2019 facelift at about 7.6-7.8 seconds 0-100 km/h, which matches the half-second improvement that Autocar's facelift test reported. The relative ordering tracks correctly even when absolute numbers carry the cluster band.",
  },
  {
    type: "h2",
    text: "Where the 0.9 Seconds to an RC 390 Live",
  },
  {
    type: "p",
    text: "The Dominar 400 and the KTM RC 390 share 40-odd percent of their bill of materials — both are bored on the same machines in Chakan, both use Bosch fuel injection, both run a 6-speed cassette with similar internal ratios — and the Dominar's engine even pre-dates the RC 390's LC4c by a model generation. So why does the RC 390 run 13.5 s on the same simulator while the Dominar runs 14.62 s? Three things, in order of impact.",
  },
  {
    type: "table",
    rows: [
      ["Spec", "Dominar 400", "RC 390", "ET cost on Dominar"],
      ["Dry mass", "168 kg", "149 kg", "~0.42 s"],
      ["Peak power", "40 hp @ 8,000", "43.5 hp @ 8,000", "~0.18 s"],
      ["Final drive (F/R)", "16/46 520", "16/45 520", "~0.08 s"],
      ["Cd × A", "0.387 (0.79 × 0.49)", "0.279 (0.68 × 0.41)", "~0.22 s"],
      ["Total accounted", "—", "—", "~0.90 s"],
    ],
  },
  {
    type: "p",
    text: "Mass is the headline number. The Dominar is 19 kilograms heavier than an RC 390 in dry-weight terms — that single difference is worth roughly four tenths of ET on a 40 hp bike. The Dominar is a sport-tourer chassis with a steel perimeter frame, larger tank, more substantial bodywork, and a rear monoshock placed to favour two-up riding comfort over launch dynamics. Bajaj did not design this bike to be a strip weapon, and it shows. Every gear shift, every clutch dump, every traction event drags 168 kg of bike along; the RC 390 carries 19 kilograms less through the same physics.",
  },
  {
    type: "p",
    text: "Aerodynamics is the second-biggest factor. The Dominar's Cd is 0.79 with a 0.49 m² frontal area — typical for an upright naked with wide bars, a tall fuel tank, and an exposed rider torso. The RC 390 wears a full sport fairing and clip-ons, dropping its Cd to 0.68 with a smaller 0.41 m² projected frontal area. The Cd × A product on the Dominar is 39 percent larger, which costs roughly 0.22 seconds of ET above 130 km/h where aerodynamic drag becomes the dominant resistance term. Below 130 km/h aerodynamic drag is small compared to the wheel torque the engine is putting down; above it, drag scales with the square of velocity and the lighter, slipperier bike pulls clear.",
  },
  {
    type: "p",
    text: "Power and gearing make up the remaining 0.26 seconds. The Dominar's 40 hp peak is 8 percent below the RC 390's 43.5 hp at the same redline, costing roughly 0.18 s of ET on its own. The 16F/46R sprocket pair gives a 2.4 percent shorter final-drive than the RC 390's 16F/45R, which sounds like it should help acceleration — but the Dominar's flatter power curve means it cannot exploit the shorter ratio the way a peakier engine would, and the longer absolute gearing through the gearbox (the cassette runs the same ratios on both bikes, but the final drive determines road speed per gear) puts the Dominar into fifth gear at the trap line where the RC 390 is still pulling hard in fifth at higher revs. Net result: gearing costs another 0.08 s.",
  },
  {
    type: "h2",
    text: "What Limits the Dominar at the Strip",
  },
  {
    type: "p",
    text: "Three things limit this bike on a drag strip, in descending order:",
  },
  {
    type: "p",
    text: "1. The launch RPM window. The Dominar's peak torque sits at 6,250 rpm — relatively low for a 373cc single. A clean launch dumps the clutch at roughly 5,500-6,000 rpm to maximise wheel torque while keeping the engine in the meat of the torque curve through the clutch-slip phase. Below 5,000 rpm the bike bogs hard on launch and the 60-foot time blows out past 2.4 seconds. Above 6,500 rpm the engine has already crested peak torque and the launch becomes a power-side proposition where the Dominar's 40 hp simply isn't enough to spin the rear tire usefully. The window is narrow and most Dominar owners on YouTube videos are visibly launching at 4,000-4,500 rpm, which is leaving 0.3-0.4 seconds on the table.",
  },
  {
    type: "p",
    text: "2. The 16/46 sprocket pair. Bajaj geared this bike for highway cruising — Dominar marketing has always leaned on the long-distance touring credentials. A 16F/47R or 15F/46R swap (both available cheaply from Indian retailers like Motousher or Store4Riders for under ₹2,500) shortens the final drive by 2.2 percent. That brings sixth gear into reach inside the quarter, drops the trap-line RPM in fifth into a more favourable band (about 7,400 rpm — still below peak power but pulling harder), and shaves roughly 0.10 seconds of ET. It is the cheapest tenth you can buy on this bike.",
  },
  {
    type: "p",
    text: "3. The MRF Zapper FY1 OEM tire. The rear is a 150/60R17 with a tread compound aimed at long-distance durability rather than peak grip. MotoQuant pegs the Zapper's μ_peak at 1.10 — adequate, but a Pirelli Diablo Rosso III in the same 150/60R17 size hits μ_peak around 1.30, and a Metzeler Sportec M9 RR (still legal for street use) gets to 1.32. The tire is not the limiting factor at launch because the Dominar's 40 hp cannot break the OEM tire loose under most conditions, but in the top half of the run the higher-grip tire pays back in the gear-change recovery phase where transient slip eats time. A Diablo Rosso III swap on the rear costs about ₹7,500 and is worth about 0.05 s of ET — modest, but it also transforms how the bike feels on a wet road, which is the more practical reason to do it.",
  },
  {
    type: "h2",
    text: "How It Compares to Its Indian Rivals",
  },
  {
    type: "p",
    text: "The Dominar 400 sits in a busy Indian segment that has shifted significantly since the bike's 2016 launch. The closest direct rivals on the showroom floor today are the KTM 390 Adventure (390cc, lighter frame), the Honda CB350RS (350cc retro-styled, much less power), the Royal Enfield Hunter 350 / Classic 350 (heavier, less power, different segment), and the BMW G310R (313cc, less displacement but lighter). All numbers below are MotoQuant stock-tune sims under matched Aamby Valley November conditions:",
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
    text: "The Dominar 400 is genuinely competitive at its ₹2.4 lakh on-road price. The KTM RC 390 is 1.1 seconds quicker but costs ₹1 lakh more on the road — that works out to roughly ₹91,000 per second of ET, which is poor value if drag-strip performance is the only thing you care about. The Duke 390 splits the difference at ₹3.2 lakh and 13.7 s. The BMW G310R is half a second slower at a higher price point, and the CB350RS / Classic 350 are in a different performance class entirely. For a buyer optimising for cost-per-second-of-ET at the strip, the Dominar 400 is the better value than the entire Royal Enfield range and competitive with the BMW G310 platform.",
  },
  {
    type: "callout",
    text: "The Dominar 400's value math: ₹2.4 lakh on-road, 14.62 s, 156 km/h trap. The next bike that runs quicker at the strip costs ₹1 lakh more (Duke 390). The next bike that runs slower at the strip (G310R) costs ₹60,000 more. The Dominar sits at the exact inflection point where price and performance cross over in the Indian 350-400cc segment.",
  },
  {
    type: "h2",
    text: "Cost-Per-Tenth: Four Mods Under ₹18,000",
  },
  {
    type: "p",
    text: "MotoQuant's parts-ROI engine ranks every catalog part by cost-per-tenth at current Indian retail prices. The May 2026 pricing-refresh pass scraped or formula-priced parts against Store4Riders, Motousher, RidersPlanet, KustomHub, and Performance Racing Store. Below are the four best-value upgrades on the Dominar 400, each under ₹18,000.",
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
    text: "The sprocket is the cheapest tenth on the bike by a wide margin — ₹2,300 buys ₹23,000 of equivalent performance benefit if measured by Powertronic flash pricing. Do it first. The air filter pays back because the OEM paper element is genuinely restrictive on this engine at peak revs, but the gain is modest because the bike's flatter torque curve doesn't punish intake restriction the way a peakier engine does. The Diablo Rosso III is the surprise pick here — most Dominar owners think the rear tire is fine because the bike doesn't break the OEM loose on launch, but the higher μ_peak pays back in gear-change recovery and is also a substantial safety upgrade.",
  },
  {
    type: "p",
    text: "The Powertronic Stage 1 flash is the biggest single ET drop available on the bike under ₹20,000. Powertronic's Dominar-specific map (their part number PT-DOM400) opens up the throttle response and adds about 3 hp at peak. On the simulator that maps to 0.18 seconds of ET — meaningful, but not transformative. The flash is at its best when stacked with the sprocket swap: the shorter final drive plus the sharper throttle gives a more responsive bike on the street that also happens to run a 14.25 at the strip instead of a 14.62. Total stack cost ₹30,100 for a 0.37-second improvement, which is a cost-per-tenth of about ₹8,100. That is competitive with much more expensive bikes in absolute terms.",
  },
  {
    type: "h2",
    text: "The Indian Drag-Strip Reality",
  },
  {
    type: "p",
    text: "The Dominar 400 shows up at Indian drag meets — Aamby Valley, MMRT Chennai, occasional Pune-area informal runs — with surprising regularity. The reason is not that it is the fastest bike there; it isn't, by a wide margin. The reason is that it is one of the cheapest road-legal bikes that can clear a 15-second pass without serious mod money, which lowers the barrier to entry for someone who wants to learn drag-racing technique without burning ₹3-4 lakh on a faster machine first. A stock Dominar at Aamby Valley in October-November conditions will run 14.4-14.9 seconds in the hands of a competent street rider. The bottom of that range (14.4 s) requires a clean launch — clutch dumped near 5,500 rpm, weight shifted forward, first gear treated as a slip-managed traction interval rather than a full-throttle blast. The top of the range (14.9 s) is what an unfamiliar rider gets on the first pass.",
  },
  {
    type: "p",
    text: "For context: a stock Dominar running 14.62 s puts it in roughly the same ET window as a stock Suzuki Gixxer SF 250 and noticeably ahead of a stock Honda CB350RS or any of the Royal Enfield 350 platforms. It is behind a stock RC 390 by about 1.1 s and a Duke 390 by about 0.9 s. With the four-mod stack above (₹30,100, 14.25 s) it closes the gap to a stock RC 390 to about 0.75 seconds — at less than a third of the RC 390's purchase price. That is the value proposition of a modded Dominar in India: similar ET to a more expensive bike, with money left over for fuel, tires, and strip entry fees.",
  },
  {
    type: "h2",
    text: "Run Your Own Numbers",
  },
  {
    type: "p",
    text: "If you own a Dominar 400 or are considering one against the KTM 390 platform, the simulator at motoquant.in lets you sweep rider weight, ambient temperature, density altitude, and parts-catalog mods to see exactly where your tenths come from. The mid-twin-300-500 cluster carries a ±0.4 second bias band per the May 2026 calibration sweep — when the simulator says 14.62 s, expect the strip to confirm somewhere between 14.4 and 14.9 s depending on launch quality and surface prep.",
  },
  {
    type: "p",
    text: "The parts ROI view is particularly useful on the Dominar because the bike's mod ladder has a very sharp inflection point at the ₹18,000 mark. Below that, every rupee buys you measurable tenths (sprocket, filter, tire, flash). Above it, the marginal return drops steeply — a slip-on exhaust on the Dominar adds maybe 0.04-0.06 seconds of ET for ₹25,000-40,000, which is ₹500,000-650,000 per tenth. The bike's stock exhaust restriction is not the limiting factor in the way it is on, say, an RC 390. The simulator makes that inflection visible before you spend the money.",
  },
  {
    type: "p",
    text: "One practical note worth stating plainly: every number in this post is a stock-tune simulation under Aamby Valley November conditions. Rider weight, ambient temperature, surface condition, and launch technique all move the absolute numbers. The relative ordering of which mods help — sprocket first, flash second, tire third, exhaust last — holds stable across those variations, which is the point of running the model before spending money at a Pune tuner.",
  },
  {
    type: "p",
    text: "If you take one practical thing from this post: the Bajaj Dominar 400 is a sport-tourer that got geared and weighted for highway cruising, not for the strip. The cheapest 0.10 seconds of ET available on the bike is a ₹2,300 sprocket swap that takes a competent mechanic 45 minutes. Before you spend ₹20,000 on a slip-on or ₹40,000 on suspension upgrades, do the sprocket. It is the closest thing to a free tenth that any Indian bike sells.",
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
          datePublished: "2026-05-24",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["Bajaj", "Dominar 400", "Indian 400cc", "sport-tourer", "physics"].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Bajaj Dominar 400 Quarter-Mile Physics: 373cc Single at the Strip
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            24 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

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
                KTM Duke 390 vs RC 390: Quarter-Mile Physics at Aamby Valley
              </Link>{" "}
              — the two bikes the Dominar gets compared to in every showroom,
              broken down spec-by-spec.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/best-mods-for-ktm-rc-390-budget-vs-cost-per-tenth"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Best Mods for KTM RC 390: A Cost-Per-Tenth Ladder
              </Link>{" "}
              — the modding playbook that turns a stock RC 390 into an 11.3-second
              bike; some of the same tactics apply to the Dominar at lower
              budget.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/pulsar-ns400z-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Pulsar NS400Z Quarter-Mile Physics (and Why an RC 390 Still Wins)
              </Link>{" "}
              — Bajaj's other 400cc product, on the same Chakan production line.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The Physics of a Perfect Launch
              </Link>{" "}
              — clutch engagement RPM, slip phase, and weight transfer in the
              first 0.4 seconds. Critical reading if your Dominar 60-foots are
              past 2.4 seconds.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{" "}
              — density altitude, temperature, and surface conditions at the
              venue where most of the numbers in this post were generated.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>{" "}
              — every spec, every gear ratio, every Cd value used by the
              simulator. The Dominar 400 entry is in the Bajaj section.
            </li>
            <li>
              ·{" "}
              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant on GitHub
              </a>{" "}
              — free and open source: audit the physics behind every number in this post, or run it yourself.
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
              Free simulator — pick the Bajaj Dominar 400, dial in your local
              conditions, and watch the ET update live as you toggle a sprocket
              swap, a Powertronic flash, and a Diablo Rosso III rear.
            </div>
          </div>
          <Link
            href="/simulator?bike=bajaj-dominar-400"
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
