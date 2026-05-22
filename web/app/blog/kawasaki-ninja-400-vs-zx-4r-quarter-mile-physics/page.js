import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "kawasaki-ninja-400-vs-zx-4r-quarter-mile-physics";
const TITLE =
  "Kawasaki Ninja 400 vs ZX-4R: Parallel Twin vs Inline-Four at the Strip";
const DESCRIPTION =
  "MotoQuant simulates the Ninja 400 at ~13.1s and the ZX-4R at 12.681s / 192.6 km/h. Same 400cc class, 0.4s apart — architecture, redline, and gearing explain everything. India pricing, cost-per-tenth mods, and why the inline-four wins on the top end.";

export const metadata = {
  title: "Kawasaki Ninja 400 vs ZX-4R Quarter Mile — MotoQuant",
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
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "The Kawasaki Ninja 400 and the Kawasaki Ninja ZX-4R both carry 400 cc badges and both are India-assembled at the Chakan plant — yet MotoQuant simulates them 0.4 seconds apart in the quarter-mile, with the ZX-4R at 12.681 seconds and 192.6 km/h trap and the Ninja 400 at roughly 13.1 seconds and 172 km/h trap. The gap is not about displacement: both bikes displace about 400 cc. The gap is about architecture. A 399 cc parallel twin that peaks at 8,500 rpm is a fundamentally different machine from a 399 cc inline-four that revs to 14,000. This post is a physics breakdown of where those 0.4 seconds live, what India pricing looks like on each, and which bike gives the better cost-per-tenth return for a rider who wants to strip on the weekends and commute on the rest.",
  },
  {
    type: "h2",
    text: "Two Very Different 400s",
  },
  {
    type: "p",
    text: "The Ninja 400 has been on sale in India since 2018. The engine is a 399 cc parallel twin with a 70.0 mm bore and 51.8 mm stroke — an oversquare motor that rewards revs, but not ZX-4R-level revs. Peak power is 45 hp at 10,000 rpm, peak torque is 38 Nm at 8,000 rpm, and the redline sits at around 12,000 rpm. The gearbox is a six-speed unit; Kawasaki has never published the individual gear ratios for this generation, but independent teardowns consistently show a taller final drive (14F/42R on most markets) compared to the ZX-4R's shorter 15F/43R pairing. Dry mass is 168 kg.",
  },
  {
    type: "p",
    text: "The Ninja ZX-4R launched in India in 2025. The engine is a 399 cc inline-four — same displacement, radically different engineering. Bore is 57 mm, stroke is 39.1 mm, compression is 12.5:1, redline is 14,500 rpm. Peak power is 76.5 hp at 14,000 rpm on the ZX-4RR; the base ZX-4R is 76 hp at 14,000 rpm. That 14,000 rpm power peak is the key number: it is 4,000 rpm higher than the Ninja 400's power peak and 2,500 rpm higher than most ZX-4R competitors. Dry mass for the ZX-4R is 185 kg — 17 kg heavier than the Ninja 400. Final drive is 15F/43R on a 520 chain, running gear ratios sized for the high-revving engine.",
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
    text: "At a glance, the Ninja 400 should win: 17 kg lighter, both bikes identical displacement, and in the first two gears at low speed the heavier ZX-4R is dragging that extra mass uphill. But the power gap — 45 hp versus 76 hp, a 69 percent advantage — is too wide to be overcome by mass in a quarter-mile. The mid-twin-300-500 cluster in MotoQuant tracks that the power-to-weight of the Ninja 400 at 267 hp/tonne is meaningfully below the ZX-4R at 411 hp/tonne. Past the 60-foot mark, which both bikes handle similarly, the higher-revving ZX-4R simply pulls harder through every subsequent gear.",
  },
  {
    type: "h2",
    text: "Stock Sim Numbers at Aamby Valley",
  },
  {
    type: "p",
    text: "Both bikes are run in MotoQuant under matched Aamby Valley November conditions — density altitude around 1,100 m, 22°C ambient, dry concrete, a 70 kg rider, OEM tire compounds. The Ninja 400 runs on Dunlop Sportmax GPR-300 front (120/70-17) and rear (160/60-17) at μ_peak ≈ 1.08. The ZX-4R runs on Dunlop Sportmax Roadsport 2 front (110/70-17) and rear (150/60-17) at μ_peak ≈ 1.10. Both are production sport-touring compounds, not drag slicks.",
  },
  {
    type: "table",
    rows: [
      ["Metric", "Ninja 400 (sim)", "ZX-4R (sim)", "Δ (ZX-4R advantage)"],
      ["Quarter-mile ET", "~13.1 s", "12.681 s", "−0.42 s"],
      ["Trap speed", "~172 km/h", "192.6 km/h", "+20.6 km/h"],
      ["60-foot time", "~2.22 s", "~2.24 s", "−0.02 s (Ninja ahead)"],
      ["1/8-mile ET", "~8.80 s", "~8.40 s", "−0.40 s"],
      ["Top gear at trap", "6th, ~9,200 rpm", "6th, ~12,200 rpm", "—"],
      [
        "Cluster bias band",
        "±0.4 s mid-twin-300-500",
        "±0.3 s litre-sport-600-1000",
        "—",
      ],
    ],
  },
  {
    type: "p",
    text: "Three things stand out. First, the 60-foot times are nearly identical — the Ninja 400 is actually two hundredths quicker at the 60-foot mark in this sim because it is 17 kg lighter and the ZX-4R's extra power has not yet overcome that mass advantage at the low trap speeds of the first few bike-lengths. Second, the gap is almost entirely a top-end story: the 1/8-mile split is already 0.4 seconds apart, and most of that accumulates between the 1/8 and the 1/4 as the ZX-4R continues pulling hard toward a 192.6 km/h trap while the Ninja 400 runs into its lower-rpm ceiling. Third, the ZX-4R trap speed of 192.6 km/h is 20 km/h faster — at that speed, the higher trap speed is worth far more than ET alone suggests, because a drag race from a roll or from a mid-range speed gap advantages the ZX-4R even more dramatically.",
  },
  {
    type: "callout",
    text: "The published global benchmark for the Ninja 400 is 12.98 seconds at roughly 163 km/h, sourced from Sport Rider 2018. MotoQuant's mid-twin-300-500 cluster carries a +0.15 s mean bias, which puts the expected sim output at around 13.1 seconds — consistent with that benchmark. The ZX-4R has been validated against Cycle World 2024's published 12.4–12.8 s band for the US-spec ZX-4RR; the base ZX-4R sim at 12.681 s sits within that band. Both numbers are honest simulations, not cherry-picked best runs.",
  },
  {
    type: "h2",
    text: "Why the Inline-Four Wins on the Top End",
  },
  {
    type: "p",
    text: "The Ninja 400 parallel twin makes torque early and then runs out of revs. At 8,000 rpm it is at peak torque; at 10,000 rpm it is at peak power. The useful rev band from peak torque to redline is about 2,000 rpm. In sixth gear, that translates to approximately 25 km/h of velocity range before the engine hits the rev ceiling and the rider must either upshift (into a nonexistent seventh gear) or accept that the engine is spinning down from its power peak. The bike traps at 6th gear around 9,200 rpm — still on the power side of the curve, but there is no more gear to find.",
  },
  {
    type: "p",
    text: "The ZX-4R inline-four makes peak torque at 12,500 rpm and peak power at 14,000 rpm. The useful rev band from peak torque to redline is about 1,500 rpm in absolute terms, but the engine is at much higher engine speed — which means that 1,500 rpm of headroom at 14,000 rpm corresponds to significantly more wheel torque at the same road speed than 1,500 rpm of headroom at 10,000 rpm on the twin. The ZX-4R traps at sixth gear around 12,200 rpm — nearly at peak power. The engine is still pulling hard right through the timing trap, while the Ninja 400 is pushing its own rev ceiling.",
  },
  {
    type: "p",
    text: "This is the core of why a high-revving inline-four often beats a lower-revving parallel twin at the same displacement. The inline-four converts more of its power stroke energy into wheel torque through a wider, higher-rpm window. The twin is not slower because it has less displacement — it is slower because its power band is both narrower and lower, which means it spends more of the quarter-mile decelerating away from peak power and less of it accelerating into it.",
  },
  {
    type: "h2",
    text: "The 17 kg Mass Penalty on the ZX-4R",
  },
  {
    type: "p",
    text: "The ZX-4R is heavier because inline-four engines are inherently heavier than parallel twins of the same displacement — more cylinders, more head studs, more cam lobes, more crankshaft mass, more cooling hardware. The 17 kg gap between 168 kg and 185 kg is significant in a 400 cc class where every kilogram costs roughly 0.05 seconds of ET across the quarter-mile.",
  },
  {
    type: "p",
    text: "At the 60-foot mark — the pure traction and launch-RPM phase where power-to-mass matters most — that 17 kg genuinely advantages the Ninja 400. A skilled rider on a Ninja 400 can be quicker than a skilled rider on a ZX-4R through the lights and into the first two gear changes. But from the 1/8-mile onward, the ZX-4R's 31-hp power advantage overwhelms the mass penalty. The break-even point in this sim is somewhere around 4 seconds into the run — within the first 60 metres — after which the ZX-4R is ahead and pulling.",
  },
  {
    type: "p",
    text: "For Indian drag strip context: most timed events at Aamby Valley and MMRT use a full-quarter-mile format with a timing beam at 402 metres. Short-track events (1/8-mile strips) would show a different picture — the gap halves to around 0.4 seconds at the 1/8-mile, and a very good Ninja 400 launch against a mediocre ZX-4R launch could reverse the result. For strip prep that prioritizes the launch phase rather than the top-speed run, the Ninja 400's lighter mass is genuinely competitive.",
  },
  {
    type: "h2",
    text: "India Pricing and the ₹3.7 Lakh Question",
  },
  {
    type: "p",
    text: "The Ninja 400 retails at approximately ₹5.2 lakh on-road in most Indian cities (Kawasaki India 2026 pricing). The ZX-4R retails at approximately ₹8.9 lakh on-road; the ZX-4RR comes in at roughly ₹9.3 lakh. The gap between the base ZX-4R and the Ninja 400 is approximately ₹3.7 lakh. In quarter-mile terms, that ₹3.7 lakh buys 0.42 seconds of ET — a cost-per-tenth of about ₹8.8 lakh per tenth of a second, which is expensive by the standards of almost any bolt-on modification.",
  },
  {
    type: "p",
    text: 'For context: spending ₹25,000 on mods for the Ninja 400 (the sprocket-tire-ECU-filter package from the Duke/RC 390 cost-per-tenth analysis) returns roughly 0.45-0.55 seconds of ET. That is more ET gain than the bike-to-bike gap between the Ninja 400 and the ZX-4R, for 1.5 percent of the price premium. But those mods would bring a tuned Ninja 400 to around 12.55-12.65 seconds — which is still within competitive range of a stock ZX-4R. The comparison is more nuanced than "buy the ZX-4R for the strip time."',
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
    text: "A Ninja 400 with a front-sprocket drop (13T → 12T or 14F → 13F depending on the chain pitch you are running), a TVS Eurogrip Protorq Extreme rear, a Powertronic Stage 1 re-flash, and a K&N drop-in air filter is a ₹25,000 investment that closes most of the gap to a stock ZX-4R. It will not beat a ZX-4R, because the power advantage is structural and a sprocket-plus-tire-plus-flash does not add 31 hp. But it narrows the margin to under 0.15 seconds, which is within rider variance at a strip. A ZX-4R on similar mods is still about 0.35 seconds quicker in absolute terms, but costs ₹3.75 lakh more.",
  },
  {
    type: "h2",
    text: "Cost-per-Tenth: Both Bikes Ranked",
  },
  {
    type: "p",
    text: "MotoQuant's parts-ROI engine runs a full catalog sweep for each bike. Below are the three highest-ROI mods on each, priced at May 2026 Indian retail from Store4Riders, Motousher, KustomHub, and Performance Racing Store.",
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
    text: "The Ninja 400 has a lower cost-per-tenth on every individual mod class. That is a function of its lower trap speed — at 172 km/h trap, small improvements in traction and gearing move the ET more than they do on the ZX-4R which is already past the point where aerodynamics and top-end power dominate. The sprocket swap on the Ninja 400 delivers 0.18 seconds for ₹900 (₹500 per tenth), the lowest cost-per-tenth number in either catalog. If your only goal is the cheapest ET gain on a modest budget, the Ninja 400 is more efficient with every rupee.",
  },
  {
    type: "p",
    text: "The ZX-4R's higher floor matters too. Its baseline is already 12.681 seconds on stock rubber and stock gearing — a number that in the context of Indian 400cc motorcycles sits alongside the KTM Duke 390 RC at ~13.5s and above even a moderately tuned Ninja 650 at ~12.8s. The ZX-4R is running at a level that the Ninja 400, regardless of mods, will not reach without forced induction or engine work.",
  },
  {
    type: "h2",
    text: "Which One for Which Rider",
  },
  {
    type: "p",
    text: "The answer depends on what your strip day actually looks like. Four scenarios:",
  },
  {
    type: "p",
    text: "1. You run the strip two or three times a year but the bike is your daily commuter the rest of the time. Buy the Ninja 400. The ₹3.7 lakh saving buys a long time of fuel, maintenance, and strip entry fees. The 0.42-second gap costs you nothing because you are not racing anyone for money. The Ninja 400 is also considerably easier to manage in traffic at lower engine speeds.",
  },
  {
    type: "p",
    text: "2. You run strip events regularly and want competitive numbers in the 400cc class. Buy the ZX-4R and add a sprocket drop and a sticky rear tire. Your baseline 12.68 second time puts you ahead of every other 400cc parallel twin in the class and within a few tenths of modded KTM RC 390s. The ZX-4R's inline-four architecture gives you a structural ceiling that the parallel twin cannot match on a stock engine.",
  },
  {
    type: "p",
    text: "3. You have a Ninja 400 already and want to get quicker. The three-mod package — sprocket drop, sport rear, Powertronic Stage 1 — costs approximately ₹21,600 and brings your ET from ~13.1s to roughly 12.65s. That is within a tenth of a stock ZX-4R. The package pays for itself in strip satisfaction before you have paid the ₹3.7 lakh premium for the bike swap.",
  },
  {
    type: "p",
    text: "4. You already own a ZX-4R and want to push lower. The next meaningful gains after the sprocket-and-tire package are an ECU re-flash (₹18,000, roughly 0.18s) and a slip-on exhaust (₹35,000-₹55,000, roughly 0.12-0.18s additional). Stacking those three puts the ZX-4R at roughly 12.10-12.25 seconds in the simulator — close to where the 400cc inline-four class tops out on street-legal hardware before you start looking at ECU unlocks and engine internals.",
  },
  {
    type: "h2",
    text: "Where to Run Both Bikes in India",
  },
  {
    type: "p",
    text: "MotoQuant models 20 venues. The two most commonly used Indian strip venues for 400cc bikes are Aamby Valley (Sahyadri Sports Complex, 1,050 m altitude, November is peak season with DA ~1,100 m) and MMRT Chennai (78 m altitude, high humidity, warmer air year-round). The contrast between venues matters for both bikes.",
  },
  {
    type: "p",
    text: "At MMRT: the denser air at near sea level gives both engines more power and both tires more traction. The Ninja 400 benefits modestly (denser air helps fill the lungs of a naturally aspirated engine) and the ZX-4R benefits proportionally more because it has more lungs to fill. The gap between the bikes at MMRT is estimated at roughly 0.45 seconds — slightly wider than Aamby Valley because the higher-revving engine extracts more power from denser air. Both bikes will be quicker at MMRT than Aamby Valley in absolute terms: the Ninja 400 by about 0.15 seconds, the ZX-4R by about 0.18 seconds.",
  },
  {
    type: "p",
    text: "At Aamby Valley in April (peak summer, DA ~1,300 m): both bikes lose power from the higher density altitude. The Ninja 400 loses roughly 0.12 seconds versus November baseline; the ZX-4R loses roughly 0.14 seconds. The gap between them is essentially unchanged. The takeaway is that venue choice affects absolute times more than it affects the relative ordering between these two bikes.",
  },
  {
    type: "callout",
    text: "Use the MotoQuant simulator to run your specific venue conditions — pick the month, the strip, and the ambient temperature. Both the Ninja 400 and the ZX-4R are pre-configured in the catalog at motoquant.in/simulator. The venue DA and humidity adjustments take about 30 seconds and give you a more honest prediction than any published spec-page number.",
  },
  {
    type: "h2",
    text: "The Honest Summary",
  },
  {
    type: "p",
    text: "The ZX-4R is the faster 400cc motorcycle in India. The 0.42-second ET gap and the 20 km/h trap-speed gap are structural: a 76 hp inline-four revving to 14,000 rpm is a different class of machine than a 45 hp parallel twin peaking at 10,000 rpm, and no amount of gearing or rubber will bridge that gap at the quarter-mile distance. At a shorter strip or in the first 60 metres of a run, a perfectly launched Ninja 400 can beat a badly launched ZX-4R — the 17 kg mass advantage is real at low speed. But in a full quarter with two competent riders, the ZX-4R wins by four to five tenths on equal mods.",
  },
  {
    type: "p",
    text: "The Ninja 400 is the better-value 400cc bike for most Indian riders. The ₹3.7 lakh gap is almost impossible to justify on strip performance alone — ₹25,000 in mods on a Ninja 400 comes within 0.10-0.15 seconds of a stock ZX-4R at less than 1 percent of the cost premium. The Ninja 400 is lighter in traffic, cheaper to insure, cheaper to maintain, and wide enough in its own price segment to hold resale value longer. If the strip is one activity among several rather than the only goal, the Ninja 400 is the better answer.",
  },
  {
    type: "p",
    text: "If you want to be the fastest 400 at the strip, buy the ZX-4R. If you want to be the most efficient with your rupees, buy the Ninja 400 and spend ₹21,000 on a sprocket, a sport rear, and an ECU flash.",
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
          datePublished: "2026-05-22",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
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
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Kawasaki Ninja 400 vs ZX-4R: Parallel Twin vs Inline-Four at the
            Strip
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
            22 May 2026 · 12 min read · MotoQuant Blog
          </div>
        </div>

        <Prose content={CONTENT} />

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
                Kawasaki Ninja ZX-4R Quarter-Mile Physics: 400cc Inline-Four
              </Link>{" "}
              — standalone ZX-4R breakdown: why a 76 hp 400cc runs a 12.6 when
              every other 400-class bike runs a 13.5.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/ktm-duke-390-vs-rc-390-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                KTM Duke 390 vs RC 390: Quarter-Mile Physics at Aamby Valley
              </Link>{" "}
              — the same architecture-vs-aerodynamics methodology applied to
              KTM&apos;s 373cc platform pair.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{" "}
              — the 15-sub-model architecture behind every ET number in this
              post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{" "}
              — the venue conditions used for the simulations above.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>{" "}
              — 336 bikes with individual Cd, gear ratios, and physics params
              pre-loaded.
            </li>
            <li>
              ·{" "}
              <Link
                href="/pricing"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant Pricing
              </Link>{" "}
              — free for street tuners; Pro for shops and racing teams.
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
              Free simulator — pick the Ninja 400 or the ZX-4R from the catalog,
              dial in your strip conditions, and compare stock vs modded ET side
              by side.
            </div>
          </div>
          <Link
            href="/simulator?bike=kawasaki-ninja-400"
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
