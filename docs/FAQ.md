# MotoQuant — Frequently Asked Questions

## General Questions

### What is MotoQuant?
MotoQuant is a free, open-source, physics-based quarter-mile drag racing simulator for motorcycles. It uses first-principles aerodynamics, tyre grip and temperature, drivetrain dynamics, and engine modeling to predict your bike's quarter-mile ET (elapsed time) and trap speed. The simulator lets you test modifications—power increases, gear ratios, tire swaps, weight reduction—and see their impact on performance *before* spending money at the tuner or parts shop.

### Is it free? Is it open source?
Yes to both. Everything (the simulator, parts ROI, build optimizer, autotune, Dragy/dyno calibration, chat) is free, with no paid tiers, no quotas and no license keys. The code is open source under the **Apache License 2.0**: <https://github.com/toto171/MotoQuant.in>. You can use the hosted site at motoquant.in or run your own copy ([SELF_HOSTING.md](SELF_HOSTING.md)). There is no account: runs you save stay in your browser, and a timeslip link shares one.

### Who should use it?
- **Drag racers** — predict ET gains from mods, plan builds within budget constraints
- **Tuning shops** — validate customer expectations, show ROI on parts before installation
- **Enthusiasts** — curiosity about physics, benchmark against known times
- **Students** — learn motorcycle physics with a working model

### Is it accurate?
MotoQuant is validated against **250 published benchmarks** (magazine road tests, instrumented GPS runs, timeslips), weighted by source quality. Across 263 matches to catalog bikes the weighted mean error is about **0.25 s** and the mean bias **+0.02 s**. Reference bikes, simulated at sea level: GSX-R 1000 K5 10.04 s vs 9.97 s (Cycle World), YZF-R1 10.11 s vs 10.30 s (Sport Rider), Hayabusa Gen1 10.11 s vs 10.40 s (Cycle World). Small-cc bikes are the weakest class: few instrumented benchmarks exist for them, and many still carry a generic primary gear ratio in the catalog. For bikes not in the library, results are estimates; use them to guide decisions, not as law. The full breakdown is at motoquant.in/validation.

### Where does the simulator run?
- **Web simulator** on motoquant.in — enter your bike and mods, get ET in ~50 ms
- **CLI** (`python -m motoquant.run sim ...`) — batch simulations, scripting
- **API** — FastAPI backend for integration into your own tools
- **Your own server** — self-host the whole stack from the open-source repo ([SELF_HOSTING.md](SELF_HOSTING.md))

---

## Using the Simulator

### How do I start a simulation?
Open the simulator at motoquant.in/simulator. It starts in **Simple** mode:
1. Choose your bike (search by make, model or year)
2. Set the rider weight
3. Say where you are racing (a city or a drag strip), or leave the default conditions

The quarter-mile time and trap speed update as you change things, and the result always says which conditions it was computed for.

### What does Simple mode do?
Simple mode answers one question: how quick is this bike, with this rider, at this place? Under the result it offers the next steps: add parts and mods, find the best parts for a budget ("Upgrades"), get a race-day setup, compare with another bike, see charts and splits, or save and share the run.

A result marked **Instant estimate** comes from a fast model that runs in your browser; **Exact** means the full physics simulation ran. Only exact results can be saved and shared as a timeslip; the leaderboard ranks every catalog bike by its simulated stock time.

### What's Advanced mode?
Advanced mode is the full workbench, with everything in one place:
- **Setup**: bike, rider weight, an engine power change (−20 % to +50 %), weight added or removed, air and altitude (venue, air and track temperature, humidity, headwind) and front and rear tyres
- **Parts and mods**: pick individual parts from the catalog (ECU tunes, exhausts, intake filters, sprockets and chains, suspension, weight reduction, turbo and supercharger kits, nitrous, and more). Parts are **bike-specific**: a part only appears for the bikes it fits
- **Results**: Quarter mile, Top speed, Charts, Splits, Compare, My data (your own Dragy runs and dyno sheets) and Specs

The result shows the build cost and the change against the stock bike.

