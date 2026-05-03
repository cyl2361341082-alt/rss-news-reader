"""Deduper tests."""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session


def test_url_normalization_removes_tracking_params() -> None:
    """URL normalization should strip common tracking parameters."""

    from rss_news_reader.utils import normalize_url

    normalized = normalize_url("https://example.local/story?utm_source=x&id=42#section")

    assert normalized == "https://example.local/story?id=42"


def test_deduper_recognizes_existing_url(session: Session) -> None:
    """Deduper should match an existing feed entry by normalized URL hash."""

    from rss_news_reader.models import FeedEntry
    from rss_news_reader.repositories.articles import ArticleRepository
    from rss_news_reader.repositories.feed_entries import FeedEntryRepository
    from rss_news_reader.services.deduper import Deduper
    from rss_news_reader.utils import short_hash

    repo = FeedEntryRepository(session)
    repo.add(
        FeedEntry(
            source_id="sample-local",
            title="Duplicate story",
            url="https://example.local/story",
            canonical_url="https://example.local/story",
            slug="duplicate-story-20240401",
            summary="Summary",
            published_at=datetime(2024, 4, 1, 12, 0, 0),
            url_hash=short_hash("https://example.local/story"),
            title_published_hash=short_hash("duplicate story::2024-04-01T12:00:00"),
            raw_entry_json="{}",
        )
    )

    deduper = Deduper(repo, ArticleRepository(session))
    assert deduper.url_hash_exists("https://example.local/story")
