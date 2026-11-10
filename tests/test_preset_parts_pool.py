"""Optimizer/outlaw preset requests filter parts by the preset's catalog row.

Before: a ``bike_preset`` request passed ``bike_model_id=None`` to the parts
search, so the candidate pool was not compatibility-filtered for the bike.
"""

import sqlite3

import pytest

from motoquant import api

DB = "motoquant.db"


@pytest.fixture(scope="module")
def conn():
    c = sqlite3.connect(DB)
    yield c
    c.close()


def _id_for(conn, name):
    return conn.execute(
        "SELECT id FROM bike_models WHERE model_name = ? ORDER BY id LIMIT 1", (name,)
    ).fetchone()[0]


def test_explicit_bike_id_wins(conn):
    assert api._parts_model_id(conn, 42, "hayabusa_gen1") == 42


@pytest.mark.parametrize("preset", sorted(api._PRESET_MODEL_NAMES))
def test_presets_resolve_to_their_catalog_rows(conn, preset):
    expected = _id_for(conn, api._PRESET_MODEL_NAMES[preset])
    assert api._parts_model_id(conn, None, preset) == expected


def test_no_bike_defaults_to_the_k5_row(conn):
    # _build_config falls back to the K5 when nothing is specified, so the
    # parts pool must follow the same bike.
    expected = _id_for(conn, api._PRESET_MODEL_NAMES["gsxr1000_k5"])
    assert api._parts_model_id(conn, None, None) == expected


def test_unknown_preset_gives_no_filter(conn):
    assert api._parts_model_id(conn, None, "not_a_preset") is None