### How do I choose between tires?
In Advanced mode the front and rear tyre pickers start on **Original tyre (stock)**. You can swap in any tyre from the library; each entry shows its size and compound (sport, sport-touring, race, drag radial or slick, commuter). The picker does not stop you choosing a size that will not fit your rims, so check the size yourself. Each bike's page under motoquant.in/bikes lists the tyres recorded as fitting it; from the command line, `python -m motoquant.run bikes --fitments BIKE_ID` shows the original, recommended and drag-prep tyres recorded for a bike.

### Can I change rider weight?
Yes. Use the **Rider Weight** slider (50–130 kg). Heavier riders = slower acceleration (more inertia), later wheelies, different weight transfer. How much it matters depends on the bike: on a litre bike, which is limited by wheelies and grip at launch, 20 kg is only a few hundredths of a second; on a 150 cc bike it can be several tenths.

### What does "Engine power change" do in Advanced mode?
It is a multiplier on the bike's whole power and torque curve: +20 % on a 180 hp bike is 216 hp. Use it for a quick what-if; to model a real build, pick the parts instead.

---

## Understanding Results

### What does "ET" mean?
**ET** = Elapsed Time, how many seconds to complete 402.336 meters (0.25 miles / quarter mile). Lower is faster. Like a strip timeslip, MotoQuant starts the clock when the bike has rolled the first foot (0.3048 m) out of the stage beam, not at first motion. A 10-second ET is very respectable for a street bike; 9 seconds is excellent.

### What's "Trap Speed"?
Trap Speed is your velocity at the finish line (402.336 m mark), measured in km/h or mph. It reflects your power-to-weight ratio and aerodynamics. A 250 km/h trap is typical for a literbike; 280+ km/h requires significant mods.

### What are the "Split Times"?
Standard quarter-mile splits let you see your acceleration profile:
- **60 ft** (18.3 m) — off-the-line traction and launch quality
- **330 ft** (100 m) — mid-range power delivery
- **660 ft** (200 m) — where top bikes start to gap slower ones
- **Trap** (402 m) — finish

Use splits to diagnose problems: if your 60 ft is slow, you have a wheel-spin or launch control issue; if trap is slow but early splits are good, you're running out of power or hitting a gear wall.

### What does "Traction %" mean?
Traction % is the **grip margin**: 100 % = maximum tire grip available. Values below 100 % mean you have headroom; values above mean you're on the edge of wheel-spin. A value of 98 % is ideal (barely spinning, maximum acceleration). 105 % means you're slipping — you'd benefit from a softer tire or weight reduction to improve traction.

### Why is my 60-foot time slow?
Common causes:
1. **Soft tires** — sticky but too much slippage; try a stiffer compound
2. **Too much power** — wheel-spin right off the line; reduce boost or add weight to the rear
3. **Poor rider technique** — two-step bouncing, delayed launch, bad clutch control (see Staging topic)
4. **Staging line grip** — rain, oil, loose surface reduces grip multiplier

### Can I see a graph of my acceleration over time?
Yes — the web simulator's Charts tab shows **v(t), RPM(t), gear(t), and tire temperature(t)** plots after a full sim; the CLI can emit the same timeseries as JSON.

---

## Physics & Modeling

### How does the simulator predict power delivery?
The engine model uses a torque curve — a table of RPM → Torque (Nm). Stock curves come from service manuals or dyno data. When you add a tune or bolt-on, we adjust the curve (typical: +8–15 % peak torque, broadened power band). ECU flash effects are modeled as curve shape changes, not just a flat +%.

### What's a "Dyno curve"?
A dyno (dynamometer) measurement of **real, actual power** at the wheels. You can import dyno data directly, and the simulator will use your actual curve instead of estimates. This is crucial for tuned bikes.

### How is aerodynamic drag calculated?
Drag force = 0.5 × ρ × Cd × A × v². Each bike has a **drag coefficient (Cd)** and **frontal area (A)** based on design. Sport bikes (Cd ≈ 0.65) are more slippery than naked bikes (Cd ≈ 0.80). In a quarter-mile, aero is ~5–10 % of your total power loss.

