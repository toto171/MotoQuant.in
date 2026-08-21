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

import threading
import time
import uuid
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
        "result",
        "error",
        "created_at",
        "updated_at",
        "cancel_requested",
        "owner_id",
    )

    def __init__(self, kind: str, owner_id: int | None = None):
        self.id = uuid.uuid4().hex[:16]
        self.kind = kind
        self.status = "queued"  # queued | running | done | error
        self.progress = 0.0  # 0..1, monotonic non-decreasing
        self.stage = ""
        self.result: Any | None = None
        self.error: str | None = None
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.cancel_requested = False
        # Authenticated creator's user id, or None for anonymous jobs. Owned
        # jobs are only pollable/cancellable by their owner (api.py enforces
        # it); anonymous jobs stay world-pollable — the random 64-bit id is
        # their only capability token, exactly as before owner-scoping.
        self.owner_id = owner_id


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
        if j.status in ("done", "error") and now - j.updated_at > JOB_TTL_S
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


def create_job(
    kind: str, runner: Callable[[Callable], Any], owner_id: int | None = None
) -> Job:
    """
    Start ``runner(progress)`` on a daemon thread and return its Job.

    ``runner`` receives ``progress(frac: float, stage: str | None = None)``
    and must return a JSON-serialisable result. Progress is clamped to
    [0, 1] and made monotonic so the client bar can never run backwards.

    ``owner_id`` scopes the job to an authenticated creator (see ``Job``).

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
        job = Job(kind, owner_id=owner_id)
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
