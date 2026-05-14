"""Experiment repository."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from apps.api.repositories.models import ExperimentRow


class ExperimentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, row: ExperimentRow) -> ExperimentRow:
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def get(self, experiment_id: UUID) -> ExperimentRow | None:
        return self.session.get(ExperimentRow, experiment_id)

    def list_rows(self, limit: int = 50, offset: int = 0) -> list[ExperimentRow]:
        stmt = (
            select(ExperimentRow)
            .order_by(ExperimentRow.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.exec(stmt))

    def count(self) -> int:
        result = self.session.exec(select(func.count()).select_from(ExperimentRow))
        return int(result.one() or 0)

    def update_status(
        self,
        experiment_id: UUID,
        *,
        status: str,
        progress: float | None = None,
        message: str | None = None,
        error: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> ExperimentRow | None:
        row = self.get(experiment_id)
        if row is None:
            return None
        row.status = status
        if progress is not None:
            row.progress = progress
        if message is not None:
            row.message = message
        if error is not None:
            row.error = error
        if started_at is not None:
            row.started_at = started_at
        if finished_at is not None:
            row.finished_at = finished_at
        row.updated_at = datetime.now(tz=UTC)
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def attach_results(
        self,
        experiment_id: UUID,
        *,
        summary: dict[str, Any],
        metrics: dict[str, Any],
        artifacts: list[dict[str, Any]],
    ) -> ExperimentRow | None:
        row = self.get(experiment_id)
        if row is None:
            return None
        row.summary_json = summary
        row.metrics_json = metrics
        row.artifacts_json = artifacts
        row.updated_at = datetime.now(tz=UTC)
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def request_cancel(self, experiment_id: UUID) -> ExperimentRow | None:
        row = self.get(experiment_id)
        if row is None:
            return None
        row.cancel_requested = True
        row.updated_at = datetime.now(tz=UTC)
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def is_cancel_requested(self, experiment_id: UUID) -> bool:
        row = self.get(experiment_id)
        return bool(row and row.cancel_requested)

    def touch_heartbeat(self, experiment_id: UUID) -> None:
        row = self.get(experiment_id)
        if row is None:
            return
        row.last_heartbeat = datetime.now(tz=UTC)
        self.session.add(row)
        self.session.flush()
