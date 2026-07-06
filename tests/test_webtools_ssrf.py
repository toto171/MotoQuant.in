"""
SSRF-guard regression tests for the chat agent's web tools
(motoquant/llm/webtools.py).

The guard must reject not just a directly-supplied internal URL but also a
*redirect* to one — `requests`/`urllib` follow 3xx by default, so a hostile
public page could 302 the fetcher to 169.254.169.254 (cloud metadata) or
localhost, bypassing the initial _check_url. `_http_get` follows redirects
manually and re-runs the guard on every hop.

Pure unit tests — no DB, no network, no LLM. The single network primitive
(`_http_get_once`) is scripted.

Run with:  python -m pytest tests/test_webtools_ssrf.py -v
"""

from __future__ import annotations

import unittest
import urllib.parse
from unittest import mock

from motoquant.llm import webtools as wt


class TestCheckUrl(unittest.TestCase):
    def test_rejects_non_http_scheme(self):
        self.assertIsNotNone(wt._check_url("file:///etc/passwd"))
        self.assertIsNotNone(wt._check_url("ftp://host/x"))
        self.assertIsNotNone(wt._check_url("gopher://host/x"))

    def test_rejects_loopback_and_metadata(self):
        self.assertIsNotNone(wt._check_url("http://127.0.0.1/"))
        self.assertIsNotNone(wt._check_url("http://169.254.169.254/latest/meta-data/"))
        self.assertIsNotNone(wt._check_url("http://[::1]/"))

    def test_rejects_private_rfc1918(self):
        self.assertIsNotNone(wt._check_url("http://10.0.0.5/"))
        self.assertIsNotNone(wt._check_url("http://192.168.1.1/"))

    def test_rejects_unresolvable_host(self):
        # Unresolvable hosts are refused (fail closed).
        self.assertIsNotNone(
            wt._check_url("http://nonexistent.invalid.example.notarealtld/")
        )


class TestRedirectSSRF(unittest.TestCase):
    def test_redirect_to_cloud_metadata_blocked(self):
        seq = [(302, b"", "http://169.254.169.254/latest/meta-data/")]
        with mock.patch.object(
            wt, "_http_get_once", side_effect=lambda u, **k: seq.pop(0)
        ):
            with self.assertRaises(ValueError):
                wt._http_get("http://public.example/", timeout=5)

    def test_redirect_to_localhost_blocked(self):
        seq = [(301, b"", "http://localhost:8000/admin")]
        with mock.patch.object(
            wt, "_http_get_once", side_effect=lambda u, **k: seq.pop(0)
        ):
            with self.assertRaises(ValueError):
                wt._http_get("http://public.example/", timeout=5)

    def test_relative_redirect_to_internal_blocked(self):
        # A relative Location that urljoins back onto a private base is caught
        # only because the base itself would have been blocked — here we assert
        # an absolute internal target expressed via urljoin is re-checked.
        seq = [(307, b"", "//10.0.0.1/x")]
        with mock.patch.object(
            wt, "_http_get_once", side_effect=lambda u, **k: seq.pop(0)
        ):
            with self.assertRaises(ValueError):
                wt._http_get("http://public.example/", timeout=5)

    def test_normal_fetch_returns_body(self):
        with mock.patch.object(
            wt, "_http_get_once", side_effect=lambda u, **k: (200, b"<p>hi</p>", None)
        ):
            status, body = wt._http_get("http://public.example/", timeout=5)
        self.assertEqual(status, 200)
        self.assertIn(b"hi", body)

    def test_public_redirect_is_followed(self):
        seq = [
            (302, b"", "https://other.example/canonical"),
            (200, b"<p>final</p>", None),
        ]
        with (
            mock.patch.object(
                wt, "_http_get_once", side_effect=lambda u, **k: seq.pop(0)
            ),
            mock.patch.object(wt, "_check_url", return_value=None),
        ):
            status, body = wt._http_get("http://public.example/", timeout=5)
        self.assertEqual(status, 200)
        self.assertIn(b"final", body)

    def test_redirect_loop_is_bounded(self):
        with (
            mock.patch.object(
                wt,
                "_http_get_once",
                side_effect=lambda u, **k: (302, b"", "https://other.example/loop"),
            ),
            mock.patch.object(wt, "_check_url", return_value=None),
        ):
            with self.assertRaises(ValueError):
                wt._http_get("http://public.example/", timeout=5)

    def test_web_fetch_surfaces_blocked_redirect_as_error(self):
        # End-to-end: web_fetch must not raise; it returns {"error": ...}.
        # Guard allows the initial public host, blocks the internal redirect.
        def guard(u):
            host = urllib.parse.urlparse(u).hostname
            return "blocked" if host in ("127.0.0.1", "localhost") else None

        seq = [(302, b"", "http://127.0.0.1/")]
        with (
            mock.patch.object(wt, "_check_url", side_effect=guard),
            mock.patch.object(
                wt, "_http_get_once", side_effect=lambda u, **k: seq.pop(0)
            ),
        ):
            out = wt.web_fetch("http://public.example/")
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
