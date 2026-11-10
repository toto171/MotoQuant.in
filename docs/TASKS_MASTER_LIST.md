# MotoQuant — Master Task List
**Generated:** April 13, 2026  
**Total Bikes:** 81 (was 56)  
**Total Tires:** 29 (need 120–150)  
**Status:** Phase 2 Remaining + New Tasks from Generalization Audit

---

## ✅ COMPLETED THIS SESSION

- [x] Add 25 missing competitive drag bikes to `known_bikes.py`
  - Suzuki: GSX-R 1000 K1, K3, K7 + TL1000R
  - Yamaha: R1 2002, 2004, 2007, 2009 (4 generations)
  - Honda: CBR1000RR SC59 (2008-12)
  - Kawasaki: ZX-10R 2004, 2006, 2008 + ZX-9R + ZZR1400 + ZX-6R 636 + ZX-6R 2019
  - Ducati: 848, 959, 1199, 1299 Panigales
  - Harley-Davidson: V-Rod Muscle + Sportster S
  - Indian: FTR 1200 S + Scout
  - Aprilia: RSV4 1000 (2009-14)
- [x] Import all 78 new bikes to production DB (81 total)
- [x] Update validator bounds for belt-drive bikes (sprockets: 12-38 / 30-80)
- [x] Run full test suite (245/245 passing)
- [x] Parameter generalization audit (documented in CLAUDE.md + PARAMETER_AUDIT.txt)

---

## ⏳ PHASE 1 — REMAINING

**Status:** ✅ ALL COMPLETE (April 2026)

All 15 sub-models implemented:
- [x] `submodels/rider_dynamics.py` — rider CoG shift + tuck transition
- [x] `submodels/staging.py` — rollout, reaction time, two-step init
- [x] `submodels/environmental.py` — ρ, DA, surface grip/RR multipliers, wind
- [x] Adaptive RK45 solver (`use_adaptive_dt=True`, dt_min=0.5ms, dt_max=5ms)
- [x] 245 unit tests passing

---

## 🔲 PHASE 2 — REMAINING (In Progress)

### 2a. Scraper & Bike Library (Partially Done)

**Completed:**
- [x] SQLite WAL-fallback (DELETE mode on mounted FS)
- [x] Full schema + 12 seed venues (5 Indian, 7 international)
- [x] Bike scraper pipeline (bikez.com blocked by JS; known_bikes.py is active path)
- [x] 81 bikes seeded (was 56)
- [x] 53 curated known_bikes entries (expanded to 78)

**Remaining:**
- [ ] Spot-check gear ratios on 25 new bikes vs service manuals; add missing model families to `gear_ratios.py`
- [ ] Extend `known_bikes.py` with ~30 more hand-curated bikes
  - Indian-market focus: Pulsar 200NS, Dominar 250, Hero Xtreme 160R, KTM Duke 200, etc.
  - Missing historic generations: Suzuki GSX-R 1000 K5/K6, more Yamaha R1 variants, CBR1000RR SC57
  - **Effort:** 6–8 hours research + entry

### 2b. Tire Library (Critical Gap — NEW PRIORITY)

**Current:** 29 tires (heavily Suzuki-biased)

**Critical Findings:**
- 71% of bikes use Cd=0.32 (over-generalization)
- 73% of bikes use frontal area=0.45 m² (over-generalization)
- Tire library missing major OEM manufacturers on 81 bikes
- No drag-specific compounds (Dunlop ET Street, Michelin Pilot Sport Comp)
- Only 1 drag slick (MV Agusta 295/35R18)

**Expansion Required:** 120–150 unique tire specs

**Priority Tier 1 (40–50 tires) — OEM fitments on 81 bikes:**
- Dunlop (Harley, Kawasaki ZX-9R, historical Yamaha R1, ZZR1400, etc.)
- Michelin (Yamaha R1 gen 2-3, Aprilia RSV4 gen 1)
- Pirelli (Ducati 1199/1299, Aprilia RSV4, Triumph)
- Bridgestone (Honda CBR1000RR SC57, some Kawasaki)
- Continental (Indian Scout)
- Metzeler (some BMW, KTM)
- Goodyear (historical Harley-Davidson)
- Regional: Indian market variants (TVS Apache RR310 compound, Bajaj Dominar)

