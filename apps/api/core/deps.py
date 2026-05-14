"""FastAPI dependencies wiring services together (composition root)."""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends
from sqlmodel import Session

from apps.api.core.db import get_session
from apps.api.core.settings import Settings, get_settings
from services.agent.research_agent import ResearchAgent
from services.artifacts.artifact_service import ArtifactService
from services.data.dataset_service import DatasetService
from services.evaluation.evaluation_service import EvaluationService
from services.experiments.experiment_service import ExperimentService
from services.jobs import JobRunner, get_job_runner
from services.ml.model_service import ModelService
from services.ml.providers import build_provider


@lru_cache(maxsize=1)
def get_artifact_service() -> ArtifactService:
    return ArtifactService(settings=get_settings())


@lru_cache(maxsize=1)
def get_model_service() -> ModelService:
    settings: Settings = get_settings()
    provider = build_provider(settings.inference_provider, settings=settings)
    return ModelService(provider=provider)


@lru_cache(maxsize=1)
def get_evaluation_service() -> EvaluationService:
    return EvaluationService()


def get_dataset_service(
    session: Session = Depends(get_session),
) -> DatasetService:
    """Per-request dataset service (owns the request session)."""
    return DatasetService(session=session, settings=get_settings())


def get_experiment_service(
    session: Session = Depends(get_session),
) -> ExperimentService:
    """Per-request experiment service."""
    return ExperimentService(session=session)


def get_research_agent(
    session: Session = Depends(get_session),
    artifacts: ArtifactService = Depends(get_artifact_service),
) -> ResearchAgent:
    return ResearchAgent(session=session, settings=get_settings(), artifacts=artifacts)


def get_job_runner_dep() -> JobRunner:
    return get_job_runner()


def reset_dependency_cache() -> None:
    """Clear cached app singletons (used by tests)."""
    for factory in (
        get_artifact_service,
        get_model_service,
        get_evaluation_service,
    ):
        factory.cache_clear()
