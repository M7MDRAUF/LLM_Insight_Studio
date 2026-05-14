"""Report retrieval routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from apps.api.core.deps import get_artifact_service
from services.artifacts.artifact_service import ArtifactService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}", response_class=PlainTextResponse)
def get_report(
    report_id: UUID,
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> str:
    return artifacts.load_report(report_id)
