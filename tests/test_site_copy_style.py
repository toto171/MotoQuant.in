"""House style for text visitors can read on the site.

docs/WRITING.md sets the style. These checks enforce the two rules a
reviewer is most likely to miss:

* no em dashes in visible text (strings, JSX text, metadata); code comments
  may keep them;
* the product is "MotoQuant", never "MotoQuant Pro".
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB_DIRS = ("web/app", "web/components", "web/lib")
EM_DASH = "—"


def _web_sources() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", *WEB_DIRS],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [ROOT / f for f in out if f.endswith((".js", ".jsx", ".mjs"))]


def visible_text(source: str) -> str:
    """Return the source with every JavaScript comment removed.

    A small scanner that tracks strings (single, double and template quotes)
    so that "//" inside a URL string is not mistaken for a comment. What is
    left is code plus string and JSX text, which is where visible copy lives.
    """
    out: list[str] = []
    i, n = 0, len(source)
    quote = None  # active string delimiter
    while i < n:
        c = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(nxt)
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            continue
        if c == "/" and nxt == "/":
            j = source.find("\n", i)
            i = n if j == -1 else j
            continue
        if c == "/" and nxt == "*":
            j = source.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def test_scanner_drops_comments_and_keeps_strings():
    src = (
        "// a — comment\n"
        "const url = 'https://x.y/z'; /* block — */\n"
        'const s = "keep — me";\n'
        "{/* jsx — comment */}<p>text</p>\n"
    )
    text = visible_text(src)
    assert "comment" not in text
    assert "https://x.y/z" in text
    assert text.count(EM_DASH) == 1  # only the one inside the string


@pytest.mark.parametrize("path", _web_sources(), ids=lambda p: str(p.relative_to(ROOT)))
def test_no_em_dash_in_visible_site_text(path):
    text = visible_text(path.read_text(encoding="utf-8"))
    lines = [ln.strip() for ln in text.splitlines() if EM_DASH in ln]
    assert not lines, f"em dash in visible text (see docs/WRITING.md): {lines[:3]}"


@pytest.mark.parametrize("path", _web_sources(), ids=lambda p: str(p.relative_to(ROOT)))
def test_product_is_never_called_motoquant_pro(path):
    text = visible_text(path.read_text(encoding="utf-8"))
    assert "MotoQuant Pro" not in text and "Motoquant Pro" not in text
