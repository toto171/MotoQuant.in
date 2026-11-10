# MotoQuant FAQ

## General questions

### What is MotoQuant?
MotoQuant is a free, open-source quarter-mile drag racing simulator for motorcycles. It predicts your bike's quarter-mile ET (elapsed time) and trap speed from first-principles physics: aerodynamics, tyre grip and temperature, the drivetrain and the engine. You can try a modification, such as more power, other gear ratios, a tyre swap or less weight, and see what it does to the time *before* you spend money at the tuner or the parts shop.

### Is it free? Is it open source?
Yes to both. Everything (the simulator, parts ROI, build optimizer, autotune, Dragy/dyno calibration, chat) is free, with no paid tiers, no quotas and no license keys. The code is open source under the Apache License 2.0: <https://github.com/toto171/MotoQuant.in>. You can use the hosted site at motoquant.in or run your own copy ([SELF_HOSTING.md](SELF_HOSTING.md)). There are no accounts: runs you save stay in your browser, and a timeslip link shares one.

### Who should use it?
- Drag racers, to predict the ET gain from a mod and plan a build within a budget.
- Tuning shops, to check customer expectations and show the return on a part before fitting it.
- Enthusiasts who are curious about the physics or want to benchmark against known times.
- Students, who get a working model of motorcycle physics to learn from.

### Is it accurate?
MotoQuant is validated against 250 published benchmarks (magazine road tests, instrumented GPS runs and timeslips), weighted by source quality. Across 263 matches to catalog bikes the weighted mean error is about **0.25 s** and the mean bias **+0.02 s**. Reference bikes, simulated at sea level: GSX-R 1000 K5 10.04 s vs 9.97 s (Cycle World), YZF-R1 10.11 s vs 10.30 s (Sport Rider), Hayabusa Gen1 10.11 s vs 10.40 s (Cycle World). Small-cc bikes are the weakest class: few instrumented benchmarks exist for them, and many still carry a generic primary gear ratio in the catalog. For a bike not in the library the result is an estimate. Use it to guide a decision, not as a guarantee. The full breakdown is at motoquant.in/validation.

### Where does the simulator run?
- The web simulator on motoquant.in: enter your bike and mods and get an ET in about 50 ms.
- The CLI (`python -m motoquant.run sim ...`), for batch runs and scripts.
- The API, a FastAPI backend you can call from your own tools.
- Your own server: self-host the whole stack from the open-source repo ([SELF_HOSTING.md](SELF_HOSTING.md)).

---

## Using the simulator

### How do I start a simulation?
Open the simulator at motoquant.in/simulator. It starts in **Simple** mode:
1. Choose your bike (search by make, model or year)
2. Set the rider weight
3. Say where you are racing (a city or a drag strip), or leave the default conditions

The quarter-mile time and trap speed update as you change things, and the result always says which conditions it was computed for.

### What does Simple mode do?
Simple mode answers one question: how quick is this bike, with this rider, at this place? Under the result it offers the next steps: add parts and mods, find the best parts for a budget ("Upgrades"), get a race-day setup, compare with another bike, see charts and splits, or save and share the run.

A result marked **Instant estimate** comes from a fast model that runs in your browser; **Exact** means the full physics simulation ran. Only exact results can be saved and shared as a timeslip. The leaderboard ranks every catalog bike by its simulated stock time.

### What's Advanced mode?
Advanced mode puts the full workbench in one place:
- Setup: bike, rider weight, an engine power change (−20 % to +50 %), weight added or removed, air and altitude (venue, air and track temperature, humidity, headwind) and front and rear tyres.
- Parts and mods: pick individual parts from the catalog (ECU tunes, exhausts, intake filters, sprockets and chains, suspension, weight reduction, turbo and supercharger kits, nitrous, and more). A part only appears for the bikes it fits.
- Results: Quarter mile, Top speed, Charts, Splits, Compare, My data (your own Dragy runs and dyno sheets) and Specs.

The result shows the build cost and the change against the stock bike.

### How do I choose tyres?
In Advanced mode the front and rear tyre pickers start on **Original tyre (stock)**. You can swap in any tyre from the library; each entry shows its size and compound (sport, sport-touring, race, drag radial or slick, commuter). The picker does not stop you choosing a size that will not fit your rims, so check the size yourself. Each bike's page under motoquant.in/bikes lists the tyres recorded as fitting it. From the command line, `python -m motoquant.run bikes --fitments BIKE_ID` shows the original, recommended and drag-prep tyres recorded for a bike.

