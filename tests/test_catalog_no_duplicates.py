"""
MotoQuant — Catalog Duplicate / Regen-Determinism Guard
=======================================================
The 2026-07-25 weekly audit (reports/session_2026_07_25_weekly_audit.md
section 3.3) found that ``ALL_KNOWN_BIKES`` held 542 entries for 541 bikes.
Four were *exact-key* duplicates — same manufacturer, model and year range —
because ``known_bikes_extended`` re-declared bikes already present in the base
list with materially different mass, gearing and aero:

    ('royal enfield', 'hunter 350',  2022, 2026)
    ('yezdi',         'roadster',    2022, 2026)
    ('yezdi',         'adventure',   2022, 2026)
    ('kawasaki',      'versys 650',  2015, 2024)

That is not merely untidy. The two documented DB-regen steps resolved the
collision in OPPOSITE directions:

  * ``python -m motoquant.run import --known-bikes`` walks ALL_KNOWN_BIKES in
    order and upserts, so the LAST declaration wins;
  * ``scripts/reseed_configs_from_specs.py`` groups specs by
    (manufacturer, year-stripped model) and picks by year-range overlap, so on
    an exact tie the FIRST declaration wins.

A bike's stored physics therefore depended on which script ran last, flipping
catalog ET by up to 0.38 s with no code change. A second, wider class of the
same defect: entries for the same bike under *different* year keys carrying
physically impossible geometry disagreements (a Suzuki V-Strom SX 250 with two
different engines; Royal Enfield 650 twins with two different bore/stroke
pairs; a 194 cc Honda Hornet 2.0 that has never existed).

This module is the regression guard. It must FAIL if either class comes back:

  (a) no exact-key duplicates anywhere in ALL_KNOWN_BIKES;
  (b) no two entries sharing a manufacturer + year-stripped model name with
      OVERLAPPING year ranges may disagree by more than 5 % on displacement,
      bore or stroke. Legitimate generation splits are unaffected: they are
      either keyed under distinct model names (``GSX-R 1000 K5`` vs
      ``GSX-R 1000 K7``) or carry non-overlapping year ranges, and either way
      never reach this check;
  (c) the reseed winner is a pure function of ALL_KNOWN_BIKES — an exactly
      year-matched DB row always resolves to its own spec, never a sibling's.

All three drive the real production paths (the shipped ALL_KNOWN_BIKES list and
``reseed_configs_from_specs``'s own matcher), not a re-implementation.
"""

import importlib.util
import itertools
import os
import re
import sys
from collections import defaultdict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from motoquant.scraper.known_bikes import ALL_KNOWN_BIKES

# Fields whose disagreement between two overlapping entries means the catalog
# is describing two different engines for one motorcycle.
GEOMETRY_FIELDS = ("displacement_cc", "bore_mm", "stroke_mm")

# Tolerance for (b). Real sources round differently (184 vs 184.4 cc, 648 vs
# 649 cc), so a few tenths of a percent is noise; 5 % is far above any rounding
# spread and far below every defect the audit found (the smallest was 5.2 %,
# the largest 26.7 %).
GEOMETRY_TOLERANCE_PCT = 5.0

_YEAR_SUFFIX = re.compile(r"\s*\(\d{4}(?:-\d{4})?\)\s*$")

# The four exact-key duplicates removed on 2026-08-08. Named explicitly so the
# guard is legible and so a re-add of any one of them is reported by name.
DEDUPED_2026_08_08 = [
    ("Royal Enfield", "Hunter 350", 2022, 2026),
    ("Yezdi", "Roadster", 2022, 2026),
    ("Yezdi", "Adventure", 2022, 2026),
    ("Kawasaki", "Versys 650", 2015, 2024),
]


def _strip_year(name):
    return _YEAR_SUFFIX.sub("", name or "").strip()


def _exact_key(spec):
    return (
        spec.manufacturer.strip().lower(),
        spec.model_name.strip().lower(),
        spec.year_from,
        spec.year_to,
    )


def _family_key(spec):
    """(manufacturer, year-stripped model) — the exact key
    ``reseed_configs_from_specs`` groups specs by, so this test collides
    entries in precisely the cases that script has to disambiguate."""
    return (spec.manufacturer.strip().lower(), _strip_year(spec.model_name).lower())


