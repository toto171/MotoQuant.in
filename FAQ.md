# MotoQuant Pro — Frequently Asked Questions

## General Questions

### What is MotoQuant Pro?
MotoQuant Pro is a physics-based quarter-mile drag racing simulator for motorcycles. It uses first-principles aerodynamics, tire physics (Pacejka slip characteristics), drivetrain dynamics, and engine modeling to predict your bike's quarter-mile ET (elapsed time) and trap speed. The simulator lets you test modifications—power increases, gear ratios, tire swaps, weight reduction—and see their impact on performance *before* spending money at the tuner or parts shop.

### Who should use it?
- **Drag racers** — predict ET gains from mods, plan builds within budget constraints
- **Tuning shops** — validate customer expectations, show ROI on parts before installation
- **Enthusiasts** — curiosity about physics, benchmark against known times
- **Students** — learn motorcycle physics with a working model

### Is it accurate?
Our validation benchmarks show **±0.07 seconds** on known quarter-mile times (GSX-R 1000 K5: 9.97 s actual vs. 10.04 s simulated). The engine is validated on 3 reference bikes. For bikes not in the library, results are estimates — use them to guide decisions, not as law.

### Where does the simulator run?
- **Web simulator** on motoquant.in — enter your bike and mods, get ET in ~50 ms
- **Streamlit app** (`streamlit run app.py`) — local installation with full advanced mode
- **CLI** (`python -m motoquant.run sim ...`) — batch simulations, scripting
- **API** — FastAPI backend for integration into your own tools

---

## Using the Simulator

### How do I start a simulation?
1. Search for your bike by make, model, and year
2. Select front and rear tires (OEM fitments are highlighted ✅)
3. Choose **Basic** mode (quick power/weight sliders) or **Advanced** mode (individual parts)
4. Click **Simulate**
5. See your ET, trap speed, and build cost

### What does "Basic Mode" do?
Basic Mode is the quick path. Adjust a **Power Boost** slider (0–50 %) and **Weight Reduction** slider. The simulator shows your expected ET and cost. Use this when you want a fast estimate.

### What's "Advanced Mode"?
Advanced Mode lets you pick individual parts from the catalog. You can add:
- ECU tunes / flashes (+ HP, – consistency in cold weather)
- Exhaust systems (small HP/TQ gains, weight savings)
- Intake filters (marginal gains, noise character)
- Sprocket & chain combos (gear ratio change)
- Suspension parts (reduced unsprung mass, handling)
- Weight reduction (bodywork, seats, batteries)
- Turbo/supercharger kits (large HP jumps, setup risk)
- Nitrous systems (controlled HP addition)
- And more

The simulator shows the **net effect** of all selected parts before you run the sim: "+14 hp · –2.5 kg mass · –0.08 s ET estimate". Parts are **bike-specific** — a 530-chain sprocket won't appear for a bike that runs 530 chain.

### How do I choose between tires?
1. The **OEM fitments** (with ✅) are what the manufacturer recommends — safest choice
2. **Recommended tires** are compatible and trusted by racers
3. **Drag-specific tires** are slicks or DOT drag tires for serious racers

The web simulator and app warn you if you pick a tire that doesn't physically fit your bike.

### Can I change rider weight?
Yes. Use the **Rider Weight** slider (50–130 kg). Heavier riders = slower acceleration (more inertia), later wheelies, different weight transfer. A 20 kg change is worth ~0.1 s.

### What's the difference between my bike's power and the "Power %" in Basic mode?
**Power %** is a multiplier on your base bike power. So a GSX-R 1000 K5 (182 hp stock) at +20 % gets 182 × 1.20 = **218 hp**. In Advanced mode, you pick parts and see the exact HP and torque curve.

---

## Understanding Results

### What does "ET" mean?
**ET** = Elapsed Time, how many seconds to complete 402.336 meters (0.25 miles / quarter mile). Lower is faster. A 10-second ET is very respectable for a street bike; 9 seconds is excellent.

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
Yes — the Streamlit app shows **v(t), RPM(t), gear(t), and tire temperature(t)** plots. The web simulator shows these as a future feature.

---

## Physics & Modeling

### How does the simulator predict power delivery?
The engine model uses a torque curve — a table of RPM → Torque (Nm). Stock curves come from service manuals or dyno data. When you add a tune or bolt-on, we adjust the curve (typical: +8–15 % peak torque, broadened power band). ECU flash effects are modeled as curve shape changes, not just a flat +%.

### What's a "Dyno curve"?
A dyno (dynamometer) measurement of **real, actual power** at the wheels. You can import dyno data directly, and the simulator will use your actual curve instead of estimates. This is crucial for tuned bikes.

### How is aerodynamic drag calculated?
Drag force = 0.5 × ρ × Cd × A × v². Each bike has a **drag coefficient (Cd)** and **frontal area (A)** based on design. Sport bikes (Cd ≈ 0.65) are more slippery than naked bikes (Cd ≈ 0.80). In a quarter-mile, aero is ~5–10 % of your total power loss.

### What about tire physics?
The simulator uses the **Pacejka slip model** — a real-world formula that predicts grip as a function of slip ratio (wheel speed vs. ground speed). Your slip ratio changes dynamically during the run. We also model tire temperature rise, which affects grip and rolling resistance.

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
Yes — the CLI and Streamlit app support dyno CSV import (`python -m motoquant.run calibrate import-dyno FILE`). After import, the simulator uses your real curve instead of estimates. This is the best way to get accurate predictions for a tuned bike.

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
Yes — run Bike A, save it, then search for Bike B and run that. The **Leaderboard** view shows all your saved runs ranked by ET. Use this to settle debates ("Is my R1 faster than my mate's Hayabusa?").

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
Email us at **support@motoquant.in** with:
- Your bike model (make, year)
- Modifications you applied
- The unexpected result
- Expected result (if you know)
- Actual quarter-mile time (if you've run it)

Or use the bug report form on motoquant.in.

### Can I request a new bike or tire?
Yes — email **requests@motoquant.in** with the make, model, year, and any available specs (power, weight, dimensions, OEM tire fitment). We prioritize Indian-market bikes and popular international models.

### Is there a community or forum?
We're building one — watch motoquant.in for launch. In the meantime, reach out directly or join our Discord (link at motoquant.in).

### What's your roadmap?
- **Phase 3 (Current):** Web launch, calibration pipeline, public leaderboard
- **Phase 4:** AI optimization (Bayesian tuning within budget)
- **Phase 5:** Desktop app with live PINN simulation (instant slider feedback)
- **Phase 6:** B2C freemium / B2B pro tiers, OBD-II live telemetry

See the full roadmap at motoquant.in/roadmap.

---

## Legal & Disclaimers

### Is this simulator a substitute for real testing?
No. This is a **predictive tool**, not ground truth. Real quarter-mile results vary with weather, driver skill, tire temperature, surface condition, and equipment wear. Use the simulator to make informed decisions, not as a guarantee.

### Can I use your data in a tuning shop?
Yes, if you include proper attribution: "Simulated with MotoQuant Pro." For commercial use (shops, racing teams, OEMs), contact us about licensing.

### What data do you collect?
- Simulation runs (anonymized: bike ID, mods, results — no personal info)
- Dragy/dyno imports you choose to upload
- Leaderboard submissions (you can opt out)

See our Privacy Policy at motoquant.in/privacy.

### Is my data private?
Yes — simulation runs are your own unless you explicitly submit to the public leaderboard. Leaderboard submissions show your time and bike, not your name or contact info (unless you choose to add it).

---

**Last updated:** April 2026  
**Questions?** Contact support@motoquant.in or visit motoquant.in
