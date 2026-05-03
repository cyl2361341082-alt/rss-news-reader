"""Article fetcher tests."""

from __future__ import annotations

import httpx
from rss_news_reader.models import FeedEntry
from sqlmodel import Session


def test_article_fetcher_uses_feed_fallback_on_network_error(session: Session) -> None:
    """Fetcher should store a fallback article from RSS summary when the page request fails."""

    from rss_news_reader.config import get_settings
    from rss_news_reader.repositories.articles import ArticleRepository
    from rss_news_reader.repositories.feed_entries import FeedEntryRepository
    from rss_news_reader.repositories.sources import SourceRepository
    from rss_news_reader.services.article_fetcher import ArticleFetcher
    from rss_news_reader.utils import json_dumps, short_hash

    source = SourceRepository(session).get("wsj-world-news")
    assert source is not None

    summary = (
        "Israel allowed displaced Gazans to begin crossing a military zone that bisects the enclave "
        "after a deadlock over hostage releases was broken, according to the Wall Street Journal feed. "
        "Witnesses described families moving north on foot while aid groups and regional officials tried "
        "to assess whether the corridor would remain open. The report framed the crossing as one of the "
        "first visible signs that negotiations had temporarily changed conditions on the ground."
    )
    entry = FeedEntry(
        source_id=source.id,
        title="Palestinians Stream Back to Northern Gaza on Foot",
        url="https://www.wsj.com/articles/palestinians-flock-back-to-northern-gaza-on-foot-after-hostage-release-breakthrough-3f60e2db",
        canonical_url="https://www.wsj.com/articles/palestinians-flock-back-to-northern-gaza-on-foot-after-hostage-release-breakthrough-3f60e2db",
        slug="palestinians-stream-back-20260415",
        summary=summary,
        url_hash=short_hash("https://www.wsj.com/articles/palestinians-flock-back-to-northern-gaza-on-foot-after-hostage-release-breakthrough-3f60e2db"),
        title_published_hash=short_hash("palestinians stream back::none"),
        raw_entry_json=json_dumps(
            {
                "summary": summary,
                "content": [{"type": "text/html", "value": ""}],
            }
        ),
    )
    feed_repo = FeedEntryRepository(session)
    article_repo = ArticleRepository(session)
    feed_repo.add(entry)

    fetcher = ArticleFetcher(get_settings(), feed_repo, article_repo)

    def raise_network_error(_url: str, _source=None) -> str:
        raise httpx.ConnectError("boom")

    fetcher._read_article_html = raise_network_error
    article = fetcher.fetch_entry(entry, source)

    assert article is not None
    assert article.extraction_method == "feed_fallback"
    assert "hostage releases" in article.content_text
    assert article.top_image is None
    stored_entry = session.get(FeedEntry, entry.id)
    assert stored_entry is not None
    assert stored_entry.fetch_status == "fetched"


def test_article_fetcher_keeps_failure_when_feed_fallback_is_too_short(session: Session) -> None:
    """Fetcher should preserve the original failure when feed content is not useful."""

    from rss_news_reader.config import get_settings
    from rss_news_reader.repositories.articles import ArticleRepository
    from rss_news_reader.repositories.feed_entries import FeedEntryRepository
    from rss_news_reader.repositories.sources import SourceRepository
    from rss_news_reader.services.article_fetcher import ArticleFetcher, BlockedBySourceError
    from rss_news_reader.utils import json_dumps, short_hash

    source = SourceRepository(session).get("wsj-markets")
    assert source is not None

    entry = FeedEntry(
        source_id=source.id,
        title="Video Only Entry",
        url="https://www.wsj.com/video/example-video",
        canonical_url="https://www.wsj.com/video/example-video",
        slug="video-only-entry-20260415",
        summary="Short blurb.",
        url_hash=short_hash("https://www.wsj.com/video/example-video"),
        title_published_hash=short_hash("video only entry::none"),
        raw_entry_json=json_dumps(
            {
                "summary": "Short blurb.",
                "content": [{"type": "text/plain", "value": "Caption only."}],
            }
        ),
    )
    feed_repo = FeedEntryRepository(session)
    article_repo = ArticleRepository(session)
    feed_repo.add(entry)

    fetcher = ArticleFetcher(get_settings(), feed_repo, article_repo)

    def raise_blocked(_url: str, _source) -> str:
        raise BlockedBySourceError("blocked")

    fetcher._read_article_html = raise_blocked
    article = fetcher.fetch_entry(entry, source)

    assert article is None
    stored_entry = session.get(FeedEntry, entry.id)
    assert stored_entry is not None
    assert stored_entry.fetch_status == "failed"
    assert stored_entry.error_reason == "blocked"


def test_article_fetcher_uses_browser_fallback_for_blocked_sources(session: Session) -> None:
    """Fetcher should try browser HTML when the HTTP client is blocked for configured sources."""

    from rss_news_reader.config import get_settings
    from rss_news_reader.repositories.articles import ArticleRepository
    from rss_news_reader.repositories.feed_entries import FeedEntryRepository
    from rss_news_reader.repositories.sources import SourceRepository
    from rss_news_reader.services.article_fetcher import ArticleFetcher, BlockedBySourceError
    from rss_news_reader.utils import json_dumps, short_hash

    source = SourceRepository(session).get("wsj-world-news")
    assert source is not None

    entry = FeedEntry(
        source_id=source.id,
        title="Browser Fallback Entry",
        url="https://www.wsj.com/articles/browser-fallback-entry",
        canonical_url="https://www.wsj.com/articles/browser-fallback-entry",
        slug="browser-fallback-entry-20260415",
        summary="Fallback summary that should not be used when browser HTML succeeds.",
        url_hash=short_hash("https://www.wsj.com/articles/browser-fallback-entry"),
        title_published_hash=short_hash("browser fallback entry::none"),
        raw_entry_json=json_dumps({"summary": "Fallback summary that should not be used when browser HTML succeeds."}),
    )
    feed_repo = FeedEntryRepository(session)
    article_repo = ArticleRepository(session)
    feed_repo.add(entry)

    fetcher = ArticleFetcher(get_settings(), feed_repo, article_repo)

    def raise_blocked(_url: str, _source) -> str:
        raise BlockedBySourceError("blocked")

    def return_browser_html(_url: str, _source) -> str:
        return "<html><body><article><p>This browser path returned a much longer body with enough detail to store.</p><p>Second paragraph with more context.</p></article></body></html>"

    fetcher._read_http_article_html = raise_blocked
    fetcher._read_browser_article_html = return_browser_html

    article = fetcher.fetch_entry(entry, source)

    assert article is not None
    assert article.extraction_method != "feed_fallback"
    assert "much longer body" in article.content_text
