"""Experiment orchestrator backed by the SQLite-persisted experiment store.

The service exposes a clean request-scoped API (create / get / cancel / list)
that operates on :class:`apps.api.repositories.experiments.ExperimentRepository`
and a worker function (:func:`run_experiment`) that the in-process job runner
invokes inside a dedicated worker thread. The worker opens its own DB session,
polls a cancellation flag between lanes and persists results atomically.
"""

from __future__ import annotations

from datetime import UTC, datetime
from threading import Event
from typing import Any
from uuid import UUID

from sqlmodel import Session

from apps.api.core.db import session_scope
from apps.api.core.errors import ExperimentExecutionError
from apps.api.core.logging import get_logger
from apps.api.core.settings import Settings, get_settings
from apps.api.repositories.experiments import ExperimentRepository
from apps.api.repositories.models import ExperimentRow
from apps.api.schemas.datasets import TaskLane
from apps.api.schemas.experiments import (
    ArtifactRef,
    ExperimentCreateRequest,
    ExperimentResult,
    ExperimentStatus,
    ExperimentStatusResponse,
    ExperimentSummary,
    MetricsByLane,
    SamplingConfig,
)
from services.artifacts.artifact_service import ArtifactService
from services.data.dataset_service import DatasetService
from services.evaluation.evaluation_service import EvaluationService
from services.ml.defaults import default_model_for
from services.ml.model_service import ModelService
from services.ml.providers import build_provider

_log = get_logger(__name__)


