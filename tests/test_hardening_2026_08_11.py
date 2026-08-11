"""
Hardening pins — 2026-08-11 commercial-launch-readiness pass.

Pins the JSON-LD injection hardening in web/app/StructuredData.js: the
serialized payload MUST escape "<" as \\u003c so a "</script>" inside any
data value (bike names, blog titles, FAQ answers are all interpolated into
structured data) can never terminate the <script type="application/ld+json">
tag early and break out into live HTML. \\u003c parses identically as JSON,
so crawler-visible semantics are unchanged.

These are source-level pins (the JS runs on Vercel, not in this suite) in
the same spirit as the headline-stat audit regexes: reverting the fix in
StructuredData.js turns them red.

Run:  python -m pytest tests/test_hardening_2026_08_11.py -v
"""

from pathlib import Path

STRUCTURED_DATA_JS = Path(__file__).parent.parent / "web" / "app" / "StructuredData.js"


class TestStructuredDataScriptEscape:
    def test_serialization_escapes_left_angle_bracket(self):
        """The dangerouslySetInnerHTML payload must chain the \\u003c escape."""
        src = STRUCTURED_DATA_JS.read_text(encoding="utf-8")
        assert "JSON.stringify(data).replace(/</g, '\\\\u003c')" in src, (
            "StructuredData.js no longer escapes '<' in the JSON-LD payload — "
            "a '</script>' inside any data value can break out of the tag"
        )

    def test_no_unescaped_stringify_injection_remains(self):
        """No code path may hand raw JSON.stringify output to __html."""
        src = STRUCTURED_DATA_JS.read_text(encoding="utf-8")
        for line in src.splitlines():
            if "__html" in line and "JSON.stringify" in line:
                assert "\\u003c" in line, f"Unescaped JSON-LD injection: {line.strip()}"
