"""Experiment schemas."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from apps.api.schemas.common import APIModel
from apps.api.schemas.datasets import TaskLane


class ExperimentStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SamplingConfig(APIModel):
    max_rows: int = Field(default=200, ge=1, le=5_000)
    strategy: str = Field(default="head", pattern="^(head|random|stratified)$")
    seed: int = Field(default=42, ge=0)


class GenerationParams(APIModel):
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_new_tokens: int = Field(default=256, ge=1, le=4_096)
    batch_size: int = Field(default=8, ge=1, le=256)


class ReportOptions(APIModel):
    enabled: bool = True
    include_references: bool = True


class ExperimentCreateRequest(APIModel):
    dataset_manifest_id: UUID
    task_lanes: list[TaskLane] = Field(min_length=1)
    models: dict[TaskLane, str] = Field(default_factory=dict)
    sampling: SamplingConfig = Field(default_factory=SamplingConfig)
    generation: GenerationParams = Field(default_factory=GenerationParams)
    report: ReportOptions = Field(default_factory=ReportOptions)
    notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("task_lanes")
    @classmethod
    def _unique_lanes(_cls, value: list[TaskLane]) -> list[TaskLane]:  # noqa: N804
        if len(value) != len(set(value)):
            raise ValueError("task_lanes must be unique")
        return value


class MetricsByLane(APIModel):
    classification: dict[str, Any] | None = None
    summarization: dict[str, Any] | None = None
    qa: dict[str, Any] | None = None
    instruct: dict[str, Any] | None = None


class ArtifactRef(APIModel):
    type: str
    path: str
    bytes: int | None = None


class ExperimentResult(APIModel):
    experiment_id: UUID
    status: ExperimentStatus
    summary: dict[str, Any] = Field(default_factory=dict)
    metrics: MetricsByLane = Field(default_factory=MetricsByLane)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    error: str | None = None


class ExperimentStatusResponse(APIModel):
    experiment_id: UUID
    status: ExperimentStatus
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    message: str | None = None


class ExperimentSummary(APIModel):
    id: UUID
    dataset_manifest_id: UUID
    task_lanes: list[TaskLane]
    status: ExperimentStatus
    created_at: str
