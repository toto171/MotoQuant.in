import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";
import { REPO_URL } from "../../../lib/site";

const SLUG = "how-a-2-stroke-expansion-chamber-actually-works";
const TITLE = "How a 2-Stroke Expansion Chamber Actually Works";
const DESCRIPTION =
  "A pressure wave travelling at 500 m/s, a tuned-RPM peak that lasts roughly 1,500 rpm, and a 0.494 s sim bias on the 2T cluster. Plain-English physics for RX100, RD350, RGV250 and the rest.";

export const metadata = {
  title: "How a 2-Stroke Expansion Chamber Actually Works — MotoQuant",
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
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "A 2-stroke expansion chamber is a precision-tuned acoustic instrument that, on a Yamaha RX100, swings peak torque from roughly 35 % of its potential to 100 % across a window only about 1,500 rpm wide. Get the geometry right and the bike makes its rated 11 hp at 7,500 rpm. Get it wrong and the bike pulls like a lawnmower. The physics is simple, the numbers are unforgiving, and the simulator currently runs the 2-stroke cluster at a +0.494 s bias against published benchmarks across five bikes — honest data, mostly limited by how few real instrumented timeslips exist for vintage Indian and Japanese 2T machines.",
  },
  {
    type: "h2",
    text: "The Problem a 4-Stroke Engineer Does Not Have",
  },
  {
    type: "p",
    text: "A 4-stroke engine has a closed exhaust valve for half of every cycle. Burnt charge cannot leak back, fresh charge cannot leak out. The intake and exhaust events are mechanically separated by camshaft geometry. A 2-stroke has no such luxury. The piston uncovers the exhaust port before the transfer port closes, which means there is a window — typically 30–60 degrees of crank rotation — where fresh charge from the transfer port is being pushed straight out through the open exhaust port. On a piston-port engine like the RX100 there is no reed valve, no rotary valve, nothing to stop it.",
  },
  {
    type: "p",
    text: "Every gram of fresh charge that escapes the cylinder is a gram of fuel that did no work. A typical un-tuned piston-port 2T loses 25–40 % of its fresh charge through this window. That is most of the reason 2-strokes have a reputation for being dirty, smoky, and inefficient. It is also the reason an expansion chamber matters: the chamber is what catches the lost charge and stuffs it back into the cylinder before the exhaust port closes.",
  },
  {
    type: "h2",
    text: "How the Pipe Catches the Charge",
  },
  {
    type: "p",
    text: "When the exhaust port opens, a high-pressure pulse leaves the cylinder and races down the header pipe. The speed of sound in 600 °C exhaust gas is roughly 500 m/s — about 1,800 km/h. The pulse hits the diverging cone (the forward-tapering section of the chamber) and reflects as a low-pressure wave that travels back toward the cylinder. That low-pressure return arrives at the exhaust port and helps suck even more fresh charge out — which is the part that sounds wrong but is actually doing useful work. The fresh charge fills the header pipe.",
  },
  {
    type: "p",
    text: "Then the pulse hits the converging cone (the rear-tapering section) and reflects again — this time as a high-pressure wave that comes back toward the cylinder. The geometry is timed so this returning high-pressure wave arrives at the exhaust port just before it closes, and stuffs the lost fresh charge back into the cylinder. Net effect: the cylinder gets supercharged on the cheap, fuel that would have escaped is recovered, and torque jumps by a factor of two or more in the band where the timing works.",
  },
  {
    type: "callout",
    text: 'The key insight: an expansion chamber is not a muffler. Mufflers reduce noise. Expansion chambers move charge. The two are different acoustic objects with opposite design priorities, and a "loud expansion chamber" is mostly a side effect of the geometry needed to hit resonance.',
  },
  {
    type: "h2",
    text: "Why the Powerband Is So Narrow",
  },
  {
    type: "p",
    text: "The pressure-wave round trip — out, reflect off the diverging cone, back, reflect off the converging cone, back to the port — only takes the right amount of time at one engine speed. That speed is the tuned RPM. On the RX100 the chamber is sized for 7,500 rpm. On the Suzuki RGV250 VJ22 it is sized for 10,500 rpm. On the Aprilia RS125 race kit it is sized for 11,000 rpm. The chamber length, cone angles, and belly diameter are all geometric inputs to a single timing equation, and the equation has one root.",
  },
  {
    type: "p",
    text: "Run the engine 1,000 rpm slower than tuned RPM and the returning high-pressure wave arrives early — before the exhaust port has finished sucking out the fresh charge. The wave bounces off the still-open port and does nothing useful. Run 1,000 rpm faster than tuned RPM and the wave arrives late — after the port has already closed. Either way, you lose the charge-stuffing effect and torque collapses.",
  },
  {
    type: "p",
    text: "The MotoQuant 2-stroke torque-curve generator, which lives in motoquant/defaults.py and is documented in the physics-engine post, models this with a Gaussian centred on tuned_rpm. The width of the Gaussian is set by two parameters called band_lo (below tuned RPM) and band_hi (above tuned RPM). For a single-cylinder race 2T without a powervalve the defaults are band_lo = 0.25 and band_hi = 0.15 — meaning the curve drops to baseline torque (about 25 % of peak) when you fall 25 % of tuned RPM below or 15 % above. On a 7,500-rpm-tuned RX100 that is a usable window from about 5,600 rpm to 8,600 rpm. Three thousand rpm. That is your entire powerband.",
  },
  {
    type: "h2",
    text: "Tuned-RPM Geometry: Five Bikes, Five Pipes",
  },
  {
    type: "p",
    text: "The catalog currently models 20 two-stroke bikes. Five representative ones, with their tuned RPM, redline, and the resulting usable band the simulator computes from the geometry above:",
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
    text: "Two patterns matter for drag racing. First, the smaller and more highly-tuned the engine, the higher the tuned RPM and the narrower the usable band. The RX100 has a usable range only about three thousand rpm wide; the RGV250 has roughly the same absolute width but at much higher rpm where the gear ratios are tighter, so the rider sees fewer dropped revs between shifts. Second, every powervalve in the table widens the band on both sides — typically band_lo from 0.25 to 0.18 and band_hi from 0.15 to 0.12 in the simulator constants — and lifts the off-pipe baseline from 25 % of peak to closer to 30 %. That is what YPVS, RC Valve, KIPS, AETC, and HPP all do. The mechanism varies (rotating exhaust-port shutter on YPVS, sliding sub-port on KIPS), but the outcome is the same: take some of the resonance specificity away from the chamber and recover it through a mechanical valve that retunes the port timing per rpm.",
  },
  {
    type: "h2",
    text: "Why the RX100 Is the Way It Is",
  },
  {
    type: "p",
    text: "Indian 2-stroke nostalgia is mostly about the RX100, and the RX100 is mostly about the pipe. Yamaha sized the OEM expansion chamber for 7,500 rpm and a peak torque of 10.5 Nm at 6,500 rpm, with rated 11 hp at the 7,500 rpm tuned point. The 50 mm × 50 mm bore-and-stroke geometry is short-stroke for a piston-port single, which keeps mean piston speed reasonable up to redline. The 4-speed gearbox with a 2.833 first ratio and a 14F/50R 428-pitch chain keeps the engine in the powerband at street speeds — first gear redline is around 32 km/h, second is 53 km/h, third is 73 km/h, fourth is 93 km/h. A drag run barely uses the gearbox; most timeslips are won or lost in third gear.",
  },
  {
    type: "p",
    text: 'When Indian RX100 owners fit aftermarket pipes, the choice is usually between a "street" pipe and a "race" pipe. A street pipe — what the simulator branch for sub-200 cc piston-port singles models with band_lo = 0.35, band_hi = 0.25, baseline = 0.35 — keeps a wide off-pipe shoulder so the bike still pulls cleanly at 4,000 rpm in traffic. A race pipe pushes tuned RPM up to 8,500–9,000, narrows the band to maybe 1,800 rpm wide, and demands the engine never drop below 7,000. The tuned RPM choice is purely a function of the chamber geometry: longer header, smaller belly diameter, sharper cones equal a higher tuned RPM. There is no software, no electronics, and no rider input — the pipe IS the tune.',
  },
  {
    type: "callout",
    text: "Why a stock RX100 sounds nothing like a stock RD350: the RD has two independent expansion chambers fired 180° apart. The simulator branch for two-cylinder piston-port 2T (RD350, RD400, non-RAVE NSR250) uses band_lo = 0.30, band_hi = 0.15, baseline = 0.25 — wider off-pipe shoulder than a single, because two pipes firing alternately smooth out the cycle-to-cycle resonance gaps. That is also why an RD350 is so much easier to ride than an RGV250 at street speeds despite making more peak power.",
  },
  {
    type: "h2",
    text: "Drag-Strip Reality: Why 2T Bikes Are Hard to Predict",
  },
  {
    type: "p",
    text: "The simulator currently runs a +0.494 s bias on the 2-stroke cluster across five matched benchmarks (mean |Δ| = 0.848 s, per the April 27 calibration sweep). That is the largest cluster bias in the catalog after the small-cc 4T entry segment. There are three reasons.",
  },
  {
    type: "p",
    text: '1. Benchmark scarcity. The five 2T bikes that match published instrumented data are RD350, RD400 Daytona, NSR250R MC21, RS250, and RZV500R. The Indian-market RX100 / RX135 / RXZ135 trio has zero published timed quarter-mile data — every "12.4 second RX100" claim on a forum is a Dragy GPS app reading on a public road, not a strip timing trap. The simulator carries those bikes but cannot validate their absolute ET against magazine data.',
  },
  {
    type: "p",
    text: "2. Launch-RPM sensitivity. Because the powerband is narrow, the launch RPM matters more on a 2T than on any 4T bike. The MotoQuant staging block uses launch_rpm = max(peak_torque_rpm, tuned_rpm) capped at 0.96 × redline for 2-stroke bikes — a fix added in April 2026 after the original implementation tried to launch a 2T at peak_torque_rpm and ended up below the powerband. A real rider on a real RD350 has to two-step (launch with the throttle held against an RPM limiter) at exactly tuned RPM or the bike bogs straight off the line. A 200 rpm error in launch RPM moves the simulated ET by 0.15–0.25 seconds. A real rider gets it within maybe 500 rpm. The cluster bias absorbs that uncertainty.",
  },
  {
    type: "p",
    text: "3. Modded versus stock. Most published RD350 and RGV250 quarter-mile times are from modified bikes — bigger pipes, ported barrels, jet kits, sometimes a head shave. The simulator runs them stock. So when the simulator sims an RD350 at 14.18 seconds and a Cycle World 1973 magazine test reads 13.9 seconds, the magazine bike was likely running stage-1 mods that nobody bothered to log. The +0.5 second residual is real but mostly a documentation problem, not a physics problem.",
  },
  {
    type: "h2",
    text: "What an Expansion Chamber Costs in Cost-per-Tenth Terms",
  },
  {
    type: "p",
    text: "The MotoQuant parts catalog ships 13 dedicated expansion chambers across the 2T fleet — JL, Tyga, Jolly Moto, Arrow, DEP, Higgspeed, Moto Carrera, MAC, FMF — covering RD350, RD400, RD500, RX, RS, GP250, H2, GT750, KTM, CR500, TZR, and Yezdi. A typical aftermarket pipe for an RX100 lists at roughly ₹4,500–₹8,500 in India. For an RD350 with twin expansion chambers, the pair runs ₹15,000–₹28,000. The simulator scores these explicitly per part per bike: a JL Hand-Made expansion chamber on an RX100 moves the simulated ET by roughly 0.5–0.7 seconds at a cost of about ₹6,000, which works out to ₹900–₹1,200 per tenth — among the highest-ROI mods anywhere in the catalog. Compare that with a Powertronic ECU flash on a 4T 200cc bike at ₹14,000 for ~0.25 seconds (₹5,600 per tenth) or an Akrapovic slip-on at ₹35,000 for ~0.15 seconds (₹23,000 per tenth).",
  },
  {
    type: "p",
    text: "The reason 2T pipes are such a good ROI is exactly the physics described above. An aftermarket 4T exhaust changes flow restriction by maybe 5–15 %; the engine still has cams, valves, and a closed exhaust event between fresh charge and exhaust gas. A 2T pipe changes the fundamental thermodynamics of the cycle. There is no equivalent leverage on a 4-stroke.",
  },
  {
    type: "h2",
    text: "What This Means for the Indian 2T Crowd",
  },
  {
    type: "p",
    text: "If you ride a 2-stroke in India in 2026, you are in a small and shrinking community. Most production 2T bikes are gone — KTM 300 EXC and the imported pre-loved Japanese stuff is what is left. Used RX100s in clean condition trade for ₹1.2–₹1.8 lakh in Mumbai and Bangalore. RD350s in Punjab and Tamil Nadu trade for ₹4–8 lakh. The simulator catalog covers 20 of these bikes precisely because they are the heart of the Indian drag-strip and street-ride 2T scene, and because the Indian aftermarket sustains a meaningful supply of pipes, reed valves, and powervalve controllers (Zeeltronic, Nova SAPC) for them.",
  },
  {
    type: "p",
    text: "For drag racing specifically, the practical advice from the physics is short. First, match your launch RPM to your tuned RPM — not to peak torque RPM, not to peak power RPM, but to the resonance frequency of your specific pipe. Second, do not lean on gearing changes the way 4T riders do; the powerband is narrower than your gear-ratio steps so the bike will fall off the pipe between shifts no matter what you do. Third, prioritise the pipe over everything else. A perfect pipe with a stock barrel beats a tuned barrel with a wrong pipe every single time. Fourth, expect the simulator to be optimistic by roughly half a second on stock 2T bikes — the calibration bias is documented and being closed as more Dragy uploads come in from real Indian 2T owners.",
  },
  {
    type: "h2",
    text: "Run the Numbers",
  },
  {
    type: "p",
    text: "The simulator at motoquant.in lets you pick any of the 20 catalog 2T bikes and sweep tuned RPM, launch RPM, rider weight, ambient temperature, and pipe choice live. The torque curve plots in real time so you can see the Gaussian narrow when you flip a powervalve flag off, or the off-pipe baseline rise when you change a band_lo parameter. It is the cheapest way in India to feel the physics without committing to a pipe purchase.",
  },
  {
    type: "p",
    text: "The honest takeaway: 2-stroke racing is half engineering and half acoustics. The chamber is doing supercharging without a turbo, charge recovery without a valve, and the whole trick is timed to the speed of sound in the exhaust gas. When you understand the chamber, you understand why every other tuning choice on a 2T bike — gearing, ignition, jetting, port timing — is downstream of getting the pipe right. The pipe is the engine.",
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
          datePublished: "2026-05-08",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {["2-stroke", "expansion chamber", "physics", "RX100", "RD350"].map(
              (t) => (
                <span
                  key={t}
                  className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
                >
                  {t}
                </span>
              ),
            )}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            How a 2-Stroke Expansion Chamber Actually Works
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                How the MotoQuant Physics Engine Works
              </Link>{" "}
              — the 15-sub-model architecture, including the 2T torque-curve
              branch referenced in this post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The Physics of a Perfect Launch
              </Link>{" "}
              — why 2T launch RPM matters more than 4T launch RPM, in
              clutch-and-slip terms.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/why-your-r15-wont-hit-14s"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Why Your R15 Won&apos;t Hit 14s
              </Link>{" "}
              — the 4-stroke counterpart to this post: small-cc gearing and
              traction limits.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-aamby-valley-in-november"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for Aamby Valley in November
              </Link>{" "}
              — the venue conditions used for the simulation numbers in this
              post.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>{" "}
              — including all 20 two-stroke entries (RD350, RX100, RGV250,
              RS125, NSR250, KTM 300 EXC, and more).
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
              Sweep tuned RPM live
            </div>
            <div className="text-white/60 text-sm">
              Free simulator — pick an RX100, RD350, or RGV250, drag the
              launch-RPM slider, and watch the Gaussian torque curve and ET
              update in real time.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-rx100"
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
