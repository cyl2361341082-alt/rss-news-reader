"""RSS fetching service."""

from __future__ import annotations

import feedparser
import httpx

from rss_news_reader.config import Settings
from rss_news_reader.logging import get_logger
from rss_news_reader.models import FeedEntry, Source
from rss_news_reader.repositories.articles import ArticleRepository
from rss_news_reader.repositories.feed_entries import FeedEntryRepository
from rss_news_reader.services.deduper import Deduper
from rss_news_reader.services.rate_limit import RateLimiter
from rss_news_reader.utils import build_entry_slug, entry_to_dict, json_dumps, normalize_url, parse_datetime, resolve_local_path, short_hash, text_excerpt


class RSSFetcher:
    """Fetch and persist RSS feed entries."""

    def __init__(
        self,
        settings: Settings,
        feed_entries: FeedEntryRepository,
        articles: ArticleRepository,
    ) -> None:
        self.settings = settings
        self.feed_entries = feed_entries
        self.articles = articles
        self.deduper = Deduper(feed_entries, articles)
        self.rate_limiter = RateLimiter(settings.fetch_delay_seconds)
        self.logger = get_logger("rss_fetcher")

    def fetch_source(self, source: Source) -> dict[str, int]:
        """Fetch one source and store new feed entries."""

        self.rate_limiter.wait()
        try:
            raw = self._read_feed_content(source.rss_url)
        except Exception as exc:
            self.logger.error("feed_fetch_failed", source_id=source.id, error=str(exc))
            return {"fetched": 0, "created": 0, "failed": 1}

        parsed = feedparser.parse(raw)
        created = 0
        local_feed = not source.rss_url.startswith(("http://", "https://"))
        for item in parsed.entries:
            title = (item.get("title") or "Untitled").strip()
            raw_link = item.get("link") or ""
            link = raw_link if local_feed and "://" not in raw_link else normalize_url(raw_link, base_url=source.site_url)
            published_at = parse_datetime(item.get("published_parsed") or item.get("updated_parsed") or item.get("published"))
            summary = text_excerpt(item.get("summary") or item.get("description") or "", 280)
            canonical_url = normalize_url(item.get("id") or link, base_url=source.site_url)
            duplicate_reason = self.deduper.first_duplicate_reason(canonical_url, link, title, published_at)
            if duplicate_reason:
                continue

            entry = FeedEntry(
                source_id=source.id,
                title=title,
                url=link,
                canonical_url=canonical_url,
                slug=build_entry_slug(title, published_at, url=link),
                summary=summary,
                published_at=published_at,
                url_hash=short_hash(link),
                title_published_hash=short_hash(f"{title.strip().lower()}::{published_at.isoformat() if published_at else 'none'}"),
                raw_entry_json=json_dumps(entry_to_dict(item)),
            )
            self.feed_entries.add(entry)
            created += 1
        self.logger.info("feed_fetch_completed", source_id=source.id, items=len(parsed.entries), created=created)
        return {"fetched": len(parsed.entries), "created": created, "failed": 0}

    def _read_feed_content(self, rss_url: str) -> str:
        """Read RSS content from HTTP or local files."""

        if rss_url.startswith(("http://", "https://")):
            with httpx.Client(
                timeout=self.settings.request_timeout_seconds,
                headers={"User-Agent": self.settings.user_agent},
                follow_redirects=True,
            ) as client:
                response = client.get(rss_url)
                response.raise_for_status()
                return response.text
        path = resolve_local_path(rss_url, self.settings.project_root)
        return path.read_text(encoding="utf-8")
