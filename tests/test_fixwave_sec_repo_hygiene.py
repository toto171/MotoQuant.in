"""Open-source readiness: repo-level security configuration.

These files ARE the production artifact (GitHub runs the workflows as
written), so the tests parse the real files and pin the properties that
make them safe for a public repository:

* deploy.yml had a pwn-request: deploy-production ran on ``workflow_run`` of
  CI / web-verify (which run on fork PRs), guarded only by
  ``head_branch == 'main'`` (a fork's branch named ``main`` passes), then
  checked out the untrusted ``head_sha`` and built it with VERCEL_TOKEN via
  an unpinned ``vercel@latest``.
* keepalive.yml pinged the hard-coded production URL from any copy of the
  repo.
* The secret scan missed several live-key formats; .gitignore missed common
  secret files; the pre-commit ruff pin was far outside requirements-dev.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    # PyYAML (YAML 1.1) reads the bare key `on` as boolean True.
    if True in data and "on" not in data:
        data["on"] = data.pop(True)
    return data


# ── deploy.yml ────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def deploy():
    return _load_yaml(WORKFLOWS / "deploy.yml")


def _norm(expr: str) -> str:
    return re.sub(r"\s+", " ", expr or "")


def test_production_deploy_requires_a_push_to_this_repo(deploy):
    cond = _norm(deploy["jobs"]["deploy-production"]["if"])
    assert "github.event.workflow_run.conclusion == 'success'" in cond
    assert "github.event.workflow_run.event == 'push'" in cond
    assert "github.event.workflow_run.head_branch == 'main'" in cond
    assert (
        "github.event.workflow_run.head_repository.full_name == github.repository"
        in cond
    )
    assert "||" not in cond, "an OR would let a fork run bypass the guard"


def test_preview_deploy_never_runs_for_fork_prs(deploy):
    cond = _norm(deploy["jobs"]["deploy-preview"]["if"])
    assert "github.event.pull_request.head.repo.full_name == github.repository" in cond


def test_permissions_are_least_privilege(deploy):
    assert deploy["permissions"] == {"contents": "read"}
    preview = deploy["jobs"]["deploy-preview"]["permissions"]
    assert preview == {"contents": "read", "pull-requests": "write"}


def test_token_is_scoped_to_vercel_steps_only(deploy):
    assert "VERCEL_TOKEN" not in deploy.get("env", {}), (
        "a workflow-level VERCEL_TOKEN reaches every step, incl. checkout"
    )
    for job in deploy["jobs"].values():
        assert "VERCEL_TOKEN" not in job.get("env", {})
        for step in job["steps"]:
            uses_token = "VERCEL_TOKEN" in str(step.get("run", ""))
            if uses_token:
                assert "VERCEL_TOKEN" in step.get("env", {}), step.get("name")
            if "actions/checkout" in str(step.get("uses", "")):
                assert "VERCEL_TOKEN" not in step.get("env", {})
                assert step.get("with", {}).get("persist-credentials") is False


def test_vercel_cli_is_pinned(deploy):
    text = (WORKFLOWS / "deploy.yml").read_text()
    assert "vercel@latest" not in text
    assert re.fullmatch(r"\d+\.\d+\.\d+", deploy["env"]["VERCEL_CLI_VERSION"])


def test_no_template_expansion_inside_scripts(deploy):
    """${{ }} inside run/script bodies is a code-injection vector; values
    must arrive through env instead."""
    for job in deploy["jobs"].values():
        for step in job["steps"]:
            body = str(step.get("run", "")) + str(
                step.get("with", {}).get("script", "")
            )
            assert "${{" not in body, step.get("name")


# ── keepalive.yml ─────────────────────────────────────────────────────────


def test_keepalive_is_opt_in_per_repository():
    wf = _load_yaml(WORKFLOWS / "keepalive.yml")
    job = wf["jobs"]["ping"]
    assert _norm(job["if"]) == "${{ vars.RENDER_API_URL != '' }}"
    text = (WORKFLOWS / "keepalive.yml").read_text()
    assert "|| 'https://" not in text, "no hard-coded fallback deployment URL"


# ── dependabot ────────────────────────────────────────────────────────────


def test_dependabot_covers_every_ecosystem_weekly():
    cfg = _load_yaml(ROOT / ".github" / "dependabot.yml")
    assert cfg["version"] == 2
    got = {(u["package-ecosystem"], u["directory"]) for u in cfg["updates"]}
    assert got == {
        ("pip", "/"),
        ("npm", "/web"),
        ("cargo", "/rust"),
        ("github-actions", "/"),
    }
    assert all(u["schedule"]["interval"] == "weekly" for u in cfg["updates"])
    for _eco, directory in got:
        assert (ROOT / directory.lstrip("/")).is_dir()


# ── pre-commit ruff pin ───────────────────────────────────────────────────


def _ver(s: str) -> tuple[int, ...]:
    return tuple(int(x) for x in s.split("."))


def test_precommit_ruff_rev_is_inside_requirements_dev_range():
    cfg = _load_yaml(ROOT / ".pre-commit-config.yaml")
    repo = next(r for r in cfg["repos"] if r["repo"].endswith("ruff-pre-commit"))
    rev = _ver(repo["rev"].lstrip("v"))
    req = (ROOT / "requirements-dev.txt").read_text()
    m = re.search(r"^ruff>=([\d.]+),<([\d.]+)", req, re.M)
    assert m, "requirements-dev.txt must pin a ruff range"
    lo, hi = _ver(m.group(1)), _ver(m.group(2))
    assert lo <= rev < hi, (repo["rev"], m.group(0))


# ── secret scan ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def health_check():
    spec = importlib.util.spec_from_file_location(
        "mq_health_check", ROOT / "scripts" / "health_check.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Sample tokens are assembled at runtime so this file never trips the scan.
_A = "a1B2c3D4e5F6g7H8i9J0" * 3
SAMPLES = {
    "stripe secret": "sk" + "_live_" + _A[:24],
    "stripe restricted": "rk" + "_live_" + _A[:24],
    "stripe webhook": "wh" + "sec_" + _A[:32],
    "razorpay": "rzp" + "_live_" + _A[:14],
    "resend": "re" + "_" + _A[:8] + "_" + _A[:24],
    "anthropic": "sk-" + "ant-api03-" + _A[:40],
    "openai project": "sk-" + "proj-" + _A[:48],
    "aws": "AK" + "IA" + "IOSFODNN7ABCDEFG",
    "posthog": "ph" + "c_" + _A[:40],
    "owm in url": "?q=Pune&app" + "id=" + "0123456789abcdef" * 2,
    "pkcs8 encrypted": "-----BEGIN " + "ENCRYPTED PRIVATE KEY-----",
    "pem rsa": "-----BEGIN " + "RSA PRIVATE KEY-----",
    "github oauth": "gh" + "o_" + _A[:36],
}


@pytest.mark.parametrize("name", sorted(SAMPLES))
def test_secret_patterns_catch_live_key_formats(health_check, name):
    pat = re.compile("|".join(health_check._SECRET_PATTERNS))
    assert pat.search(f"KEY = '{SAMPLES[name]}'"), name


@pytest.mark.parametrize(
    "benign",
    [
        "import re_compile_helper",
        "re_validation_message_for_the_user",
        "sk_test_" + _A[:24],  # Stripe TEST keys are not secrets
        "appid=YOUR_OPENWEATHERMAP_KEY",
        "-----BEGIN PUBLIC KEY-----",
        "-----BEGIN CERTIFICATE-----",
        "AKIAIOSFODNN7",  # too short for an access key id
    ],
)
def test_secret_patterns_ignore_benign_strings(health_check, benign):
    pat = re.compile("|".join(health_check._SECRET_PATTERNS))
    assert not pat.search(benign), benign


def test_tracked_tree_is_clean(health_check):
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    check = health_check.check_secrets()
    assert check.status != "fail", check.detail


# ── .gitignore ────────────────────────────────────────────────────────────


def _git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


@pytest.fixture(scope="module")
def git_ok():
    if shutil.which("git") is None or not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "web/.env.production",
        ".env.local",
        "deploy/server.pem",
        "signing.key",
        "cert.p12",
        "cert.pfx",
        "id_rsa",
        "id_rsa.pub",
        "credentials.json",
        "gcp-credentials-prod.json",
        ".npmrc",
        "web/.npmrc",
        ".vercel/project.json",
        "web/.vercel/project.json",
        "coverage.xml",
        ".hypothesis/examples/x",
    ],
)
def test_secret_files_are_ignored(git_ok, path):
    assert _git("check-ignore", "-q", "--no-index", path).returncode == 0, path


@pytest.mark.parametrize("path", [".env.example", "web/.env.local.example"])
def test_env_templates_stay_tracked(git_ok, path):
    assert _git("check-ignore", "-q", "--no-index", path).returncode == 1, path


def test_no_tracked_file_is_newly_ignored(git_ok):
    # motoquant.db predates the `*.db` rule and is tracked on purpose.
    ignored = set(_git("ls-files", "-ci", "--exclude-standard").stdout.split())
    assert ignored <= {"motoquant.db"}, sorted(ignored)
