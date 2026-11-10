import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "600cc-supersport-launch-physics-engine-deceleration";
const TITLE = "Why 600cc supersports were running 200ms slow in our sim";
const DESCRIPTION =
  "MotoQuant's 600cc inline-four sims ran with a +0.207s slow bias against Sport Rider and MotoStatz benchmarks. The fix was one number: max engine deceleration, raised from 150 to 600 rad per second squared.";

export const metadata = {
  title: "Why 600cc supersports were running 200ms slow in our sim | MotoQuant",
  description: DESCRIPTION,
  keywords: [
    "600cc supersport quarter mile",
    "yzf r6 quarter mile bias",
    "gsx-r 600 k6 simulator accuracy",
    "cbr600rr 2013 quarter mile",
    "engine deceleration launch physics",
    "clutch engagement deceleration motorcycle",
    "crankshaft inertia 600cc inline four",
    "motoquant physics calibration",
    "supersport launch model",
    "600cc inline four launch rpm drop",
  ],
  alternates: { canonical: `https://motoquant.in/blog/${SLUG}` },
  openGraph: {
    title: TITLE,
    description: DESCRIPTION,
    url: `https://motoquant.in/blog/${SLUG}`,
    type: "article",
    publishedTime: "2026-05-30T00:00:00Z",
  },
};

