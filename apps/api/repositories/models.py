"""SQLModel ORM entities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class DatasetManifestRow(SQLModel, table=True):
    __tablename__: ClassVar[str] = "dataset_manifests"  # pyright: ignore[reportIncompatibleVariableOverride]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    dataset_id: str = Field(index=True, max_length=250)
    source: str = Field(max_length=32)
    task_lanes_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    splits_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    schema_mapping_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    row_count: int = 0
    license: str | None = Field(default=None, max_length=250)
    snapshot: str | None = Field(default=None, max_length=250)
    preview_json: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow)


class ExperimentRow(SQLModel, table=True):
    __tablename__: ClassVar[str] = "experiments"  # pyright: ignore[reportIncompatibleVariableOverride]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    dataset_manifest_id: UUID = Field(index=True, foreign_key="dataset_manifests.id")
    task_lanes_json: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    models_json: dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    params_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    status: str = Field(default="queued", max_length=32, index=True)
    progress: float = 0.0
    message: str | None = Field(default=None, max_length=1_000)
    metrics_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    summary_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    artifacts_json: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    error: str | None = Field(default=None, max_length=2_000)
    notes: str | None = Field(default=None, max_length=2_000)
    cancel_requested: bool = Field(default=False)
    started_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    last_heartbeat: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class ReportRow(SQLModel, table=True):
    __tablename__: ClassVar[str] = "reports"  # pyright: ignore[reportIncompatibleVariableOverride]

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    experiment_id: UUID = Field(index=True, foreign_key="experiments.id")
    path: str = Field(max_length=500)
    reference_count: int = 0
    references_json: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_utcnow)
