"""Report schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from apps.api.schemas.agent import AgentReferenceItem
from apps.api.schemas.common import APIModel


class ReportMeta(APIModel):
    id: UUID
    experiment_id: UUID
    path: str
    created_at: str
    reference_count: int = Field(ge=0)


class ReportPayload(APIModel):
    meta: ReportMeta
    markdown: str
    references: list[AgentReferenceItem] = Field(default_factory=list)