class ExperimentService:
    """Request-scoped experiment registrar / inspector."""

    def __init__(
        self,
        session: Session,
        repository: ExperimentRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or ExperimentRepository(session)

    # ---------------------- API surface ---------------------- #

    def create(self, request: ExperimentCreateRequest) -> ExperimentStatusResponse:
        # Autofill missing models with sensible defaults so callers can omit
        # the models dict entirely (or partially) and still get a valid run.
        autofilled = {
            lane: request.models.get(lane, default_model_for(lane)) for lane in request.task_lanes
        }
        row = ExperimentRow(
            dataset_manifest_id=request.dataset_manifest_id,
            task_lanes_json=[lane.value for lane in request.task_lanes],
            models_json={lane.value: model for lane, model in autofilled.items()},
            params_json={
                "sampling": request.sampling.model_dump(mode="json"),
                "generation": request.generation.model_dump(mode="json"),
                "report": request.report.model_dump(mode="json"),
            },
            status=ExperimentStatus.QUEUED.value,
            progress=0.0,
            message="queued",
            notes=request.notes,
        )
        self.repository.create(row)
        return ExperimentStatusResponse(
            experiment_id=row.id,
            status=ExperimentStatus.QUEUED,
            progress=0.0,
            message="queued",
        )

    def get_status(self, experiment_id: UUID) -> ExperimentStatusResponse:
        row = self._require(experiment_id)
        # Stale-heartbeat watchdog: if the worker silently died, surface a
        # FAILED status instead of leaving the row pinned at RUNNING forever.
        if row.status == ExperimentStatus.RUNNING.value and row.last_heartbeat is not None:
            from apps.api.core.settings import get_settings as _get_settings

            timeout_s = _get_settings().experiment_timeout_s
            # SQLite stores datetimes naively; normalise to UTC before comparing.
            heartbeat = row.last_heartbeat
            if heartbeat.tzinfo is None:
                heartbeat = heartbeat.replace(tzinfo=UTC)
            age = (datetime.now(tz=UTC) - heartbeat).total_seconds()
            if age > timeout_s:
                self.repository.update_status(
                    experiment_id,
                    status=ExperimentStatus.FAILED.value,
                    message="watchdog: heartbeat timeout",
                    error=f"no heartbeat for {age:.0f}s (limit {timeout_s}s)",
                    finished_at=datetime.now(tz=UTC),
                )
                row = self._require(experiment_id)
        return ExperimentStatusResponse(
            experiment_id=row.id,
            status=ExperimentStatus(row.status),
            progress=row.progress,
            message=row.message,
        )

    def get_result(self, experiment_id: UUID) -> ExperimentResult:
        row = self._require(experiment_id)
        return _row_to_result(row)

    def list_summaries(self) -> list[ExperimentSummary]:
        rows = self.repository.list_rows(limit=200)
        return [
            ExperimentSummary(
                id=row.id,
                dataset_manifest_id=row.dataset_manifest_id,
                task_lanes=[TaskLane(t) for t in row.task_lanes_json],
                status=ExperimentStatus(row.status),
                created_at=row.created_at.isoformat(),
            )
            for row in rows
        ]

    def cancel(self, experiment_id: UUID) -> ExperimentStatusResponse:
        row = self._require(experiment_id)
        terminal = {ExperimentStatus.COMPLETED.value, ExperimentStatus.FAILED.value}
        if row.status in terminal:
            return ExperimentStatusResponse(
                experiment_id=row.id,
                status=ExperimentStatus(row.status),
                progress=row.progress,
                message=row.message,
            )
        self.repository.request_cancel(experiment_id)
        # If the worker is still queued (never started) flip status now so callers
        # see immediate feedback. The running worker will short-circuit on its
        # next poll otherwise.
        if row.status == ExperimentStatus.QUEUED.value:
            self.repository.update_status(
                experiment_id,
                status=ExperimentStatus.CANCELLED.value,
                message="cancelled before start",
                finished_at=datetime.now(tz=UTC),
            )
        return self.get_status(experiment_id)

    # ---------------------- helpers ---------------------- #

    def _require(self, experiment_id: UUID) -> ExperimentRow:
        row = self.repository.get(experiment_id)
        if row is None:
            raise ExperimentExecutionError(
                f"Unknown experiment: {experiment_id}",
                {"experiment_id": str(experiment_id)},
            )
        return row


# ---------------------------------------------------------------------------
# Worker — runs in a background thread spawned by the JobRunner.
# ---------------------------------------------------------------------------


def run_experiment(  # noqa: PLR0915 - end-to-end orchestration is intentionally linear
    experiment_id: UUID,
    cancel_event: Event,
    settings: Settings | None = None,
) -> ExperimentResult:
    """Execute the experiment end-to-end. Designed to run in a worker thread."""
    cfg = settings or get_settings()
    started = datetime.now(tz=UTC)
    artifact_service = ArtifactService(settings=cfg)
    model_service = ModelService(provider=build_provider(cfg.inference_provider, settings=cfg))
    evaluation_service = EvaluationService()

    try:
        with session_scope() as session:
            repo = ExperimentRepository(session)
            row = repo.get(experiment_id)
            if row is None:
                raise ExperimentExecutionError(
                    f"Unknown experiment: {experiment_id}",
                    {"experiment_id": str(experiment_id)},
                )
            if row.cancel_requested or cancel_event.is_set():
                repo.update_status(
                    experiment_id,
                    status=ExperimentStatus.CANCELLED.value,
                    message="cancelled",
                    finished_at=datetime.now(tz=UTC),
                )
                return _row_to_result(row)

            repo.update_status(
                experiment_id,
                status=ExperimentStatus.RUNNING.value,
                progress=0.05,
                message="loading dataset",
                started_at=started,
            )

            dataset_service = DatasetService(session=session, settings=cfg)
            try:
                records = dataset_service.get_records(row.dataset_manifest_id)
            except Exception as exc:
                raise ExperimentExecutionError(
                    f"Failed to load dataset records: {exc}",
                    {"dataset_manifest_id": str(row.dataset_manifest_id)},
                ) from exc
            sampling = SamplingConfig.model_validate(row.params_json.get("sampling", {}))
            available = len(records)
            if sampling.max_rows > available:
                _log.warning(
                    "sampling_downcast experiment_id=%s requested=%d available=%d",
                    experiment_id,
                    sampling.max_rows,
                    available,
                )
            records = records[: sampling.max_rows]
            if not records:
                raise ExperimentExecutionError(
                    "Dataset has no usable records for this experiment",
                    {"experiment_id": str(experiment_id)},
                )

            lanes = [TaskLane(t) for t in row.task_lanes_json]
            model_overrides: dict[TaskLane, str] = {
                TaskLane(k): v
                for k, v in row.models_json.items()
                if k in {lane.value for lane in TaskLane}
            }

            best_by_task: dict[str, str] = {}
            metrics_payload = MetricsByLane()

            for idx, lane in enumerate(lanes, start=1):
                if cancel_event.is_set() or repo.is_cancel_requested(experiment_id):
                    repo.update_status(
                        experiment_id,
                        status=ExperimentStatus.CANCELLED.value,
                        message=f"cancelled before {lane.value}",
                        finished_at=datetime.now(tz=UTC),
                    )
                    refreshed = repo.get(experiment_id)
                    return _row_to_result(refreshed) if refreshed else _empty_result(experiment_id)

                model_id = model_overrides.get(lane) or default_model_for(lane)
                repo.update_status(
                    experiment_id,
                    status=ExperimentStatus.RUNNING.value,
                    # Progress reflects lanes *completed* so far, not the one starting now.
                    progress=(idx - 1) / max(1, len(lanes)),
                    message=f"running {lane.value}",
                )
                repo.touch_heartbeat(experiment_id)
                metrics_for_lane = _execute_lane(
                    lane, model_id, records, model_service, evaluation_service
                )
                setattr(metrics_payload, lane.value, metrics_for_lane)
                best_by_task[lane.value] = model_id

            summary = {
                "dataset_manifest_id": str(row.dataset_manifest_id),
                "rows_evaluated": len(records),
                "best_model_by_task": best_by_task,
            }
            artifact_path = artifact_service.save_experiment(
                experiment_id,
                {
                    "experiment_id": str(experiment_id),
                    "summary": summary,
                    "metrics": metrics_payload.model_dump(),
                    "status": ExperimentStatus.COMPLETED.value,
                    "created_at": row.created_at.isoformat(),
                },
            )
            artifacts = [
                {
                    "type": "experiment_json",
                    "path": str(artifact_path),
                    "bytes": artifact_path.stat().st_size,
                }
            ]
            repo.attach_results(
                experiment_id,
                summary=summary,
                metrics=metrics_payload.model_dump(),
                artifacts=artifacts,
            )
            repo.update_status(
                experiment_id,
                status=ExperimentStatus.COMPLETED.value,
                progress=1.0,
                message="completed",
                finished_at=datetime.now(tz=UTC),
            )
            refreshed = repo.get(experiment_id)
            return _row_to_result(refreshed) if refreshed else _empty_result(experiment_id)
    except ExperimentExecutionError as exc:
        _persist_failure(experiment_id, exc.message)
        _log.exception("experiment_failed experiment_id=%s", experiment_id)
        return _empty_result(experiment_id, status=ExperimentStatus.FAILED, error=exc.message)
    except Exception as exc:  # pragma: no cover - safety net
        _persist_failure(experiment_id, str(exc))
        _log.exception("experiment_failed_unexpected experiment_id=%s", experiment_id)
        return _empty_result(experiment_id, status=ExperimentStatus.FAILED, error=str(exc))


def _persist_failure(experiment_id: UUID, message: str) -> None:
    try:
        with session_scope() as session:
            ExperimentRepository(session).update_status(
                experiment_id,
                status=ExperimentStatus.FAILED.value,
                message="execution error",
                error=message,
                finished_at=datetime.now(tz=UTC),
            )
    except Exception:  # pragma: no cover - defensive
        _log.exception("failed_to_persist_failure experiment_id=%s", experiment_id)


def _execute_lane(
    lane: TaskLane,
    model_id: str,
    records: Any,
    model_service: ModelService,
    evaluation_service: EvaluationService,
) -> dict[str, Any]:
    if lane is TaskLane.CLASSIFICATION:
        texts = [r.text for r in records]
        labels = [r.label for r in records if r.label is not None]
        result = model_service.run_classification(texts, model_id)
        preds = [o.label for o in result.outputs]
        metrics: dict[str, Any]
        if labels and len(labels) == len(preds):
            metrics = dict(evaluation_service.classification(labels, preds))
        else:
            metrics = {"coverage": round(len(preds) / max(1, len(texts)), 6)}
        metrics["latency_ms"] = round(result.latency_ms, 3)
        metrics["model_id"] = model_id
        return metrics

    if lane is TaskLane.SUMMARIZATION:
        texts = [r.text for r in records]
        result = model_service.run_summarization(texts, model_id)
        summaries = [o.summary for o in result.outputs]
        refs = [r.text for r in records]
        metrics = dict(evaluation_service.summarization(refs, summaries))
        metrics["latency_ms"] = round(result.latency_ms, 3)
        metrics["model_id"] = model_id
        return metrics

    if lane is TaskLane.QA:
        qa_records = [r for r in records if r.question and r.context]
        if not qa_records:
            return {
                "exact_match": 0.0,
                "f1": 0.0,
                "evidence_hit_rate": 0.0,
                "support": 0,
                "model_id": model_id,
                "latency_ms": 0.0,
            }
        questions = [r.question or "" for r in qa_records]
        contexts = [r.context or "" for r in qa_records]
        truths = [r.answer or "" for r in qa_records]
        result = model_service.run_extractive_qa(questions, contexts, model_id)
        preds = [o.answer for o in result.outputs]
        metrics = dict(evaluation_service.qa(preds, truths, contexts))
        metrics["latency_ms"] = round(result.latency_ms, 3)
        metrics["model_id"] = model_id
        return metrics

    # INSTRUCT — qualitative only
    prompts = [r.text for r in records]
    result = model_service.run_instruct(prompts, model_id)
    return {
        "latency_ms": round(result.latency_ms, 3),
        "support": len(prompts),
        "model_id": model_id,
    }


def _row_to_result(row: ExperimentRow) -> ExperimentResult:
    metrics = MetricsByLane.model_validate(row.metrics_json or {})
    artifacts = [ArtifactRef.model_validate(a) for a in (row.artifacts_json or [])]
    return ExperimentResult(
        experiment_id=row.id,
        status=ExperimentStatus(row.status),
        summary=row.summary_json or {},
        metrics=metrics,
        artifacts=artifacts,
        error=row.error,
    )


def _empty_result(
    experiment_id: UUID,
    *,
    status: ExperimentStatus = ExperimentStatus.FAILED,
    error: str | None = None,
) -> ExperimentResult:
    return ExperimentResult(
        experiment_id=experiment_id,
        status=status,
        summary={},
        metrics=MetricsByLane(),
        artifacts=[],
        error=error,
    )


def reset_experiment_store() -> None:
    """Test helper retained for backwards compatibility (no-op now)."""
    return None
