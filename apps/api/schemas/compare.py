"""Model comparison schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from apps.api.schemas.common import APIModel
from apps.api.schemas.datasets import TaskLane


class CompareRow(APIModel):
    model_id: str
    task: TaskLane
    metrics: dict[str, float] = Field(default_factory=dict)
    latency_ms: float = Field(ge=0.0)
    notes: str | None = None


class CompareRequest(APIModel):
    experiment_ids: list[UUID] = Field(min_length=1, max_length=10)


class CompareResponse(APIModel):
    rows: list[CompareRow]
    best_by_task: dict[TaskLane, str] = Field(default_factory=dict)