### Can I change rider weight?
Yes, with the **Rider weight** slider (50–130 kg). A heavier rider means slower acceleration (more inertia), later wheelies and different weight transfer. How much it matters depends on the bike. A litre bike is limited by wheelies and grip at launch, so 20 kg costs it only a few hundredths of a second; on a 150 cc bike it can be several tenths.

### What does "Engine power change" do in Advanced mode?
It multiplies the bike's whole power and torque curve: +20 % on a 180 hp bike is 216 hp. Use it for a quick what-if. To model a real build, pick the parts instead.

---

## Understanding results

### What does "ET" mean?
ET is elapsed time: the seconds taken to cover 402.336 m (0.25 mile, a quarter mile). Lower is faster. As on a strip timeslip, MotoQuant starts the clock when the bike has rolled the first foot (0.3048 m) out of the stage beam, not at first motion. A 10-second ET is very respectable for a street bike; 9 seconds is excellent.

### What's trap speed?
Trap speed is your speed at the finish line (the 402.336 m mark), in km/h or mph. It follows your power-to-weight ratio and aerodynamics. A 250 km/h trap is typical for a litre bike; 280 km/h or more needs serious mods.

### What are the split times?
The standard quarter-mile splits show your acceleration through the run:
- 60 ft (18.3 m): off-the-line traction and the launch
- 330 ft (100 m): mid-range power delivery
- 660 ft (200 m): where the top bikes start to pull away from slower ones
- Trap (402 m): the finish

If your 60 ft is slow, look at wheelspin or the launch. If the trap is slow but the early splits are good, you're running out of power or hitting a gear wall.

### What does "Traction %" mean?
Traction % is the grip margin. At 100 % the tyre is using all the grip it has. Below 100 % you have headroom; above it you're on the edge of wheelspin. About 98 % is ideal: barely spinning, maximum acceleration. At 105 % you're slipping, and a softer tyre or less weight would improve traction.

### Why is my 60-foot time slow?
The usual causes:
1. Soft tyres: sticky, but too much slip. Try a stiffer compound.
2. Too much power: wheelspin right off the line. Reduce boost or add weight to the rear.
3. Rider technique: two-step bouncing, a late launch, poor clutch control (see "What's staging in the simulator?" below).
4. Grip at the staging line: rain, oil or a loose surface lowers the grip multiplier.

### Can I see a graph of my acceleration over time?
Yes. After a full simulation the web simulator's Charts tab plots speed, RPM, gear and tyre temperature against time. The CLI can write the same time series as JSON.

---

## Physics and modeling

### How does the simulator predict power delivery?
The engine model uses a torque curve: a table of torque (Nm) against RPM. Stock curves come from service manuals or dyno data. When you add a tune or a bolt-on, we adjust the curve (typically +8–15 % peak torque and a broader power band). The model treats an ECU flash as a change to the curve's shape, not just a flat percentage.

### What's a dyno curve?
A dyno (dynamometer) measures the real power at the wheels. If you import your dyno data, the simulator uses your curve instead of an estimate.

### How is aerodynamic drag calculated?
Drag force = 0.5 × ρ × Cd × A × v². Each bike has a drag coefficient (Cd) and a frontal area (A) based on its design. Sport bikes (Cd ≈ 0.65) are more slippery than naked bikes (Cd ≈ 0.80). In a quarter mile, aero is about 5–10 % of your total power loss.

### What about tyre physics?
The rear tyre's grip limit is its peak friction coefficient times the load on the rear wheel. The coefficient drops slightly as load rises, and it changes with tread temperature, tyre pressure (which rises as the tyre warms) and track preparation. The tread heats from wheel slip and loses heat to the road and the air, so grip changes during the run. The model also includes a Pacejka slip curve, but the simulation does not use it yet.

### How does weight affect acceleration?
In two ways, and the simulator models both:
1. Inertia: heavier things accelerate more slowly (F = ma).
2. Traction: more weight means more normal force, which means more grip.

