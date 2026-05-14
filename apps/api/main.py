"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api.core.db import init_db
from apps.api.core.errors import APIError
from apps.api.core.logging import configure_logging, get_logger
from apps.api.core.middleware import RequestIDMiddleware
from apps.api.core.settings import get_settings
from apps.api.routers import (
    agent,
    artifacts,
    compare,
    datasets,
    experiments,
    health,
    metrics,
    reports,
)
from services.jobs import get_job_runner

_log = get_logger(__name__)


async def _handle_api_error(_request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status, content=exc.to_payload())


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.ensure_directories()
    init_db()
    _log.info("api_started provider=%s", settings.inference_provider)
    try:
        yield
    finally:
        await get_job_runner().shutdown()
        _log.info("api_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="LLM Insight Studio API",
        version="0.1.0",
        lifespan=_lifespan,
    )

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.add_exception_handler(APIError, _handle_api_error)  # type: ignore[arg-type]

    api_prefix = "/api/v1"
    for router in (
        health.router,
        datasets.router,
        experiments.router,
        compare.router,
        agent.router,
        reports.router,
        artifacts.router,
    ):
        app.include_router(router, prefix=api_prefix)

    # Metrics is exposed at the root (Prometheus scrape convention).
    app.include_router(metrics.router)

    return app


app = create_app()
