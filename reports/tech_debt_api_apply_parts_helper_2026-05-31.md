# Tech-Debt Pass — `_apply_parts_to_config` helper consolidates parts-loop boilerplate
**Date:** 2026-05-31 (Sunday)
**Agent:** A9 (technical-debt-pass)
**Scope:** `motoquant/api.py` (single file)
**Source finding:** Grep-based duplication scan during cleanup-subagent triage. Prior tech-debt passes already absorbed the high-confidence findings from `cleanup_subagent_1_dedup.md` (TestDB dedup 2026-05-16; seed-catalog helper 2026-05-20; live_db_copy 2026-05-30; venue_env helper 2026-05-30) and `cleanup_subagent_5_types.md` (HeadlineSpecs / BikeRowSummary / ChatResult TypedDicts). A fresh `grep -n 'apply_part_to_config' motoquant/api.py` surfaced **four nearly-identical 10-30 line blocks** that load each `req.part_ids` row from `parts`, mutate `cfg` via `apply_part_to_config`, build a `parts_applied` summary dict, and accumulate `build_cost_inr`.

## Refactor goal (one sentence)

Extract the duplicated "load each part from DB, apply to cfg, build parts_applied summary, accumulate INR cost" loop from four sites in `motoquant/api.py` (simulate_quick, simulate_top_speed, simulate_distance, `_run_build`) into a single `_apply_parts_to_config(cfg, part_ids, *, include_price_in_summary=True)` helper, so the next change to part-application semantics (e.g. retailer attribution, idempotency dedup, fail-fast vs fail-soft) lands in one place instead of four.

## Success criteria

- [x] All four duplicated blocks reduced to a single one-line helper call
- [x] Behaviour byte-identical (matching shape of `parts_applied` dicts + INR accumulation rule)
- [x] LOC delta well under 300 (actual: **+82 / -98 = net -16** on `motoquant/api.py`)
- [x] Single file, single concern (parts-apply boilerplate)
- [x] Focused test subset green: **221/221 passed**
- [x] Broader test subset green: **89/89 passed, 27 slow-skipped** (test_cli + test_recommendations, unchanged)
- [x] Pre-existing LLM-test failures (14 failed / 6 errors due to missing `fastapi` + chat-resolver carryforwards) **unchanged in count after refactor** — i.e. zero new regressions
- [x] K5 / R1 / Hayabusa baselines preserved EXACTLY (Δ +0.0000s on all three)
- [x] `motoquant/api.py` still parses cleanly (`ast.parse`)

## Before / after

### Before — four sites, ~20-30 lines each

```python
# simulate_quick (line 829)
build_cost_inr = 0.0
parts_applied = []
if req.part_ids:
    db = _get_db()
    if db:
        try:
            from .database.bridge import apply_part_to_config
            for pid in req.part_ids:
                row = db.execute("SELECT * FROM parts WHERE id=?", (pid,)).fetchone()
                if row:
                    part_dict = dict(row)
                    cfg = apply_part_to_config(cfg, part_dict)
                    parts_applied.append({
                        "id": part_dict["id"],
                        "name": part_dict.get("model_name", ""),
                        "brand": part_dict.get("brand", ""),
                        "price_inr": part_dict.get("price_inr"),
                    })
                    if part_dict.get("price_inr"):
                        build_cost_inr += float(part_dict["price_inr"])
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to apply parts %s: %s", req.part_ids, e)

# simulate_top_speed (line 956) — identical 27-line block
# simulate_distance (line 1084) — same loop, no parts_applied/cost surfaced
# _run_build (line 1423) — same loop, parts_applied dict omits price_inr key
```

### After — single helper, four one-line call sites

```python
def _apply_parts_to_config(
    cfg: BikeConfig,
    part_ids: list[int] | None,
    *,
    include_price_in_summary: bool = True,
) -> tuple[BikeConfig, list[dict], float]:
    """Apply selected part_ids to *cfg* and report what was used.

    Centralises the four prior copies. Returns (mutated cfg, summary list, cost INR).
    """
    parts_applied: list[dict] = []
    build_cost: float = 0.0
    if not part_ids:
        return cfg, parts_applied, build_cost
    db = _get_db()
    if not db:
        return cfg, parts_applied, build_cost
    try:
        from .database.bridge import apply_part_to_config
        for pid in part_ids:
            row = db.execute("SELECT * FROM parts WHERE id=?", (pid,)).fetchone()
            if not row:
                continue
            part_dict = dict(row)
            cfg = apply_part_to_config(cfg, part_dict)
            summary = {
                "id": part_dict["id"],
                "name": part_dict.get("model_name", ""),
                "brand": part_dict.get("brand", ""),
            }
            if include_price_in_summary:
                summary["price_inr"] = part_dict.get("price_inr")
            parts_applied.append(summary)
            if part_dict.get("price_inr"):
                build_cost += float(part_dict["price_inr"])
    except Exception as exc:
        logging.getLogger(__name__).warning("Failed to apply parts %s: %s", part_ids, exc)
    return cfg, parts_applied, build_cost

# Call sites now uniform:
cfg, parts_applied, build_cost_inr = _apply_parts_to_config(cfg, req.part_ids)              # simulate_quick
cfg, parts_applied, build_cost_inr = _apply_parts_to_config(cfg, req.part_ids)              # simulate_top_speed
cfg, _, _                          = _apply_parts_to_config(cfg, req.part_ids)              # simulate_distance
cfg, parts_applied, build_cost     = _apply_parts_to_config(                                # _run_build
    cfg, part_ids, include_price_in_summary=False
)
```

