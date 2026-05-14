"""Comparison routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.core.deps import get_experiment_service
from apps.api.schemas.compare import CompareRequest, CompareResponse, CompareRow
from apps.api.schemas.datasets import TaskLane
from apps.api.schemas.experiments import ExperimentStatus
from services.experiments.experiment_service import ExperimentService
from services.ml.defaults import BEST_METRIC_BY_LANE

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
def compare_experiments(
    payload: CompareRequest,
    service: ExperimentService = Depends(get_experiment_service),
) -> CompareResponse:
    rows: list[CompareRow] = []
    best_by_task: dict[TaskLane, tuple[str, float]] = {}

    for exp_id in payload.experiment_ids:
        result = service.get_result(exp_id)
        # Skip non-completed experiments rather than failing the whole compare —
        # callers can still surface them in the UI via the missing rows.
        if result.status is not ExperimentStatus.COMPLETED:
            continue
        for lane in TaskLane:
            metrics = getattr(result.metrics, lane.value)
            if not metrics:
                continue
            model_id = str(metrics.get("model_id", ""))
            latency = float(metrics.get("latency_ms", 0.0) or 0.0)
            key_metric = BEST_METRIC_BY_LANE[lane]
            score_val = metrics.get(key_metric)
            score = float(score_val) if isinstance(score_val, (int, float)) else 0.0
            numeric_metrics = {
                k: float(v)
                for k, v in metrics.items()
                if isinstance(v, (int, float)) and k != "latency_ms"
            }
            rows.append(
                CompareRow(
                    model_id=model_id,
                    task=lane,
                    metrics=numeric_metrics,
                    latency_ms=latency,
                )
            )
            current_best = best_by_task.get(lane)
            if current_best is None or score > current_best[1]:
                best_by_task[lane] = (model_id, score)

    return CompareResponse(
        rows=rows,
        best_by_task={lane: winner for lane, (winner, _) in best_by_task.items()},
    )