def _years_overlap(a, b):
    a_to = a.year_to or a.year_from
    b_to = b.year_to or b.year_from
    if a.year_from is None or b.year_from is None:
        return False
    return min(a_to, b_to) >= max(a.year_from, b.year_from)


def _pct_diff(x, y):
    if x is None or y is None:
        return None
    x, y = float(x), float(y)
    if x == 0 or y == 0:
        return None
    return abs(x - y) / max(x, y) * 100.0


def _label(spec):
    return (
        f"{spec.manufacturer} {spec.model_name} "
        f"({spec.year_from}-{spec.year_to}, code={spec.model_code!r})"
    )


@pytest.fixture(scope="module")
def reseed_module():
    """Load scripts/reseed_configs_from_specs.py by path.

    ``scripts/`` is not a package, so this is the only way to exercise the
    real matcher rather than a copy of it. If the import ever breaks, that is
    itself worth failing on — the regen chain would be broken too.
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scripts",
        "reseed_configs_from_specs.py",
    )
    spec = importlib.util.spec_from_file_location("_mq_reseed_configs_from_specs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestNoExactDuplicates:
    """(a) Two entries on the same key make the DB-regen order load-bearing."""

    def test_no_exact_key_duplicates(self):
        seen = defaultdict(list)
        for spec in ALL_KNOWN_BIKES:
            seen[_exact_key(spec)].append(spec)

        dupes = {k: v for k, v in seen.items() if len(v) > 1}
        assert not dupes, (
            "ALL_KNOWN_BIKES contains exact-key duplicates. `import "
            "--known-bikes` keeps the LAST of each group while "
            "reseed_configs_from_specs.py keeps the FIRST, so the stored "
            "physics depends on which regen step ran last:\n"
            + "\n".join(
                f"  {key}\n" + "\n".join(f"      - {_label(s)}" for s in group)
                for key, group in sorted(dupes.items(), key=lambda kv: str(kv[0]))
            )
        )

    def test_entry_count_matches_unique_key_count(self):
        keys = {_exact_key(s) for s in ALL_KNOWN_BIKES}
        assert len(keys) == len(ALL_KNOWN_BIKES), (
            f"{len(ALL_KNOWN_BIKES)} entries collapse to {len(keys)} unique "
            "keys — every entry must be its own bike."
        )

    @pytest.mark.parametrize(
        "manufacturer,model_name,year_from,year_to", DEDUPED_2026_08_08
    )
    def test_previously_duplicated_bike_appears_once(
        self, manufacturer, model_name, year_from, year_to
    ):
        """Targeted pin on the four bikes de-duplicated on 2026-08-08."""
        key = (
            manufacturer.strip().lower(),
            model_name.strip().lower(),
            year_from,
            year_to,
        )
        matches = [s for s in ALL_KNOWN_BIKES if _exact_key(s) == key]
        assert len(matches) == 1, (
            f"{manufacturer} {model_name} ({year_from}-{year_to}) appears "
            f"{len(matches)} times; it was de-duplicated on 2026-08-08 and "
            "must stay a single canonical entry (see the tombstone comment in "
            "motoquant/scraper/known_bikes_extended.py)."
        )


class TestNoContradictoryGeometry:
    """(b) One motorcycle, one engine — whatever the year keys say."""

    def test_overlapping_entries_agree_on_engine_geometry(self):
        families = defaultdict(list)
        for spec in ALL_KNOWN_BIKES:
            families[_family_key(spec)].append(spec)

        problems = []
        for _key, group in sorted(families.items(), key=lambda kv: str(kv[0])):
            if len(group) < 2:
                continue
            for a, b in itertools.combinations(group, 2):
                if not _years_overlap(a, b):
                    # Non-overlapping year ranges = a legitimate generation
                    # split (different engines are expected and fine).
                    continue
                for field in GEOMETRY_FIELDS:
                    diff = _pct_diff(getattr(a, field, None), getattr(b, field, None))
                    if diff is not None and diff > GEOMETRY_TOLERANCE_PCT:
                        problems.append(
                            f"  {_label(a)}\n  vs {_label(b)}\n"
                            f"      {field}: {getattr(a, field)} vs "
                            f"{getattr(b, field)}  ({diff:.1f}% apart)"
                        )

        assert not problems, (
            "Entries for the same bike with OVERLAPPING year ranges disagree "
            f"by more than {GEOMETRY_TOLERANCE_PCT:.0f}% on engine geometry — "
            "the catalog is describing two different engines for one "
            "motorcycle, and which one a DB row gets depends on year-overlap "
            "tie-breaking:\n" + "\n".join(problems)
        )


class TestReseedWinnerIsDeterministic:
    """(c) The regen winner must follow from the data, not from run order."""

    def test_exact_year_row_resolves_to_its_own_spec(self, reseed_module):
        """Drive the real ``match_spec_to_row``.

        Every spec is turned into the ``bike_models`` row that
        ``import --known-bikes`` would have created for it, then fed back
        through the reseed matcher. Each row must resolve to the spec it came
        from. An exact-key duplicate makes this ambiguous, and a degraded
        tie-break makes a row adopt a sibling generation's physics — both show
        up here as a mismatch.
        """
        specs_by_key = defaultdict(list)
        for spec in ALL_KNOWN_BIKES:
            specs_by_key[_family_key(spec)].append(spec)

        mismatches = []
        for spec in ALL_KNOWN_BIKES:
            row = {
                "manufacturer": spec.manufacturer,
                "model_name": (
                    f"{_strip_year(spec.model_name)} ({spec.year_from}-{spec.year_to})"
                ),
                "year_from": spec.year_from,
                "year_to": spec.year_to,
            }
            winner = reseed_module.match_spec_to_row(row, specs_by_key)
            if winner is None:
                mismatches.append(f"  {_label(spec)} -> no spec matched")
            elif (winner.year_from, winner.year_to) != (spec.year_from, spec.year_to):
                mismatches.append(f"  {_label(spec)} -> resolved to {_label(winner)}")

        assert not mismatches, (
            "reseed_configs_from_specs.match_spec_to_row did not return a "
            "bike's own spec for an exactly year-matched row:\n" + "\n".join(mismatches)
        )

    def test_winner_is_stable_across_repeated_calls(self, reseed_module):
        """The same inputs must always give the same winner."""
        specs_by_key = defaultdict(list)
        for spec in ALL_KNOWN_BIKES:
            specs_by_key[_family_key(spec)].append(spec)

        rows = [
            {
                "manufacturer": s.manufacturer,
                "model_name": _strip_year(s.model_name),
                "year_from": s.year_from,
                "year_to": s.year_to,
            }
            for s in ALL_KNOWN_BIKES
        ]
        first = [id(reseed_module.match_spec_to_row(r, specs_by_key)) for r in rows]
        second = [id(reseed_module.match_spec_to_row(r, specs_by_key)) for r in rows]
        assert first == second

    def test_full_tie_resolves_to_earliest_declared_spec(self, reseed_module):
        """Pin the documented tie-break: earliest-declared spec wins.

        Two specs can tie on BOTH year-overlap and year_from distance (the two
        V-Strom SX 250 entries do, against the 2022-2024 row), and the winner
        decides which physics a bike_configs row gets.

        Honest scope note: this pins the BEHAVIOUR, not the implementation.
        ``_pick_generation`` now carries an explicit declaration-index key so
        the rule is stated rather than inherited from CPython's stable sort —
        but because the two are equivalent by construction, this test cannot
        distinguish them and will not fail if the explicit key is dropped. It
        WILL fail if the resolution order itself changes.
        """
        candidates = [
            s for s in ALL_KNOWN_BIKES if _family_key(s) == ("suzuki", "v-strom sx 250")
        ]
        assert len(candidates) == 2, (
            "This pin assumes the two overlapping V-Strom SX 250 entries; "
            f"found {len(candidates)}. Update the fixture if the catalog "
            "changed intentionally."
        )
        row = {"year_from": 2022, "year_to": 2024}
        # Both candidates overlap 2022-2024 by 3 years and share year_from,
        # so this exercises the tie-break and nothing else.
        assert reseed_module._pick_generation(candidates, row) is candidates[0]
        assert (
            reseed_module._pick_generation(list(reversed(candidates)), row)
            is candidates[1]
        )