### What about tire physics?
The rear tyre's grip limit is its peak friction coefficient times the load on the rear wheel. The coefficient drops slightly as load rises, and it changes with tread temperature, tyre pressure (which rises as the tyre warms) and track preparation. The tread heats from wheel slip and loses heat to the road and the air, so grip changes during the run. The model also includes a Pacejka slip curve, but the simulation does not use it yet.

### How does weight affect acceleration?
Weight affects acceleration in two ways:
1. **Inertia** — heavier things accelerate slower (F = ma)
2. **Traction** — more weight = more normal force = more grip

For a lightweight 200 cc bike, adding 5 kg is a ~1–2 % power loss. For a 200 kg superbike, 5 kg is almost nothing. The simulator accounts for both.

### What's "weight transfer"?
As you accelerate, weight shifts from the front wheel to the rear wheel (because the rear wheel is accelerating the bike upward). This is modeled dynamically — early in the run, more weight on the rear = more rear-wheel traction. Late in the run (higher speeds), weight transfers back to the front. The simulator calculates this at every instant.

### Why do you lose speed at high RPMs?
Aerodynamic drag increases with the square of velocity. At high speeds, more power goes into fighting the air, less goes into accelerating the bike. That's why top fuel dragsters have parachutes — they can't slow down any other way at 500 km/h.

---

## Customization & Accuracy

### Can I upload my own dyno data?
Yes — the CLI supports dyno CSV import (`python -m motoquant.run calibrate import-dyno FILE`), and the web app accepts dyno uploads. After import, the simulator uses your real curve instead of estimates. This is the best way to get accurate predictions for a tuned bike.

### Can I import Dragy GPS data from my runs?
Yes — the simulator can import Dragy CSV or VBO files from RaceChrono. It detects your real acceleration profile and can auto-calibrate the model to match your actual performance. Use `calibrate import-dragy FILE`.

### What about ECU log data (Woolich / PC-Link / MoTeC)?
The simulator can parse ECU logs to extract real-world run data: RPM, TPS, speed, gear, AFR, temperatures. This data can be overlaid against simulations to validate your current bike's performance.

### How often is the bike and tire library updated?
- **Bikes:** ~quarterly (new model years, Indian-market additions)
- **Tires:** ~monthly (new compounds, OEM fitments)
- **Parts catalog:** ~quarterly (new ECU flashes, exhaust systems)

You can always request a new bike or tire — send us the spec and source, and we'll add it.

### Why isn't my bike in the library?
Common reasons:
1. **Too new** — 2025+ models take time to spec accurately
2. **Regional** — we prioritize Indian market + major international bikes
3. **Rare / niche** — one-off builds or limited-production models

You can add your bike via `--spec-json` (CLI), or request it on our forum.

---

## Comparing Modifications

### How do I compare "stock vs. modified"?
1. Run the simulator with your **stock** bike and save the result
2. Run again with mods added
3. Click **Compare** — you'll see ΔET (seconds gained/lost), Δtrap speed, and build cost

The comparison shows you exactly what each modification is worth.

### Can I compare two completely different bikes?
Yes. Open the simulator, switch to Advanced and choose **Compare**: pick a second bike and both run in the same conditions. The **Leaderboard** ranks every catalog bike by its simulated stock time, if you just want to know which is quicker.

### How do I know if a modification is worth the money?
The **cost ROI** shows you $/hp and $/ET-second. A turbo kit that costs ₹2,00,000 and gains 80 hp might be ₹2,500/hp — compare that against a ₹50,000 ECU flash that gains 20 hp (₹2,500/hp). Same cost efficiency, but the ECU flash is less risky and faster to install.

---

## Venues & Weather

### What are "Seasonal Conditions"?
The simulator models **air temperature, pressure (density altitude), and humidity**. These affect engine power output and air density. A hot, humid July at sea level is very different from a cool, dry December at elevation. The simulator shows you a **DA (density altitude) penalty** — how much power you lose vs. ISA standard conditions.

For example, at 35°C and sea level in Pune, you lose ~3–5 % power vs. 15°C standard. This explains why monsoon season is faster than summer.

