"""Database bootstrap utilities."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlmodel import Session, SQLModel, create_engine

from rss_news_reader.config import get_settings


@lru_cache(maxsize=1)
def get_engine():
    """Create and cache the SQLModel engine."""

    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)
    if settings.database_url.startswith("sqlite"):
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            conn.exec_driver_sql("PRAGMA busy_timeout=5000")
    return engine


def init_db() -> None:
    """Create all database tables."""

    settings = get_settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(get_engine())


def get_session() -> Generator[Session, None, None]:
    """Yield a database session for FastAPI dependency injection.

    Automatically rolls back on unhandled exceptions so that partial
    changes never leak into subsequent requests.
    """

    session = Session(get_engine())
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
