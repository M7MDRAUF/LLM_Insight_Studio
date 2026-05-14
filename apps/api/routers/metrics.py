"""Lightweight metrics endpoint (Prometheus-style text exposition)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func
from sqlmodel import Session, select

from apps.api.core.db import get_session
from apps.api.repositories.datasets import DatasetRepository
from apps.api.repositories.models import ExperimentRow
from apps.api.schemas.experiments import ExperimentStatus

router = APIRouter(tags=["metrics"])


@router.get("/metrics", include_in_schema=False)
def metrics(session: Session = Depends(get_session)) -> Response:
    datasets = DatasetRepository(session).count()

    # Single GROUP BY query — O(1) regardless of table size.
    stmt = select(ExperimentRow.status, func.count().label("cnt")).group_by(ExperimentRow.status)
    rows = session.exec(stmt).all()
    by_status: dict[str, int] = {s.value: 0 for s in ExperimentStatus}
    for status_val, cnt in rows:
        by_status[status_val] = cnt
    in_flight = by_status.get(ExperimentStatus.RUNNING.value, 0)

    lines: list[str] = [
        "# HELP studio_datasets_total Number of dataset manifests persisted.",
        "# TYPE studio_datasets_total gauge",
        f"studio_datasets_total {datasets}",
        "# HELP studio_experiments_total Total experiments grouped by status.",
        "# TYPE studio_experiments_total gauge",
    ]
    for status_name, count in by_status.items():
        lines.append(f'studio_experiments_total{{status="{status_name}"}} {count}')
    lines += [
        "# HELP studio_jobs_in_flight Currently-running experiment workers.",
        "# TYPE studio_jobs_in_flight gauge",
        f"studio_jobs_in_flight {in_flight}",
        "",
    ]
    return Response(content="\n".join(lines), media_type="text/plain; version=0.0.4")
