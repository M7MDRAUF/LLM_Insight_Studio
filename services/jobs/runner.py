"""Lightweight in-process job runner used to execute experiments asynchronously.

We deliberately avoid Celery / RQ / Dramatiq dependencies for the local-first
demo profile. Jobs run in a worker thread (via ``anyio.to_thread.run_sync``)
and expose a co-operative cancellation flag that the worker function must
poll. A single global :class:`JobRunner` instance is shared by the application;
tests reset it via :func:`reset_job_runner`.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Event
from typing import Any
from uuid import UUID

from anyio.to_thread import run_sync as _thread_run_sync

from apps.api.core.logging import get_logger

_log = get_logger(__name__)


@dataclass
class JobHandle:
    """Metadata for an in-flight job."""

    job_id: UUID
    task: asyncio.Task[Any]
    cancel_event: Event = field(default_factory=Event)


class JobRunner:
    """Manages background jobs keyed by experiment id."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, JobHandle] = {}
        self._lock = asyncio.Lock()

    async def submit(
        self,
        job_id: UUID,
        worker: Callable[[Event], Any],
    ) -> JobHandle:
        """Schedule ``worker(cancel_event)`` to run in a worker thread."""
        async with self._lock:
            existing = self._jobs.get(job_id)
            if existing is not None and not existing.task.done():
                return existing
            cancel_event = Event()

            async def _run() -> None:
                try:
                    await _thread_run_sync(worker, cancel_event)
                except Exception:  # pragma: no cover - logged for diagnostics
                    _log.exception("job_failed job_id=%s", job_id)

            task = asyncio.create_task(_run(), name=f"job-{job_id}")
            handle = JobHandle(job_id=job_id, task=task, cancel_event=cancel_event)
            self._jobs[job_id] = handle
            task.add_done_callback(lambda _t: self._jobs.pop(job_id, None))
            return handle

    def request_cancel(self, job_id: UUID) -> bool:
        """Signal the worker to stop. Returns True if a live job was found."""
        handle = self._jobs.get(job_id)
        if handle is None:
            return False
        handle.cancel_event.set()
        return True

    async def wait(self, job_id: UUID, timeout: float | None = None) -> bool:
        """Test helper: block until the job finishes or the timeout elapses."""
        handle = self._jobs.get(job_id)
        if handle is None:
            return True
        try:
            await asyncio.wait_for(asyncio.shield(handle.task), timeout=timeout)
            return True
        except TimeoutError:
            return False

    def is_running(self, job_id: UUID) -> bool:
        handle = self._jobs.get(job_id)
        return handle is not None and not handle.task.done()

    async def shutdown(self) -> None:
        """Cancel every outstanding job (best-effort)."""
        for handle in list(self._jobs.values()):
            handle.cancel_event.set()
            handle.task.cancel()
        if self._jobs:
            await asyncio.gather(*(h.task for h in self._jobs.values()), return_exceptions=True)
        self._jobs.clear()


_RUNNER: JobRunner | None = None


def get_job_runner() -> JobRunner:
    """Return the process-wide :class:`JobRunner` instance."""
    global _RUNNER  # noqa: PLW0603 - intentional module-level singleton
    if _RUNNER is None:
        _RUNNER = JobRunner()
    return _RUNNER


def reset_job_runner() -> None:
    """Test helper — drop any cached runner so a fresh one is created."""
    global _RUNNER  # noqa: PLW0603
    _RUNNER = None
