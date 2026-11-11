import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema, OG_IMAGE } from "../../StructuredData";
import PostBikeLinks from '../../../components/PostBikeLinks';

const SLUG = "kawasaki-ninja-400-vs-zx-4r-quarter-mile-physics";
const TITLE =
  "Kawasaki Ninja 400 vs ZX-4R: parallel twin vs inline-four at the strip";
const DESCRIPTION =
  "MotoQuant simulates the Ninja 400 at ~13.1s and the ZX-4R at 12.681s / 192.6 km/h. Same 400cc class, 0.4s apart. Architecture, redline and gearing explain the gap. India pricing, cost-per-tenth mods, and why the inline-four wins on the top end.";

export const metadata = {
  title: "Kawasaki Ninja 400 vs ZX-4R quarter mile",
  description: DESCRIPTION,
  keywords: [
    "kawasaki ninja 400 quarter mile india",
    "ninja 400 drag time india",
    "kawasaki zx-4r quarter mile",
    "ninja 400 vs zx-4r which is faster",
    "ninja zx-4r vs ninja 400 india",
    "ninja 400 0-100 india",
    "zx-4r inline four drag time",
    "kawasaki 400cc comparison india",
    "ninja 400 best mods india",
    "zx-4r vs ninja 400 cost",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-22T00:00:00Z",
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "The Kawasaki Ninja 400 and Ninja ZX-4R both carry 400 cc badges and are both assembled in India at the Chakan plant, yet MotoQuant simulates them 0.4 seconds apart over the quarter-mile: the ZX-4R at 12.681 seconds with a 192.6 km/h trap, the Ninja 400 at roughly 13.1 seconds with a 172 km/h trap. Both displace about 400 cc, so the gap comes from architecture. A 399 cc parallel twin that peaks at 8,500 rpm behaves very differently from a 399 cc inline-four that revs to 14,000. This post covers where those 0.4 seconds come from, what each bike costs in India, and which gives the better cost-per-tenth for a rider who races on weekends and commutes the rest of the week.",
  },
  {
    type: "h2",
    text: "Two very different 400s",
  },
  {
    type: "p",
    text: "The Ninja 400 has been on sale in India since 2018. Its engine is a 399 cc parallel twin with a 70.0 mm bore and 51.8 mm stroke, an oversquare motor that likes revs, though not ZX-4R revs. Peak power is 45 hp at 10,000 rpm, peak torque is 38 Nm at 8,000 rpm, and the redline sits at around 12,000 rpm. The gearbox has six speeds. Kawasaki has never published the individual gear ratios for this generation, but independent teardowns consistently show a taller final drive (14F/42R in most markets) than the ZX-4R's shorter 15F/43R. Dry mass is 168 kg.",
  },
  {
    type: "p",
    text: "The Ninja ZX-4R arrived in India in 2025. Its engine is a 399 cc inline-four: the same displacement, built a very different way. Bore is 57 mm, stroke 39.1 mm, compression 12.5:1, redline 14,500 rpm. Peak power is 76.5 hp at 14,000 rpm on the ZX-4RR and 76 hp at 14,000 rpm on the base ZX-4R. That 14,000 rpm power peak is the number that matters: 4,000 rpm higher than the Ninja 400's and 2,500 rpm higher than most of the ZX-4R's competitors. The ZX-4R weighs 185 kg dry, 17 kg more than the Ninja 400. Final drive is 15F/43R on a 520 chain, with gear ratios sized for the high-revving engine.",
  },
  {
    type: "table",
    rows: [
      ["Spec", "Ninja 400 (2018-2025)", "Ninja ZX-4R (2024-2026)"],
      ["Engine layout", "Parallel twin", "Inline-four"],
      ["Displacement", "399 cc", "399 cc"],
      ["Peak power", "45 hp @ 10,000 rpm", "76 hp @ 14,000 rpm"],
      ["Peak torque", "38 Nm @ 8,000 rpm", "40 Nm @ 12,500 rpm"],
      ["Redline (approx.)", "~12,000 rpm", "~14,500 rpm"],
      ["Dry mass", "168 kg", "185 kg"],
      ["Final drive", "14F/42R, 520 chain", "15F/43R, 520 chain"],
      [
        "India price (on-road, 2026)",
        "~₹5.2 lakh",
        "~₹8.9 lakh (ZX-4R) / ₹9.3 lakh (ZX-4RR)",
      ],
    ],
  },
  {
    type: "p",
    text: "On paper the Ninja 400 should win: it is 17 kg lighter at the same displacement, and in the first two gears the heavier ZX-4R is dragging that extra mass uphill. But the power gap (45 hp against 76 hp, 69 percent more) is too wide for the weight difference to make up over a quarter-mile. In MotoQuant's mid-twin-300-500 cluster, the Ninja 400's power-to-weight of 267 hp/tonne sits well below the ZX-4R's 411 hp/tonne. Past the 60-foot mark, which both bikes handle similarly, the higher-revving ZX-4R pulls harder in every gear.",
  },
  {
    type: "h2",
    text: "Stock sim numbers at Aamby Valley",
  },
  {
    type: "p",
    text: "Both bikes run in MotoQuant under the same Aamby Valley November conditions: density altitude around 1,100 m, 22°C ambient, dry asphalt, a 70 kg rider and OEM tire compounds. The Ninja 400 runs on Dunlop Sportmax GPR-300 front (120/70-17) and rear (160/60-17) at μ_peak ≈ 1.08. The ZX-4R runs on Dunlop Sportmax Roadsport 2 front (110/70-17) and rear (150/60-17) at μ_peak ≈ 1.10. Both are production sport-touring compounds, not drag slicks.",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Ninja 400 (sim)", "ZX-4R (sim)", "Δ (ZX-4R advantage)"],
      ["Quarter-mile ET", "~13.1 s", "12.681 s", "−0.42 s"],
      ["Trap speed", "~172 km/h", "192.6 km/h", "+20.6 km/h"],
      ["60-foot time", "~2.22 s", "~2.24 s", "−0.02 s (Ninja ahead)"],
      ["1/8-mile ET", "~8.80 s", "~8.40 s", "−0.40 s"],
      ["Top gear at trap", "6th, ~9,200 rpm", "6th, ~12,200 rpm", "–"],
      [
        "Cluster bias band",
        "±0.4 s mid-twin-300-500",
        "±0.3 s litre-sport-600-1000",
        "–",
      ],
    ],
  },
  {
    type: "p",
    text: "The 60-foot times are nearly identical. In this sim the Ninja 400 is two hundredths quicker at 60 feet, because it is 17 kg lighter and, at the low speeds of the first few bike-lengths, the ZX-4R's extra power has not yet made up for the weight. After that the gap is almost all top end. The 1/8-mile splits are already 0.4 seconds apart, and most of that builds between the 1/8 and the 1/4 as the ZX-4R keeps pulling toward a 192.6 km/h trap while the Ninja 400 runs into its lower rpm ceiling. The ZX-4R's 192.6 km/h trap is 20 km/h higher than the Ninja's, and it is worth far more than the ET suggests: in a race from a roll, or from mid-range speed, the ZX-4R's advantage is larger still.",
  },
  {
    type: "callout",
    text: "The published global benchmark for the Ninja 400 is 12.98 seconds at roughly 163 km/h (Sport Rider, 2018). MotoQuant's mid-twin-300-500 cluster carries a +0.15 s mean bias, which puts the expected sim output at around 13.1 seconds, in line with that benchmark. The ZX-4R has been validated against the 12.4–12.8 s band Cycle World published in 2024 for the US-spec ZX-4RR, and the base ZX-4R sim at 12.681 s sits inside it. Neither number is a cherry-picked best run.",
  },
  {
    type: "h2",
    text: "Why the inline-four wins on the top end",
  },
  {
    type: "p",
    text: "The Ninja 400's twin makes its torque early and then runs out of revs. Peak torque comes at 8,000 rpm and peak power at 10,000 rpm. The useful band from peak torque to redline is about 2,000 rpm, which in sixth gear is roughly 25 km/h of road speed before the engine hits its rev ceiling. Then the rider has nowhere to go: there is no seventh gear to shift into, so the engine falls away from its power peak. The bike traps in 6th at around 9,200 rpm, still on the power side of the curve, with no gear left to find.",
  },
  {
    type: "p",
    text: "The ZX-4R's inline-four makes peak torque at 12,500 rpm and peak power at 14,000 rpm. Its band from peak torque to redline is about 1,500 rpm, but at much higher engine speed, so 1,500 rpm of headroom at 14,000 rpm gives a lot more wheel torque at the same road speed than 1,500 rpm at 10,000 rpm on the twin. The ZX-4R traps in sixth at around 12,200 rpm, close to peak power, and is still pulling hard through the timing trap while the Ninja 400 is at its rev ceiling.",
  },
  {
    type: "p",
    text: "That is why a high-revving inline-four often beats a lower-revving parallel twin of the same displacement. The four turns more of its power-stroke energy into wheel torque over a wider, higher-rpm window. The twin has the same displacement; it is slower because its power band is narrower and lower, so it spends more of the quarter-mile falling away from peak power and less of it climbing toward it.",
  },
  {
    type: "h2",
    text: "The 17 kg mass penalty on the ZX-4R",
  },
  {
    type: "p",
    text: "The ZX-4R is heavier because an inline-four weighs more than a parallel twin of the same displacement: more cylinders, head studs and cam lobes, a heavier crankshaft and more cooling hardware. The 17 kg between 168 kg and 185 kg matters in a 400 cc class, where every kilogram costs roughly 0.05 seconds of ET over the quarter-mile.",
  },
  {
    type: "p",
    text: "Up to the 60-foot mark, the traction and launch-rpm phase where power-to-mass matters most, those 17 kg help the Ninja 400. A skilled rider on a Ninja 400 can be quicker than a skilled rider on a ZX-4R through the lights and into the first two gear changes. From the 1/8-mile on, the ZX-4R's 31 hp advantage outweighs the extra mass. In this sim the break-even point comes around 4 seconds into the run (within the first 60 metres), and from there the ZX-4R is ahead and pulling away.",
  },
  {
    type: "p",
    text: "Most timed events at Aamby Valley and MMRT run the full quarter mile, with the timing beam at 402 metres. A 1/8-mile strip would look different: the gap halves to around 0.4 seconds at the 1/8-mile, and a very good Ninja 400 launch against a mediocre ZX-4R launch could reverse the result. If your strip prep is about the launch rather than the top end, the Ninja 400's lower weight makes it competitive.",
  },
  {
    type: "h2",
    text: "India pricing and the ₹3.7 lakh question",
  },
  {
    type: "p",
    text: "The Ninja 400 costs about ₹5.2 lakh on-road in most Indian cities (Kawasaki India 2026 pricing), the ZX-4R about ₹8.9 lakh and the ZX-4RR roughly ₹9.3 lakh. The base ZX-4R costs about ₹3.7 lakh more than the Ninja 400. Over the quarter-mile that ₹3.7 lakh buys 0.42 seconds of ET, a cost-per-tenth of about ₹8.8 lakh per tenth of a second, which is expensive next to almost any bolt-on modification.",
  },
  {
    type: "p",
    text: 'Compare that with ₹25,000 of mods on the Ninja 400 (the sprocket-tire-ECU-filter package from the Duke/RC 390 cost-per-tenth analysis), which returns roughly 0.45-0.55 seconds of ET. That is more than the whole gap between the two bikes, for 1.5 percent of the price premium, and it brings a tuned Ninja 400 to around 12.55-12.65 seconds, close enough to race a stock ZX-4R. So "buy the ZX-4R for the strip time" is too simple an answer.',
  },
  {
    type: "table",
    rows: [
      ["Scenario", "Quarter-mile ET", "India cost"],
      ["Stock Ninja 400", "~13.1 s", "~₹5.2 lakh on-road"],
      ["Stock ZX-4R", "~12.681 s", "~₹8.9 lakh on-road"],
      ["Stock ZX-4RR", "~12.58 s", "~₹9.3 lakh on-road"],
      ["Ninja 400 + sprocket + tire + ECU + filter", "~12.6 s", "~₹5.45 lakh"],
      ["ZX-4R + sprocket + sticky rear + ECU", "~12.35 s", "~₹9.2 lakh"],
    ],
  },
  {
    type: "p",
    text: "A Ninja 400 with a front-sprocket drop (13T → 12T or 14F → 13F depending on the chain pitch you are running), a TVS Eurogrip Protorq Extreme rear, a Powertronic Stage 1 re-flash and a K&N drop-in air filter costs ₹25,000 and closes most of the gap to a stock ZX-4R. It will not beat a ZX-4R: the power advantage is built into the engine, and a sprocket, tire and flash do not add 31 hp. But it cuts the margin to under 0.15 seconds, which is within rider variance at a strip. A ZX-4R on similar mods is still about 0.35 seconds quicker, but it costs ₹3.75 lakh more.",
  },
  {
    type: "h2",
    text: "Cost-per-tenth: both bikes ranked",
  },
  {
    type: "p",
    text: "MotoQuant's parts-ROI engine sweeps the full catalog for each bike. These are the three highest-ROI mods on each, at May 2026 Indian retail prices from Store4Riders, Motousher, KustomHub and Performance Racing Store.",
  },
  {
    type: "table",
    rows: [
      ["Mod", "Bike", "ΔET (sim)", "Indian price", "₹/tenth"],
      [
        "Front sprocket drop (one tooth)",
        "Ninja 400",
        "~0.18 s",
        "₹900",
        "~₹500",
      ],
      [
        "TVS Eurogrip Protorq Extreme rear",
        "Ninja 400",
        "~0.12 s",
        "₹6,200",
        "~₹5,170",
      ],
      [
        "Powertronic Stage 1 re-flash",
        "Ninja 400",
        "~0.20 s",
        "₹14,500",
        "~₹7,250",
      ],
      ["Front sprocket drop (one tooth)", "ZX-4R", "~0.14 s", "₹950", "~₹680"],
      [
        "Sticky sport rear (Pirelli Diablo Rosso III)",
        "ZX-4R",
        "~0.10 s",
        "₹8,800",
        "~₹8,800",
      ],
      [
        "Powertronic Stage 2 ECU re-flash",
        "ZX-4R",
        "~0.18 s",
        "₹18,000",
        "~₹10,000",
      ],
    ],
  },
  {
    type: "p",
    text: "The Ninja 400 has the lower cost-per-tenth in every mod class. That comes from its lower trap speed: at a 172 km/h trap, small gains in traction and gearing move the ET more than on the ZX-4R, which is already past the point where aerodynamics and top-end power dominate. The Ninja 400's sprocket swap gives 0.18 seconds for ₹900 (₹500 per tenth), the lowest cost-per-tenth in either catalog. If all you want is the cheapest ET gain on a modest budget, the Ninja 400 gets more from every rupee.",
  },
  {
    type: "p",
    text: "The ZX-4R starts from a higher floor, though. It runs 12.681 seconds on stock rubber and stock gearing, which among Indian 400cc motorcycles sits alongside the KTM Duke 390 RC at ~13.5s and above even a moderately tuned Ninja 650 at ~12.8s. Whatever the mods, the Ninja 400 will not reach that level without forced induction or engine work.",
  },
  {
    type: "h2",
    text: "Which one for which rider",
  },
  {
    type: "p",
    text: "It depends on what your strip day looks like. Four cases:",
  },
  {
    type: "p",
    text: "1. You run the strip two or three times a year and commute on the bike the rest of the time. Buy the Ninja 400. The ₹3.7 lakh you save pays for a lot of fuel, maintenance and strip entry fees, and the 0.42-second gap costs you nothing because you are not racing anyone for money. The Ninja 400 is also much easier to manage in traffic at lower engine speeds.",
  },
  {
    type: "p",
    text: "2. You run strip events regularly and want competitive numbers in the 400cc class. Buy the ZX-4R and add a sprocket drop and a sticky rear tire. A baseline of 12.68 seconds puts you ahead of every other 400cc parallel twin in the class and within a few tenths of modded KTM RC 390s. On a stock engine, no parallel twin can match the ceiling the ZX-4R's inline-four gives you.",
  },
  {
    type: "p",
    text: "3. You already have a Ninja 400 and want to go quicker. The three-mod package (sprocket drop, sport rear, Powertronic Stage 1) costs about ₹21,600 and takes your ET from ~13.1s to roughly 12.65s. That is within a tenth of a stock ZX-4R, without paying the ₹3.7 lakh premium for a new bike.",
  },
  {
    type: "p",
    text: "4. You already own a ZX-4R and want to go lower. After the sprocket-and-tire package, the next real gains are an ECU re-flash (₹18,000, roughly 0.18s) and a slip-on exhaust (₹35,000-₹55,000, roughly 0.12-0.18s more). With all three the simulator puts the ZX-4R at roughly 12.10-12.25 seconds, close to where the 400cc inline-four class tops out on street-legal hardware, before you start on ECU unlocks and engine internals.",
  },
  {
    type: "h2",
    text: "Where to run both bikes in India",
  },
  {
    type: "p",
    text: "MotoQuant models 20 venues. The two Indian strips most used by 400cc bikes are Aamby Valley (679 m altitude, November DA about 1,100 m) and MMRT Chennai (78 m altitude, high humidity, warmer air year-round).",
  },
  {
    type: "p",
    text: "At MMRT the denser air near sea level gives both engines more power and both tires more traction. The Ninja 400 gains a little, as any naturally aspirated engine does in denser air, and the ZX-4R gains proportionally more because it has more cylinders to fill. The gap at MMRT is estimated at roughly 0.45 seconds, slightly wider than at Aamby Valley because the higher-revving engine gets more power from the denser air. Both bikes are quicker at MMRT than at Aamby Valley: the Ninja 400 by about 0.15 seconds, the ZX-4R by about 0.18 seconds.",
  },
  {
    type: "p",
    text: "At Aamby Valley in April (peak summer, DA ~1,300 m) both bikes lose power to the higher density altitude. The Ninja 400 runs roughly 0.12 seconds slower than in November and the ZX-4R roughly 0.14 seconds slower. The gap between them is essentially unchanged. The venue moves the absolute times more than it moves the order of these two bikes.",
  },
  {
    type: "callout",
    text: "To run your own venue conditions in the MotoQuant simulator, pick the month, the strip and the ambient temperature. Both the Ninja 400 and the ZX-4R are already set up in the catalog at motoquant.in/simulator. Setting the venue DA and humidity takes about 30 seconds and gives a more honest prediction than any published spec-page number.",
  },
  {
    type: "h2",
    text: "The verdict",
  },
  {
    type: "p",
    text: "The ZX-4R is the faster 400cc motorcycle in India. The 0.42-second ET gap and the 20 km/h trap-speed gap come from the engines: a 76 hp inline-four revving to 14,000 rpm is a different class of machine from a 45 hp parallel twin peaking at 10,000 rpm, and no amount of gearing or rubber will close that gap over a quarter mile. On a shorter strip, or in the first 60 metres of a run, a perfectly launched Ninja 400 can beat a badly launched ZX-4R; the 17 kg weight advantage is real at low speed. But in a full quarter with two competent riders on equal mods, the ZX-4R wins by four to five tenths.",
  },
  {
    type: "p",
    text: "The Ninja 400 is the better-value 400cc bike for most Indian riders. The ₹3.7 lakh gap is almost impossible to justify on strip performance alone: ₹25,000 of mods on a Ninja 400 comes within 0.10-0.15 seconds of a stock ZX-4R for less than 1 percent of the price difference. The Ninja 400 is also lighter in traffic, cheaper to insure and maintain, and wide enough in its own price segment to hold its resale value longer.",
  },
  {
    type: "p",
    text: "If you want the fastest 400 at the strip, buy the ZX-4R. If you want the most from your rupees, buy the Ninja 400 and spend ₹21,000 on a sprocket, a sport rear and an ECU flash.",
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
          datePublished: "2026-05-22",
        })}
      />
      <SiteNav />

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-6">
            {[
              "Kawasaki",
              "Ninja 400",
              "ZX-4R",
              "Indian 400cc",
              "comparison",
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
            Kawasaki Ninja 400 vs ZX-4R: parallel twin vs inline-four at the
            strip
          </h1>
          <div className="text-sm text-white/60 mb-12">
            22 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

        <PostBikeLinks ids={[88, 752]} />

        {/* Related reading */}
        <div className="max-w-2xl mx-auto mt-16">
          <h3 className="font-display font-bold text-lg text-white mb-4">
            Related reading
          </h3>
          <ul className="text-sm text-white/70 space-y-2">
            <li>
              ·{" "}
              <Link
                href="/blog/kawasaki-ninja-zx-4r-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Kawasaki Ninja ZX-4R quarter-mile physics: 400cc inline-four
              </Link>:{" "}
              the ZX-4R on its own: why a 76 hp 400cc runs a 12.6 when every
              other 400-class bike runs a 13.5.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM Duke 390 vs RC 390: quarter-mile physics at Aamby Valley
              </Link>:{" "}
              the same architecture-vs-aerodynamics method applied to
              KTM&apos;s two 373cc bikes.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>:{" "}
              the 15-sub-model architecture behind every ET number in this
              post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>:{" "}
              the venue conditions used for the simulations above.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the bike catalog
              </Link>:{" "}
              534 bikes, each with its own Cd, gear ratios and physics
              parameters loaded.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">
              Run both bikes yourself
            </div>
            <div className="text-white/60 text-sm">
              The simulator is free. Pick the Ninja 400 or the ZX-4R, set your
              strip conditions, and compare stock and modded ET side by side.
            </div>
          </div>
          <Link
            href="/simulator?bike=kawasaki-ninja-400"
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
