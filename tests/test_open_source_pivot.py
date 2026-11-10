"""
Open-source pivot (2026-10-23) — regression pins.

MotoQuant became free and open source: payments, subscriptions, license keys,
tier gating and the free-tier sim-quota meter were deleted. What stays and
what replaced the old protections is pinned here, each through the REAL app
(docs/INVARIANTS.md I8):

1. Optional accounts are still MOUNTED. The old router-mount block wrapped
   auth + payments + subscriptions in one ``except ImportError: warning``, so a
   single stale import silently 404'd /api/auth/* AND the garage. GET
   /api/auth/me must answer 401 (route exists, needs a token), never 404.
2. The monetization surface is GONE — routes, modules, and the auth knobs.
3. Every formerly gated route answers anonymous callers (no 401/402).
4. Save + garage still work end-to-end: anonymous save → leaderboard only;
   signed-in save → attributed and listed by /api/me/runs.
5. The per-IP DAILY chat cap (MOTOQUANT_CHAT_DAILY_LIMIT, LLM-bill fuse) —
   shared by /api/chat and /api/jobs/chat, 0 disables it.
6. The startup schema hook no longer re-creates the dropped billing tables.
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sqlite3
import sys
import tempfile
import types
import unittest

try:
    from fastapi.testclient import TestClient

    from motoquant import api as api_mod, ratelimit
    from motoquant.api import app

    _FASTAPI_OK = True
except ImportError:  # pragma: no cover — CI installs requirements-api.txt
    _FASTAPI_OK = False

# ── Isolated DB (same pattern as tests/test_public_route_fuses.py) ─────────
_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="motoquant_oss_pivot_", suffix=".db", delete=False
)
_tmp_db_file.close()
_TMP_DB_PATH = _tmp_db_file.name
# Asserted in setUpModule (run time), NOT at import: an import-time write would
# poison sibling modules' _PRIOR captures (see tests/test_agent.py).
_PRIOR_MOTOQUANT_DB: str | None = None

_BIKE_MODEL_ID = 77


def _reset_api_db_singletons() -> None:
    mod = sys.modules.get("motoquant.api")
    if mod is not None:
        if getattr(mod, "_db_conn", None) is not None:
            try:
                mod._db_conn.close()
            except Exception:  # noqa: BLE001
                pass
        mod._db_conn = None
        mod._db_facade = None


def _init_schema() -> None:
    """Catalog schema + one bike_config to save runs against."""
    from motoquant.database.connection import MotoQuantDB

    db = MotoQuantDB(_TMP_DB_PATH)
    db.initialize()
    conn = db._conn
    conn.execute("INSERT OR IGNORE INTO manufacturers (id, name) VALUES (1, 'Testco')")
    conn.execute(
        "INSERT OR IGNORE INTO bike_models (id, manufacturer_id, model_name) "
        "VALUES (?, 1, 'Pivot 1000')",
        (_BIKE_MODEL_ID,),
    )
    params = (
        "chassis_params, engine_params, forced_induction_params, "
        "drivetrain_params, clutch_params, tire_params, aero_params, "
        "suspension_params, braking_params, wheelie_params, rider_params, "
        "parasitic_params, staging_params"
    )
    conn.execute(
        f"INSERT OR IGNORE INTO bike_configs (id, bike_model_id, {params}) "
        f"VALUES (1, ?, {', '.join(['?'] * 13)})",
        (_BIKE_MODEL_ID, *(["{}"] * 13)),
    )
    conn.commit()
    db.close()


def setUpModule():
    global _PRIOR_MOTOQUANT_DB
    _PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH
    _reset_api_db_singletons()
    _init_schema()
    if _FASTAPI_OK:
        # The startup hook is what adds sim_runs.user_id + the account tables.
        asyncio.run(api_mod._ensure_runtime_schema())


def tearDownModule():
    _reset_api_db_singletons()
    for suffix in ("", "-wal", "-shm"):
        try:
            os.unlink(_TMP_DB_PATH + suffix)
        except OSError:
            pass
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB


@unittest.skipUnless(_FASTAPI_OK, "fastapi not installed")
class _AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app, raise_server_exceptions=False)

    def setUp(self):
        self._prior_enabled = ratelimit.RATE_LIMIT_ENABLED
        ratelimit.RATE_LIMIT_ENABLED = True
        ratelimit.reset()

    def tearDown(self):
        ratelimit.RATE_LIMIT_ENABLED = self._prior_enabled
        ratelimit.reset()


# ───────────────────────────────────────────────────────────────────────────
# 1. Accounts stay mounted
# ───────────────────────────────────────────────────────────────────────────


class TestAccountsAreMounted(_AppTest):
    def test_auth_me_is_401_not_404(self):
        r = self.client.get("/api/auth/me")
        self.assertEqual(
            r.status_code,
            401,
            "GET /api/auth/me must exist and demand a token — a 404 means the "
            f"account router silently failed to mount: {r.status_code} {r.text}",
        )

    def test_garage_is_401_not_404(self):
        self.assertEqual(self.client.get("/api/me/runs").status_code, 401)

    def test_every_account_route_is_registered(self):
        # app.openapi() rather than app.routes: newer FastAPI keeps included
        # routers as lazy _IncludedRouter entries, so their paths are not
        # flat in app.routes.
        paths = set(app.openapi()["paths"])
        for p in (
            "/api/auth/magic-link",
            "/api/auth/verify",
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/password/change",
            "/api/auth/refresh",
            "/api/auth/logout",
            "/api/auth/me",
            "/api/me/runs",
        ):
            self.assertIn(p, paths)

    def test_auth_import_did_not_fail(self):
        self.assertIsNone(api_mod._AUTH_IMPORT_ERROR)
        self.assertIsNotNone(api_mod._auth_mod)


# ───────────────────────────────────────────────────────────────────────────
# 2. The monetization surface is gone
# ───────────────────────────────────────────────────────────────────────────


class TestMonetizationIsGone(_AppTest):
    def test_no_payment_or_subscription_routes(self):
        prefixes = ("/api/payments", "/api/subscriptions")
        stray = [p for p in app.openapi()["paths"] if p.startswith(prefixes)]
        self.assertEqual(stray, [])
        for method, path in (
            ("get", "/api/payments/config"),
            ("post", "/api/payments/checkout"),
            ("post", "/api/payments/webhook/stripe"),
            ("get", "/api/subscriptions/status"),
            ("post", "/api/subscriptions/webhook"),
            ("post", "/api/subscriptions/license-key/validate"),
        ):
            r = getattr(self.client, method)(path)
            self.assertEqual(r.status_code, 404, f"{method.upper()} {path}")

    def test_monetization_modules_are_deleted(self):
        for name in (
            "motoquant.payments",
            "motoquant.subscriptions",
            "motoquant.usage",
            "motoquant.database.subscriptions_repo",
        ):
            with self.subTest(module=name):
                sys.modules.pop(name, None)
                with self.assertRaises(ImportError):
                    importlib.import_module(name)

    def test_auth_has_no_billing_knobs(self):
        import motoquant.auth as auth

        for attr in ("BILLING_ENFORCE", "require_tier"):
            self.assertFalse(hasattr(auth, attr), attr)
        for field in ("tier", "subscription_status", "license_keys"):
            self.assertNotIn(field, auth.MeResponse.model_fields)
        self.assertNotIn("tier", auth.TokenResponse.model_fields)

    def test_agent_has_no_paywall(self):
        import motoquant.llm.agent as agent

        for attr in ("PRO_TOOLS", "pro_tools_locked", "_upgrade_required"):
            self.assertFalse(hasattr(agent, attr), attr)

    def test_full_sim_carries_no_quota_headers(self):
        r = self.client.post("/api/simulate", json={"bike_preset": "gsxr1000_k5"})
        self.assertEqual(r.status_code, 200, r.text[:300])
        self.assertNotIn("X-Sims-Limit", r.headers)
        self.assertNotIn("X-Sims-Remaining", r.headers)

    def test_openapi_mentions_no_pricing(self):
        spec = self.client.get("/openapi.json").text.lower()
        for word in (
            "upgrade_url",
            "quota_exceeded",
            "razorpay",
            "stripe",
            "license-key",
            "/api/payments",
            "/api/subscriptions",
        ):
            self.assertNotIn(word, spec)
        self.assertEqual(self.client.get("/").json()["service"], "MotoQuant API")


# ───────────────────────────────────────────────────────────────────────────
# 3. Formerly gated routes answer anonymous callers
# ───────────────────────────────────────────────────────────────────────────


class TestFormerlyGatedRoutesAreOpen(_AppTest):
    """An unknown preset makes each route fail CHEAPLY after any auth layer
    would already have answered — so "404/202, never 401/402" proves there
    is no gate without running an optimizer."""

    _UNKNOWN = {"bike_preset": "no_such_preset"}

    def _cancel(self, r):
        if r.status_code == 202:
            self.client.post(f"/api/jobs/{r.json()['job_id']}/cancel")

    def test_sync_tooling_routes(self):
        for path in ("/api/optimize/build", "/api/autotune/ecu"):
            with self.subTest(route=path):
                r = self.client.post(path, json=self._UNKNOWN)
                self.assertNotIn(r.status_code, (401, 402, 403), r.text[:200])
                self.assertEqual(r.status_code, 404, r.text[:200])

    def test_job_tooling_routes(self):
        for path in ("/api/jobs/optimize", "/api/jobs/autotune", "/api/jobs/outlaw"):
            with self.subTest(route=path):
                r = self.client.post(path, json=self._UNKNOWN)
                self._cancel(r)
                self.assertEqual(r.status_code, 202, r.text[:200])

    def test_calibration_uploads(self):
        csv = b"time,speed\n0,0\n"
        for path in ("/api/calibrate/dragy", "/api/calibrate/dyno"):
            with self.subTest(route=path):
                r = self.client.post(path, files={"file": ("x.csv", csv, "text/csv")})
                self.assertNotIn(r.status_code, (401, 402, 403), r.text[:200])


# ───────────────────────────────────────────────────────────────────────────
# 4. Save + garage end-to-end
# ───────────────────────────────────────────────────────────────────────────


class TestSaveAndGarage(_AppTest):
    _RUN = {"bike_id": _BIKE_MODEL_ID, "et_quarter_s": 10.25, "trap_speed_kmh": 240.0}

    def test_anonymous_save_lands_on_the_leaderboard_only(self):
        r = self.client.post("/api/simulate/save", json=self._RUN)
        self.assertEqual(r.status_code, 201, r.text[:300])
        self.assertFalse(r.json()["saved_to_account"])

    def test_signed_in_save_is_attributed_to_the_garage(self):
        reg = self.client.post(
            "/api/auth/register",
            json={"email": "garage@test.in", "password": "lights-out-9s"},
        )
        self.assertEqual(reg.status_code, 201, reg.text[:300])
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}
        r = self.client.post(
            "/api/simulate/save",
            json={**self._RUN, "notes": "pivot garage"},
            headers=headers,
        )
        self.assertEqual(r.status_code, 201, r.text[:300])
        self.assertTrue(r.json()["saved_to_account"])
        runs = self.client.get("/api/me/runs", headers=headers)
        self.assertEqual(runs.status_code, 200, runs.text[:300])
        notes = [row["notes"] for row in runs.json()["runs"]]
        self.assertIn("pivot garage", notes)
        me = self.client.get("/api/auth/me", headers=headers).json()
        self.assertEqual(me["email"], "garage@test.in")
        self.assertNotIn("tier", me)


# ───────────────────────────────────────────────────────────────────────────
# 5. Daily chat cap (LLM-bill fuse)
# ───────────────────────────────────────────────────────────────────────────


class TestChatDailyCap(_AppTest):
    """The model client is overridden with an UNCONFIGURED stub, so each turn
    answers 200 + llm_not_configured without any LLM call — the dependency
    chain (both rate limits) still runs in full."""

    def setUp(self):
        super().setUp()
        self._prior_limit = api_mod.CHAT_DAILY_LIMIT
        stub = types.SimpleNamespace(is_configured=False, provider="stub")
        app.dependency_overrides[api_mod.get_llm_client] = lambda: stub

    def tearDown(self):
        api_mod.CHAT_DAILY_LIMIT = self._prior_limit
        app.dependency_overrides.pop(api_mod.get_llm_client, None)
        super().tearDown()

    def _chat(self, path="/api/chat", ip="203.0.113.10"):
        return self.client.post(
            path, json={"query": "how fast is a K5"}, headers={"x-forwarded-for": ip}
        )

    def _assert_daily_429(self, r):
        self.assertEqual(r.status_code, 429, r.text[:300])
        detail = r.json()["detail"]
        self.assertEqual(detail["error"], "rate_limited")
        self.assertIn("chat_day", detail["message"])
        self.assertIn("per day", detail["message"])
        self.assertGreater(int(r.headers["Retry-After"]), 3600)

    def test_default_is_200_per_day(self):
        self.assertEqual(api_mod._parse_nonneg_int_env("NO_SUCH_VAR_XYZ", 200), 200)
        self.assertEqual(self._prior_limit, 200)

    def test_cap_trips_and_is_shared_with_the_job_route(self):
        api_mod.CHAT_DAILY_LIMIT = 3
        for _ in range(3):
            r = self._chat()
            self.assertEqual(r.status_code, 200, r.text[:300])
            self.assertEqual(r.json()["error"], "llm_not_configured")
        self._assert_daily_429(self._chat())
        self._assert_daily_429(self._chat(path="/api/jobs/chat"))

    def test_cap_is_per_ip(self):
        api_mod.CHAT_DAILY_LIMIT = 1
        self.assertEqual(self._chat(ip="198.51.100.1").status_code, 200)
        self._assert_daily_429(self._chat(ip="198.51.100.1"))
        self.assertEqual(self._chat(ip="198.51.100.2").status_code, 200)

    def test_zero_disables_the_cap(self):
        api_mod.CHAT_DAILY_LIMIT = 0
        for _ in range(5):
            self.assertEqual(self._chat().status_code, 200)

    def test_env_parsing_rejects_garbage_without_crashing(self):
        old = os.environ.get("MQ_TEST_CAP")
        try:
            for raw, expected in (
                ("50", 50),
                ("0", 0),
                (" 7 ", 7),
                ("-3", 200),
                ("lots", 200),
                ("", 200),
            ):
                os.environ["MQ_TEST_CAP"] = raw
                self.assertEqual(
                    api_mod._parse_nonneg_int_env("MQ_TEST_CAP", 200), expected, raw
                )
        finally:
            if old is None:
                os.environ.pop("MQ_TEST_CAP", None)
            else:
                os.environ["MQ_TEST_CAP"] = old


# ───────────────────────────────────────────────────────────────────────────
# 6. Boot no longer re-creates the billing tables
# ───────────────────────────────────────────────────────────────────────────


class TestStartupSchemaHook(_AppTest):
    def test_hook_creates_account_tables_but_no_billing_tables(self):
        asyncio.run(api_mod._ensure_runtime_schema())
        conn = sqlite3.connect(_TMP_DB_PATH)
        try:
            tables = {
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
            run_cols = {r[1] for r in conn.execute("PRAGMA table_info(sim_runs)")}
        finally:
            conn.close()
        for live in ("users", "sessions", "magic_links"):
            self.assertIn(live, tables)
        for dead in ("subscriptions", "license_keys", "payment_events", "sim_usage"):
            self.assertNotIn(dead, tables)
        for dead in ("tier", "razorpay_customer_id", "stripe_customer_id"):
            self.assertNotIn(dead, user_cols)
        self.assertIn("user_id", run_cols)


if __name__ == "__main__":
    unittest.main()
