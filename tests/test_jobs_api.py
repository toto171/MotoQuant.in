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
        self.assertAlmostEqual(et_plain, 10.0334, places=3)

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
        self.assertAlmostEqual(final["result"]["et_quarter_s"], 10.0334, places=2)
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
        self.assertAlmostEqual(result["a"]["et_quarter_s"], 10.0334, places=2)
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


if __name__ == "__main__":
    unittest.main()
