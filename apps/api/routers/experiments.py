"""Experiment routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from apps.api.core.deps import get_experiment_service, get_job_runner_dep
from apps.api.core.settings import get_settings
from apps.api.schemas.experiments import (
    ExperimentCreateRequest,
    ExperimentResult,
    ExperimentStatusResponse,
    ExperimentSummary,
)
from services.experiments.experiment_service import ExperimentService, run_experiment
from services.jobs import JobRunner

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentStatusResponse, status_code=202)
async def create_experiment(
    payload: ExperimentCreateRequest,
    service: ExperimentService = Depends(get_experiment_service),
    runner: JobRunner = Depends(get_job_runner_dep),
) -> ExperimentStatusResponse:
    status = service.create(payload)
    experiment_id = status.experiment_id

    def _worker(cancel_event: object) -> None:
        # ``cancel_event`` is threading.Event; typed loosely to avoid coupling.
        from threading import Event

        if not isinstance(cancel_event, Event):
            raise TypeError("cancel_event must be a threading.Event")
        run_experiment(experiment_id, cancel_event)

    await runner.submit(experiment_id, _worker)
    return status


@router.get("", response_model=list[ExperimentSummary])
def list_experiments(
    service: ExperimentService = Depends(get_experiment_service),
) -> list[ExperimentSummary]:
    return service.list_summaries()


@router.get("/{experiment_id}/status", response_model=ExperimentStatusResponse)
def get_experiment_status(
    experiment_id: UUID,
    service: ExperimentService = Depends(get_experiment_service),
) -> ExperimentStatusResponse:
    return service.get_status(experiment_id)


@router.get("/{experiment_id}/result", response_model=ExperimentResult)
async def get_experiment_result(
    experiment_id: UUID,
    service: ExperimentService = Depends(get_experiment_service),
    runner: JobRunner = Depends(get_job_runner_dep),
) -> ExperimentResult:
    # Wait for the worker to finish so polling-style clients (and tests) can see
    # a terminal state without manual sleeps. Bounded by the experiment timeout so
    # a stalled job cannot hold the request open indefinitely.
    if runner.is_running(experiment_id):
        timeout_s = get_settings().experiment_timeout_s
        finished = await runner.wait(experiment_id, timeout=float(timeout_s))
        if not finished:
            return JSONResponse(
                status_code=503,
                content={"detail": "Experiment still running; retry after it completes."},
            )  # type: ignore[return-value]
    return service.get_result(experiment_id)


@router.post("/{experiment_id}/cancel", response_model=ExperimentStatusResponse)
def cancel_experiment(
    experiment_id: UUID,
    service: ExperimentService = Depends(get_experiment_service),
    runner: JobRunner = Depends(get_job_runner_dep),
) -> ExperimentStatusResponse:
    from apps.api.schemas.experiments import ExperimentStatus

    # Guard: no-op if already in a terminal state (including CANCELLED)
    terminal = {
        ExperimentStatus.COMPLETED.value,
        ExperimentStatus.FAILED.value,
        ExperimentStatus.CANCELLED.value,
    }
    current = service.get_status(experiment_id)
    if current.status.value in terminal:
        return current
    response = service.cancel(experiment_id)
    runner.request_cancel(experiment_id)
    return response
