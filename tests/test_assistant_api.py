"""
The assistant HTTP surface: GET /api/assistant, the X-Anthropic-Key header,
the assistant field and the server-key-only daily cap on POST /api/chat and
POST /api/jobs/chat.

These tests run the REAL client builder: the Anthropic SDK constructor
(``motoquant.llm.client._build_sdk``) is patched to return a fake SDK that
records which key it was built with and every request it receives. Fake
keys are built at runtime (the repo's secret scan flags a literal
``sk-ant-`` followed by 32+ key characters).

Run with:  python -m pytest tests/test_assistant_api.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest import mock

import anthropic
from fastapi.testclient import TestClient

from motoquant import ratelimit
from motoquant.llm import client as client_mod

_REPO_DB = os.path.join(os.path.dirname(__file__), "..", "motoquant.db")
_tmp = tempfile.NamedTemporaryFile(
    prefix="mq_assistant_api_", suffix=".db", delete=False
)
_tmp.close()
shutil.copyfile(_REPO_DB, _tmp.name)
_PRIOR_DB: str | None = None


def _reset_api_db() -> None:
    import motoquant.api as api_mod

    api_mod._db_conn = None
    api_mod._db_facade = None


def setUpModule():
    global _PRIOR_DB
    _PRIOR_DB = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = _tmp.name
    _reset_api_db()


def tearDownModule():
    _reset_api_db()
    for suffix in ("", "-wal", "-shm"):
        try:
            os.unlink(_tmp.name + suffix)
        except OSError:
            pass
    if _PRIOR_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_DB


def fake_key(tag: str) -> str:
    return "sk-ant-" + "api03-" + tag * 40


class _FakeSDK:
    def __init__(self, key, log, reply):
        self.key = key
        self.closed = False
        self._log = log
        self._reply = reply
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self._log.append({"key": self.key, "kwargs": kw})
        r = self._reply(kw) if callable(self._reply) else self._reply
        if isinstance(r, Exception):
            raise r
        return r

    def close(self):
        self.closed = True


def _text_msg(t):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=t)], stop_reason="end_turn"
    )


class _ApiTest(unittest.TestCase):
    SERVER_KEY = fake_key("s")
    VISITOR_KEY = fake_key("v")

    @classmethod
    def setUpClass(cls):
        import motoquant.api as api_mod

        cls.api = api_mod
        cls.client = TestClient(api_mod.app)

    def setUp(self):
        self._prior_enabled = ratelimit.RATE_LIMIT_ENABLED
        ratelimit.RATE_LIMIT_ENABLED = True
        ratelimit.reset()
        self._prior_limit = self.api.CHAT_DAILY_LIMIT
        client_mod.reset_server_key_resting()
        client_mod._SERVER_SDK.clear()
        self.calls: list[dict] = []
        self.built: list[_FakeSDK] = []
        self.reply = _text_msg("answer")
        self._env = mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": self.SERVER_KEY})
        self._env.start()

        self.visitor_flags: list[bool] = []

        def build(key, _timeout, *, visitor=False):
            self.visitor_flags.append(visitor)
            sdk = _FakeSDK(key, self.calls, lambda kw: self.reply)
            self.built.append(sdk)
            return sdk

        self._build = mock.patch.object(client_mod, "_build_sdk", build)
        self._build.start()

    def tearDown(self):
        self._build.stop()
        self._env.stop()
        self.api.CHAT_DAILY_LIMIT = self._prior_limit
        ratelimit.RATE_LIMIT_ENABLED = self._prior_enabled
        ratelimit.reset()
        client_mod.reset_server_key_resting()
        client_mod._SERVER_SDK.clear()
        self.api.app.dependency_overrides.clear()

    def chat(self, body=None, key=None, path="/api/chat", ip="203.0.113.7"):
        headers = {"x-forwarded-for": ip}
        if key is not None:
            headers["X-Anthropic-Key"] = key
        return self.client.post(
            path, json=body or {"query": "how fast is a K5?"}, headers=headers
        )

    def wait_job(self, job_id):
        for _ in range(300):
            jr = self.client.get(f"/api/jobs/{job_id}").json()
            if jr["status"] in ("done", "error", "cancelled"):
                return jr
            time.sleep(0.03)
        self.fail("job did not finish")


class TestAssistantInfo(_ApiTest):
    def test_shape(self):
        r = self.client.get("/api/assistant")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json(),
            {
                "free_available": True,
                "assistants": [
                    {"id": "doctor", "label": "The doctor", "model": "Claude Opus 5.5"},
                    {
                        "id": "mechanic",
                        "label": "The mechanic",
                        "model": "Claude Sonnet 5.5",
                    },
                ],
                "default": "mechanic",
                "daily_free_limit": self.api.CHAT_DAILY_LIMIT,
            },
        )

    def test_free_unavailable_without_a_server_key(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            self.assertFalse(self.client.get("/api/assistant").json()["free_available"])

    def test_free_unavailable_while_the_server_key_rests(self):
        client_mod.note_server_key_resting()
        self.assertFalse(self.client.get("/api/assistant").json()["free_available"])

    def test_limit_follows_the_setting(self):
        self.api.CHAT_DAILY_LIMIT = 7
        self.assertEqual(
            self.client.get("/api/assistant").json()["daily_free_limit"], 7
        )


class TestVisitorKey(_ApiTest):
    def test_visitor_key_builds_a_per_request_client_with_that_key_only(self):
        r = self.chat({"query": "hi", "assistant": "doctor"}, key=self.VISITOR_KEY)
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIsNone(d["error"], d)
        self.assertTrue(d["own_key"])
        self.assertEqual(d["assistant"], "doctor")
        self.assertEqual([c["key"] for c in self.calls], [self.VISITOR_KEY])
        self.assertEqual(self.calls[0]["kwargs"]["model"], "claude-opus-5-5")
        # Built as a visitor client: api.anthropic.com, no env headers.
        self.assertEqual(self.visitor_flags, [True])
        # Never cached, closed after the turn, never echoed back.
        self.assertNotIn(self.VISITOR_KEY, client_mod._SERVER_SDK)
        self.assertTrue(self.built[0].closed)
        self.assertNotIn(self.VISITOR_KEY, r.text)

    def test_without_a_header_the_server_key_answers(self):
        r = self.chat({"query": "hi"})
        d = r.json()
        self.assertIsNone(d["error"], d)
        self.assertFalse(d["own_key"])
        self.assertEqual(d["assistant"], "mechanic")
        self.assertEqual([c["key"] for c in self.calls], [self.SERVER_KEY])
        self.assertEqual(self.calls[0]["kwargs"]["model"], "claude-sonnet-5-5")
        self.assertEqual(self.visitor_flags, [False])

    def test_visitor_key_never_falls_back_to_the_server_key(self):
        self.reply = anthropic.AuthenticationError(
            "invalid x-api-key",
            response=_http_response(401),
            body=None,
        )
        d = self.chat(key=self.VISITOR_KEY).json()
        self.assertEqual(d["error"], "key_rejected")
        self.assertEqual({c["key"] for c in self.calls}, {self.VISITOR_KEY})

    def test_malformed_header_is_invalid_key_format_and_never_used(self):
        for bad in ("hello", "sk-ant-short", "sk-proj-" + "a" * 40):
            d = self.chat(key=bad).json()
            self.assertEqual(d["error"], "invalid_key_format", bad)
            self.assertFalse(d["own_key"])
        self.assertEqual(self.calls, [])

    def test_blank_header_means_server_key(self):
        d = self.chat(key="   ").json()
        self.assertIsNone(d["error"], d)
        self.assertFalse(d["own_key"])

    def test_raw_model_ids_are_rejected(self):
        for value in ("claude-opus-5-5", "groq", ""):
            r = self.chat({"query": "hi", "assistant": value})
            self.assertEqual(r.status_code, 422, value)

    def test_key_in_an_error_is_redacted_on_both_routes(self):
        self.reply = anthropic.BadRequestError(
            f"bad thing near {self.VISITOR_KEY}",
            response=_http_response(400),
            body=None,
        )
        r = self.chat(key=self.VISITOR_KEY)
        self.assertEqual(r.json()["error"], "agent_failed")
        self.assertNotIn(self.VISITOR_KEY, r.text)
        self.assertNotIn("sk-ant-", r.json()["error_detail"])
        jr = self.chat(key=self.VISITOR_KEY, path="/api/jobs/chat")
        self.assertEqual(jr.status_code, 202)
        job = self.wait_job(jr.json()["job_id"])
        self.assertNotIn(self.VISITOR_KEY, json.dumps(job))
        self.assertEqual(job["result"]["error"], "agent_failed")

    def test_job_route_reads_the_header_once_at_start(self):
        jr = self.chat({"query": "hi"}, key=self.VISITOR_KEY, path="/api/jobs/chat")
        self.assertEqual(jr.status_code, 202)
        job = self.wait_job(jr.json()["job_id"])  # polls carry no header
        self.assertEqual(job["status"], "done")
        self.assertTrue(job["result"]["own_key"])
        self.assertEqual(job["result"]["summary"], "answer")
        self.assertEqual([c["key"] for c in self.calls], [self.VISITOR_KEY])
        self.assertNotIn(self.VISITOR_KEY, json.dumps(job))

    def test_no_server_key_and_no_visitor_key_is_unavailable(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            d = self.chat().json()
        self.assertEqual(d["error"], "assistant_unavailable")
        self.assertEqual(self.calls, [])

    def test_resting_server_key_answers_without_a_model_call(self):
        client_mod.note_server_key_resting()
        d = self.chat().json()
        self.assertEqual(d["error"], "free_assistant_resting")
        self.assertEqual(self.calls, [])
        # The rest lasts minutes, not the day.
        self.assertNotIn("today", d["error_detail"])
        self.assertIn("for now", d["error_detail"])
        # ...but a visitor key still works.
        d = self.chat(key=self.VISITOR_KEY).json()
        self.assertIsNone(d["error"], d)

    def test_server_spend_limit_429_marks_the_free_assistant_resting(self):
        self.reply = anthropic.RateLimitError(
            "You have reached your specified API usage limits.",
            response=_http_response(429),
            body={
                "type": "error",
                "error": {
                    "type": "rate_limit_error",
                    "message": "You have reached your specified API usage limits.",
                    "details": {"error_code": "enforced_spend_limit_reached"},
                },
            },
        )
        self.assertEqual(self.chat().json()["error"], "free_assistant_resting")
        self.assertFalse(self.client.get("/api/assistant").json()["free_available"])
        n = len(self.calls)
        # The next keyless question is answered without a model call.
        self.assertEqual(self.chat().json()["error"], "free_assistant_resting")
        self.assertEqual(len(self.calls), n)

    def test_server_credit_error_marks_the_free_assistant_resting(self):
        self.reply = anthropic.BadRequestError(
            "Your credit balance is too low to access the Anthropic API.",
            response=_http_response(400),
            body=None,
        )
        self.assertEqual(self.chat().json()["error"], "free_assistant_resting")
        self.assertFalse(self.client.get("/api/assistant").json()["free_available"])


class TestDailyCap(_ApiTest):
    def _assert_daily_429(self, r):
        self.assertEqual(r.status_code, 429, r.text[:300])
        self.assertIn("chat_day", r.json()["detail"]["message"])

    def test_doctor_costs_two_units_mechanic_one(self):
        self.api.CHAT_DAILY_LIMIT = 3
        self.assertEqual(
            self.chat({"query": "a", "assistant": "doctor"}).status_code, 200
        )
        self.assertEqual(self.chat({"query": "b"}).status_code, 200)
        self._assert_daily_429(self.chat({"query": "c"}))

    def test_doctor_is_refused_when_only_one_unit_is_left(self):
        self.api.CHAT_DAILY_LIMIT = 2
        self.assertEqual(self.chat({"query": "a"}).status_code, 200)
        self._assert_daily_429(self.chat({"query": "b", "assistant": "doctor"}))

    def test_visitor_key_skips_the_daily_cap(self):
        self.api.CHAT_DAILY_LIMIT = 1
        for _ in range(4):
            r = self.chat({"query": "x", "assistant": "doctor"}, key=self.VISITOR_KEY)
            self.assertEqual(r.status_code, 200)
        r = self.chat({"query": "x"}, key=self.VISITOR_KEY, path="/api/jobs/chat")
        self.assertEqual(r.status_code, 202)
        # The server key still has its whole allowance.
        self.assertEqual(self.chat({"query": "x"}).status_code, 200)
        self._assert_daily_429(self.chat({"query": "x"}))

    def test_no_server_key_does_not_spend_the_cap(self):
        self.api.CHAT_DAILY_LIMIT = 1
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            for path in ("/api/chat", "/api/jobs/chat", "/api/chat"):
                r = self.chat({"query": "x", "assistant": "doctor"}, path=path)
                self.assertIn(r.status_code, (200, 202), r.text[:300])
                d = r.json() if r.status_code == 200 else None
                if d is None:
                    d = self.wait_job(r.json()["job_id"])["result"]
                self.assertEqual(d["error"], "assistant_unavailable")
        self.assertEqual(self.calls, [])
        # The whole allowance is still there once the server has a key.
        self.assertEqual(self.chat({"query": "x"}).status_code, 200)
        self._assert_daily_429(self.chat({"query": "x"}))

    def test_malformed_key_does_not_spend_the_cap(self):
        self.api.CHAT_DAILY_LIMIT = 1
        for _ in range(3):
            self.assertEqual(
                self.chat(key="nope").json()["error"], "invalid_key_format"
            )
        self.assertEqual(self.chat().status_code, 200)

    def test_per_minute_bucket_still_applies_to_visitor_keys(self):
        codes = [self.chat(key=self.VISITOR_KEY).status_code for _ in range(21)]
        self.assertEqual(codes[:20], [200] * 20)
        self.assertEqual(codes[20], 429)


def _http_response(status):
    try:
        import httpx2 as hx
    except ImportError:  # anthropic < 1.0
        import httpx as hx
    req = hx.Request("POST", "https://api.anthropic.com/v1/messages")
    return hx.Response(status, request=req)


if __name__ == "__main__":
    unittest.main()
