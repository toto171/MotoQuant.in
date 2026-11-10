"""
In-memory background-job registry for the website's real progress bars.

``POST /api/jobs/*`` creates a Job and runs the supplied callable on a
daemon thread; the callable receives a ``progress(frac, stage=None)``
callback and returns a JSON-ready dict. ``GET /api/jobs/{id}`` polls it.

Deliberately simple — single-process registry (matches the single-instance
Render deployment), bounded size, TTL eviction, no persistence. If the
service restarts mid-job the client gets a 404 and re-runs; the synchronous
routes remain available as a fallback for older clients / the desktop app.
"""

from __future__ import annotations

import json
import math
import threading
import time
import uuid
import zlib
from collections.abc import Callable
from typing import Any

JOB_TTL_S = 900.0  # evict finished jobs this long after their last update
MAX_JOBS = 200  # hard cap on registry size (memory bound)
MAX_RUNNING = 6  # concurrent-job guard (free-tier CPU)
# A worker running past this is treated as hung (wedged network call, runaway
# loop). We can't kill a daemon thread, but we stop counting it toward
# MAX_RUNNING and request its cancellation so it can't permanently starve the
# registry. Deliberately far above any legitimate job (chat ≤ ~8×30s LLM
# calls, optimizer a few minutes) — this only ever trips a true wedge.
MAX_JOB_RUNTIME_S = 1800.0
# Finished results are retained as zlib-compressed JSON, and the registry keeps
# the compressed total under this budget by evicting the oldest finished jobs
# first (a running job is never evicted). Without it 200 retained top-speed
# results (~3 MB each as Python objects) approach the 512 MB instance limit.
MAX_RESULT_BYTES_TOTAL = 48 * 1024 * 1024
_RESULT_ZLIB_LEVEL = 3
_TERMINAL = ("done", "error", "cancelled")


class JobCapacityError(RuntimeError):
    """Raised when too many jobs are already queued/running."""


class JobCancelled(BaseException):
    """
    Raised inside a worker thread when its job has been cancelled.

    Deliberately a ``BaseException``: the simulation / analysis layers (and
    the API impls) wrap work in ``except Exception`` blocks — including the
    exception-proofed progress hooks — and none of them may swallow a
    cancellation. Only the job runner itself catches this.
    """


class Job:
    """One background simulation/optimisation run."""

    __slots__ = (
        "id",
        "kind",
        "status",
        "progress",
        "stage",
        "_result_z",
        "error",
        "created_at",
        "updated_at",
        "cancel_requested",
    )

    def __init__(self, kind: str):
        self.id = uuid.uuid4().hex[:16]
        self.kind = kind
        self.status = "queued"  # queued | running | done | error
        self.progress = 0.0  # 0..1, monotonic non-decreasing
        self.stage = ""
        self._result_z: bytes | None = None  # zlib(JSON) of the finished result
        self.error: str | None = None
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.cancel_requested = False

    @property
    def result(self) -> Any | None:
        """The finished result, decoded from its compressed JSON form."""
        raw = self.result_json()
        return None if raw is None else json.loads(raw)

    @result.setter
    def result(self, value: Any | None) -> None:
        self._result_z = (
            None
            if value is None
            else zlib.compress(_dumps(value).encode("utf-8"), _RESULT_ZLIB_LEVEL)
        )

    @property
    def result_bytes(self) -> int:
        """Retained size of the result (compressed bytes)."""
        return len(self._result_z) if self._result_z is not None else 0

    def result_json(self) -> bytes | None:
        """The result as raw JSON bytes (lets the route splice it into a
        response without a decode/encode round trip)."""
        z = self._result_z
        return None if z is None else zlib.decompress(z)


def _json_default(obj: Any) -> Any:
    """Serialise numpy scalars/arrays the way FastAPI's encoder would."""
    if hasattr(obj, "tolist"):
        return obj.tolist()
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"{type(obj).__name__} is not JSON serialisable")


