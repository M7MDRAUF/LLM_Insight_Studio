"""Dataset manifest repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from apps.api.repositories.models import DatasetManifestRow


class DatasetRepository:
    """CRUD operations for dataset manifests."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, row: DatasetManifestRow) -> DatasetManifestRow:
        self.session.add(row)
        self.session.flush()
        self.session.refresh(row)
        return row

    def get(self, manifest_id: UUID) -> DatasetManifestRow | None:
        return self.session.get(DatasetManifestRow, manifest_id)

    def list(self, limit: int = 50, offset: int = 0) -> list[DatasetManifestRow]:
        stmt = (
            select(DatasetManifestRow)
            .order_by(DatasetManifestRow.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.exec(stmt))

    def count(self) -> int:
        result = self.session.exec(select(func.count()).select_from(DatasetManifestRow))
        return int(result.one() or 0)
