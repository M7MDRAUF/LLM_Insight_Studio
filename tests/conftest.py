"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("INFERENCE_PROVIDER", "mock")

from apps.api.core.db import init_db, reset_engine
from apps.api.core.deps import reset_dependency_cache
from apps.api.core.settings import get_settings
from apps.api.main import create_app
from services.agent.research_agent import reset_report_store
from services.data.dataset_service import reset_dataset_memory
from services.experiments.experiment_service import reset_experiment_store
from services.jobs.runner import reset_job_runner


@pytest.fixture(autouse=True)
def _reset_state(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    # Isolate artifact dirs and the SQLite database per test.
    artifacts = tmp_path_factory.mktemp("artifacts")
    db_path = artifacts / "studio.db"
    os.environ["ARTIFACTS_DIR"] = str(artifacts)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    get_settings.cache_clear()
    reset_engine()
    reset_dependency_cache()
    reset_dataset_memory()
    reset_experiment_store()
    reset_report_store()
    reset_job_runner()
    init_db()
    yield
    reset_dataset_memory()
    reset_experiment_store()
    reset_report_store()
    reset_job_runner()
    reset_engine()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as tc:
        yield tc