**Priority Tier 2 (20–30 tires) — Drag-specific compounds:**
- Dunlop ET Street (multiple variants: ET Street R, ET Street R Radial)
- Michelin Pilot Sport Cup 2 R, Michelin Pilot Sport Comp
- Avon 3D Ultra Sport
- Bridgestone Battlax SB130 (drag compound)
- DOT slick variants (R-compound, semi-slick)

**Effort:** 8–12 hours research (cross-ref: spec sheets, drag forums, dyno shops) + entry

**Database schema change:**
- Link `bike_configs` ↔ `tire_models` (1-to-many: front/rear)
- Store OEM tire pair as default for each `bike_config`
- Add `is_oem_fitment: BOOLEAN` to link table

### 2c. Tire Selector Feature (NEW — UNBLOCKS USER CALIBRATION)

**Scope:** Allow users to swap front/rear tires and see ET impact in real-time

**App (Streamlit):**
- [ ] Add sidebar dropdowns: "Front tire" + "Rear tire"
- [ ] Filter by: bike category, tire size, compound (stock|DOT drag|R-compound|slick)
- [ ] Real-time ET update on tire change
- [ ] Show ET delta from stock (e.g., "+0.15s" in red, "-0.08s" in green)
- [ ] Optional: tire temp curve overlay on existing plots
- **Effort:** 2–3 hours

**CLI:**
- [ ] New flags: `--front-tire SIZE/COMPOUND --rear-tire SIZE/COMPOUND`
- [ ] Preset: `--tire-set {stock|drag_dot|r_compound|slick}`
- [ ] Output: ET, traction%, tire temps before/after
- **Effort:** 1–2 hours

**Database:**
- [ ] Create `bike_config_tires` link table (bike_config_id, front_tire_id, rear_tire_id)
- [ ] Populate OEM defaults for all 81 bikes
- **Effort:** 1 hour

**Total effort:** 4–6 hours  
**Unlock:** User calibration workflows, validation accuracy ±0.15–0.2s

### 2d. Aero Parameter Generalization Fix (PHYSICS RIGOR)

**Problem:**
- 58/81 bikes share Cd=0.32 (unrealistic)
- 59/81 bikes share frontal area=0.45 m² (unrealistic)
- Combined: 2.6× drag variance across fleet
- Impact: ±0.25–0.35s ET error (unacceptable for physics-first approach)

**Solution:** Bike-specific Cd + frontal area for all 81 models

**Research methodology:**
1. Sport bikes (45 bikes): dyno sheets, manufacturer wind tunnel data
   - GSX-R 1000 variants: Cd 0.68–0.72, area 0.45–0.50
   - R1 variants: Cd 0.68–0.72, area 0.44–0.46
   - CBR1000RR: Cd 0.67, area 0.47
   - ZX-10R variants: Cd 0.65–0.70, area 0.46–0.48
   - Ducati twins: Cd 0.62–0.68, area 0.48–0.50
   - Aprilia RSV4: Cd 0.65, area 0.46

2. Naked/Streetfighter (18 bikes): estimated from fairing geometry
   - Default: Cd 0.40, area 0.52 (uprights)
   - Aggressive naked: Cd 0.38, area 0.50

3. Cruiser/Muscle (10 bikes): estimated from upright stance
   - V-Rod, Sportster S: Cd 0.50–0.55, area 0.55
   - Scout: Cd 0.50, area 0.56
   - FTR 1200: Cd 0.42, area 0.52

4. Sport Touring (8 bikes): screen + saddlebags
   - ZZR1400: Cd 0.55–0.60, area 0.50

**Sources to cross-reference:**
- Manufacturer tech specs (Honda, Suzuki, Yamaha publishes some)
- Dyno shop data (Dynojet, Power Commander)
- Motorcycle magazines (Cycle World, Motorcyclist, MCN dyno tests)
- Academic papers: motorcycle aerodynamics
- CFD estimates (if no data available)

