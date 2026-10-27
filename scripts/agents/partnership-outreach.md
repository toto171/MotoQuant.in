# Agent A12: partnership-outreach

Read AGENTS.md, docs/adr/0006-open-source-pivot.md and docs/ROADMAP.md ("Community data").

MotoQuant is **free and open source (Apache-2.0)**. There is nothing to sell: no
licences, seats or paid tiers. Outreach is about **data partnerships** that make
the simulator more accurate for everyone.

## Goal

Draft 3-5 outreach email templates targeted at Indian motorcycle tuning shops, dyno owners and drag-strip operators, asking for **instrumented data** (Dragy/VBOX/Racelogic runs, timeslips with conditions, dyno sheets) and offering the free tool in return. The maintainer sends them manually (we never auto-send).

## Today's target list priority

1. **Pune / Narhe drag shops** — closest to user's network, most aligned target
2. **Bangalore / Hyderabad performance shops** — high-volume markets
3. **Dyno vendors / importers** (DynoJet India, Powertronic, Shree Engineering)
4. **Indian moto-press contacts** for product mentions
5. **Drag-strip operators** (Aamby Valley owners, MMRT scheduling)

## Workflow

1. Pick ONE target category. Research 5-10 named businesses (Google + JustDial + Maps).
2. For each: name, location, website, contact form URL or email if public, owner name if findable.
3. Write a custom outreach template per business (3-5 paragraph cold email):
   - Lead with ONE specific local insight ("noticed your shop does Pulsar NS200 builds — our simulator predicts those within ±0.4s")
   - Explain the ask: a handful of instrumented runs or dyno sheets for named bikes, credited by name on the validation page if they agree
   - Explain what they get: a free, open-source simulator their customers can use (build ROI in ₹, gearing what-ifs), plus better accuracy for the bikes they work on. Self-hosting is possible for shops that want their own instance
   - Soft CTA (no high-pressure ask): "would a 15-min demo be useful?"
   - Signature: real founder name, not "MotoQuant Team"

## Deliverable

- New file: `outreach/<region>/<business_slug>.md` (a fresh `outreach/` tree; the commercial-era drafts and their `CONTACTS.csv` are archived read-only under `docs/archive/outreach/` — reuse contact details from there, never the old pitch)
- Update: `outreach/CONTACTS.csv` with ALL targets (sent + drafted)
- Report: `reports/partnership_outreach_YYYY-MM-DD.md` listing what was drafted

## Don't

- Never auto-send. Always queue for user to review and personalise the final touches.
- Never claim features we don't have (no "ML magic" puffery).
- Never offer or imply anything paid (licences, seats, plans, "Pro"). It doesn't exist.
- Never ask for data without saying how it will be used and credited.
- Never use a generic template. Each email is custom for the recipient.
- Don't include the PAT or any credential in any draft (obvious but say it).

Cap ~700 words.