### Which venues do you have data for?
**India:**
- Aamby Valley (Pune) — the standard drag strip
- MMRT (Mumbai)
- Kari Motor Speedway (Chennai)
- Buddh International Circuit (Noida)
- Hyderabad International Motor Racetrack

**International:**
- Santa Pod (UK), Pomona (USA), Gainesville (USA), Sydney (Australia), Dubai (UAE), Al-Ain (UAE), Jerez (Spain)

Each venue has seasonal weather data (temperature, pressure, humidity) for a full year.

### Can I use custom weather?
Yes — the CLI and API let you set **temperature, pressure, and humidity** manually. The web simulator will add this as an advanced option.

---

## Building & Parts

### What's included in the parts catalog?
- **ECU flashes** — bike-specific (Woolich, Power Commander, etc.)
- **Exhaust systems** — full systems, mid-pipes, slip-ons
- **Air filters & intakes** — stock replacements, high-flow
- **Sprockets & chains** — gear ratio changes
- **Fuel systems** — injectors, pumps, rails
- **Suspension** — springs, dampers, weight reduction
- **Weight reduction** — carbon bodywork, lighter seats, batteries
- **Turbo / supercharger kits** — forced induction
- **Nitrous oxide systems** — NOS injection
- **Clutch kits** — modulated engagement
- **Brakes** — performance calipers, rotors
- **Wheelie bars** — drag-specific traction aids

### Are the parts prices accurate?
Parts are sourced from Indian suppliers and online catalogs. Prices in INR are approximate and change with availability. Use them as a guide, not a quote. For final pricing, contact your local tuner or parts supplier.

### Can I add custom parts?
CLI only — `--spec-json` lets you define custom parts as JSON. The web simulator will support this as a future feature.

### What's a "gear ratio" and why does it matter?
Gear ratio is the number of times the engine spins to turn the wheel once. A bike with a 2.5:1 first gear spins the engine 2.5 times per wheel rotation. Lower ratio = more wheel torque but lower top speed per RPM; higher ratio = less torque but higher speed.

For drag racing, a lower first gear ratio (more aggressive) gets you off the line faster. A higher sixth-gear ratio lets you run higher RPM at trap speed (more power). The simulator lets you swap sprockets to change these ratios.

---

## Troubleshooting

### My ET is slower than I expected. What's wrong?
1. **Check traction %** — if >105 %, you're slipping; softer tire or more rear weight
2. **Check power** — are you running at sea level? High altitude / hot weather = less power
3. **Check staging** — cold engine, bad reaction time, wheel-spin off the line all add time
4. **Check ride height** — very low bikes wheelie harder (instability)
5. **Compare splits** — if only the 60 ft is slow, it's a launch issue; if trap is slow, it's power

### My trap speed seems too low.
Trap speed is determined by power-to-weight. Check:
- **Bike weight** — is the weight correct? (overweight configurations are common)
- **Power** — have you included all mods? A 20 hp error is ~5 km/h at trap
- **Aerodynamics** — high-drag configs (heavy bodywork, poor posture) kill trap speed
- **Tire grip** — slipping at high speeds reduces trap; try a stiffer tire

### The simulator won't accept my tire/bike combo. Why?
The simulator warns if:
- **Physical fitment mismatch** — e.g., a 120/70R17 won't fit a 150/70R17 wheel
- **Pressure/load rating mismatch** — the tire can't handle the bike's weight at rated pressure
- **Extreme outliers** — e.g., a drag slick on a street cruiser (unsafe)

In rare cases, you can override these warnings via the CLI.

### Can I use a bike that's not in your library?
Yes — use `--spec-json` with complete bike parameters (mass, power, aero, tires, gears, etc.). The simulator will run, but accuracy depends on how complete your spec is.

---

## Advanced Topics

### What's "Staging" in the simulator?
Staging models the pre-launch window: rollout distance (to reach stage line), reaction time (human delay), and two-step bouncing (revving to a target RPM for consistent launches). Faster reaction times and zero wheel-spin off the line improve 60 ft. The simulator lets you set these in Advanced mode.

