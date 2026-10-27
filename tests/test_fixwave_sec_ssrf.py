"""Regression tests for two SSRF holes in the chat agent's ``web_fetch``
(motoquant/llm/webtools.py), found by the 2026-10-23 core audit.

1. URL-parser differential. ``_check_url`` vetted the host that
   ``urllib.parse`` sees, but ``requests``/urllib3 connect to the host THEY
   parse. For ``http://127.0.0.1:PORT\\@example.com/`` urllib.parse reads the
   host as example.com (it treats ``127.0.0.1:PORT\\`` as userinfo) while
   urllib3 connects to 127.0.0.1, so a loopback service was fetched and its
   body handed to the LLM.
2. ``100.64.0.0/10`` (shared / carrier-grade NAT, which holds Alibaba Cloud's
   metadata service 100.100.100.200) passed every individual
   ``ipaddress`` flag the guard checked.

The end-to-end test runs the REAL ``web_fetch`` against a real HTTP server on
127.0.0.1. Only ``getaddrinfo`` is stubbed, and only so the decoy host
(example.com) resolves to a public address without network access.
"""

from __future__ import annotations

import http.server
import socket
import threading
from unittest import mock

import pytest

from motoquant.llm import webtools as wt

_PUBLIC_ADDRINFO = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", 0))]
_REAL_GETADDRINFO = socket.getaddrinfo


def _fake_getaddrinfo(host, *args, **kwargs):
    if host == "example.com":
        return _PUBLIC_ADDRINFO
    return _REAL_GETADDRINFO(host, *args, **kwargs)


class _SecretHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - stdlib API
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<p>INTERNAL-SECRET</p>")

    def log_message(self, *args):  # silence the test log
        pass


@pytest.fixture()
def loopback_server():
    srv = http.server.HTTPServer(("127.0.0.1", 0), _SecretHandler)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield srv.server_address[1]
    finally:
        srv.shutdown()
        srv.server_close()


@pytest.fixture(autouse=True)
def _web_tools_on(monkeypatch):
    monkeypatch.setenv("MOTOQUANT_WEB_TOOLS", "1")


class TestBackslashParserDifferential:
    def test_backslash_userinfo_payload_does_not_reach_loopback(self, loopback_server):
        url = f"http://127.0.0.1:{loopback_server}\\@example.com/"
        with mock.patch.object(wt.socket, "getaddrinfo", side_effect=_fake_getaddrinfo):
            out = wt.web_fetch(url)
        assert "text" not in out, f"SSRF: loopback body leaked: {out}"
        assert "error" in out
        assert "INTERNAL-SECRET" not in str(out)

    def test_direct_loopback_still_blocked(self, loopback_server):
        out = wt.web_fetch(f"http://127.0.0.1:{loopback_server}/")
        assert "error" in out and "text" not in out

    def test_metadata_backslash_variant_blocked(self):
        with mock.patch.object(wt.socket, "getaddrinfo", side_effect=_fake_getaddrinfo):
            assert wt._check_url(
                "http://169.254.169.254\\@example.com/latest/meta-data/"
            )

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com/a b",
            "http://example.com/\tpath",
            "http://example.com/\x00",
            "http://exa\nmple.com/",
        ],
    )
    def test_whitespace_and_control_characters_refused(self, url):
        with mock.patch.object(wt.socket, "getaddrinfo", return_value=_PUBLIC_ADDRINFO):
            assert wt._check_url(url)

    @pytest.mark.parametrize(
        "url", ["http://user:pw@example.com/", "http://user@example.com/"]
    )
    def test_embedded_credentials_refused(self, url):
        with mock.patch.object(wt.socket, "getaddrinfo", return_value=_PUBLIC_ADDRINFO):
            assert wt._check_url(url)

    def test_parsers_must_agree_on_the_host(self):
        # Any input where urllib.parse and urllib3 disagree is refused, even
        # one no explicit character rule anticipates.
        with (
            mock.patch.object(wt.socket, "getaddrinfo", return_value=_PUBLIC_ADDRINFO),
            mock.patch.object(wt, "_requests_host", return_value="127.0.0.1"),
        ):
            assert wt._check_url("http://example.com/")

    def test_redirect_to_backslash_payload_blocked(self):
        seq = [(302, b"", "http://127.0.0.1:8000\\@example.com/")]
        with (
            mock.patch.object(wt.socket, "getaddrinfo", side_effect=_fake_getaddrinfo),
            mock.patch.object(
                wt, "_http_get_once", side_effect=lambda u, **k: seq.pop(0)
            ),
        ):
            with pytest.raises(ValueError):
                wt._http_get("http://example.com/", timeout=5)

    @pytest.mark.parametrize(
        "url",
        [
            "https://en.wikipedia.org/wiki/Suzuki_GSX-R1000?action=raw#History",
            "http://example.com:8080/path?q=1",
            "http://bücher.de/x",  # IDN: urllib3 punycodes, urllib.parse does not
            "HTTP://EXAMPLE.COM/",
        ],
    )
    def test_ordinary_public_urls_still_allowed(self, url):
        with mock.patch.object(wt.socket, "getaddrinfo", return_value=_PUBLIC_ADDRINFO):
            assert wt._check_url(url) is None


class TestNonGlobalAddresses:
    @pytest.mark.parametrize(
        "ip",
        [
            "100.100.100.200",  # Alibaba Cloud metadata (shared address space)
            "100.64.0.1",  # CGNAT / Tailscale
            "192.0.0.8",  # IETF protocol assignments
            "198.18.0.1",  # benchmarking
            "::ffff:127.0.0.1",  # IPv4-mapped loopback
            "::ffff:100.64.0.1",  # IPv4-mapped CGNAT
            "fd00::1",  # unique-local IPv6
        ],
    )
    def test_non_public_ranges_blocked(self, ip):
        assert wt._check_url(f"http://[{ip}]/" if ":" in ip else f"http://{ip}/")

    def test_cgnat_host_resolution_blocked(self):
        info = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("100.100.100.200", 0))]
        with mock.patch.object(wt.socket, "getaddrinfo", return_value=info):
            out = wt.web_fetch("http://metadata.example/latest/meta-data/")
        assert out.get("error", "").startswith("host resolves to a private")

    def test_public_address_allowed(self):
        assert not wt._ip_is_blocked(wt.ipaddress.ip_address("93.184.215.14"))
        assert not wt._ip_is_blocked(wt.ipaddress.ip_address("2606:4700::1111"))
