"""Shared pytest fixtures."""

from __future__ import annotations

from importlib import reload
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session


@pytest.fixture()
def backend_root() -> Path:
    """Return the backend project root."""

    return Path(__file__).resolve().parents[1]


@pytest.fixture()
def configured_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, backend_root: Path):
    """Configure isolated settings for a test run."""

    monkeypatch.setenv("RSS_NEWS_READER_DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    monkeypatch.setenv("RSS_NEWS_READER_SAMPLES_DIR", str((backend_root / "samples").resolve()))
    monkeypatch.setenv("RSS_NEWS_READER_EXPORT_DIR", str((tmp_path / "exports").resolve()))
    monkeypatch.setenv("RSS_NEWS_READER_FAILED_REQUESTS_PATH", str((tmp_path / "failed_requests.jsonl").resolve()))

    import rss_news_reader.config as config_module
    import rss_news_reader.db as db_module

    config_module.get_settings.cache_clear()
    config_module.get_sources_config.cache_clear()
    db_module.get_engine.cache_clear()

    from rss_news_reader.config import get_sources_config
    from rss_news_reader.db import get_engine, init_db
    from rss_news_reader.repositories.sources import SourceRepository

    init_db()
    with Session(get_engine()) as session:
        SourceRepository(session).upsert_many(get_sources_config())
    return {"tmp_path": tmp_path}


@pytest.fixture()
def session(configured_env):
    """Return an isolated database session."""

    from rss_news_reader.db import get_engine

    with Session(get_engine()) as db_session:
        yield db_session


@pytest.fixture()
def seeded_data(session: Session):
    """Seed sample feed entries and articles."""

    from rss_news_reader.config import get_settings
    from rss_news_reader.repositories.articles import ArticleRepository
    from rss_news_reader.repositories.feed_entries import FeedEntryRepository
    from rss_news_reader.repositories.sources import SourceRepository
    from rss_news_reader.services.article_fetcher import ArticleFetcher
    from rss_news_reader.services.rss_fetcher import RSSFetcher

    source = SourceRepository(session).get("sample-local")
    assert source is not None
    feed_repo = FeedEntryRepository(session)
    article_repo = ArticleRepository(session)
    RSSFetcher(get_settings(), feed_repo, article_repo).fetch_source(source)
    for entry in feed_repo.list_pending(limit=20):
        ArticleFetcher(get_settings(), feed_repo, article_repo).fetch_entry(entry, source)
    return {"source": source}


@pytest.fixture()
def client(configured_env):
    """Return a FastAPI test client."""

    import rss_news_reader.api as api_module

    reload(api_module)
    return TestClient(api_module.create_app())
