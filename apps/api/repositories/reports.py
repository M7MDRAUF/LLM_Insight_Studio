"""Report repository."""

from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from apps.api.repositories.models import ReportRow


class ReportRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, row: ReportRow) -> ReportRow:
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def get(self, report_id: UUID) -> ReportRow | None:
        return self.session.get(ReportRow, report_id)

    def list_for_experiment(self, experiment_id: UUID) -> list[ReportRow]:
        stmt = select(ReportRow).where(ReportRow.experiment_id == experiment_id)
        return list(self.session.exec(stmt))
