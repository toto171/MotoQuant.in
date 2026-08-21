"""
Background-jobs API + engine progress-callback regression tests (2026-06-07).

The website's real progress bars poll ``/api/jobs/*``; these tests pin:

- the job-registry lifecycle (done / error / truncation / capacity / unknown id)
- progress monotonicity through the real RK4 loop (production path, not a mock)
- that ``progress_cb`` has ZERO effect on the physics (bit-identical ET on the
  K5 reference baseline — this test fails if the callback ever leaks into the
  integration math)
- the ``/api/jobs/*`` routes end-to-end on the reference presets (no DB rows
  required, so the suite stays green on a fresh checkout)
"""

import os
import sys
import tempfile
import threading
import time
import unittest

from motoquant import MotoQuantEngine, gsxr1000_k5, jobs as jobs_mod

try:  # route tests are gated on fastapi being installed (CI always has it)
    from fastapi import HTTPException
    from fastapi.testclient import TestClient

    HAS_FASTAPI = True
except ImportError:  # pragma: no cover
    HAS_FASTAPI = False

# ---------------------------------------------------------------------------
# Isolated DB -- the metered routes (/api/jobs/simulate, /api/jobs/topspeed)
# record sim_usage rows via connect(), which falls back to the repo's tracked
# motoquant.db when MOTOQUANT_DB is unset. Point it at a throwaway tmp DB so
# a suite run never dirties the working tree (same pattern as test_api.py).
# No seeding needed: these tests use bike_presets only, and record_and_check
# creates the sim_usage table on demand.
# ---------------------------------------------------------------------------
_tmp_db_file = tempfile.NamedTemporaryFile(
    prefix="motoquant_jobs_test_", suffix=".db", delete=False
)
_tmp_db_file.close()
_TMP_DB_PATH = _tmp_db_file.name
# Captured at import as a solo-run fallback ONLY. In a full-suite run this
# value is unreliable for restore: collection imports every module before any
# test runs, so by the time THIS module imports, an alphabetically-earlier
# module (test_api) has already pointed MOTOQUANT_DB at ITS tmp copy — and
# restoring that path after test_api's teardown deleted it left every later
# module (test_llm_runner, test_power_boost_regression) reading an empty DB.
_IMPORT_PRIOR_MOTOQUANT_DB = os.environ.get("MOTOQUANT_DB")
_PRIOR_MOTOQUANT_DB = _IMPORT_PRIOR_MOTOQUANT_DB
os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def setUpModule():
    """Re-assert this module's tmp DB right before its tests run.

    Module-level MOTOQUANT_DB overrides execute at COLLECTION time, so a
    sibling module imported after this one (e.g. test_api also sets
    MOTOQUANT_DB at import) leaves the env pointing at ITS tmp DB by the
    time these tests actually run. Re-asserting here makes ordering
    irrelevant.

    The restore value is captured HERE (run time), not at import: the
    previous env-overriding module's tearDownModule has restored the true
    session value by now, whereas the import-time snapshot may hold a
    sibling's since-deleted tmp path. If the current value is our own tmp
    (solo-file run — nothing ran in between), keep the import-time capture.
    """
    global _PRIOR_MOTOQUANT_DB
    current = os.environ.get("MOTOQUANT_DB")
    if current != _TMP_DB_PATH:
        _PRIOR_MOTOQUANT_DB = current
    os.environ["MOTOQUANT_DB"] = _TMP_DB_PATH


def tearDownModule():
    """Remove the tmp DB and restore MOTOQUANT_DB after all tests finish."""
    _api_mod = sys.modules.get("motoquant.api")
    if _api_mod is not None and getattr(_api_mod, "_db_conn", None) is not None:
        try:
            _api_mod._db_conn.close()
        except Exception:  # noqa: BLE001
            pass
        _api_mod._db_conn = None
    try:
        os.unlink(_TMP_DB_PATH)
    except OSError:
        pass
    if _PRIOR_MOTOQUANT_DB is None:
        os.environ.pop("MOTOQUANT_DB", None)
    else:
        os.environ["MOTOQUANT_DB"] = _PRIOR_MOTOQUANT_DB


