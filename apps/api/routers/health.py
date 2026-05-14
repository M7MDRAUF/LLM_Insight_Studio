"""Liveness and readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from apps.api.core.settings import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "inference_provider": settings.inference_provider,
        "agent_enabled": settings.agent_enabled,
    }
