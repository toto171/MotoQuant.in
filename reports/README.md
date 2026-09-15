# reports/

Machine-readable sweep artefacts only:

- `acc_final_YYYY_MM_DD.json`, `acc_verify_*.json` — authoritative weighted
  benchmark sweeps (`scripts/phys_weighted_sweep.py`). The newest one is what
  the `/validation` page and `scripts/gen_accuracy_viz_data.py` read.
- `sweep_et_*.json`, `sweep_topspeed_*.json`, `validation_*.json` — raw
  per-bike sweep outputs.
- `scrape_2026_07_10/` — the July-2026 web-verification pass: 214 spec checks
  and 103 benchmark finds, each with a source URL. This is the only
  URL-backed provenance the catalog has (see `docs/DATA_PROVENANCE.md`).
- `test_count.txt` — the fast-tier test count read by `scripts/audit_headline_stats.py`.

The per-session prose write-ups that used to live here were removed from the
tree in the open-source release (2026-09-15); they remain in git history and
the milestone view is `CHANGELOG.md`.
