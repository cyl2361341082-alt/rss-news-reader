"""RSS fetcher tests."""

from __future__ import annotations

from sqlmodel import Session


def test_rss_fetcher_parses_sample_feed(session: Session) -> None:
    """RSS fetcher should persist sample feed entries."""

    from rss_news_reader.config import get_settings
    from rss_news_reader.repositories.articles import ArticleRepository
    from rss_news_reader.repositories.feed_entries import FeedEntryRepository
    from rss_news_reader.repositories.sources import SourceRepository
    from rss_news_reader.services.rss_fetcher import RSSFetcher

    source = SourceRepository(session).get("sample-local")
    assert source is not None

    result = RSSFetcher(get_settings(), FeedEntryRepository(session), ArticleRepository(session)).fetch_source(source)

    assert result["created"] >= 2
