import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema, OG_IMAGE } from "../../StructuredData";

const SLUG = "how-a-2-stroke-expansion-chamber-actually-works";
const TITLE = "How a 2-stroke expansion chamber actually works";
const DESCRIPTION =
  "A pressure wave travelling at 500 m/s, a tuned-RPM peak that lasts roughly 1,500 rpm, and a 0.494 s sim bias on the 2T cluster. Plain-English physics for RX100, RD350, RGV250 and the rest.";

export const metadata = {
  title: "How a 2-stroke expansion chamber actually works",
  description: DESCRIPTION,
  keywords: [
    "two stroke expansion chamber physics",
    "2T expansion chamber tuning",
    "RX100 expansion chamber",
    "RD350 expansion chamber",
    "tuned RPM 2-stroke",
    "YPVS RC valve powervalve",
    "how 2 stroke pipe works",
    "Indian 2 stroke drag racing",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-08T00:00:00Z",
    images: [OG_IMAGE],
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "A 2-stroke expansion chamber is a tuned acoustic device. On a Yamaha RX100 it swings peak torque from roughly 35 % of its potential to 100 % across a window only about 1,500 rpm wide. Get the geometry right and the bike makes its rated 11 hp at 7,500 rpm. Get it wrong and the bike pulls like a lawnmower. The simulator currently runs the 2-stroke cluster at a +0.494 s bias against published benchmarks across five bikes. That figure is limited mostly by how few real instrumented timeslips exist for vintage Indian and Japanese 2T machines.",
  },
  {
    type: "h2",
    text: "The problem a 4-stroke engineer does not have",
  },
  {
    type: "p",
    text: "A 4-stroke engine has a closed exhaust valve for half of every cycle. Burnt charge cannot leak back, and fresh charge cannot leak out. Camshaft geometry keeps the intake and exhaust events mechanically separate. A 2-stroke has no such luxury. The piston uncovers the exhaust port before the transfer port closes, so for a window of typically 30–60 degrees of crank rotation, fresh charge from the transfer port is pushed straight out through the open exhaust port. On a piston-port engine like the RX100 there is no reed valve, no rotary valve, nothing to stop it.",
  },
  {
    type: "p",
    text: "Every gram of fresh charge that escapes the cylinder is a gram of fuel that did no work. A typical untuned piston-port 2T loses 25–40 % of its fresh charge through this window. That is most of why 2-strokes are known as dirty, smoky and inefficient. It is also why the expansion chamber matters: it catches the lost charge and stuffs it back into the cylinder before the exhaust port closes.",
  },
  {
    type: "h2",
    text: "How the pipe catches the charge",
  },
  {
    type: "p",
    text: "When the exhaust port opens, a high-pressure pulse leaves the cylinder and races down the header pipe. The speed of sound in 600 °C exhaust gas is roughly 500 m/s, about 1,800 km/h. The pulse hits the diverging cone (the forward-tapering section of the chamber) and reflects as a low-pressure wave that travels back toward the cylinder. That low-pressure return reaches the exhaust port and pulls even more fresh charge out. It sounds wrong, but it does useful work: the fresh charge fills the header pipe.",
  },
  {
    type: "p",
    text: "Then the pulse hits the converging cone (the rear-tapering section) and reflects again, this time as a high-pressure wave heading back toward the cylinder. The geometry is timed so this wave arrives at the exhaust port just before it closes, and stuffs the lost fresh charge back into the cylinder. The cylinder gets supercharged on the cheap, fuel that would have escaped is recovered, and in the band where the timing works, torque jumps by a factor of two or more.",
  },
  {
    type: "callout",
    text: 'An expansion chamber is not a muffler. A muffler reduces noise; an expansion chamber moves charge. The two are different acoustic objects with opposite design priorities, and the noise of a "loud expansion chamber" is mostly a side effect of the geometry needed to hit resonance.',
  },
  {
    type: "h2",
    text: "Why the powerband is so narrow",
  },
  {
    type: "p",
    text: "The pressure-wave round trip (out, reflect off the diverging cone, back, reflect off the converging cone, back to the port) takes the right amount of time at only one engine speed. That speed is the tuned RPM. On the RX100 the chamber is sized for 7,500 rpm. On the Suzuki RGV250 VJ22 it is sized for 10,500 rpm, and on the Aprilia RS125 race kit for 11,000 rpm. Chamber length, cone angles and belly diameter are all inputs to a single timing equation, and the equation has one root.",
  },
  {
    type: "p",
    text: "Run the engine 1,000 rpm slower than tuned RPM and the returning high-pressure wave arrives early, before the exhaust port has finished sucking out the fresh charge. The wave bounces off the still-open port and does nothing useful. Run 1,000 rpm faster than tuned RPM and the wave arrives late, after the port has already closed. Either way, you lose the charge-stuffing effect and torque collapses.",
  },
  {
    type: "p",
    text: "The MotoQuant 2-stroke torque-curve generator lives in motoquant/defaults.py and is documented in the physics-engine post. It models this with a Gaussian centred on tuned_rpm. Two parameters set the width of the Gaussian: band_lo (below tuned RPM) and band_hi (above tuned RPM). For a single-cylinder race 2T without a powervalve the defaults are band_lo = 0.25 and band_hi = 0.15, so the curve drops to baseline torque (about 25 % of peak) when you fall 25 % below tuned RPM or rise 15 % above it. On an RX100 tuned for 7,500 rpm, that is a usable window from about 5,600 rpm to 8,600 rpm. Three thousand rpm. That is your entire powerband.",
  },
  {
    type: "h2",
    text: "Tuned-RPM geometry: five bikes, five pipes",
  },
  {
    type: "p",
    text: "The catalog currently models 20 two-stroke bikes. Five of them, with tuned RPM, redline and the usable band the simulator computes from the geometry above:",
  },
  {
    type: "table",
    rows: [
      [
        "Bike",
        "Displacement",
        "Tuned RPM",
        "Redline",
        "Usable band",
        "Powervalve",
      ],
      ["Yamaha RX100", "98 cc", "7,500", "8,500", "~5,600–8,400", "No"],
      ["Yamaha RD350 (1974)", "347 cc", "7,500", "8,500", "~5,250–8,400", "No"],
      ["Aprilia RS125", "125 cc", "11,000", "12,500", "~8,250–12,400", "No"],
      [
        "Suzuki RGV250 VJ22",
        "249 cc",
        "10,500",
        "12,000",
        "~8,600–11,800",
        "AETC",
      ],
      ["Yamaha RD500LC", "499 cc", "9,500", "10,500", "~7,800–10,400", "YPVS"],
    ],
  },
  {
    type: "p",
    text: "Two patterns matter for drag racing. First, the smaller and more highly tuned the engine, the higher the tuned RPM and the narrower the usable band. The RX100's usable range is only about three thousand rpm wide. The RGV250's is roughly as wide, but at much higher rpm where the gear ratios are closer together, so the rider loses fewer revs between shifts. Second, every powervalve in the table widens the band on both sides (in the simulator constants, typically band_lo from 0.25 to 0.18 and band_hi from 0.15 to 0.12) and lifts the off-pipe baseline from 25 % of peak to closer to 30 %. YPVS, RC Valve, KIPS, AETC and HPP all do this. The mechanism varies (a rotating exhaust-port shutter on YPVS, a sliding sub-port on KIPS), but the outcome is the same: some of the resonance tuning moves from the chamber to a mechanical valve that retunes the port timing with rpm.",
  },
  {
    type: "h2",
    text: "Why the RX100 is the way it is",
  },
  {
    type: "p",
    text: "Indian 2-stroke nostalgia is mostly about the RX100, and the RX100 is mostly about the pipe. Yamaha sized the OEM expansion chamber for 7,500 rpm and a peak torque of 10.5 Nm at 6,500 rpm, with the rated 11 hp at the 7,500 rpm tuned point. The 50 mm × 50 mm bore and stroke is short-stroke for a piston-port single, which keeps mean piston speed reasonable up to redline. The 4-speed gearbox, with a 2.833 first gear and a 14F/50R 428-pitch chain, keeps the engine in the powerband at street speeds: first gear redline is around 32 km/h, second 53 km/h, third 73 km/h and fourth 93 km/h. A drag run barely uses the gearbox; most timeslips are won or lost in third gear.",
  },
  {
    type: "p",
    text: 'When Indian RX100 owners fit an aftermarket pipe, they usually choose between a "street" pipe and a "race" pipe. A street pipe (which the simulator branch for sub-200 cc piston-port singles models with band_lo = 0.35, band_hi = 0.25, baseline = 0.35) keeps a wide off-pipe shoulder, so the bike still pulls cleanly at 4,000 rpm in traffic. A race pipe pushes tuned RPM up to 8,500–9,000, narrows the band to maybe 1,800 rpm, and needs the engine to stay above 7,000. The tuned RPM depends only on the chamber geometry: longer header, smaller belly diameter and sharper cones equal a higher tuned RPM. No software, no electronics, no rider input. The pipe is the tune.',
  },
  {
    type: "callout",
    text: "Why a stock RX100 sounds nothing like a stock RD350: the RD has two independent expansion chambers fired 180° apart. The simulator branch for two-cylinder piston-port 2T (RD350, RD400, non-RAVE NSR250) uses band_lo = 0.30, band_hi = 0.15, baseline = 0.25, a wider off-pipe shoulder than a single, because two pipes firing alternately smooth out the cycle-to-cycle resonance gaps. That is also why an RD350 is so much easier to ride than an RGV250 at street speeds despite making more peak power.",
  },
  {
    type: "h2",
    text: "Drag-strip reality: why 2T bikes are hard to predict",
  },
  {
    type: "p",
    text: "The simulator currently runs a +0.494 s bias on the 2-stroke cluster across five matched benchmarks (mean |Δ| = 0.848 s, per the April 27 calibration sweep). That is the largest cluster bias in the catalog after the small-cc 4T entry segment. There are three reasons.",
  },
  {
    type: "p",
    text: '1. Benchmark scarcity. The five 2T bikes that match published instrumented data are RD350, RD400 Daytona, NSR250R MC21, RS250 and RZV500R. The Indian-market RX100 / RX135 / RXZ135 trio has zero published timed quarter-mile data. Every "12.4 second RX100" claim on a forum is a Dragy GPS app reading on a public road, not a strip timing trap. The simulator carries those bikes but cannot validate their absolute ET against magazine data.',
  },
  {
    type: "p",
    text: "2. Launch-RPM sensitivity. With a narrow powerband, launch RPM matters more on a 2T than on any 4T bike. For 2-stroke bikes, the MotoQuant staging block uses launch_rpm = max(peak_torque_rpm, tuned_rpm), capped at 0.96 × redline. That fix went in during April 2026, after the original code tried to launch a 2T at peak_torque_rpm and ended up below the powerband. A real rider on a real RD350 has to two-step (launch with the throttle held against an RPM limiter) at exactly tuned RPM, or the bike bogs straight off the line. A 200 rpm error in launch RPM moves the simulated ET by 0.15–0.25 seconds. A real rider gets within maybe 500 rpm. The cluster bias absorbs that uncertainty.",
  },
  {
    type: "p",
    text: "3. Modded versus stock. Most published RD350 and RGV250 quarter-mile times come from modified bikes: bigger pipes, ported barrels, jet kits, sometimes a head shave. The simulator runs them stock. So when the simulator puts an RD350 at 14.18 seconds and a Cycle World 1973 magazine test reads 13.9 seconds, the magazine bike was likely running stage-1 mods that nobody bothered to log. The +0.5 second residual is real, but it is mostly a documentation problem rather than a physics one.",
  },
  {
    type: "h2",
    text: "What an expansion chamber costs per tenth",
  },
  {
    type: "p",
    text: "The MotoQuant parts catalog has 13 dedicated expansion chambers across the 2T fleet (JL, Tyga, Jolly Moto, Arrow, DEP, Higgspeed, Moto Carrera, MAC, FMF) covering RD350, RD400, RD500, RX, RS, GP250, H2, GT750, KTM, CR500, TZR and Yezdi. A typical aftermarket pipe for an RX100 lists at roughly ₹4,500–₹8,500 in India. For an RD350 with twin expansion chambers, the pair runs ₹15,000–₹28,000. The simulator scores each part on each bike. A JL Hand-Made expansion chamber on an RX100 moves the simulated ET by roughly 0.5–0.7 seconds for about ₹6,000, which works out to ₹900–₹1,200 per tenth, among the highest-ROI mods anywhere in the catalog. Compare that with a Powertronic ECU flash on a 4T 200cc bike at ₹14,000 for ~0.25 seconds (₹5,600 per tenth) or an Akrapovic slip-on at ₹35,000 for ~0.15 seconds (₹23,000 per tenth).",
  },
  {
    type: "p",
    text: "2T pipes pay back this well because of the physics described above. An aftermarket 4T exhaust changes flow restriction by maybe 5–15 %; the engine still has cams, valves and a closed exhaust event between fresh charge and exhaust gas. A 2T pipe changes the thermodynamics of the whole cycle. No single part on a 4-stroke has that much effect.",
  },
  {
    type: "h2",
    text: "What this means for Indian 2T riders",
  },
  {
    type: "p",
    text: "If you ride a 2-stroke in India in 2026, you are in a small and shrinking community. Most production 2T bikes are gone; the KTM 300 EXC and imported second-hand Japanese bikes are what is left. Used RX100s in clean condition trade for ₹1.2–₹1.8 lakh in Mumbai and Bangalore. RD350s in Punjab and Tamil Nadu trade for ₹4–8 lakh. The simulator catalog covers 20 of these bikes because they are the heart of the Indian 2T drag-strip and street scene, and because the Indian aftermarket still supplies pipes, reed valves and powervalve controllers (Zeeltronic, Nova SAPC) for them.",
  },
  {
    type: "p",
    text: "For drag racing, the physics gives four pieces of advice. First, match your launch RPM to your tuned RPM, which is the resonance of your own pipe, not the peak torque or peak power RPM. Second, do not lean on gearing changes the way 4T riders do; the powerband is narrower than your gear-ratio steps, so the bike will fall off the pipe between shifts whatever you do. Third, put the pipe ahead of everything else. A perfect pipe with a stock barrel beats a tuned barrel with the wrong pipe every time. Fourth, expect the simulator to be optimistic by roughly half a second on stock 2T bikes. That calibration bias is documented, and it is closing as more real Indian 2T owners submit timeslips.",
  },
  {
    type: "h2",
    text: "Run the numbers",
  },
  {
    type: "p",
    text: "The simulator at motoquant.in lets you pick any of the 20 catalog 2T bikes and sweep tuned RPM, launch RPM, rider weight, ambient temperature and pipe choice live. The torque curve redraws as you go, so you can watch the Gaussian narrow when you switch a powervalve flag off, or the off-pipe baseline rise when you change band_lo. It is the cheapest way in India to feel the physics before you buy a pipe.",
  },
  {
    type: "p",
    text: "The chamber supercharges without a turbo and recovers charge without a valve, and the whole trick is timed to the speed of sound in the exhaust gas. Every other tuning choice on a 2T bike (gearing, ignition, jetting, port timing) comes after getting the pipe right.",
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
          datePublished: "2026-05-08",
        })}
      />
      <SiteNav />

      <article id="main" className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["2-stroke", "expansion chamber", "physics", "RX100", "RD350"].map(
              (t) => (
                <span
                  key={t}
                  className="px-2.5 py-1 rounded-full bg-accent/10 border border-accent/25 text-xs font-medium text-accent"
                >
                  {t}
                </span>
              ),
            )}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            How a 2-stroke expansion chamber actually works
          </h1>
          <div className="text-sm text-white/60 mb-12">
            8 May 2026 · 11 min read · MotoQuant Blog
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
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>:{" "}
              the 15-sub-model architecture, including the 2T torque-curve
              branch referenced in this post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The physics of a perfect launch
              </Link>:{" "}
              why 2T launch RPM matters more than 4T launch RPM, in
              clutch-and-slip terms.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why your R15 won&apos;t hit 14s
              </Link>:{" "}
              the 4-stroke counterpart to this post (small-cc gearing and
              traction limits).
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for Aamby Valley in November
              </Link>:{" "}
              the venue conditions used for the simulation numbers in this
              post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>,{" "}
              including all 20 two-stroke entries (RD350, RX100, RGV250,
              RS125, NSR250, KTM 300 EXC, and more).
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">
              Sweep tuned RPM live
            </div>
            <div className="text-white/60 text-sm">
              Free simulator: pick an RX100, RD350 or RGV250, drag the
              launch-RPM slider and watch the Gaussian torque curve and ET
              update in real time.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-rx100"
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
