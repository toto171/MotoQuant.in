# Data provenance and caveats

> Read this before citing, redistributing or building on any MotoQuant data.
> The data is licensed under ODbL 1.0 (`LICENSE-DATA`). This document says
> what each table actually is, because "541 bikes with individual Cd" and
> "593 parts with ROI" mean less than they sound like. Last audited
> 2026-09-15.

## Summary table

| Dataset | Rows | How it was produced | Confidence | Machine-readable provenance? |
|---|---|---|---|---|
| Bike specs (`motoquant/scraper/known_bikes*.py`) | 541 | Typed from public manufacturer spec sheets and spec aggregators during AI-assisted sessions, then partially web-verified in July 2026 (214 field checks with URLs). | Headline specs (displacement, bore/stroke, claimed power, kerb mass, gearing where a service manual was found): medium–high. Everything derived from them: see below. | No. `bike_models.data_source` is `estimated` for every row and `data_provenance.source_url` is NULL. The July-2026 verification URLs live in `reports/scrape_2026_07_10/*.json`. |
| Aerodynamics (`cd`, `frontal_area_m2`) | 541 | Class templates from `CATEGORY_AERO` in the importer, hand-adjusted for a minority of bikes. 540 Cd values collapse to 41 distinct numbers; frontal areas to 35. | Low–medium. Relative differences between classes are physically sensible; per-bike values are not measurements. | No. |
| Torque curves (`dyno_curves`) | 553 | 25 bikes carry curves digitised from published dyno charts. The rest are synthetic curves generated from peak power / peak torque / redline with class-dependent shape constants, declared as crank-side and scaled by a single calibration constant (`_CRANK_MODE_RECAL = 1.08`). | Digitised curves: medium. Synthetic curves: low; shape is a model, not data. | Partly (the digitised curves cite their source in `dyno_curves.py`). |
| Gear ratios (`motoquant/scraper/gear_ratios.py`) | ~150 families | Service-manual and press-kit values where found; family defaults otherwise. | Medium–high for named families; low for defaults. | Comments only. |
| Tires (`tire_models`) | 254 | Sizes and compounds from public fitment data. Pacejka coefficients are templated: 254 rows share 112 distinct (B, C, D, E) tuples, `D` equals `mu_peak`, and the stored confidence is ~0.45–0.55. | Grip *ordering* (slick > race > sport > commuter) is sensible; absolute coefficients are estimates, not measured tyre data. | No. |
| Parts (`parts`) | 593 | Catalogue of real product lines from named brands, with prices estimated by a landed-cost formula (a web-verified subset is stamped `last_price_check`). Performance effects are hand-assigned class-level deltas (`param_deltas` / `param_multipliers`): a full exhaust is "+N hp, −M kg" for its displacement class, not a measurement of that part on that bike. 28 rows are `Generic` class placeholders. | Prices: low–medium. Performance deltas: low. Nothing has measured before/after data. | No source field exists on parts. |
| Part numbers (`parts.part_number`) | 593 | **Synthetic internal keys** (e.g. `AK-HAYA-FS-TI`) used only as the `UNIQUE(brand, part_number)` dedupe key in `parts_repo`. They are not vendor SKUs and must not be used to order parts. | n/a | n/a |
| Benchmarks (`scripts/validation_sweep.py` BENCHMARKS, `topspeed_sweep.py`) | 250 ET / 86 top speed | Published quarter-mile results with a free-text source label, classified and weighted by `scripts/sweep_lib.py::source_weight` (instrumented 1.0 · magazine 0.7 · aggregator 0.5 · forum 0.3 · DERIVED 0.1). DERIVED rows are 0–100 km/h times × 1.6 with a declared ±0.7 s uncertainty and dominate the Indian sub-400cc clusters; some are physically implausible and are kept only so the sweep is reproducible. | Instrumented and magazine rows: medium–high. DERIVED rows: do not use as ground truth. | Labels only; 103 benchmark URLs from the July-2026 verification live in `reports/scrape_2026_07_10/`. |
| Venues (`venues`, `venue_seasonal`) | 20 / 144 | Public elevation and climatological monthly averages. | Medium. | No. |
| Cluster calibration (`motoquant/category_profiles.py`) | ~60 scalars | Grid-tuned against the weighted benchmark corpus (`scripts/tune_cluster_knobs.py`). These are fitted constants: the engine is first-principles in structure, calibrated per bike class in practice. | Reproducible from the corpus. | Yes (the sweep JSONs under `reports/`). |
| Surrogate (`artifacts/surrogate/`, `web/public/surrogate/`) | 1 model | Numpy MLP trained on ~9k of the engine's own simulations. It is a cache of the physics, not independent data. | As good as the engine, within its training envelope. | Yes (README in the artefact folder). |

## What the accuracy numbers mean

- Weighted mean absolute ET error across 276 matched benchmarks is 0.263 s;
  the unweighted mean is 0.372 s. For litre-class sportbikes (the best-
  benchmarked clusters) the raw error is roughly 0.15–0.18 s. For Indian
  sub-400cc bikes the raw error is ~0.9 s against benchmarks that are
  themselves mostly DERIVED, so the true error there is unknown.
- The simulated ET has no rollout and no reaction time; published ETs use the
  1-ft rollout convention. The difference is absorbed by the calibration
  constants above.
- Real-world spread between credible published ETs for the same bike is
  0.5–2.0 s. Treat absolute predictions as class-level; relative A/B deltas
  (sprocket, mass, venue, density altitude) are the engine's strength because
  it is deterministic.

## How to correct something

Open a pull request against the relevant source file with a URL for the
value you are changing (manufacturer page, service manual, instrumented
test). After changing anything that feeds `spec_to_bike_config`, run the
reseed chain in `CLAUDE.md` → *CURRENT STATE*, then `make baselines`. For
benchmark additions, follow the source-labelling conventions in
`scripts/sweep_lib.py` so the weighting classifies your row correctly, and
prefer instrumented (Dragy / VBox / Racelogic) rows over magazine or
aggregator ones.