### Can I model a wheelie?
Yes — the simulator detects wheelies dynamically. If front-wheel normal force drops to zero, the front lifts, and you're on the rear wheel only. Wheelies slow you down (less front traction = unstable steering, longer travel time). The simulator shows wheelie timing in the graphs.

### What's "adaptive timestep"?
By default, the simulator integrates at a fixed 1 ms timestep (1000 steps over 1 second). For faster computers, you can enable adaptive timestep (`use_adaptive_dt=True`), which uses smaller steps near the start (where acceleration changes fast) and larger steps at high speed. This is 3–5× faster, and results are identical.

### How do I run batch simulations?
CLI: `python -m motoquant.run sim --bike-id 1 --part-ids 10,20,30 --json > results.json`. Useful for parameter sweeps or tuning comparisons.

---

## Support & Feedback

### How do I report a bug?
Open a [GitHub issue](https://github.com/toto171/MotoQuant.in/issues/new/choose) with the bug-report template, and include:
- Your bike model (make, year)
- Modifications you applied
- The unexpected result
- Expected result (if you know)
- Actual quarter-mile time (if you've run it)

Security problems should be reported privately instead; see [SECURITY.md](../SECURITY.md).

### Can I request a new bike or tire?
Yes. Open a GitHub issue with the **bike data** template and include the make, model, year and any available specs (power, weight, dimensions, OEM tire fitment), with sources. Better still, add it yourself in a PR (see [CONTRIBUTING.md](../CONTRIBUTING.md)). Indian-market bikes and popular international models are prioritized. Every spec needs a citable source; we never fabricate data.

### Can I contribute a real timeslip or dyno sheet?
Please do. Instrumented runs (Dragy, VBOX, Racelogic, timeslips with conditions) are the single most valuable contribution, because small-cc accuracy is limited by data rather than by the model. Use the **Submit a timeslip** issue form; the simulator's Dragy comparison can fill it in for you.

### Is there a community or forum?
GitHub is the community hub: [issues](https://github.com/toto171/MotoQuant.in/issues) for bugs and data corrections, and [discussions](https://github.com/toto171/MotoQuant.in/discussions) for questions and ideas. Please follow the [Code of Conduct](../CODE_OF_CONDUCT.md).

### What's your roadmap?
- **Done:** physics engine, catalog, calibration pipeline, stock leaderboard, shareable timeslips, AI build optimization and chat, MCP server.
- **Discontinued:** the desktop app (July 2026). The web app is the product.
- **Now:** open-source launch, community benchmark contributions, the optional Rust core (exact sims in the browser), accuracy work on small-cc bikes.
- **Later:** OBD-II live telemetry.

The prioritized backlog is [ROADMAP.md](ROADMAP.md).

---

## Legal & Disclaimers

### Is this simulator a substitute for real testing?
No. This is a **predictive tool**, not ground truth. Real quarter-mile results vary with weather, driver skill, tire temperature, surface condition, and equipment wear. Use the simulator to make informed decisions, not as a guarantee.

### Can I use MotoQuant in a tuning shop, a racing team or a commercial product?
Yes. The code is licensed under the **Apache License 2.0**, which permits commercial use, modification and redistribution as long as you keep the license and the `NOTICE` file and mark modified files. Attribution such as "Simulated with MotoQuant" is appreciated. Benchmark figures are cited facts from their original publishers, and bike and parts names are trademarks of their owners (see `NOTICE`). For heavy automated use, please self-host rather than hammering the public instance, which is rate-limited.

### What data do you collect?
Almost none. There are no accounts and no cookies. Simulation requests and uploaded files are used to produce your result and not kept; saved runs stay in your browser. Anonymous usage events (a label, the page and a random per-page id) go to the server log. The full list, including which outside services see what, is at [motoquant.in/privacy](https://www.motoquant.in/privacy).

### Is my data private?
Yes. Nothing you simulate is published. A timeslip link shows its setup to whoever you send it to, and nothing else.

---

**Last updated:** November 2026  
**Questions?** Open a [GitHub discussion](https://github.com/toto171/MotoQuant.in/discussions) or visit motoquant.in