On a light 200 cc bike, adding 5 kg costs about as much as losing 1–2 % of power. On a 200 kg superbike, 5 kg is almost nothing.

### What's weight transfer?
As you accelerate, weight shifts from the front wheel to the rear (because the rear wheel is accelerating the bike upward). Early in the run, more weight on the rear gives more rear-wheel traction. Late in the run, at higher speed, weight moves back to the front. The simulator calculates this at every instant.

### Why do you lose speed at high RPMs?
Aerodynamic drag increases with the square of speed. At high speed more power goes into pushing the air and less into accelerating the bike. That's why top fuel dragsters have parachutes: they can't slow down any other way at 500 km/h.

---

## Customization and accuracy

### Can I upload my own dyno data?
Yes. The CLI imports dyno CSVs (`python -m motoquant.run calibrate import-dyno FILE`) and the web app accepts dyno uploads. After import the simulator uses your real curve instead of an estimate. For a tuned bike this is the best way to get an accurate prediction.

### Can I import Dragy GPS data from my runs?
Yes. The simulator can import Dragy CSV or VBO files from RaceChrono. It reads your real acceleration profile and can calibrate the model automatically to match it. Use `calibrate import-dragy FILE`.

### What about ECU log data (Woolich / PC-Link / MoTeC)?
The simulator can read ECU logs and pull out the run data: RPM, TPS, speed, gear, AFR and temperatures. You can overlay that data on a simulation to check your bike's real performance.

### How often is the bike and tyre library updated?
- Bikes: about quarterly (new model years, Indian-market additions)
- Tyres: about monthly (new compounds, OEM fitments)
- Parts catalog: about quarterly (new ECU flashes, exhaust systems)

To request a new bike or tyre, send us the spec and its source and we'll add it.

### Why isn't my bike in the library?
The usual reasons:
1. It is too new: 2025 and later models take time to spec accurately.
2. It is regional: we prioritize the Indian market and major international bikes.
3. It is rare: a one-off build or a limited-production model.

You can add your bike with `--spec-json` (CLI), or request it on our forum.

---

## Comparing modifications

### How do I compare stock and modified?
1. Run the simulator with your stock bike and save the result
2. Run it again with the mods added
3. Click **Compare** to see ΔET (seconds gained or lost), Δtrap speed and the build cost

### Can I compare two completely different bikes?
Yes. Open the simulator, switch to Advanced and choose **Compare**: pick a second bike and both run in the same conditions. If you only want to know which is quicker, the **Leaderboard** ranks every catalog bike by its simulated stock time.

### How do I know if a modification is worth the money?
The cost ROI shows $/hp and $/ET-second. A turbo kit that costs ₹2,00,000 and gains 80 hp works out at ₹2,500/hp. A ₹50,000 ECU flash that gains 20 hp is also ₹2,500/hp. The cost per hp is the same, but the ECU flash is less risky and faster to install.

---

## The chat assistant

### What can I ask the chat?
Anything you would ask the simulator, in plain English: "How fast is a Duke 390 at Aamby Valley?", "Compare a ZX-10R and an S1000RR", or a build plan such as "Hayabusa, 1.5 lakh, quickest ET". It runs the real simulations and the build optimizer to answer, and every number comes from those runs.

### Who answers?
Claude, made by Anthropic, so your questions are sent to Anthropic. The **Assistant** dropdown has two choices:

1. The doctor: Claude Opus 5.5. Slower, digs deeper.
2. The mechanic (the default): Claude Sonnet 5.5. Quick, practical answers.

Your browser remembers your choice.

### Is there a limit?
The free assistant allows 200 questions a day per connection by default. A question to the mechanic counts as one and a question to the doctor as two. If you use your own key, the daily limit does not apply. A short per-minute limit still does, because every answer runs simulations on our server.

