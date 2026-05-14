"""Artifact retrieval routes (experiment JSON)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends

from apps.api.core.deps import get_artifact_service
from services.artifacts.artifact_service import ArtifactService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/experiments/{experiment_id}")
def get_experiment_artifact(
    experiment_id: UUID,
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> dict[str, Any]:
    return artifacts.load_experiment(experiment_id)
