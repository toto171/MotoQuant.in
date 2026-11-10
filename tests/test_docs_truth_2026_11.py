"""Docs-truth checks: the live docs must not point at things that do not exist.

Cheap and deterministic (no simulation, no network): link targets, ``make``
targets, CLI subcommands, CODEOWNERS patterns, packaging metadata and a
phrase blacklist for retired product language.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
from pathlib import Path

import pytest

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10: tomllib arrived in 3.11
    tomllib = None


ROOT = Path(__file__).resolve().parent.parent

OWNED_DOCS = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "AGENTS.md",
    "docs/MCP.md",
    "docs/ONBOARDING.md",
    "docs/README.md",
    "docs/FAQ.md",
    "docs/ARCHITECTURE.md",
    "docs/INVARIANTS.md",
    "docs/KNOWN_TRAPS.md",
    "docs/CHAT_AGENT.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
]
SKILL_DOCS = sorted(
    str(p.relative_to(ROOT)) for p in (ROOT / "skills" / "motoquant").rglob("*.md")
)
ALL_DOCS = OWNED_DOCS + SKILL_DOCS

FENCE = re.compile(r"^(```|~~~)")


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _split(text: str) -> tuple[list[str], list[str]]:
    """Return (prose lines, fenced-code lines)."""
    prose, code, in_fence = [], [], False
    for line in text.splitlines():
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            continue
        (code if in_fence else prose).append(line)
    return prose, code


def test_relative_markdown_links_resolve():
    link = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
    broken = []
    for rel in OWNED_DOCS:
        prose, _ = _split(_read(rel))
        base = (ROOT / rel).parent
        for line in prose:
            for target in link.findall(line):
                if re.match(r"^(https?:|mailto:|#)", target):
                    continue
                path = target.split("#", 1)[0]
                if path and not (base / path).exists():
                    broken.append(f"{rel}: {target}")
    assert not broken, broken


def _make_targets() -> set[str]:
    return set(re.findall(r"^([A-Za-z][\w-]*):", _read("Makefile"), flags=re.MULTILINE))


def test_make_targets_mentioned_exist():
    targets = _make_targets()
    inline = re.compile(r"`make ([A-Za-z][\w-]*)")
    bad = []
    for rel in ALL_DOCS:
        prose, code = _split(_read(rel))
        for line in prose:
            for t in inline.findall(line):
                if t not in targets:
                    bad.append(f"{rel}: make {t}")
        for line in code:
            m = re.match(r"\s*(?:\$ )?make ([A-Za-z][\w-]*)", line)
            if m and m.group(1) not in targets:
                bad.append(f"{rel}: make {m.group(1)}")
    assert not bad, bad


def _cli_paths(parser: argparse.ArgumentParser, prefix=()) -> set[tuple[str, ...]]:
    out: set[tuple[str, ...]] = set()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                out.add((*prefix, name))
                out |= _cli_paths(sub, (*prefix, name))
    return out


def test_cli_subcommands_mentioned_exist():
    from motoquant.run import build_parser

    paths = _cli_paths(build_parser())
    top = {p[0] for p in paths}
    cmd = re.compile(r"python3? -m motoquant\.run((?:\s+\S+)*)")
    bad = []
    for rel in ALL_DOCS:
        for line in _read(rel).splitlines():
            for m in cmd.finditer(line):
                # Stop at a trailing shell comment or the closing backtick.
                words = re.split(r"#|`", m.group(1))[0].split()
                # Drop global options (--db PATH) before the subcommand.
                i = 0
                while i < len(words) and words[i].startswith("-"):
                    i += 2 if words[i] == "--db" else 1
                words = [w.strip("`\"'") for w in words[i:]]
                if not words or not re.fullmatch(r"[a-z][a-z0-9-]*", words[0]):
                    continue  # `--help`, `…`, `<subcommand>`, trailing comments
                if words[0] not in top:
                    bad.append(f"{rel}: {words[0]}")
                    continue
                children = {p[1] for p in paths if len(p) > 1 and p[0] == words[0]}
                if (
                    children
                    and len(words) > 1
                    and not words[1].startswith(("-", '"', "<"))
                    and words[1] not in children
                ):
                    bad.append(f"{rel}: {words[0]} {words[1]}")
    assert not bad, bad


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    return out.stdout.splitlines()


def test_codeowners_patterns_match_tracked_files():
    files = _tracked_files()
    unmatched = []
    for raw in _read(".github/CODEOWNERS").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        pattern = line.split()[0]
        pat = pattern.lstrip("/")
        if pat.endswith("/"):
            ok = any(f.startswith(pat) for f in files)
        elif "*" in pat:
            ok = any(fnmatch.fnmatch(f, pat) for f in files)
        else:
            ok = pat in files
        if not ok:
            unmatched.append(pattern)
    assert not unmatched, unmatched


def test_packaging_declares_dependencies_and_license():
    if tomllib is None:
        pytest.skip("tomllib needs Python 3.11+")
    meta = tomllib.loads(_read("pyproject.toml"))
    project = meta["project"]
    assert "dependencies" in project["dynamic"]
    dyn = meta["tool"]["setuptools"]["dynamic"]
    assert dyn["dependencies"]["file"] == ["requirements-api.txt"]
    assert dyn["optional-dependencies"]["dev"]["file"] == ["requirements-dev.txt"]
    for req in ("requirements-api.txt", "requirements-dev.txt"):
        names = [ln for ln in _read(req).splitlines() if ln.strip() and ln[0].isalpha()]
        assert names, f"{req} lists no requirements"
    assert project["license"]["text"] == "MIT"
    front = _read("skills/motoquant/SKILL.md").split("---")[1]
    assert re.search(r"^license:\s*MIT\s*$", front, flags=re.MULTILINE)
    assert "MIT License" in _read("LICENSE")


BANNED = [
    re.compile(r"\bmetered\b", re.I),
    re.compile(r"free[- ]tier", re.I),
    re.compile(r"\bPro tier\b", re.I),
    re.compile(r"MotoQuant Pro"),
    re.compile(r"\bProprietary\b"),
]
# "free tier" may describe a third party's hosting plan, never a product plan.
THIRD_PARTY = re.compile(r"Render|Groq|Vercel|hosting|host\b|cold", re.I)


def test_no_retired_product_language():
    hits = []
    for rel in ALL_DOCS:
        for n, line in enumerate(_read(rel).splitlines(), 1):
            for pat in BANNED:
                if pat.search(line):
                    if pat.pattern.startswith("free") and THIRD_PARTY.search(line):
                        continue
                    hits.append(f"{rel}:{n}: {line.strip()[:80]}")
    assert not hits, hits


def test_single_contact_address():
    """Security / conduct / FAQ use the address the site's contact page shows."""
    site = _read("web/app/contact/page.js")
    m = re.search(r"[\w.+-]+@[\w-]+\.[a-z.]+", site)
    assert m, "contact page publishes no address"
    addr = m.group(0)
    for rel in ("SECURITY.md", "CODE_OF_CONDUCT.md", "docs/FAQ.md"):
        found = set(re.findall(r"[\w.+-]+@[\w-]+\.[a-z.]+", _read(rel)))
        assert found <= {addr}, (rel, found)
