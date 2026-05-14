"""Structured logging configuration."""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger once with an opinionated format."""
    global _CONFIGURED  # noqa: PLW0603 - idempotent module guard
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())

    # Quiet overly-chatty libraries.
    for noisy in ("httpx", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str, **context: Any) -> logging.LoggerAdapter[logging.Logger]:
    """Return a logger adapter that renders bound structured context."""
    return _ContextAdapter(logging.getLogger(name), context)


class _ContextAdapter(logging.LoggerAdapter[logging.Logger]):
    """Adapter that appends key=value context to every log message."""

    def process(
        self, msg: str, kwargs: MutableMapping[str, Any]
    ) -> tuple[str, MutableMapping[str, Any]]:
        if not self.extra:
            return msg, kwargs
        ctx = " ".join(f"{k}={v}" for k, v in self.extra.items() if v is not None)
        return f"{msg} [{ctx}]" if ctx else msg, kwargs