def _poll_until_finished(client, job_id, timeout_s=180.0, interval_s=0.05):
    """Poll GET /api/jobs/{id} until done/error; return (final, snapshots)."""
    snapshots = []
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = client.get(f"/api/jobs/{job_id}")
        assert r.status_code == 200, r.text
        j = r.json()
        snapshots.append(j)
        if j["status"] in ("done", "error", "cancelled"):
            return j, snapshots
        time.sleep(interval_s)
    raise AssertionError(f"job {job_id} did not finish in {timeout_s}s")


class TestEngineProgressCallback(unittest.TestCase):
    """progress_cb is a pure observer on the RK4 loop."""

    def test_progress_monotonic_and_physics_identical(self):
        fractions = []
        et_with_cb = (
            MotoQuantEngine(gsxr1000_k5())
            .run(progress_cb=fractions.append)
            .time_quarter
        )
        et_plain = MotoQuantEngine(gsxr1000_k5()).run().time_quarter

        # Bit-identical ET — the callback must not touch the physics.
        self.assertEqual(et_with_cb, et_plain)
        # And both still sit on the pinned K5 reference baseline.
        self.assertAlmostEqual(et_plain, 9.9331, places=3)

        self.assertGreater(len(fractions), 10)
        self.assertTrue(
            all(b >= a for a, b in zip(fractions, fractions[1:])),
            "progress went backwards",
        )
        self.assertLessEqual(max(fractions), 1.0)
        self.assertGreater(fractions[-1], 0.9)

    def test_top_speed_passthrough(self):
        fractions = []
        ts = MotoQuantEngine(gsxr1000_k5()).run_top_speed(
            max_time=20.0, progress_cb=fractions.append
        )
        self.assertGreater(ts.terminal_velocity_kmh, 100.0)
        self.assertGreater(len(fractions), 5)
        self.assertTrue(all(b >= a for a, b in zip(fractions, fractions[1:])))


class TestJobRegistry(unittest.TestCase):
    """motoquant.jobs lifecycle, independent of FastAPI."""

    def _wait(self, job, timeout_s=10.0):
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            got = jobs_mod.get_job(job.id)
            if got is not None and got.status in ("done", "error", "cancelled"):
                return got
            time.sleep(0.02)
        raise AssertionError("job did not finish")

    def test_done_lifecycle_and_monotonic_clamp(self):
        def runner(progress):
            progress(0.5, "halfway")
            progress(0.2)  # must NOT move the bar backwards
            progress(7.0)  # must clamp to 1.0
            return {"answer": 42}

        job = jobs_mod.create_job("unittest", runner)
        got = self._wait(job)
        self.assertEqual(got.status, "done")
        self.assertEqual(got.result, {"answer": 42})
        self.assertEqual(got.progress, 1.0)
        self.assertEqual(got.stage, "halfway")

    def test_error_is_truncated_and_detail_extracted(self):
        if not HAS_FASTAPI:
            exc = RuntimeError("Config error: " + "X" * 2000)
        else:
            exc = HTTPException(400, "Config error: " + "X" * 2000)

        def runner(progress):
            raise exc

        job = jobs_mod.create_job("unittest", runner)
        got = self._wait(job)
        self.assertEqual(got.status, "error")
        self.assertIn("Config error", got.error)
        self.assertLessEqual(len(got.error), 500)

    def test_unknown_job_is_none(self):
        self.assertIsNone(jobs_mod.get_job("no-such-job"))

    def test_cancel_mid_run(self):
        def runner(progress):
            for i in range(2000):  # ~10 s unless cancelled at a tick
                progress(i / 2000.0)
                time.sleep(0.005)
            return {"finished": True}

        job = jobs_mod.create_job("unittest", runner)
        time.sleep(0.1)
        flagged = jobs_mod.cancel_job(job.id)
        self.assertTrue(flagged.cancel_requested)
        got = self._wait(job)
        self.assertEqual(got.status, "cancelled")
        self.assertIsNone(got.result)
        self.assertEqual(got.stage, "Stopped")

    def test_cancel_after_done_is_noop(self):
        job = jobs_mod.create_job("unittest", lambda progress: {"ok": 1})
        got = self._wait(job)
        self.assertEqual(got.status, "done")
        again = jobs_mod.cancel_job(job.id)
        self.assertEqual(again.status, "done")  # terminal state untouched
        self.assertFalse(again.cancel_requested)
        self.assertEqual(again.result, {"ok": 1})

    def test_cancel_unknown_is_none(self):
        self.assertIsNone(jobs_mod.cancel_job("no-such-job"))

    def test_capacity_guard(self):
        original = jobs_mod.MAX_RUNNING
        jobs_mod.MAX_RUNNING = 0
        try:
            with self.assertRaises(jobs_mod.JobCapacityError):
                jobs_mod.create_job("unittest", lambda progress: None)
        finally:
            jobs_mod.MAX_RUNNING = original

    def test_hung_workers_do_not_starve_the_pool(self):
        """A worker past MAX_JOB_RUNTIME_S is treated as hung: it stops counting
        toward MAX_RUNNING (so new jobs can start) and gets cancel_requested,
        instead of permanently wedging the registry."""
        with jobs_mod._LOCK:
            jobs_mod._JOBS.clear()
            now = time.time()
            hung_ids = []
            for _ in range(jobs_mod.MAX_RUNNING):
                j = jobs_mod.Job("stuck")
                j.status = "running"
                j.created_at = now - (jobs_mod.MAX_JOB_RUNTIME_S + 100)
                jobs_mod._JOBS[j.id] = j
                hung_ids.append(j.id)
        try:
            # Pool is "full" of hung jobs, yet a fresh job must be admitted.
            job = jobs_mod.create_job("unittest", lambda progress: {"ok": 1})
            got = self._wait(job)
            self.assertEqual(got.status, "done")
            # Every hung job was asked to cancel.
            for hid in hung_ids:
                hj = jobs_mod._JOBS.get(hid)
                if hj is not None:
                    self.assertTrue(hj.cancel_requested)
        finally:
            with jobs_mod._LOCK:
                jobs_mod._JOBS.clear()

    def test_healthy_full_pool_still_blocks(self):
        """Regression guard: the hung-job carve-out must not weaken the normal
        MAX_RUNNING back-pressure for jobs that are running within budget."""
        with jobs_mod._LOCK:
            jobs_mod._JOBS.clear()
            now = time.time()
            for _ in range(jobs_mod.MAX_RUNNING):
                j = jobs_mod.Job("busy")
                j.status = "running"
                j.created_at = now  # fresh, not hung
                jobs_mod._JOBS[j.id] = j
        try:
            with self.assertRaises(jobs_mod.JobCapacityError):
                jobs_mod.create_job("unittest", lambda progress: None)
        finally:
            with jobs_mod._LOCK:
                jobs_mod._JOBS.clear()


