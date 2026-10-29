"""2026-10 epoch retune, ROUND 1 — reports/acc_epoch_2026_10_24.json is kept as
the historical record of the REJECTED round-1 retune.

Round 1's knobs were superseded by round 2 (scripts/tune_epoch2_2026_10_29.py,
reports/acc_epoch2_2026_10_29.json; tests/test_epoch2_tune_report.py pins
THAT report to the shipped code). What stays pinned here:

* the round-1 report keeps its headline shape and its old-vs-new chain from
  the published 2026-08-08 headline;
* the round-2 report carries round 1 as a measured stage (the verifier's
  apples-to-apples figure on the published metric), so the rejection is
  traceable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


REPORT = ROOT / "reports" / "acc_epoch_2026_10_24.json"


@pytest.fixture(scope="module")
def report():
    return json.loads(REPORT.read_text())


def test_report_shape(report):
    for key in ("references", "n_bikes_swept", "clusters", "overall"):
        assert key in report  # acc_final_2026_08_08.json headline shape
    for key in (
        "trap_overall",
        "topspeed",
        "by_rules",
        "old_vs_new",
        "decomposition",
        "tuning",
        "reference_fit",
        "lambda_sensitivity",
    ):
        assert key in report, key
    assert set(report["by_rules"]) == {"epoch", "legacy"}
    assert report["rules"] == "epoch"
    assert report["overall"] == report["by_rules"]["epoch"]["overall"]
    # the old-vs-new chain starts at the published 2026-08-08 headline
    head = report["old_vs_new"]["head"]["legacy_rules"]["overall"]
    assert (head["n"], head["w_mean_abs"], head["w_bias"]) == (276, 0.2629, 0.0073)


def test_round2_report_supersedes_round1(report):
    r2 = json.loads((ROOT / "reports" / "acc_epoch2_2026_10_29.json").read_text())
    r1 = r2["old_vs_new"]["r1_tuned"]
    # the round-1 references re-measured in round 2 are round 1's own pins
    assert r1["references"] == report["references"]
    # the published-metric (HEAD labels, legacy rules) figure of round 1
    c = r1["headline"]["c_legacy_head_row"]["overall"]
    assert c["n"] == 276 and c["w_mean_abs"] > 0.2629