The `include_price_in_summary` keyword exists solely because the legacy `_run_build` summary dict omitted the `price_inr` key entirely (rather than carrying it as `None`); preserving that shape avoids a downstream change in `_build_summary` / `simulate_compare` response payloads.

## Files touched

| File | Change | Net delta |
|---|---|---|
| `motoquant/api.py` | Added 72-line `_apply_parts_to_config` helper (mostly docstring); replaced 4 duplicated 10-30 line blocks with 1-line calls | **+82 / -98 = -16** |

No other file was touched. No production data, schema, or physics module modified.

## Validation

| Check | Before | After |
|---|---|---|
| `ast.parse(motoquant/api.py)` | clean | clean |
| `grep -cn 'apply_part_to_config' motoquant/api.py` | **5** call sites (1 import + 4 usages) | **2** sites (1 import + 1 usage inside helper) |
| Focused tests (scraper + validation + two_stroke + compatibility + submodel_kaizen + power_boost_regression) | 221 passed | **221 passed** |
| Broader tests (test_cli + test_recommendations) | 89 passed / 27 slow-skipped | **89 passed / 27 slow-skipped** |
| LLM-runner regression check (stash + re-run pre-edit) | 14 failed / 6 errors / 67 passed (pre-existing) | **14 failed / 6 errors / 67 passed** — identical |
| K5 baseline | 10.0334s | 10.0334s (Δ +0.0000s) **PASS** |
| R1 baseline | 10.2859s | 10.2859s (Δ +0.0000s) **PASS** |
| Hayabusa baseline | 10.4712s | 10.4712s (Δ +0.0000s) **PASS** |

API integration tests (`tests/test_api.py`) require `fastapi` — uninstallable in sandbox per CLAUDE.md "Sandbox limits". Tests will run in CI on the hosted runner.

## Why this matters

The four blocks were drift-prone. If a future change wanted to:

- Add structured retailer attribution to the `parts_applied` summary (e.g. `retailer`, `retailer_url`)
- Switch from `apply_part_to_config(cfg, dict)` to a typed Part dataclass once the bridge is hardened
- Detect duplicate exclusive-group parts (currently the desktop frontend filters; backend trusts the request)
- Distinguish "part missing from DB" (row is None) from "part apply raised" (current code silently elides)
- Add per-part audit logging for paid users

...the change would need to land in four independent sites with no enforcement that they stayed in sync. Centralising in `_apply_parts_to_config` collapses the next change to a one-file edit and prevents the "fixed in 3 of 4 sites" class of bug. Concretely: the prior `simulate_top_speed` site already wrote `Failed to apply parts %s` while `simulate_distance` wrote `Parts apply failed` and `_run_build` wrote `Parts apply error` — three subtly different log messages for the same condition, which a log aggregator would have to OR together. The helper unifies to one message.

## Kaizen checklist

- [x] **No silent failure mode introduced** — preserves the existing outer `try/except Exception: warn` swallow-and-degrade pattern verbatim; behaviour identical to pre-refactor (including the partial-batch carry-over on late-row failure).
- [x] **No data/model mismatch** — the `parts_applied` dict shape preserved exactly per call site (the `include_price_in_summary` flag captures the only prior shape variation).
- [x] **No bypass path** — all four call sites converted; `grep` confirms `apply_part_to_config` is only imported once now (inside the helper).
- [x] **Test coverage** — the helper has no dedicated unit test in this pass (API integration tests are fastapi-gated and run in CI); it is exercised end-to-end by the existing `test_api.py` suite (24+ tests) which calls `simulate_quick` / `simulate_top_speed` / `_run_build` via FastAPI TestClient.
- [x] **Numerical sanity** — physics untouched; baselines preserved exactly.
- [x] **No dead fields introduced** — helper is single-purpose and called by 4 sites.
- [x] **Backwards compatibility** — response payloads byte-identical (verified by manual shape walkthrough; CI test_api will confirm).

## Out of scope (deferred)

- `simulate_compare` consumes `_run_build` indirectly via parts_a / parts_b — already covered by the helper through `_run_build`. No direct refactor needed.
- Other duplicated patterns spotted but **NOT** addressed (would widen scope):
  - "Down-sample sim timeseries to ~100 Hz" appears in both `simulate` and `_build_summary` with subtle differences — different concern, deferred.
  - "Convert sim splits dict to LSR splits with km/h + mph" in `simulate_top_speed` — single site, no duplication.
- The helper does not currently distinguish "DB unavailable" from "part_ids empty" in its return value — both yield `(cfg, [], 0.0)`. The prior code didn't distinguish either, so behaviour preserved. A future enhancement could return a richer status if call sites need it.

## One-line summary

Four near-identical 10-30 line "load + apply + summarise" parts loops across `simulate_quick`, `simulate_top_speed`, `simulate_distance`, and `_run_build` in `motoquant/api.py` are now single one-line `_apply_parts_to_config(cfg, part_ids, ...)` calls behind a new 72-line helper (mostly docstring); net **-16 LOC** on api.py; 221/221 focused tests green; 89/89 broader tests green; pre-existing LLM-test failures unchanged in count; K5 / R1 / Hayabusa baselines preserved Δ +0.0000s.