@unittest.skipUnless(HAS_FASTAPI, "fastapi not installed")
class TestJobsRoutes(unittest.TestCase):
    """/api/jobs/* end-to-end on the reference presets (no DB rows needed)."""

    @classmethod
    def setUpClass(cls):
        from motoquant.api import app

        cls.client = TestClient(app)

    def test_simulate_job_end_to_end(self):
        r = self.client.post("/api/jobs/simulate", json={"bike_preset": "gsxr1000_k5"})
        self.assertEqual(r.status_code, 202)
        body = r.json()
        self.assertEqual(body["kind"], "simulate")

        final, snapshots = _poll_until_finished(self.client, body["job_id"])
        self.assertEqual(final["status"], "done", final.get("error"))
        # The job result is the same payload the sync route returns.
        self.assertAlmostEqual(final["result"]["et_quarter_s"], 9.9331, places=2)
        self.assertIn("timeseries", final["result"])

        progress = [s["progress"] for s in snapshots]
        self.assertTrue(all(b >= a for a, b in zip(progress, progress[1:])))
        self.assertEqual(progress[-1], 1.0)

    def test_autotune_job_reports_stages(self):
        r = self.client.post(
            "/api/jobs/autotune",
            json={"bike_preset": "gsxr1000_k5", "gear_span": 1, "launch_steps": 2},
        )
        self.assertEqual(r.status_code, 202)
        final, snapshots = _poll_until_finished(self.client, r.json()["job_id"])
        self.assertEqual(final["status"], "done", final.get("error"))
        self.assertIn("combined", final["result"])
        known = {
            "",
            "Baseline run",
            "Sweeping gearing",
            "Sweeping launch RPM",
            "Verifying combined setup",
        }
        self.assertTrue({s["stage"] for s in snapshots} <= known)

    def test_compare_job_end_to_end(self):
        """A-vs-B comparison as a background job — added for the July 2026
        redesign so the Compare tab gets a real progress bar + Stop."""
        r = self.client.post(
            "/api/jobs/compare",
            json={
                "a_bike_preset": "gsxr1000_k5",
                "b_bike_preset": "gsxr1000_k5",
                "b_mass_delta_kg": -20.0,
            },
        )
        self.assertEqual(r.status_code, 202)
        self.assertEqual(r.json()["kind"], "compare")

        final, snapshots = _poll_until_finished(self.client, r.json()["job_id"])
        self.assertEqual(final["status"], "done", final.get("error"))
        # Same payload contract as the sync /api/simulate/compare route.
        result = final["result"]
        self.assertIn("a", result)
        self.assertIn("b", result)
        self.assertIn("delta", result)
        self.assertAlmostEqual(result["a"]["et_quarter_s"], 9.9331, places=2)
        # B is 20 kg lighter → must be faster.
        self.assertEqual(result["delta"]["faster"], "B")

        progress = [s["progress"] for s in snapshots]
        self.assertTrue(all(b >= a for a, b in zip(progress, progress[1:])))
        self.assertEqual(progress[-1], 1.0)
        stages = {s["stage"] for s in snapshots}
        self.assertTrue(
            stages
            <= {"", "Simulating build A", "Simulating build B", "Building comparison"},
            stages,
        )

    def test_cancel_route_stops_running_job(self):
        # Cancel must land while the job is still active. The real
        # /api/jobs/simulate K5 sim finishes in ~0.3s, so a submit-then-cancel
        # timing race let the job reach a terminal state before the cancel POST
        # arrived (cancel-after-done is a no-op) — the old test flaked on fast
        # runners. Drive the SAME registry + cancel route with a controllable
        # long-running job so the outcome is deterministic, not timing-based.
        cancelled_cleanly = threading.Event()

        def _blocking_runner(progress):
            # Emit progress ticks forever; progress() raises JobCancelled once
            # the flag is set, unwinding the worker exactly like a real sim
            # cancels at its ~250-step ticks. The registry maps that to status
            # "cancelled"; this branch only runs if cancellation is observed.
            try:
                for i in range(1, 20_000):
                    progress(min(0.99, i / 1000.0), stage="Simulating")
                    time.sleep(0.005)
            except jobs_mod.JobCancelled:
                cancelled_cleanly.set()
                raise
            return {"unreached": True}  # pragma: no cover

        job = jobs_mod.create_job("simulate", _blocking_runner)

        # Wait until the worker is observably running (bounded poll on state,
        # never a fixed sleep) so the cancel provably hits an active job.
        for _ in range(400):
            if job.status == "running":
                break
            time.sleep(0.005)
        self.assertEqual(job.status, "running")

        rc = self.client.post(f"/api/jobs/{job.id}/cancel")
        self.assertEqual(rc.status_code, 200)
        self.assertTrue(rc.json()["cancel_requested"])

        final, _ = _poll_until_finished(self.client, job.id, timeout_s=30)
        self.assertEqual(final["status"], "cancelled")
        self.assertNotIn("result", final)
        self.assertTrue(
            cancelled_cleanly.wait(timeout=5), "worker did not unwind via JobCancelled"
        )

    def test_cancel_unknown_job_404(self):
        r = self.client.post("/api/jobs/deadbeef00000000/cancel")
        self.assertEqual(r.status_code, 404)

    def test_unknown_job_404(self):
        r = self.client.get("/api/jobs/deadbeef00000000")
        self.assertEqual(r.status_code, 404)