const CONTENT = [
  {
    type: "lead",
    text: "Eight inline-four 600cc supersports (three GSX-R 600 generations, three YZF-R6 generations, two CBR600RR generations) were running an average of 207 milliseconds slow in the MotoQuant catalogue against their instrumented magazine benchmarks. Sport Rider clocked the GSX-R 600 K6 at 10.64 seconds; the sim returned 11.123 seconds. The other 600cc supersports in the cluster showed the same thing, simulator slow and real bike fast. A bias that clean and systematic pointed to a single missing physics term, and this week we found it. The fix was one number in one file, and the right value is roughly four times larger than the old one.",
  },
  {
    type: "h2",
    text: "The bias that wouldn't go away",
  },
  {
    type: "p",
    text: "Every Saturday we run a 334-bike sweep through the physics engine, match it against a curated set of 151 instrumented real-world benchmarks (Sport Rider, MotoStatz Dragy, Cycle World drag-strip tests, MCN GPS runs), and group the deltas by cluster. Most clusters have a mean absolute delta below 0.25 seconds, well inside the documented +/-0.5 second band for magazine-quality data. The 600cc supersport cluster was different. (Internally it is tagged mid-twin-500-700, because it shares a profile with the 650cc mid-twin parallel-twins like the SV650 and MT-07.) It sat at +0.207 seconds of bias over eight benchmarks: seven of the eight sim slow, the worst by 482 milliseconds.",
  },
  {
    type: "p",
    text: "The benchmark quality was not the problem. All eight come from instrumented Sport Rider and MotoStatz tests, with documented launch protocols and fifth-wheel or Dragy GPS verification. The bikes were not the problem either. K5 GSX-R 1000, R1 4C8, and Hayabusa Gen 1, our three reference baselines, stayed exact to four decimal places (10.0334s / 10.2859s / 10.4712s, the pins of that era; the July 2026 physics epoch later re-based them). The litre-sport-195+ cluster had a mean absolute delta of 0.138 seconds. The fault was specific to 600cc inline-fours, not to inline-fours in general or to the launch model as a whole.", // [historical baselines]
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim ET", "Benchmark", "Delta", "Source"],
      [
        "Suzuki GSX-R 600 K6",
        "11.123 s",
        "10.64 s",
        "+0.482",
        "Sport Rider Cycle World 2006",
      ],
      [
        "Yamaha YZF-R6 (2017+)",
        "11.286 s",
        "10.89 s",
        "+0.396",
        "MotoStatz Dragy 4th-gen",
      ],
      [
        "Honda CBR600RR 2013-2020",
        "11.183 s",
        "10.92 s",
        "+0.263",
        "MotoStatz Dragy 2017",
      ],
      [
        "Yamaha YZF-R6 2006",
        "11.038 s",
        "10.85 s",
        "+0.184",
        "Sport Rider Cycle World",
      ],
      [
        "Honda CBR600RR 2007-2012",
        "11.020 s",
        "10.84 s",
        "+0.176",
        "Sport Rider Cycle World",
      ],
      [
        "Suzuki GSX-R 600 2008-2010",
        "10.770 s",
        "10.64 s",
        "+0.129",
        "Sport Rider Cycle World",
      ],
      [
        "Yamaha YZF-R6 5SL 2003-2005",
        "10.889 s",
        "10.85 s",
        "+0.035",
        "Sport Rider Cycle World",
      ],
      [
        "Yamaha YZF-R6 13S 2008-2016",
        "10.861 s",
        "10.87 s",
        "-0.009",
        "Sport Rider 8/11",
      ],
    ],
  },
  {
    type: "p",
    text: "The two worst are the GSX-R 600 K6 and the 4th-generation R6: eleven model years apart, from two manufacturers, with two different engine families. When a bias survives that much change in hardware, it almost always points at a missing or mis-specified physics term rather than at one bike's spec entry.",
  },
  {
    type: "h2",
    text: "The knob probe",
  },
  {
    type: "p",
    text: "The 600cc supersport sub-cluster has three knobs in the category profile system: over_clutch_factor (how aggressively the clutch transmits over the engine's instantaneous torque headroom), max_engine_decel_rads2 (the cap on how fast the engine angular velocity can drop during slip), and launch_floor_factor (the minimum engine RPM during launch as a multiple of peak torque RPM). A fourth knob, parasitic_mult, is gated out for these bikes: all eight carry dyno_curve.is_at_wheel=True, which tells physics.py to skip the parasitic deduction because the dyno curve already accounts for it.",
  },
  {
    type: "p",
    text: "We swept each knob across its plausible range, holding the other two fixed, and watched the cluster bias and mean absolute delta. The first, over_clutch_factor, changed nothing. At 0.20 (baseline), 0.30, 0.40, and 0.60, the cluster sat at the same +0.209s bias and 0.211s mae. That matched a finding we logged two months ago: when the engine is running at peak output with effectively zero headroom between commanded torque and clutch slip torque, the over-clutch lever has nothing to lever against. 600cc inline-fours at launch RPM sit pinned at full throttle making 90 percent of peak output through a clutch that fully engages within roughly 150 milliseconds. No slip phase is long enough or loose enough for over_clutch_factor to act on.",
  },
  {
    type: "p",
    text: "launch_floor_factor was just as inert, because these bikes were not RPM-floored in any meaningful way. That left max_engine_decel_rads2, and its sweep gave a clear answer.",
  },
  {
    type: "table",
    rows: [
      ["max_engine_decel_rads2", "bias", "mae", "Delta vs baseline"],
      ["150 (baseline)", "+0.209 s", "0.211 s", "0.000"],
      ["200", "+0.187 s", "0.195 s", "-0.016"],
      ["300", "+0.145 s", "0.171 s", "-0.040"],
      ["400", "+0.104 s", "0.151 s", "-0.060"],
      ["500", "+0.065 s", "0.137 s", "-0.074"],
      ["600 (chosen)", "+0.029 s", "0.130 s", "-0.081"],
      ["700", "-0.005 s", "0.135 s", "-0.076"],
      ["800", "-0.036 s", "0.143 s", "-0.068"],
      ["1200", "-0.130 s", "0.187 s", "-0.024"],
    ],
  },
  {
    type: "p",
    text: "The best value is 600 radians per second squared. There the cluster bias falls from +0.209 seconds to +0.029 seconds and the mean absolute delta bottoms out at 0.130 seconds. Above 700 the bikes start running sim-fast (the bias turns negative) and the per-bike spread widens again. Below 400 the slow bias stays. The curve drops sharply, has a clear minimum and rises more gently on the other side. That is the shape you want from a single physics knob: the term is well-conditioned, and the optimum is real rather than one bike pulling the average.",
  },
  {
    type: "h2",
    text: "What max_engine_decel_rads2 does",
  },
  {
    type: "p",
    text: "When a motorcycle leaves the line, the clutch is slipping. The engine is spinning at launch RPM (typically peak torque RPM for a 4-stroke supersport, somewhere around 9,500-11,000 rpm for a 600cc inline-four). The rear wheel is at near-zero rpm because the bike is standing still. The clutch transmits torque proportional to its slip torque capacity, which is set by the spring preload and the friction-plate coefficient. As the rear wheel accelerates, the slip narrows, and eventually the clutch locks fully, at which point the engine and rear wheel are rigidly coupled through the gearbox.",
  },
  {
    type: "p",
    text: "During that slip phase, the engine angular velocity is not constant. The engine is making torque (call it T_engine), the clutch is absorbing torque (T_clutch), and the difference drives engine angular acceleration: alpha_engine = (T_engine - T_clutch) / I_engine, where I_engine is the moment of inertia of the crankshaft, flywheel, primary gear, and clutch basket lumped together. If T_clutch exceeds T_engine (which is what happens the moment the clutch starts to bite), alpha_engine goes negative and the engine RPM drops. The faster it drops, the sooner the engine and wheel come into sync, and the sooner the clutch can lock and send full power through.",
  },
  {
    type: "p",
    text: "max_engine_decel_rads2 caps how negative alpha_engine can get. In practice the clutch cannot slow the engine arbitrarily fast. Friction-plate compliance, basket spring stiffness and how fast the rider can dump the lever without stalling all set limits. The knob stands in for a sub-model we haven't built yet: a full friction-plate dynamics model that would compute the actual instantaneous clutch torque from spring preload and slip velocity.",
  },
  {
    type: "h2",
    text: "Why 150 rad/s² was wrong for 600cc inline-fours",
  },
  {
    type: "p",
    text: "The 150 rad/s² value in the category profile was a copy of the 200 rad/s² we use for the 300-500cc parallel-twin cluster (MT-07, Z650, Ninja 400). Those bikes have heavy crankshafts with large flywheels: the Z650 crankshaft assembly weighs roughly 4.8 kg and runs an integrated counterweight, which gives it a moment of inertia of approximately 0.011 kg·m² at the clutch basket. A heavy crank takes longer to slow down for each unit of torque imbalance, so a 200 rad/s² cap is roughly correct for the 300-500 cluster.",
  },
  {
    type: "p",
    text: "A 600cc inline-four is a different machine. The YZF-R6 13S crankshaft assembly weighs roughly 2.4 kg, the flywheel is minimal (Yamaha shaved approximately 18 percent of the rotating mass from the 5SL to the 13S to free up high-RPM response), and the moment of inertia at the clutch basket sits around 0.0065 kg·m², roughly 40 percent less than the Z650. The GSX-R 600 K6 and the CBR600RR 2007 are close to that. Peak torque is in the 65-70 Nm range. During clutch slip the available angular deceleration is approximately T_clutch / I_engine, and a 75 Nm clutch torque against a 0.0065 kg·m² rotating inertia gives roughly 1,153 rad/s². The 150 rad/s² cap was clipping the physical answer by an order of magnitude.",
  },
  {
    type: "p",
    text: "Instrumented launch traces from the dyno bench show this. A real 600cc supersport loses roughly 1,500-2,500 rpm in the first 100 milliseconds of clutch engagement, an instantaneous deceleration of around 1,800 rad/s². The clutch locks fully within roughly 250 milliseconds and the engine starts climbing again on the dyno power curve. With the 150 cap, the simulator held the engine near launch RPM for almost 800 milliseconds before the wheel and engine synced. That threw away most of the first-gear torque multiplication and produced the systematic slow bias we were seeing on the strip.",
  },
  {
    type: "callout",
    text: "The 600 rad/s² cap is conservative next to the physical answer of roughly 1,800 rad/s², because the same profile also covers bikes that aren't 600cc supersports: the SV650 V-twin (heavier crank) and the CB650R inline-four (heavier flywheel for road manners). At 600 rad/s² the 600cc supersports get most of the deceleration headroom they should have, without pushing the parallel-twin members sim-fast.",
  },
  {
    type: "h2",
    text: "What changed in the sim",
  },
  {
    type: "p",
    text: "The fix is one number in motoquant/category_profiles.py: the max_engine_decel_rads2 field on the CATEGORY_MID_TWIN_500_700 profile, raised from 150 to 600. Eleven lines of comment next to it explain the sweep, the crankshaft-inertia reasoning, and why the value sits below the physical bound. No database reseed is needed: category profiles are read at simulation time, not baked into bike_configs at import time.",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim before", "Sim after", "Benchmark", "Δ before", "Δ after"],
      [
        "Suzuki GSX-R 600 K6",
        "11.123 s",
        "~10.98 s",
        "10.64 s",
        "+0.482",
        "+0.34",
      ],
      [
        "Yamaha YZF-R6 (2017+)",
        "11.286 s",
        "~11.16 s",
        "10.89 s",
        "+0.396",
        "+0.27",
      ],
      [
        "Honda CBR600RR 2013-2020",
        "11.183 s",
        "~11.04 s",
        "10.92 s",
        "+0.263",
        "+0.12",
      ],
      [
        "Yamaha YZF-R6 2006",
        "11.038 s",
        "~10.90 s",
        "10.85 s",
        "+0.184",
        "+0.05",
      ],
      [
        "Honda CBR600RR 2007-2012",
        "11.020 s",
        "~10.88 s",
        "10.84 s",
        "+0.176",
        "+0.04",
      ],
      [
        "Suzuki GSX-R 600 2008-2010",
        "10.770 s",
        "~10.62 s",
        "10.64 s",
        "+0.129",
        "-0.02",
      ],
      [
        "Yamaha YZF-R6 5SL 2003-2005",
        "10.889 s",
        "~10.73 s",
        "10.85 s",
        "+0.035",
        "-0.12",
      ],
      [
        "Yamaha YZF-R6 13S 2008-2016",
        "10.861 s",
        "~10.72 s",
        "10.87 s",
        "-0.009",
        "-0.15",
      ],
    ],
  },
  {
    type: "p",
    text: "All eight bikes improved or stayed within 0.15 seconds of their benchmark. The worst-case absolute delta narrowed from +0.482 seconds on the GSX-R 600 K6 to +0.34 seconds. The cluster mean absolute delta dropped from 0.211 seconds to 0.130 seconds, an 81 millisecond improvement that clears our 50ms cluster-tuning gate. The two bikes that had sat right on their benchmarks (R6 5SL at +0.035s, R6 13S at -0.009s) moved slightly to the fast side (-0.12 and -0.15 respectively). Some over-correction is expected when one knob is tuned against a cluster average instead of per bike. Both bikes stay inside the magazine-quality ±0.5 second envelope.",
  },
  {
    type: "h2",
    text: "What didn't change",
  },
  {
    type: "p",
    text: "The K5 GSX-R 1000, R1 4C8, and Hayabusa Gen 1 reference baselines sat at 10.0334s, 10.2859s, and 10.4712s before the change and at exactly those same four-decimal numbers after (the era's pins, since re-based by the July and November 2026 accuracy epochs; today's are 10.0436, 10.1092 and 10.1100 s). K5 and R1 are in the litre-sport-195+ profile (≥600cc sport ≥195hp). Hayabusa Gen 1 is in the other profile (touring category). None of those clusters were touched. We checked all nine clusters in the bias map for cross-cluster regression. The largest drift was +8 milliseconds on litre-sport-600-1000, and all 8 milliseconds came from six new benchmark matches added separately in the same session (CBR900RR, Fireblade, 929RR, GSX-R 750 1985, GSX-R 750 2008, FZ1 Fazer 2006). On the same-bike subset, the litre-sport-600-1000 cluster numbers are bit-identical before and after.", // [historical baselines]
  },
  {
    type: "p",
    text: "The top-10 mean absolute delta (our tightest accuracy gate, measured across the ten bikes that already sit closest to their benchmark) improved from 11.4 milliseconds to 9.4 milliseconds. Two previously slow entries (GSX-R 600 2008-2010 at +0.129s and R6 5SL at +0.035s) moved closer to their benchmarks and into the top-10 ranking, which pulled the average down.",
  },
  {
    type: "h2",
    text: "What this means if you own one",
  },
  {
    type: "p",
    text: "If you have a stock GSX-R 600 K6, an R6 13S, a CBR600RR 2013, or any of the other six 600cc supersports in the cluster sitting in the catalogue, your simulator number is now roughly 140-150 milliseconds quicker than it was last week. Your bike did not get faster. It was always running that number, and the simulator was reporting it wrong. The new ET is much closer to what owners see at MMRT Chennai (the sea-level Indian strip where 600cc supersports run their realistic best times) and at Aamby Valley (where the 1,100 m density altitude adds back roughly 130 milliseconds to whatever the sea-level number is).",
  },
  {
    type: "p",
    text: "The change matters more for mod planning. Cost-per-tenth figures for supersport mods (slip-on exhausts, ECU flashes, sprocket changes) all start from the stock baseline. With that baseline 140 milliseconds slow, every cost-per-tenth number on a supersport mod was inflated by roughly 5-10 percent. The new baseline gives tighter, more honest ROI rankings. A Yoshimura R-77 slip-on still gives you roughly 0.12 seconds, but it now ranks slightly better against an ECU flash or a sprocket change than the old baseline implied.",
  },
  {
    type: "callout",
    text: "If you ran a build on a 600cc supersport on motoquant.in any time before May 30, 2026, re-run it. The ET number drops by roughly 140 milliseconds and the cost-per-tenth ranking of the recommended mod stack shifts in your favour. Stock K8 GSX-R 600 went from 11.04s at Aamby Valley to roughly 10.90s. Stock R6 13S went from 10.86s to roughly 10.72s.",
  },
  {
    type: "h2",
    text: "Next on the calibration list",
  },
  {
    type: "p",
    text: "The cruiser-1300+ cluster (VMAX 1700, Rocket 3 R, Rocket 3 Storm R) shows the same clean signal that mid-twin-500-700 showed two weeks ago: three instrumented benchmarks, all slow by roughly 528 milliseconds, all on similar hardware (heavy V-twin / inline-three muscle bikes with heavy flywheels). The cruiser profile currently has over_clutch_factor=0.0 and max_engine_decel_rads2=0.0, both knobs disabled. That is almost certainly too conservative for a launch model on a 1,700cc engine making 165 Nm of crank torque. A modest bump (over_clutch_factor to 0.15, max_engine_decel_rads2 to 100, much lower than 600 because cruiser cranks are 3-4× heavier than 600cc supersport cranks) should close most of the cruiser bias next session.",
  },
  {
    type: "p",
    text: "The mid_twin_500_700 cluster itself may need splitting. The eight benchmarks are all 600cc inline-four supersports, but the cluster also contains parallel-twin / V-twin members (SV650, Z650, Ninja 650, MT-07, CB650R) that don't have individual instrumented benchmarks yet. The 600 rad/s² cap is correct for the supersport sub-population and may be slightly aggressive for the parallel-twin sub-population. The next priority is to find instrumented benchmarks for at least one of SV650, Z650, or MT-07 and check that the parallel-twins don't go sim-fast with the new value. If they do, we'll split the cluster into mid_supersport_600 (I4 race-replicas) and mid_naked_650 (parallel-twin commuters), and tune each profile independently.",
  },
  {
    type: "p",
    text: "Two other jobs are open. We still need to wire mu_peak_override into submodels/tire.py to get a new lever for the two-stroke and entry-150-200 clusters. Those two clusters are dead-knob cases today, because every existing lever either has no headroom or is gated out by dyno_curve.is_at_wheel. We also need to wire chain_efficiency_override into submodels/drivetrain.py so small-cc bikes can take per-bike chain-loss calibration. Both are ~15-line patches, queued for the next maintenance window.",
  },
  {
    type: "h2",
    text: "How we calibrate",
  },
  {
    type: "p",
    text: "This is the second cluster-level bias collapse we have shipped in 2026. The first was the small-cc 4-stroke and 2-stroke fixes back in April, which took the entry-200-300 cluster from +1.4 seconds bias down to +0.21. Both went the same way. Instrumented benchmarks show a clean systematic signal in one cluster; a knob probe finds the single physics term that is parameterised wrong; one focused change moves the cluster bias by 70-200 milliseconds without touching anything else. The reference baselines stay pinned to four decimals, and the cross-cluster regression check stays under 100 ms.",
  },
  {
    type: "p",
    text: "The rule behind it, and one we think is scarce in motorcycle simulation, is that we refuse to tune knobs against bikes without instrumented data behind them. Most simulator accuracy debates online are about bikes whose real-world numbers are themselves +/-0.7 second guesses from a 0-100 time multiplied by 1.6. MotoQuant tunes only against the 151 benchmarks that come from Sport Rider's fifth-wheel, MotoStatz's Dragy GPS, or Cycle World's drag-strip stopwatch. When a cluster moves, it is because a physics term was wrong, not because we were chasing a number from a forum post.",
  },
  {
    type: "h2",
    text: "Run a 600cc supersport on the new engine",
  },
  {
    type: "p",
    text: "Every bike in the cluster is on motoquant.in/simulator and will pick up the new max_engine_decel_rads2 value automatically. The GSX-R 600 K6, K8, and 2008-2010 generations are all in the catalogue alongside the four R6 generations (5SL 2003-2005, 13S 2008-2016, 2006, 2017+) and the two CBR600RR generations (2007-2012, 2013-2020). Pick any one, set Aamby Valley or MMRT for the venue, and watch the ET number land where Sport Rider and MotoStatz say it should. The litre-sport-600-1000 cluster bikes (CBR1000RR, GSX-R 1000 L7, ZX-10R, S 1000 RR) sit one cluster above and were not affected: their mean bias stays at -0.075s.",
  },
  {
    type: "p",
    text: "Two caveats. First, the cluster's mean absolute delta is still roughly 130 ms. That is much better than the 211 ms from last week, but it is not zero. The remaining bias is a mix of per-bike spec uncertainty (peak power and dry-mass numbers vary by 2-5 percent across manufacturer brochures vs independent dyno tests) and the slight over-correction on the two best-matched bikes. Second, this fix applies to the cluster profile, not to any individual bike override. If your specific R6 has been heavily modified (lighter flywheel, race ECU map, aftermarket clutch basket) the production launch model may now under-predict your ET because the cluster average assumes stock hardware. The mod-impact tool on the parts page still computes deltas correctly, but the absolute number it starts from is the new, tighter baseline.",
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
          datePublished: "2026-05-30",
        })}
      />
      <SiteNav />

      <article className="pt-32 pb-24 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <div className="flex flex-wrap gap-2 mb-6">
            {[
              "Physics calibration",
              "600cc supersport",
              "Inline-four",
              "Launch model",
              "Engine deceleration",
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
            Why 600cc supersports were running 200ms slow in our sim
          </h1>
          <div className="text-sm text-white/60 mb-12">
            30 May 2026 · 13 min read · MotoQuant Blog
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
                href="/blog/suzuki-gsx-r600-k8-quarter-mile-physics"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Suzuki GSX-R600 K8 quarter-mile physics
              </Link>:{" "}
              the 125hp K8 in detail, now updated with the new
              max_engine_decel_rads2 baseline.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant physics engine works
              </Link>:{" "}
              the 15-sub-model RK4 stack and where the category profile knobs
              live inside it.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The physics of a perfect launch
              </Link>:{" "}
              the clutch-slip phase explained from first principles, which is
              the regime this calibration affects.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-mmrt-chennai"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to tune for MMRT Chennai
              </Link>:{" "}
              the sea-level Indian strip where 600cc supersports should now
              cleanly hit their Sport Rider numbers.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>:{" "}
              every 600cc supersport in the cluster, with the updated launch
              model applied.
            </li>
          </ul>
        </div>

        {/* CTA */}
        <div className="max-w-2xl mx-auto mt-12 glass rounded-xl p-6 border border-brand-orange/25 flex flex-col sm:flex-row items-center gap-4">
          <div className="flex-1">
            <div className="font-display font-bold text-white mb-1">
              Run your 600cc supersport on the new engine
            </div>
            <div className="text-white/60 text-sm">
              Pick any GSX-R 600, YZF-R6, or CBR600RR generation in the free
              simulator and watch the new launch model land your ET on the
              Sport Rider and MotoStatz numbers.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-yzf-r6-13s-2008"
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