def _finite(obj: Any) -> Any:
    """Copy of *obj* with NaN/Infinity replaced by None (valid JSON)."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _finite(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_finite(v) for v in obj]
    return obj


def _dumps(value: Any) -> str:
    """Strict-JSON encode a job result (never emits NaN/Infinity literals)."""
    try:
        return json.dumps(
            value, default=_json_default, allow_nan=False, separators=(",", ":")
        )
    except ValueError:  # non-finite float somewhere in the payload
        return json.dumps(
            _finite(json.loads(json.dumps(value, default=_json_default))),
            default=_json_default,
            separators=(",", ":"),
        )


_JOBS: dict[str, Job] = {}
_LOCK = threading.Lock()


def _is_hung(job: Job, now: float) -> bool:
    """A running job that has blown the runtime deadline — a wedged worker."""
    return job.status == "running" and now - job.created_at > MAX_JOB_RUNTIME_S


def _evict_locked(now: float) -> None:
    """Drop expired finished jobs + oldest overflow. Caller holds ``_LOCK``."""
    # Break wedges: a worker past the deadline is asked to cancel (it unwinds
    # at its next progress tick) and, more importantly, no longer counts toward
    # MAX_RUNNING or blocks overflow eviction below.
    for job in _JOBS.values():
        if _is_hung(job, now):
            job.cancel_requested = True
    expired = [
        jid
        for jid, j in _JOBS.items()
        if j.status in _TERMINAL and now - j.updated_at > JOB_TTL_S
    ]
    for jid in expired:
        del _JOBS[jid]
    if len(_JOBS) > MAX_JOBS:
        # Finished/cancelled jobs (and hung ones past the deadline) are the
        # eviction candidates: evicting a healthy queued/running job would
        # orphan its worker and 404 the client's poll ("Progress lost").
        overflow = sorted(
            (
                (jid, j)
                for jid, j in _JOBS.items()
                if j.status not in ("queued", "running") or _is_hung(j, now)
            ),
            key=lambda kv: kv[1].created_at,
        )
        for jid, _ in overflow[: len(_JOBS) - MAX_JOBS]:
            del _JOBS[jid]
    # Byte budget: retained results are bounded by size, not just job count.
    total = sum(j.result_bytes for j in _JOBS.values())
    if total > MAX_RESULT_BYTES_TOTAL:
        finished = sorted(
            ((jid, j) for jid, j in _JOBS.items() if j.status in _TERMINAL),
            key=lambda kv: kv[1].updated_at,
        )
        for jid, j in finished:
            if total <= MAX_RESULT_BYTES_TOTAL:
                break
            total -= j.result_bytes
            del _JOBS[jid]


def create_job(kind: str, runner: Callable[[Callable], Any]) -> Job:
    """
    Start ``runner(progress)`` on a daemon thread and return its Job.

    ``runner`` receives ``progress(frac: float, stage: str | None = None)``
    and must return a JSON-serialisable result. Progress is clamped to
    [0, 1] and made monotonic so the client bar can never run backwards.

    Raises ``JobCapacityError`` when ``MAX_RUNNING`` jobs are already active.
    """
    now = time.time()
    with _LOCK:
        _evict_locked(now)
        n_active = sum(
            1
            for j in _JOBS.values()
            if j.status in ("queued", "running") and not _is_hung(j, now)
        )
        if n_active >= MAX_RUNNING:
            raise JobCapacityError(
                f"Too many simulations running ({n_active}); try again in a moment"
            )
        job = Job(kind)
        _JOBS[job.id] = job

    def _progress(frac: float, stage: str | None = None) -> None:
        if job.cancel_requested:
            # Cooperative cancel: unwind the worker at this tick (every ~250
            # RK4 steps / every sweep sim / every scored candidate).
            raise JobCancelled
        try:
            f = float(frac)
        except (TypeError, ValueError):
            return
        job.progress = min(1.0, max(job.progress, f))
        if stage:
            job.stage = str(stage)
        job.updated_at = time.time()

    def _run() -> None:
        job.status = "running"
        job.updated_at = time.time()
        try:
            job.result = runner(_progress)
            if job.cancel_requested:  # cancelled between last tick and return
                job.result = None
                job.status = "cancelled"
                job.stage = "Stopped"
            else:
                job.progress = 1.0
                job.status = "done"
        except JobCancelled:
            job.result = None
            job.status = "cancelled"
            job.stage = "Stopped"
        except Exception as exc:  # surfaced to the client via GET /api/jobs/{id}
            detail = getattr(exc, "detail", None)  # fastapi.HTTPException payload
            msg = str(detail) if detail else f"{type(exc).__name__}: {exc}"
            job.error = msg[:500]  # bound the payload — config errors can be huge
            job.status = "error"
        finally:
            job.updated_at = time.time()
            with _LOCK:  # keep retained result bytes under budget
                _evict_locked(job.updated_at)

    threading.Thread(target=_run, name=f"job-{kind}-{job.id}", daemon=True).start()
    return job


def cancel_job(job_id: str) -> Job | None:
    """
    Request cooperative cancellation of a job (None if unknown/evicted).

    Terminal jobs (done / error / cancelled) are left untouched. For active
    jobs the flag is set and the worker unwinds at its next progress tick,
    freeing its MAX_RUNNING slot within a fraction of a second.
    """
    with _LOCK:
        job = _JOBS.get(job_id)
        if job is not None and job.status in ("queued", "running"):
            job.cancel_requested = True
            job.updated_at = time.time()
        return job


def get_job(job_id: str) -> Job | None:
    """Look up a job by id (None if unknown or already evicted)."""
    now = time.time()
    with _LOCK:
        _evict_locked(now)
        return _JOBS.get(job_id)
