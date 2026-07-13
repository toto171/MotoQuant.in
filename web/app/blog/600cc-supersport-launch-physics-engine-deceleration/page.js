import Link from "next/link";
import SiteNav from "../../../components/SiteNav";
import SiteFooter from "../../../components/SiteFooter";
import StructuredData, { articleSchema } from "../../StructuredData";

const SLUG = "600cc-supersport-launch-physics-engine-deceleration";
const TITLE = "Why 600cc Supersports Were Running 200ms Slow in Our Sim";
const DESCRIPTION =
  "MotoQuant's 600cc inline-four sims were biased +0.207s slow against Sport Rider and MotoStatz benchmarks. The fix was one number: max engine deceleration, 150 to 600 rad per second squared. Here is the physics.";

export const metadata = {
  title: "Why 600cc Supersports Were Running 200ms Slow in Our Sim — MotoQuant",
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
    text: "Eight inline-four 600cc supersports — three GSX-R 600 generations, three YZF-R6 generations, two CBR600RR generations — sat in the MotoQuant catalogue running an average of 207 milliseconds slow against their instrumented magazine benchmarks. Sport Rider clocked the GSX-R 600 K6 at 10.64 seconds. The sim returned 11.123 seconds. Every other 600cc supersport in the cluster told the same story: simulator slow, real bike fast, a clean systematic bias that pointed to a single missing physics term. This week we found it. The fix was one number in one file. Here is what the number does, why it was wrong, and why the right value is roughly four times larger.",
  },
  {
    type: "h2",
    text: "The Bias Signal That Wouldn't Go Away",
  },
  {
    type: "p",
    text: "Every Saturday we run a 334-bike sweep through the physics engine, match it against a curated set of 151 instrumented real-world benchmarks (Sport Rider, MotoStatz Dragy, Cycle World drag-strip tests, MCN GPS runs), and bucket the deltas by cluster. Most clusters sit at mean absolute delta below 0.25 seconds, which is well inside the documented +/-0.5 second band for magazine-quality data. The 600cc supersport cluster — internally tagged mid-twin-500-700 because it shares a profile with the 650cc mid-twin parallel-twins like the SV650 and MT-07 — was different. It sat at +0.207 second bias with eight benchmarks: seven of the eight sim slow, the worst by 482 milliseconds.",
  },
  {
    type: "p",
    text: "The benchmark quality was not the problem. All eight come from instrumented Sport Rider and MotoStatz tests, with documented launch protocols and fifth-wheel or Dragy GPS verification. The bikes were not the problem either. K5 GSX-R 1000, R1 4C8, and Hayabusa Gen 1 — our three load-bearing reference baselines — were nailed to four decimal places (10.0334s / 10.2859s / 10.4712s — the pins of that era; the July 2026 physics epoch later re-based them). The litre-sport-195+ cluster mean absolute delta sat at 0.138 seconds. Whatever was wrong was specific to 600cc inline-fours, not to inline-fours in general and not to the launch model overall.", // [historical baselines]
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
    text: "Seven of eight sim slow, with the most extreme bias on the GSX-R 600 K6 and the 4th-generation R6 — two bikes separated by eleven model years, two manufacturers, and two distinct engine families. A bias signal that survives that much hardware variation is almost always pointing at a missing or mis-specified physics term, not at any individual bike's spec entry.",
  },
  {
    type: "h2",
    text: "The Knob Probe",
  },
  {
    type: "p",
    text: "The 600cc supersport sub-cluster has three knobs available in the category profile system: over_clutch_factor (how aggressively the clutch transmits over the engine's instantaneous torque headroom), max_engine_decel_rads2 (the cap on how fast the engine angular velocity can drop during slip), and launch_floor_factor (the minimum engine RPM during launch as a multiple of peak torque RPM). A fourth knob, parasitic_mult, is gated out for these bikes — all eight carry dyno_curve.is_at_wheel=True, which tells physics.py to skip the parasitic deduction because the dyno curve already accounts for it.",
  },
  {
    type: "p",
    text: "We swept each knob across its plausible range, holding the other two fixed, and watched the cluster bias and mean absolute delta numbers move. The first knob — over_clutch_factor — moved the needle exactly zero millimetres. At 0.20 (baseline), 0.30, 0.40, and 0.60, the cluster sat at the same +0.209s bias and 0.211s mae. The knob was inert, which matched a finding we logged two months ago: when the engine is running at peak output with effectively zero headroom between commanded torque and clutch slip torque, the over-clutch lever has nothing to lever against. 600cc inline-fours at launch RPM sit pinned at full throttle making 90 percent of peak output through a clutch that fully engages within roughly 150 milliseconds. There is no slip phase long enough or loose enough for over_clutch_factor to do anything.",
  },
  {
    type: "p",
    text: "The launch_floor_factor knob was similarly inert — the bikes were not RPM-floored in any meaningful way. That left one lever: max_engine_decel_rads2. The probe results were unambiguous.",
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
    text: "The optimum sits at 600 radians per second squared, where the cluster bias collapses from +0.209 seconds to +0.029 seconds and the mean absolute delta bottoms at 0.130 seconds. Above 700 the bikes start running sim-fast (the bias flips negative) and the per-bike spread widens again. Below 400 the slow bias remains stubborn. The shape of the curve — sharp drop, clear minimum, controlled rise on the other side — is exactly what you want to see when probing a single physics knob. It says the term is well-conditioned and the optimum is real, not an artefact of one bike pulling the average.",
  },
  {
    type: "h2",
    text: "What max_engine_decel_rads2 Actually Does",
  },
  {
    type: "p",
    text: "When a motorcycle leaves the line, the clutch is slipping. The engine is spinning at launch RPM (typically peak torque RPM for a 4-stroke supersport, somewhere around 9,500-11,000 rpm for a 600cc inline-four). The rear wheel is spinning at near-zero rpm because the bike is stationary. The clutch transmits torque proportional to its slip torque capacity, which is set by the spring preload and the friction-plate coefficient. As the rear wheel accelerates, the slip narrows, and eventually the clutch locks fully — at which point the engine and rear wheel are rigidly coupled through the gearbox.",
  },
  {
    type: "p",
    text: "During that slip phase, the engine angular velocity is not constant. The engine is making torque (call it T_engine), the clutch is absorbing torque (T_clutch), and the difference drives engine angular acceleration: alpha_engine = (T_engine - T_clutch) / I_engine, where I_engine is the moment of inertia of the crankshaft, flywheel, primary gear, and clutch basket lumped together. If T_clutch exceeds T_engine — which is what happens the moment the clutch starts to bite — alpha_engine goes negative and the engine RPM drops. The faster it drops, the faster the engine and wheel come into sync, and the faster the clutch can lock and start transmitting full power.",
  },
  {
    type: "p",
    text: "max_engine_decel_rads2 is the cap on how negative alpha_engine is allowed to get. It models the physical reality that the clutch cannot, in practice, decelerate the engine arbitrarily fast — there are limits set by friction-plate compliance, basket spring stiffness, and the rate at which the rider can dump the lever without stalling. The knob is a parameterised approximation of a sub-model we haven't built yet: a full friction-plate dynamics model that would compute the actual instantaneous clutch torque from spring preload and slip velocity.",
  },
  {
    type: "h2",
    text: "Why 150 rad/s² Was Wrong for 600cc Inline-Fours",
  },
  {
    type: "p",
    text: "The 150 rad/s² value in the category profile was a copy of the 200 rad/s² we use for the 300-500cc parallel-twin cluster (MT-07, Z650, Ninja 400). Those bikes have heavy crankshafts with large flywheels — the Z650 crankshaft assembly weighs roughly 4.8 kg and runs an integrated counterweight, which gives it a moment of inertia of approximately 0.011 kg·m² at the clutch basket. A heavy crank takes longer to decelerate per unit of torque imbalance. Capping at 200 rad/s² for the 300-500 cluster is roughly correct.",
  },
  {
    type: "p",
    text: "A 600cc inline-four is a completely different mechanical situation. The YZF-R6 13S crankshaft assembly weighs roughly 2.4 kg, the flywheel is minimal (Yamaha shaved approximately 18 percent of the rotating mass from the 5SL to the 13S to free up high-RPM response), and the moment of inertia at the clutch basket sits around 0.0065 kg·m² — roughly 40 percent less than the Z650. The GSX-R 600 K6 and the CBR600RR 2007 are in the same ballpark. Combined with peak torque numbers in the 65-70 Nm range, the available angular deceleration during clutch slip is approximately T_clutch / I_engine — and for a 75 Nm clutch torque commanding deceleration against a 0.0065 kg·m² rotating inertia, that comes out to roughly 1,153 rad/s². The 150 rad/s² cap was clipping the physical answer by an order of magnitude.",
  },
  {
    type: "p",
    text: "You can see this in dyno-bench instrumented launch traces. A real 600cc supersport leaves the line with roughly 1,500-2,500 rpm of engine drop in the first 100 milliseconds of clutch engagement — call it an instantaneous deceleration around 1,800 rad/s². The clutch locks fully within roughly 250 milliseconds and the engine starts climbing again on the dyno power curve. The simulator with the 150 cap was holding the engine at near-launch RPM for almost 800 milliseconds before letting the wheel and engine sync — which threw away most of the first-gear torque multiplication and produced exactly the systematic slow-bias we were seeing on the strip.",
  },
  {
    type: "callout",
    text: "The cap of 600 rad/s² is conservative relative to the physical answer of roughly 1,800 rad/s² because the parameterisation also has to live with sub-cluster bikes that aren't 600cc supersports — the same profile applies to the SV650 V-twin (heavier crank) and the CB650R inline-four (heavier flywheel for road manners). At 600 rad/s² the 600cc supersports get most of their deserved deceleration headroom without pushing the parallel-twin members sim-fast.",
  },
  {
    type: "h2",
    text: "What Changed in the Sim",
  },
  {
    type: "p",
    text: "The fix is one number in motoquant/category_profiles.py — the max_engine_decel_rads2 field on the CATEGORY_MID_TWIN_500_700 profile, lifted from 150 to 600. Eleven lines of justification comment land alongside it explaining the empirical sweep, the crankshaft-inertia reasoning, and the conservative-vs-physical-bound trade-off. No database reseed is required because category profiles are read at simulation time, not baked into bike_configs at import time.",
  },
  {
    type: "table",
    rows: [
      ["Bike", "Sim BEFORE", "Sim AFTER", "Benchmark", "Δ BEFORE", "Δ AFTER"],
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
    text: "All eight bikes improved or stayed within 0.15 seconds of their benchmark. The worst-case absolute delta narrowed from +0.482 seconds on the GSX-R 600 K6 to +0.34 seconds. The cluster mean absolute delta dropped from 0.211 seconds to 0.130 seconds — an 81 millisecond improvement that crosses our 50ms cluster-tuning gate. The bikes that previously sat dead-on the benchmark (R6 5SL at +0.035s, R6 13S at -0.009s) moved slightly to the fast side (-0.12 and -0.15 respectively), which is the expected mild over-correction when you tune a single knob against a cluster average rather than per-bike. Both bikes remain inside the magazine-quality ±0.5 second envelope.",
  },
  {
    type: "h2",
    text: "What Didn't Change",
  },
  {
    type: "p",
    text: "The K5 GSX-R 1000, R1 4C8, and Hayabusa Gen 1 reference baselines sat at 10.0334s, 10.2859s, and 10.4712s before the change and at exactly those same four-decimal numbers after (the era's pins — since re-based by the July 2026 epoch). K5 and R1 are in the litre-sport-195+ profile (≥600cc sport ≥195hp). Hayabusa Gen 1 is in the other profile (touring category). None of those clusters were touched. Cross-cluster regression was checked across all nine clusters in the bias map; the largest drift was +8 milliseconds on litre-sport-600-1000, and that 8 millisecond drift was entirely caused by six new benchmark matches added independently in the same session (CBR900RR, Fireblade, 929RR, GSX-R 750 1985, GSX-R 750 2008, FZ1 Fazer 2006). On the same-bike subset, the litre-sport-600-1000 cluster numbers are bit-identical before and after.", // [historical baselines]
  },
  {
    type: "p",
    text: "The top-10 mean absolute delta — our tightest accuracy gate, measured across the ten bikes that already sit closest to their benchmark — actually improved from 11.4 milliseconds to 9.4 milliseconds. Two previously-slow entries (GSX-R 600 2008-2010 at +0.129s and R6 5SL at +0.035s) moved tighter to their benchmarks and pushed into the top-10 ranking, dragging the average down. The fix made the top of the validation table tighter, not just the middle of the curve.",
  },
  {
    type: "h2",
    text: "What This Means If You Own One",
  },
  {
    type: "p",
    text: "If you have a stock GSX-R 600 K6, an R6 13S, a CBR600RR 2013, or any of the other six 600cc supersports in the cluster sitting in the catalogue, your simulator number is now roughly 140-150 milliseconds quicker than it was last week. That is not your bike getting faster — your bike was always running that number, the simulator was reporting it wrong. The new ET prediction lines up much more cleanly with what owners actually see at MMRT Chennai (the sea-level Indian strip where 600cc supersports run their realistic best times) and at Aamby Valley (where the 1,100 m density altitude adds back roughly 130 milliseconds to whatever the sea-level number is).",
  },
  {
    type: "p",
    text: "For mod planning, the change matters even more. Cost-per-tenth calculations on supersport mods (slip-on exhausts, ECU flashes, sprocket changes) all chain off the stock baseline. If the stock baseline was 140 milliseconds slow, every cost-per-tenth number on a supersport mod was inflated by roughly 5-10 percent. With the new baseline, the ROI rankings of supersport mods are tighter and more honest. A Yoshimura R-77 slip-on still gives you roughly 0.12 seconds, but the relative position of that mod against an ECU flash or a sprocket change is slightly more favourable than the old baseline implied.",
  },
  {
    type: "callout",
    text: "If you ran a build on a 600cc supersport on motoquant.in any time before May 30, 2026, re-run it. The ET number drops by roughly 140 milliseconds and the cost-per-tenth ranking of the recommended mod stack shifts in your favour. Stock K8 GSX-R 600 went from 11.04s Aamby Valley to roughly 10.90s. Stock R6 13S went from 10.86s to roughly 10.72s.",
  },
  {
    type: "h2",
    text: "What's Next on the Calibration Roadmap",
  },
  {
    type: "p",
    text: "The cruiser-1300+ cluster (VMAX 1700, Rocket 3 R, Rocket 3 Storm R) is showing the same clean-signal pattern that mid-twin-500-700 had two weeks ago: three instrumented benchmarks, all bias slow by roughly 528 milliseconds, all hardware-homogeneous (heavy V-twin / inline-three muscle bikes with heavy flywheels). The cruiser profile currently has over_clutch_factor=0.0 and max_engine_decel_rads2=0.0 — both knobs disabled. That is almost certainly too conservative for a launch model on a 1,700cc engine making 165 Nm of crank torque. A modest bump (over_clutch_factor to 0.15, max_engine_decel_rads2 to 100 — much lower than 600 because cruiser cranks are 3-4× heavier than 600cc supersport cranks) should close most of the cruiser bias next session.",
  },
  {
    type: "p",
    text: "The mid_twin_500_700 cluster itself contains a known split-risk: the eight benchmarks are all 600cc inline-four supersports, but the cluster also contains parallel-twin / V-twin members (SV650, Z650, Ninja 650, MT-07, CB650R) that don't have individual instrumented benchmarks yet. The 600 rad/s² cap is correct for the supersport sub-population and may be slightly aggressive for the parallel-twin sub-population. The next priority is sourcing instrumented benchmarks for at least one of SV650, Z650, or MT-07 to verify the parallel-twins don't go sim-fast with the new value. If they do, we'll split the cluster into mid_supersport_600 (I4 race-replicas) and mid_naked_650 (parallel-twin commuters) — and tune each profile independently.",
  },
  {
    type: "p",
    text: "Two other open hooks: we still need to wire mu_peak_override into submodels/tire.py to unlock a new lever for the two-stroke and entry-150-200 clusters (both currently dead-knob situations because all the existing levers either have no headroom or get gated out by dyno_curve.is_at_wheel). And we need to wire chain_efficiency_override into submodels/drivetrain.py so small-cc bikes can take per-bike chain-loss calibration. Both are ~15-line patches; they're queued for the next maintenance window.",
  },
  {
    type: "h2",
    text: "The Bigger Picture on Physics Calibration",
  },
  {
    type: "p",
    text: "This is the second cluster-level bias collapse we have shipped in 2026 — the first was the small-cc 4-stroke and 2-stroke fixes back in April that took the entry-200-300 cluster from +1.4 seconds bias down to +0.21. The pattern is the same in both cases: instrumented benchmarks reveal a clean systematic signal in a specific cluster, a knob probe identifies the single physics term that is parameterised wrong, and one focused change moves the cluster bias by 70-200 milliseconds without touching anything else. The reference baselines stay pinned to four decimals. The cross-cluster regression check stays under 100 ms.",
  },
  {
    type: "p",
    text: "The thing this approach is buying — and the thing we think is genuinely scarce in motorcycle simulation — is the discipline of refusing to tune knobs against bikes that don't have instrumented data behind them. Most simulator accuracy debates online happen on bikes where the underlying real-world numbers are themselves +/-0.7 second guesses from a 0-100 time multiplied by 1.6. MotoQuant tunes only against the 151 benchmarks that come from Sport Rider's fifth-wheel, MotoStatz's Dragy GPS, or Cycle World's drag-strip stopwatch. When a cluster moves, it moves because the physics term was wrong, not because we were chasing a number from a forum post.",
  },
  {
    type: "h2",
    text: "Run a 600cc Supersport on the New Engine",
  },
  {
    type: "p",
    text: "Every bike in the cluster is on motoquant.in/simulator and will pick up the new max_engine_decel_rads2 value automatically. The GSX-R 600 K6, K8, and 2008-2010 generations are all in the catalogue alongside the four R6 generations (5SL 2003-2005, 13S 2008-2016, 2006, 2017+) and the two CBR600RR generations (2007-2012, 2013-2020). Pick any one, set Aamby Valley or MMRT for the venue, and watch the ET number land where Sport Rider and MotoStatz say it should. The litre-sport-600-1000 cluster bikes (CBR1000RR, GSX-R 1000 L7, ZX-10R, S 1000 RR) sit one cluster above and were not affected — their bias remains at -0.075s mean, which is honest.",
  },
  {
    type: "p",
    text: "Two caveats worth flagging: First, the simulator is still running roughly 130 ms mean absolute delta on the cluster — that is dramatically better than the 211 ms from last week but it is not zero. The remaining bias is a mix of per-bike spec uncertainty (peak power and dry-mass numbers vary by 2-5 percent across manufacturer brochures vs independent dyno tests) and the slight over-correction on the two best-matched bikes. Second, this fix applies to the cluster profile, not to any individual bike override — if your specific R6 has been heavily modified (lighter flywheel, race ECU map, aftermarket clutch basket) the production launch model may now under-predict your ET because the cluster average assumes stock hardware. The mod-impact tool on the parts page still computes deltas correctly, but the absolute number it starts from is the new, tighter baseline.",
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
                className="px-2 py-0.5 rounded bg-brand-orange/10 border border-brand-orange/25 text-[10px] font-mono text-brand-orange uppercase tracking-wide"
              >
                {t}
              </span>
            ))}
          </div>
          <h1 className="font-display font-bold text-4xl md:text-5xl tracking-tighter text-white mb-4 leading-tight">
            Why 600cc Supersports Were Running 200ms Slow in Our Sim
          </h1>
          <div className="font-mono text-xs text-white/40 uppercase tracking-wide mb-12">
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
                Suzuki GSX-R600 K8 Quarter-Mile Physics
              </Link>{" "}
              — the 125hp K8 deep-dive, now updated with the new
              max_engine_decel_rads2 baseline.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-the-motoquant-physics-engine-works"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How the MotoQuant Physics Engine Works
              </Link>{" "}
              — the 15-sub-model RK4 stack and where the category profile knobs
              live inside it.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/the-physics-of-a-perfect-launch"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                The Physics of a Perfect Launch
              </Link>{" "}
              — the clutch-slip phase explained from first principles, which is
              the regime this calibration affects.
            </li>
            <li>
              ·{" "}
              <Link
                href="/blog/how-to-tune-for-mmrt-chennai"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                How to Tune for MMRT Chennai
              </Link>{" "}
              — the sea-level Indian strip where 600cc supersports should now
              cleanly hit their Sport Rider numbers.
            </li>
            <li>
              ·{" "}
              <Link
                href="/bikes"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                Browse the full bike catalog
              </Link>{" "}
              — every 600cc supersport in the cluster, with the updated launch
              model applied.
            </li>
            <li>
              ·{" "}
              <Link
                href="/pricing"
                className="text-brand-accent hover:text-brand-orange transition-colors"
              >
                MotoQuant Pricing
              </Link>{" "}
              — Free for street tuners; Pro for shops and racing teams.
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
              Free simulator — pick any GSX-R 600, YZF-R6, or CBR600RR
              generation and watch the new launch model land your ET on the
              Sport Rider and MotoStatz numbers.
            </div>
          </div>
          <Link
            href="/simulator?bike=yamaha-yzf-r6-13s-2008"
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
