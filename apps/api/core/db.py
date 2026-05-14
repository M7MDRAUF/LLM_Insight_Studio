"""Database engine and session management (SQLModel / SQLite).

The engine is created lazily so the resolved settings (including any test
overrides via ``ARTIFACTS_DIR`` / ``DATABASE_URL``) are honoured. SQLite
foreign-key enforcement is enabled via a ``PRAGMA`` listener.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from apps.api.core.settings import Settings, get_settings

_engine: Engine | None = None
_engine_url: str | None = None


def _build_engine(settings: Settings) -> Engine:
    connect_args: dict[str, object] = (
        {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    )
    engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)
    if settings.database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _enable_sqlite_fk(dbapi_connection: Any, _conn_record: Any) -> None:
            cur = dbapi_connection.cursor()
            try:
                cur.execute("PRAGMA foreign_keys=ON")
            finally:
                cur.close()

    return engine


def get_engine() -> Engine:
    """Return the process-wide engine, creating it on first access."""
    global _engine, _engine_url  # noqa: PLW0603 - module-level lazy singleton
    settings = get_settings()
    if _engine is None or _engine_url != settings.database_url:
        if _engine is not None:
            _engine.dispose()
        _engine = _build_engine(settings)
        _engine_url = settings.database_url
    return _engine


def reset_engine() -> None:
    """Test helper — drop the cached engine so it is rebuilt next access."""
    global _engine, _engine_url  # noqa: PLW0603
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _engine_url = None


def init_db() -> None:
    """Create tables for all registered SQLModel entities."""
    # Import models so SQLModel metadata is populated before create_all.
    from apps.api.repositories import models  # noqa: F401  (side-effect import)

    settings = get_settings()
    settings.ensure_directories()
    SQLModel.metadata.create_all(get_engine())


@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield a transactional session that commits on success, rolls back on error."""
    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a SQLModel session per request."""
    with session_scope() as session:
        yield session
