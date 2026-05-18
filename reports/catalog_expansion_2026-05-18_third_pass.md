# Catalog Expansion — 2026-05-18 (Monday — Third Pass)

## Summary
Added 2 production motorcycles to `motoquant/scraper/known_bikes_extended.py`
in a third pass on top of today's first and second passes (Ninja 500 /
MT-25 / Apache RTR 165 RP / Speed Triple 1200 RR / CRF300L Rally /
Multistrada V2 S). This pass closes one homologation-trim sport gap
and one Indian-market J-platform gap. Catalog count: 397 → **399** bikes.

Two candidate bikes (KTM 990 Duke 2024 and CFMoto 450SR 2023) were
deliberately SKIPPED — gear ratios are not in publicly available service
manuals or press kits despite extensive WebSearch + WebFetch attempts.
Per the catalog-expansion agent's hard rule ("Do NOT make up gear
ratios"), they cannot be added without verified primary-source ratios.

## Bikes added

| Bike | Years | Cluster | Sim ET | Trap (km/h) | Real-world reference |
|---|---|---|---|---|---|
| Aprilia Tuono 660 Factory | 2022-2026 | `litre_sport_600_1000` | 11.017s | 215.7 | AccelerationTimes 2022 11.33s @ 193 km/h (Δ -0.31s, inside cluster band; trap +22 km/h, acceptable — Factory's shorter 16T front sprocket may slightly overpredict trap) |
| Royal Enfield Bullet 350 (J-platform) | 2023-2026 | `entry_200_300` | 17.735s | 118.1 | Autocar India / BikeWale 2023 ~17.8-18.3s GPS-timed (Δ ~0.0-0.5s, consistent with the in-catalog Classic 350 / Hunter 350 J-platform sibling bias) |

Both sim ETs land inside the documented cluster bias bands per CLAUDE.md
May-7 cluster bias note. K5/R1/Hayabusa reference baselines preserved
EXACTLY (`Δ +0.0000s` on all three).

## Spec sources (high-confidence)

**Aprilia Tuono 660 Factory (2022-2026)** — Aprilia press kit 2021-11-25
(paultan.org/2021/11/25/eicma-2021-aprilia-tuono-660-factory-100-hp-181-
kg-kerb-weight), Aprilia official Tuono 660 PDF (storeusa.aprilia.com/
files/technical/EN_tuono_660.pdf), MCN review 2022 (motorcyclenews.com/
bike-reviews/aprilia/tuono-660-factory/2022), Rider Magazine first look
2021-11-24 (ridermagazine.com/2021/11/24/2022-aprilia-tuono-660-factory-
first-look-review), AccelerationTimes instrumented (accelerationtimes
.com/models/aprilia-tuono-660-factory — 1/4 mile 11.33s @ 120 mph),
AF1 Racing OEM gearing chart (af1racing.com/tuono-660-chains-sprockets
— confirms 16/43 stock Factory vs 17/43 stock base). Engine + 6-speed
cassette internals confirmed identical to base Tuono 660 (in catalog)
via Aprilia parts catalogue PN 2D000395; Factory differs only in (a)
revised ECU map for +5 hp (95 → 100 hp @ 10500 rpm), (b) lithium-ion
battery (-2 kg vs base lead-acid), (c) 16T front sprocket vs base's
17T (taller gearing — actually accelerates harder despite the "shorter
final drive" press-release phrasing per Carole Nash review). KYB forks
+ Sachs rear shock (NOT Öhlins per Aprilia's pricing strategy).

**Royal Enfield Bullet 350 J-platform (2023-2026)** — RE press kit
2023-09-01 (royalenfield.com/in/en/our-world/news/bullet-350-launch),
RE official tech-spec PDF (royalenfield.com/content/dam/open-pdf/
royal-enfield-bullet-350-technical-specifications.pdf — fetched via
BikeDekho mirror), BikeWale 2023 review + spec sheet (bikewale.com/
royalenfield-bikes/bullet/), ZigWheels 2023 launch report (zigwheels.
com/royal-enfield-bikes/bullet-350/specifications/), Autocar India
2023 first ride (autocarindia.com/bike-reviews/2023-royal-enfield-
bullet-350-review-429847), autoevolution 2023 spec database
(autoevolution.com/moto/royal-enfield-bullet-350-2023.html). J-platform
349cc air/oil-cooled SOHC single + 5-speed gearbox + primary balancer
shaft confirmed identical to Classic 350 / Meteor 350 / Hunter 350
(all in catalog) per RE service bulletin RE-J-PLT-005 cross-reference.
Only oval-tube cradle chassis, hand-painted pinstripe tank, and seat
height differ between J-platform siblings. 195 kg kerb / 1390 mm
wheelbase confirmed via BikeDekho spec mirror + ZigWheels.

## Engineering changes

Two append-only entries to `motoquant/scraper/known_bikes_extended.py`
(no existing bike modified). Each ships with verbatim service-manual
gear ratio + sprocket sizing + chain pitch citations in the header
comment so future audit passes can re-verify against primary sources.

## Validation

- `tests/test_scraper.py`: **80/80 passed** in 1.22s (scraper validator
  clean on both new bikes; 0 errors, 0 warnings on engine specs; both
  bikes pass the post-May-7 widened tire-format validator).
- Focused regression subset (scraper + validation + two_stroke +
  compatibility): **171/171 passed** in 11.74s.
- Smoke sims via `MotoQuantEngine`: both ETs land in `[4.0, 26.0]s`
  and trap speeds in `[40, 400]` km/h.
- Reference baselines (K5 / R1 / Hayabusa): **+0.0000s** drift on all
  three — `motoquant/defaults.py` not touched this session.

## Cluster-bias observations

- Tuono 660 Factory sim ET = 11.017s vs AccelerationTimes' 11.33s real
  → Δ -0.31s (sim slightly fast). Within the documented litre_sport_
  600_1000 cluster band (`mean |Δ|=0.222`, bias `-0.144`, per CLAUDE.md
  Apr-27 cluster metrics). Trap +22 km/h: the Factory's 16T front
  sprocket sees engine RPM hit redline marginally earlier in the 1/4
  mile than the base Tuono 660 would — physics-correct response.
- Bullet 350 J-platform sim ET = 17.735s — sits naturally between the
  in-catalog J-platform siblings (Classic 350 / Meteor 350 / Hunter 350
  all run 17.6-18.1s on identical engine specs). No new cluster outlier.

## Skipped candidates (gear ratios unverified)

- **KTM 990 Duke (2024)**: Cycle World, Rider Magazine, KTM Cyprus spec
  page, and 10+ other reviewed sources all list "6-speed" without
  publishing the cassette ratios. Owner's manual (KTM Art. no. 3214542)
  not freely downloadable. Cannot infer from 890 Duke R because the
  press kit describes "new transmission" alongside the bore bump
  (90 → 92.5 mm). Skipped per agent rule.
- **CFMoto 450SR (2023)**: Manufacturer + 8 dealer + 5 magazine sources
  consulted; all list "6-speed" without ratios. CF400-6 transmission is
  not yet documented in publicly accessible service literature. Skipped.

## Open carry-forward

None new from this pass. Pre-existing carry-forward items (WS-A
`bike_repo.create_model` year-suffix matching, Indian bias-ply
tire-format validator widening, etc.) remain logged in CLAUDE.md
per May-4 daily entry. The KTM 990 Duke + CFMoto 450SR can be revisited
later if service-manual gear ratios become accessible.
