"""Typed application errors mapped to consistent API error responses."""

from __future__ import annotations

from typing import Any


class APIError(Exception):
    """Base class for application-level errors with a stable error code."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": _truncate(self.message, 1024),
                "details": _truncate_details(self.details),
            }
        }


_MAX_DETAIL_VALUE_CHARS = 1024
_MAX_DETAIL_KEYS = 32


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _truncate_details(details: dict[str, Any]) -> dict[str, Any]:
    """Bound the size of error ``details`` to keep payloads small and safe."""
    if not details:
        return {}
    keys = list(details.keys())[:_MAX_DETAIL_KEYS]
    out: dict[str, Any] = {}
    for key in keys:
        raw = details[key]
        if isinstance(raw, str):
            out[key] = _truncate(raw, _MAX_DETAIL_VALUE_CHARS)
        elif isinstance(raw, (int, float, bool)) or raw is None:
            out[key] = raw
        else:
            out[key] = _truncate(repr(raw), _MAX_DETAIL_VALUE_CHARS)
    return out


class DatasetValidationError(APIError):
    code = "DATASET_VALIDATION_ERROR"
    http_status = 422


class UnsupportedTaskError(APIError):
    code = "UNSUPPORTED_TASK"
    http_status = 400


class ModelProviderError(APIError):
    code = "MODEL_PROVIDER_ERROR"
    http_status = 502


class ExperimentExecutionError(APIError):
    code = "EXPERIMENT_EXECUTION_ERROR"
    http_status = 500


class ArtifactWriteError(APIError):
    code = "ARTIFACT_WRITE_ERROR"
    http_status = 500


class ArtifactReadError(APIError):
    code = "ARTIFACT_READ_ERROR"
    http_status = 500


class ReferenceValidationError(APIError):
    code = "REFERENCE_VALIDATION_ERROR"
    http_status = 422


class NotFoundError(APIError):
    code = "NOT_FOUND"
    http_status = 404
