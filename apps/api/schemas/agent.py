"""Research agent schemas."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import Field, HttpUrl

from apps.api.schemas.common import APIModel
from apps.api.schemas.datasets import TaskLane

ReferenceType = Literal["paper", "docs", "dataset", "model_card", "benchmark"]


class AgentReferenceItem(APIModel):
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    type: ReferenceType
    why_it_matters: str = Field(min_length=1, max_length=1_000)


class ResearchPlanRequest(APIModel):
    topic: str = Field(min_length=3, max_length=500)
    task_lanes: list[TaskLane] = Field(min_length=1)
    dataset_hints: list[str] = Field(default_factory=list, max_length=20)
    model_hints: list[str] = Field(default_factory=list, max_length=20)


class ResearchPlanResponse(APIModel):
    plan_markdown: str
    references: list[AgentReferenceItem] = Field(default_factory=list)


class ResearchReportRequest(APIModel):
    experiment_id: UUID
    include_references: bool = True
    notes: str | None = Field(default=None, max_length=2_000)


class ResearchReportResponse(APIModel):
    report_id: UUID
    path: str
    reference_count: int = Field(ge=0)