**Data entry:**
- Add `drag_coeff` + `frontal_area_m2` fields to each bike in `known_bikes.py` (within aero_params)
- Document source for each value in comments
- Update importer to use bike-specific values instead of defaults

**Validation:**
- Rerun physics validation tests (GSX-R K5 target 10.04s should improve ±0.05s)
- Compare ET predictions across variants (e.g., K1 vs K9 should differ by ~0.15s)

**Effort:** 14–18 hours (research + entry + validation)

**Impact:** Moves validation accuracy from ±0.5s → ±0.1–0.15s range

---

## 🎯 PRIORITY ROADMAP

### Week 1 (HIGH-IMPACT, LOW-EFFORT)
1. **Tire selector UI** (3 hours) → unblocks user experimentation
2. **Expand tire library** (40–50 priority tires, 8–10 hours) → enables selector
3. **Link OEM tires to bikes** (1 hour) → selector has sensible defaults

**Subtotal: 12–14 hours** → User can now swap tires, see ET impact

### Week 2 (PHYSICS RIGOR)
4. **Research + add bike-specific Cd + frontal area** (16 hours)
   → Achieves "minimal generalization" goal
   → Moves accuracy from ±0.5s to ±0.1–0.15s

**Subtotal: 16 hours** → Physics-first quantitative simulator ready

### Week 3+ (EXPANSION & REFINEMENT)
5. **Spot-check 25 new bike gear ratios** (2–3 hours)
6. **Add ~30 more curated bikes** (6–8 hours) — Indian market focus
7. **Drag-specific tire compounds** (6–8 hours) — Dunlop ET Street, Michelin Pilot
8. **User calibration workflow** — dragy GPS import + auto-fit (Phase 3)

---

## 📊 SUMMARY

| Category | Count | Status | Effort |
|---|---|---|---|
| Bikes | 81 | ✅ Complete | — |
| Tires (current) | 29 | ❌ Gap | 8–12 hrs to add 40–50 |
| Parameter generalization | 71% over-gen | ❌ Gap | 16 hrs to fix |
| Tire selector | — | 🔲 Design | 4–6 hrs to build |
| Test suite | 245/245 | ✅ Green | — |
| **Total remaining to Phase 2 complete** | — | — | **~26–32 hours** |

---

## 📝 FILES TO UPDATE

- [ ] `motoquant/scraper/known_bikes.py` — add 30 more bikes + Cd/area for all 81
- [ ] `motoquant/scraper/gear_ratios.py` — spot-check 25 new bikes
- [ ] `motoquant/database/seed.py` — expand tire library seed (40–50 new entries)
- [ ] `motoquant/database/schema.py` — add `bike_config_tires` link table (optional, can use default_front_tire_id + default_rear_tire_id on bike_configs)
- [ ] `app.py` — add tire selector sidebars, ET delta display
- [ ] `motoquant/run.py` — add `--front-tire` / `--rear-tire` / `--tire-set` CLI flags
- [ ] `CLAUDE.md` — update Phase 2 "Remaining" checkboxes as progress happens
- [ ] `PARAMETER_AUDIT.txt` — reference document (already created)

---

## 🔗 RELATED FILES (CONTEXT)

- `PARAMETER_AUDIT.txt` — Full quantitative analysis of generalization
- `tests/test_scraper.py` — 79 tests covering bike spec validation
- `tests/test_validation.py` — Physics validation benchmarks (GSX-R K5, R1, Hayabusa)
- `motoquant/models.py` — BikeSpec, AeroParams, ChassisParams dataclasses

---

## 🚀 NEXT SESSION STRATEGY

1. **Start with tire selector** — quick win, unblocks user testing
2. **Parallel: tire library expansion** — enables selector
3. **Then: aero params** — achieves physics rigor
4. **Bonus: more known_bikes** — Indian market coverage

By end of next session: **Phase 2 substantially complete**, validation accuracy ±0.1–0.15s, user-facing tire experimentation live.