@unittest.skipUnless(HAS_FASTAPI, "fastapi not installed")
class TestJobOwnerScoping(unittest.TestCase):
    """Owner-scoped job polling/cancel (2026-08-21 hardening).

    Jobs created by an authenticated user must 404 for anyone else — with
    EXACTLY the unknown-job message, so the response is never an existence
    oracle on job ids — while anonymous jobs stay world-pollable (their
    random 64-bit id remains the capability token, as before)."""

    @classmethod
    def setUpClass(cls):
        from motoquant import api as api_mod

        cls.api = api_mod
        cls.client = TestClient(api_mod.app)

    def tearDown(self):
        self.api.app.dependency_overrides.pop(self.api.get_optional_user, None)

    def _login_as(self, user_id):
        """Simulate an authenticated caller via the get_optional_user seam."""
        self.api.app.dependency_overrides[self.api.get_optional_user] = lambda: {
            "id": user_id,
            "email": f"u{user_id}@example.com",
            "tier": "free",
            "is_active": 1,
        }

    def _logout(self):
        self.api.app.dependency_overrides.pop(self.api.get_optional_user, None)

    def _finished_job(self, owner_id):
        """Directly-seeded finished registry job — deterministic, no sim."""
        job = jobs_mod.create_job(
            "unittest", lambda progress: {"ok": 1}, owner_id=owner_id
        )
        deadline = time.time() + 10.0
        while time.time() < deadline:
            got = jobs_mod.get_job(job.id)
            if got is not None and got.status == "done":
                return job
            time.sleep(0.02)
        raise AssertionError("seed job did not finish")

    def test_owned_job_polled_anonymously_404s_like_unknown(self):
        job = self._finished_job(owner_id=7)
        r = self.client.get(f"/api/jobs/{job.id}")
        self.assertEqual(r.status_code, 404)
        # EXACT same body as a genuinely unknown job — no existence oracle.
        unknown = self.client.get("/api/jobs/deadbeef00000000")
        self.assertEqual(r.json(), unknown.json())

    def test_owned_job_polled_by_owner_200(self):
        job = self._finished_job(owner_id=7)
        self._login_as(7)
        r = self.client.get(f"/api/jobs/{job.id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "done")
        self.assertEqual(r.json()["result"], {"ok": 1})

    def test_owned_job_polled_by_other_user_404(self):
        job = self._finished_job(owner_id=7)
        self._login_as(8)
        r = self.client.get(f"/api/jobs/{job.id}")
        self.assertEqual(r.status_code, 404)

    def test_owned_job_cancel_scoping(self):
        def _slow_runner(progress):
            for i in range(20_000):  # ~100 s unless cancelled at a tick
                progress(min(0.99, i / 20_000.0))
                time.sleep(0.005)
            return {"unreached": True}  # pragma: no cover

        job = jobs_mod.create_job("unittest", _slow_runner, owner_id=7)
        try:
            # Anonymous cancel → 404 AND the cancel flag must not be set
            # (authorization happens before the mutation).
            r = self.client.post(f"/api/jobs/{job.id}/cancel")
            self.assertEqual(r.status_code, 404)
            self.assertFalse(jobs_mod.get_job(job.id).cancel_requested)
            # A different user → same 404, still no flag.
            self._login_as(8)
            r = self.client.post(f"/api/jobs/{job.id}/cancel")
            self.assertEqual(r.status_code, 404)
            self.assertFalse(jobs_mod.get_job(job.id).cancel_requested)
            # The owner → 200 and the flag is set.
            self._login_as(7)
            r = self.client.post(f"/api/jobs/{job.id}/cancel")
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.json()["cancel_requested"])
        finally:
            jobs_mod.cancel_job(job.id)  # belt-and-braces cleanup

    def test_anonymous_job_stays_world_pollable(self):
        job = self._finished_job(owner_id=None)
        r = self.client.get(f"/api/jobs/{job.id}")  # anonymous caller
        self.assertEqual(r.status_code, 200)
        self._login_as(7)
        r = self.client.get(f"/api/jobs/{job.id}")  # any signed-in user too
        self.assertEqual(r.status_code, 200)

    def test_creation_route_attaches_owner(self):
        self._login_as(7)
        r = self.client.post("/api/jobs/simulate", json={"bike_preset": "gsxr1000_k5"})
        self.assertEqual(r.status_code, 202)
        self.assertEqual(jobs_mod.get_job(r.json()["job_id"]).owner_id, 7)
        # Anonymous creation leaves owner None (world-pollable, as before).
        self._logout()
        r = self.client.post("/api/jobs/simulate", json={"bike_preset": "gsxr1000_k5"})
        self.assertEqual(r.status_code, 202)
        self.assertIsNone(jobs_mod.get_job(r.json()["job_id"]).owner_id)

    def test_progated_route_attaches_owner_from_require_tier(self):
        # require_tier resolves through get_optional_user, so the same
        # override flows into /api/jobs/autotune's auth dict.
        self._login_as(9)
        r = self.client.post(
            "/api/jobs/autotune",
            json={"bike_preset": "gsxr1000_k5", "gear_span": 1, "launch_steps": 2},
        )
        self.assertEqual(r.status_code, 202)
        job_id = r.json()["job_id"]
        self.assertEqual(jobs_mod.get_job(job_id).owner_id, 9)
        self.client.post(f"/api/jobs/{job_id}/cancel")  # as owner — cleanup


if __name__ == "__main__":
    unittest.main()
