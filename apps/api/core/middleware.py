"""HTTP middleware: request-id propagation and structured access logging."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from apps.api.core.logging import get_logger

_REQUEST_ID_HEADER = "X-Request-ID"
_log = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach an ``X-Request-ID`` header to every response and log timings."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(_REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:  # pragma: no cover - exceptions logged then re-raised
            duration_ms = (time.perf_counter() - start) * 1000.0
            _log.exception(
                "request_failed method=%s path=%s duration_ms=%.2f request_id=%s",
                request.method,
                request.url.path,
                duration_ms,
                request_id,
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000.0
        response.headers[_REQUEST_ID_HEADER] = request_id
        _log.info(
            "request method=%s path=%s status=%d duration_ms=%.2f request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response
