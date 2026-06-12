# Phantom Bikes — Railway DB vs known_bikes.py Source Diff

**Date:** 2026-04-28  
**Discovery:** Diff of live `web-production-de6eb.up.railway.app/api/bikes`
(327 bikes) vs `motoquant/scraper/known_bikes.py::ALL_KNOWN_BIKES` (287 bikes).  
**Per CLAUDE.md history:** "37 missing bikes were claimed by a previous WS-A
sub-agent but never landed on disk" — same root cause.

## What Happened

A previous Cowork session (likely the Apr 27 mega-session @ d13669b)
inserted ~40 bikes directly into `motoquant.db`, then pushed the DB binary
to origin/main (which Railway auto-deploys). The corresponding
`known_bikes.py` source updates were never committed.

Result: Railway's deployed DB has 327 bikes. Any rebuild from source
(`db reset && db init && import --known-bikes`) only produces 290 bikes
(287 ALL_KNOWN_BIKES + 3 reference K5/R1/Hayabusa from `defaults.py`).

## Phantom Bike List — present on Railway, missing from source

These 40 entries exist in production DB but have no source-of-truth Python
spec, no gear ratios, no sprocket data, no dimensions. They are NOT
simulatable — calling `/api/simulate?bike_id=N` for any of these returns
HTTP 500 because `bike_configs` was never seeded for them.

Reference bikes (already in `defaults.py`, just labeled differently on Railway):
  - Suzuki GSX-R 1000 K5/K6 (2005)
  - Suzuki Hayabusa GSX1300R Gen1 (1999)
  - Yamaha YZF-R1 4C8 (2007)

Genuinely missing from source (need full spec to recover):
  - Aprilia RS 660 Factory (2025)
  - BMW G 310 RR (2024), M 1000 RR (2025)
  - Bajaj Pulsar N160 (2023), Pulsar P150 (2023)
  - Bimota Tesi 1D (1991)
  - Ducati Panigale V4 (2025), Streetfighter V4S (2024)
  - Hero Karizma XMR 250 (2024)
  - Honda CBR1000RR-R Fireblade SP (2024), CBR900RR Fireblade (1992),
    CBR900RR (1998), Hornet 2.0 (2024), RC30 VFR750R (1988), SP 160 (2024)
  - Husqvarna Norden 901 Expedition (2025)
  - Indian Motorcycle Pursuit Dark Horse (2024)
  - KTM 390 Adventure SW (2024), 990 RC R (2025)
  - Kawasaki Z H2 SE (2024), ZX-6R (2024), ZX-9R Ninja (1994)
  - MV Agusta Superveloce 1000 Serie Oro (2025)
  - Royal Enfield Bear 650 (2024), Classic 350 Halcyon (2024),
    Goan Classic 350 (2024)
  - Suzuki GSX-R 750 (1985), Hayabusa 25th Anniversary (2024),
    V-Strom SX 250 (2022)
  - TVS Apache RTR 310 (2024), Raider 125 (2022)
  - Triumph Daytona 660 (2024), Daytona 955i (2002)
  - Yamaha FZR1000 EXUP (1989), FZS 25 (2023), SR400 (2014), YZF-R9 (2025)

## Recommendation

These 37 phantoms should be either:

**(A) Properly recovered** — for each model, source full spec from manufacturer
service manual / wikipedia / Indian Autos Mag, write a `BikeSpec` block in
`known_bikes.py`, and append to `ALL_KNOWN_BIKES`. ~3-4 hours of work.

**(B) Accepted as deleted** — let `db reset && db init && import --known-bikes`
produce 290 bikes, redeploy, accept that Railway's catalog will shrink
from 327 → 290 once `motoquant.db` is regenerated on a future deploy.

The current chat-frontend merge takes path (B) implicitly — the rebuilt
`motoquant.db` (290 bikes) is what ships to Railway when this branch goes live.

## What Tonight's Merge Does

- Ships `/api/chat` endpoint + `/api/specs/correct` endpoint to Railway
- Ships ChatBox.tsx to motoquant.in/ + /simulator
- Ships next.config.js rewrite (motoquant.in/api/* → Railway)
- Ships rebuilt motoquant.db (290 bikes / 465 parts / 159 tires / 563 fitments)

The frontend stats strings (web/components/SimulatorWidget.js, web/app/*.js)
are already aligned to 290/465/159 by the audit-pass mega-patch.

## Reference Baselines Preserved

Even after the catalog regression: K5 = 10.0334s, R1 = 10.2859s,
Hayabusa = 10.4712s. The reference bikes come from `defaults.py`, not
`ALL_KNOWN_BIKES`, so they're unaffected.