### Can I use my own Anthropic key?
Yes. Open **Use your own key** under the chat, paste an API key from the [Anthropic Console](https://console.anthropic.com/settings/keys) and press **Use key**. Your key stays in this browser: for this tab only, or until you remove it if you tick **Remember on this device**. It is sent with your questions to answer them and is never stored on our server. Questions asked with your key are billed to your Anthropic account. Press **Remove key** to delete it from the browser.

### The chat says the free assistant is resting or switched off. What now?
The site's own key has reached its spending limit, or the server has no key. Add your own Anthropic key to keep asking, or try again later. The calculator and the other tools still work without the chat.

---

## Venues and weather

### What are seasonal conditions?
The simulator models air temperature, pressure (density altitude) and humidity. These change engine power output and air density. A hot, humid July at sea level is very different from a cool, dry December at elevation. The simulator shows a DA (density altitude) penalty: how much power you lose against ISA standard conditions.

At 35°C and sea level in Pune, you lose about 3–5 % power against 15°C standard. That is why monsoon season is faster than summer.

### Which venues do you have data for?
In India:
- Aamby Valley (Pune), the standard drag strip
- MMRT (Mumbai)
- Kari Motor Speedway (Chennai)
- Buddh International Circuit (Noida)
- Hyderabad International Motor Racetrack

Elsewhere: Santa Pod (UK), Pomona (USA), Gainesville (USA), Sydney (Australia), Dubai (UAE), Al-Ain (UAE) and Jerez (Spain).

Each venue has seasonal weather data (temperature, pressure, humidity) for a full year.

### Can I use custom weather?
Yes. The CLI and the API let you set temperature, pressure and humidity by hand. The web simulator will add this as an advanced option.

---

## Building and parts

### What's included in the parts catalog?
- ECU flashes, bike-specific (Woolich, Power Commander, etc.)
- Exhaust systems: full systems, mid-pipes, slip-ons
- Air filters and intakes: stock replacements, high-flow
- Sprockets and chains, for gear ratio changes
- Fuel systems: injectors, pumps, rails
- Suspension: springs, dampers, weight reduction
- Weight reduction: carbon bodywork, lighter seats, batteries
- Turbo and supercharger kits (forced induction)
- Nitrous oxide systems (NOS injection)
- Clutch kits, for modulated engagement
- Brakes: performance calipers, rotors
- Wheelie bars, a drag-specific traction aid

### Are the parts prices accurate?
Parts are sourced from Indian suppliers and online catalogs. Prices in INR are approximate and change with availability. Use them as a guide, not a quote. For the final price, ask your local tuner or parts supplier.

### Can I add custom parts?
Only from the CLI: `--spec-json` lets you define custom parts as JSON. The web simulator will support this later.

### What's a gear ratio and why does it matter?
Gear ratio is the number of times the engine turns for one turn of the wheel. A bike with a 2.5:1 first gear spins the engine 2.5 times per wheel rotation. A lower ratio gives more wheel torque but a lower top speed per RPM; a higher ratio gives less torque but more speed.

For drag racing, a lower (more aggressive) first gear ratio gets you off the line faster. A higher sixth-gear ratio lets you run higher RPM at trap speed, where there is more power. The simulator lets you swap sprockets to change these ratios.

---

## Troubleshooting

### My ET is slower than I expected. What's wrong?
1. Check traction %. Above 105 % you're slipping: fit a softer tyre or add rear weight.
2. Check power. Are you running at sea level? High altitude or hot weather means less power.
3. Check staging. A cold engine, a slow reaction time and wheelspin off the line all add time.
4. Check ride height. Very low bikes wheelie harder (instability).
5. Compare splits. If only the 60 ft is slow, it's the launch; if the trap is slow, it's power.

### My trap speed seems too low.
Power-to-weight sets the trap speed. Check:
- Bike weight: is it correct? Overweight configurations are common.
- Power: have you included every mod? A 20 hp error is about 5 km/h at the trap.
- Aerodynamics: high-drag setups (heavy bodywork, poor posture) cost a lot of trap speed.
- Tyre grip: slipping at high speed lowers the trap. Try a stiffer tyre.

### The simulator won't accept my tyre and bike combination. Why?
The simulator warns about:
- A physical fitment mismatch, e.g. a 120/70R17 won't fit a 150/70R17 wheel.
- A pressure or load rating mismatch: the tyre can't carry the bike's weight at its rated pressure.
- Extreme outliers, e.g. a drag slick on a street cruiser (unsafe).

In rare cases you can override these warnings from the CLI.

### Can I use a bike that's not in your library?
Yes. Use `--spec-json` with the complete bike parameters (mass, power, aero, tyres, gears, etc.). The simulator will run, but accuracy depends on how complete your spec is.

---

## Advanced topics

### What's staging in the simulator?
Staging models the window before the launch: rollout distance (to reach the stage line), reaction time (human delay) and two-step bouncing (revving to a target RPM for consistent launches). Faster reactions and no wheelspin off the line improve the 60 ft. You can set these in Advanced mode.

### Can I model a wheelie?
Yes. The simulator detects wheelies as the run happens. If the front wheel's normal force drops to zero, the front lifts and you're on the rear wheel only. Wheelies slow you down (less front traction means unstable steering and a longer travel time). The graphs show when the wheelie happens.

### What's adaptive timestep?
By default the simulator integrates at a fixed 1 ms timestep (1000 steps per second). On faster computers you can turn on the adaptive timestep (`use_adaptive_dt=True`). It uses smaller steps near the start, where acceleration changes fast, and larger steps at high speed. It is 3–5× faster and the results are identical.

### How do I run batch simulations?
From the CLI: `python -m motoquant.run sim --bike-id 1 --part-ids 10,20,30 --json > results.json`. Use it for parameter sweeps or to compare tunes.

---

## Support and feedback

### How do I report a bug?
Open a [GitHub issue](https://github.com/toto171/MotoQuant.in/issues/new/choose) with the bug-report template, and include:
- Your bike model (make, year)
- The modifications you applied
- The unexpected result
- The expected result (if you know it)
- Your real quarter-mile time (if you've run it)

Report security problems privately instead; see [SECURITY.md](../SECURITY.md).

### Can I request a new bike or tyre?
Yes. Open a GitHub issue with the **bike data** template and include the make, model, year and any specs you have (power, weight, dimensions, OEM tyre fitment), with sources. Better still, add it yourself in a PR (see [CONTRIBUTING.md](../CONTRIBUTING.md)). Indian-market bikes and popular international models come first. Every spec needs a citable source; we never make up data.

### Can I contribute a real timeslip or dyno sheet?
Please do. Instrumented runs (Dragy, VBOX, Racelogic, timeslips with conditions) are the most valuable contribution, because small-cc accuracy is limited by data, not by the model. Use the **Submit a timeslip** issue form; the simulator's Dragy comparison can fill it in for you.

### Is there a community or forum?
The community is on GitHub: [issues](https://github.com/toto171/MotoQuant.in/issues) for bugs and data corrections, and [discussions](https://github.com/toto171/MotoQuant.in/discussions) for questions and ideas. Please follow the [Code of Conduct](../CODE_OF_CONDUCT.md).

### What's your roadmap?
- Done: physics engine, catalog, calibration pipeline, stock leaderboard, shareable timeslips, AI build optimization and chat, MCP server.
- Discontinued: the desktop app (July 2026). The web app is the product.
- Now: open-source launch, community benchmark contributions, the optional Rust core (exact sims in the browser), accuracy work on small-cc bikes.
- Later: OBD-II live telemetry.

The prioritized backlog is [ROADMAP.md](ROADMAP.md).

---

## Legal and disclaimers

### Is this simulator a substitute for real testing?
No. It gives a prediction, not ground truth. Real quarter-mile results vary with weather, rider skill, tyre temperature, surface condition and equipment wear. Use the simulator to inform decisions, not as a guarantee.

### Can I use MotoQuant in a tuning shop, a racing team or a commercial product?
Yes. The code is licensed under the Apache License 2.0, which permits commercial use, modification and redistribution as long as you keep the license and the `NOTICE` file and mark modified files. Attribution such as "Simulated with MotoQuant" is appreciated. Benchmark figures are cited facts from their original publishers, and bike and parts names are trademarks of their owners (see `NOTICE`). For heavy automated use, please self-host instead of hammering the public instance, which is rate-limited.

### What data do you collect?
Almost none. There are no accounts and no cookies. Simulation requests and uploaded files are used to produce your result and not kept; saved runs stay in your browser. Anonymous usage events (a label, the page and a random per-page id) go to the server log. The full list, including which outside services see what, is at [motoquant.in/privacy](https://www.motoquant.in/privacy).

### Is my data private?
Yes. Nothing you simulate is published. A timeslip link shows its setup to whoever you send it to, and nothing else.

---

Last updated: November 2026.

Questions? Open a [GitHub discussion](https://github.com/toto171/MotoQuant.in/discussions) or visit motoquant.in.
