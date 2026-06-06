"""Regression tests for scripts/stamp_status_timestamps.py.

Resolves INBOX:322 (self-review M1 Section B.2/B.3): postflight must
update STATUS.md._updated and last_run on every session, including
no-op sessions, so the GH-Actions heartbeat side-channel's staleness
check doesn't misfire.
"""

from __future__ import annotations

import importlib.util
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "stamp_status_timestamps.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "stamp_status_timestamps", SCRIPT_PATH
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


@pytest.fixture
def stamp_mod():
    return _load_module()


@pytest.fixture
def sample_status(tmp_path: pathlib.Path) -> pathlib.Path:
    p = tmp_path / "STATUS.md"
    p.write_text(
        "<!--_LAST_RUN_JSON\n"
        "{\n"
        '  "_schema": 1,\n'
        '  "_updated": null,\n'
        '  "catalog-expansion": { "date": null }\n'
        "}\n"
        "-->\n"
        "\n"
        "last_run: <!-- AUTO-UPDATED — used by catchup_detect to decide if we need recovery mode -->\n"
    )
    return p


def test_stamps_both_fields_when_null(stamp_mod, sample_status):
    rc = stamp_mod.main([str(sample_status), "--now", "2026-05-17T12:00:00Z"])
    assert rc == 0
    content = sample_status.read_text()
    assert '"_updated": "2026-05-17T12:00:00Z"' in content
    assert "last_run: 2026-05-17T12:00:00Z  <!--" in content


def test_overwrites_previous_timestamp(stamp_mod, tmp_path):
    p = tmp_path / "STATUS.md"
    p.write_text(
        '"_updated": "2026-05-16T09:00:00Z",\n'
        "last_run: 2026-05-16T09:00:00Z  <!-- AUTO-UPDATED -->\n"
    )
    rc = stamp_mod.main([str(p), "--now", "2026-05-17T12:00:00Z"])
    assert rc == 0
    content = p.read_text()
    assert '"_updated": "2026-05-17T12:00:00Z"' in content
    assert "last_run: 2026-05-17T12:00:00Z" in content
    assert "2026-05-16T09:00:00Z" not in content


def test_idempotent_with_same_now(stamp_mod, sample_status):
    stamp_mod.main([str(sample_status), "--now", "2026-05-17T12:00:00Z"])
    first = sample_status.read_text()
    rc = stamp_mod.main([str(sample_status), "--now", "2026-05-17T12:00:00Z"])
    assert rc == 0
    assert sample_status.read_text() == first


def test_missing_file_returns_nonzero(stamp_mod, tmp_path, capsys):
    rc = stamp_mod.main([str(tmp_path / "nope.md")])
    assert rc == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_malformed_status_returns_nonzero(stamp_mod, tmp_path, capsys):
    p = tmp_path / "STATUS.md"
    p.write_text("# No _updated, no last_run anywhere here\n")
    rc = stamp_mod.main([str(p)])
    assert rc == 1
    captured = capsys.readouterr()
    assert "malformed" in captured.err


def test_stamp_function_reports_changes(stamp_mod):
    src = '"_updated": null,\nlast_run: <!-- AUTO-UPDATED -->\n'
    new, updated_changed, last_run_changed = stamp_mod.stamp(
        src, "2026-05-17T00:00:00Z"
    )
    assert updated_changed is True
    assert last_run_changed is True
    assert '"_updated": "2026-05-17T00:00:00Z"' in new
    assert "last_run: 2026-05-17T00:00:00Z" in new


def test_real_status_md_smoke():
    """Run the stamp on a copy of the live STATUS.md (no write back).

    Catches the case where the live STATUS.md format drifts away from the
    script's regexes — the script would silently fail to stamp in production.
    """
    live = REPO_ROOT / "STATUS.md"
    if not live.exists():
        pytest.skip("no live STATUS.md to smoke-test against")
    mod = _load_module()
    new, did_updated, did_last_run = mod.stamp(live.read_text(), "2026-05-17T00:00:00Z")
    assert did_updated, "live STATUS.md missing _updated field — script needs update"
    assert did_last_run, "live STATUS.md missing last_run line — script needs update"
