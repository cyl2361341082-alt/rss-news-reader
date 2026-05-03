"""Deduplication helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from rss_news_reader.repositories.articles import ArticleRepository
from rss_news_reader.repositories.feed_entries import FeedEntryRepository
from rss_news_reader.utils import normalize_url, short_hash


class Deduper:
    """Check duplicates across feed entries and stored articles."""

    def __init__(self, feed_entries: FeedEntryRepository, articles: ArticleRepository):
        self.feed_entries = feed_entries
        self.articles = articles

    def canonical_exists(self, canonical_url: str | None) -> bool:
        """Return whether a canonical URL already exists."""

        if not canonical_url:
            return False
        normalized = normalize_url(canonical_url)
        return bool(
            self.feed_entries.get_by_canonical_url(normalized)
            or self.articles.get_by_canonical_url(normalized)
        )

    def url_hash_exists(self, url: str) -> bool:
        """Return whether a normalized URL hash already exists."""

        return bool(self.feed_entries.get_by_url_hash(short_hash(normalize_url(url))))

    def title_published_hash_exists(self, title: str, published_at: Optional[datetime]) -> bool:
        """Return whether a title and timestamp combination exists."""

        key = short_hash(f"{title.strip().lower()}::{published_at.isoformat() if published_at else 'none'}")
        return bool(self.feed_entries.get_by_title_published_hash(key))

    def first_duplicate_reason(self, canonical_url: str | None, url: str, title: str, published_at: Optional[datetime]) -> str | None:
        """Return the first duplicate reason that matches."""

        if canonical_url and self.canonical_exists(canonical_url):
            return "duplicate"
        if self.url_hash_exists(url):
            return "duplicate"
        if self.title_published_hash_exists(title, published_at):
            return "duplicate"
        return None
