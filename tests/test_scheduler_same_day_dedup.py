"""Regression tests for scripts/master_scheduler.sh same-day dedup.

Resolves INBOX:2026-05-24 — scheduler must not re-pick agents that
already produced a report today. Filesystem evidence (reports/PREFIX_TODAY*.md)
is authoritative because postflight only stamps STATUS.md._updated, not
per-agent timestamps.

The morning of 2026-05-24 had 3 sessions fire within 4 hours of each other
(06:42 / 08:31 / 10:30 UTC) and the scheduler re-picked the same 3 agents
each time because freshness rounds to whole days.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "master_scheduler.sh"
AGENTS_DIR = REPO_ROOT / "scripts" / "agents"
WEIGHTS = REPO_ROOT / "scripts" / "scheduler_weights.json"


def _fake_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    """Materialise a minimal repo skeleton in tmp_path."""
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "agents").mkdir()
    (tmp_path / "reports").mkdir()
    (tmp_path / "data").mkdir()

    shutil.copy(SCRIPT, tmp_path / "scripts" / "master_scheduler.sh")
    shutil.copy(WEIGHTS, tmp_path / "scripts" / "scheduler_weights.json")
    # agent prompts only need to exist for the scheduler to compose its plan
    for f in AGENTS_DIR.glob("*.md"):
        shutil.copy(f, tmp_path / "scripts" / "agents" / f.name)

    # Minimal STATUS.md with valid LAST_RUN_JSON
    (tmp_path / "STATUS.md").write_text(
        '<!-- LAST_RUN_JSON\n'
        '{\n'
        '  "_schema": 1,\n'
        '  "_updated": null,\n'
        '  "self-review":            { "date": null, "outcome": "never_run" },\n'
        '  "performance-monitor":    { "date": null, "outcome": "never_run" },\n'
        '  "claude-feature-monitor": { "date": null, "outcome": "never_run" },\n'
        '  "physics-calibration":    { "date": null, "outcome": "never_run" },\n'
        '  "catalog-expansion":      { "date": null, "outcome": "never_run" },\n'
        '  "benchmark-import":       { "date": null, "outcome": "never_run" },\n'
        '  "marketing-content":      { "date": null, "outcome": "never_run" }\n'
        '}\n'
        '-->\n'
    )
    (tmp_path / "DISPATCH_INBOX.md").write_text("# Dispatch Inbox\n\n## INSTRUCTIONS QUEUE\n")
    return tmp_path


def _run_scheduler(repo: pathlib.Path) -> str:
    env = os.environ.copy()
    env["MQ_REPO"] = str(repo)
    # Bypass pause flag location
    env["MOTOQUANT_SECRETS_DIR"] = str(repo / ".secrets")
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "master_scheduler.sh")],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"scheduler failed: {result.stderr}"
    return result.stdout


def test_no_reports_today_picks_normal_agents(tmp_path):
    """Clean repo with no reports/ files: scheduler picks per default weights."""
    repo = _fake_repo(tmp_path)
    out = _run_scheduler(repo)
    assert "### Today's selected agents" in out
    # No skipped block when nothing was skipped
    assert "### Skipped (already ran today)" not in out


def test_report_today_skips_agent(tmp_path):
    """If reports/self_review_TODAY.md exists, self-review must NOT be picked."""
    import datetime

    repo = _fake_repo(tmp_path)
    today = datetime.date.today().isoformat()
    (repo / "reports" / f"self_review_{today}.md").write_text("# fake\n")

    out = _run_scheduler(repo)
    assert "### Skipped (already ran today)" in out
    assert "**self-review**" in out.split("### Skipped")[1]
    # Self-review must NOT appear in the selected block
    selected_block = out.split("### Today's selected agents")[1].split("###")[0]
    assert "Agent 1: self-review" not in selected_block
    assert "Agent 2: self-review" not in selected_block
    assert "Agent 3: self-review" not in selected_block


def test_alias_prefix_skips_performance_monitor(tmp_path):
    """performance-monitor maps to reports/perf_monitor_TODAY*.md prefix."""
    import datetime

    repo = _fake_repo(tmp_path)
    today = datetime.date.today().isoformat()
    (repo / "reports" / f"perf_monitor_{today}.md").write_text("# fake\n")

    out = _run_scheduler(repo)
    assert "**performance-monitor**" in out.split("### Skipped")[1]


def test_failed_run_today_still_picked(tmp_path):
    """If today's run failed, the agent is allowed to retry (no skip)."""
    import datetime

    repo = _fake_repo(tmp_path)
    today = datetime.date.today().isoformat()
    (repo / "reports" / f"self_review_{today}.md").write_text("# fake\n")

    # Override outcome to "fail" in STATUS.md
    status = (repo / "STATUS.md").read_text()
    status = status.replace(
        '"self-review":            { "date": null, "outcome": "never_run" }',
        f'"self-review":            {{ "date": "{today}", "outcome": "fail" }}',
    )
    (repo / "STATUS.md").write_text(status)

    out = _run_scheduler(repo)
    # self-review should NOT be in the skipped block (fail bypasses the gate)
    if "### Skipped" in out:
        skipped_block = out.split("### Skipped")[1]
        assert "**self-review**" not in skipped_block


def test_multiple_skips_all_surface(tmp_path):
    """Multiple agents with today's reports all appear in skipped block."""
    import datetime

    repo = _fake_repo(tmp_path)
    today = datetime.date.today().isoformat()
    (repo / "reports" / f"self_review_{today}.md").write_text("x")
    (repo / "reports" / f"perf_monitor_{today}.md").write_text("x")
    (repo / "reports" / f"claude_feature_scan_{today}.md").write_text("x")

    out = _run_scheduler(repo)
    skipped = out.split("### Skipped")[1]
    assert "**self-review**" in skipped
    assert "**performance-monitor**" in skipped
    assert "**claude-feature-monitor**" in skipped


def test_dry_run_includes_skip_flag(tmp_path):
    """--dry-run emits the raw JSON scoring block with same_day_skip flags."""
    import datetime

    repo = _fake_repo(tmp_path)
    today = datetime.date.today().isoformat()
    (repo / "reports" / f"self_review_{today}.md").write_text("x")

    env = os.environ.copy()
    env["MQ_REPO"] = str(repo)
    env["MOTOQUANT_SECRETS_DIR"] = str(repo / ".secrets")
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "master_scheduler.sh"), "--dry-run"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    sr = next(s for s in data["all_scored"] if s["agent"] == "self-review")
    assert sr["same_day_skip"] is True
    assert sr["same_day_evidence"] == f"reports/self_review_{today}.md"
    assert any(s["agent"] == "self-review" for s in data["skipped_same_day"])
