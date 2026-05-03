"""Pipeline orchestration."""

from __future__ import annotations

from sqlmodel import Session, func, select

from rss_news_reader.config import get_settings, get_sources_config
from rss_news_reader.db import get_engine, init_db
from rss_news_reader.logging import get_logger
from rss_news_reader.models import Article, FeedEntry, Source
from rss_news_reader.repositories.articles import ArticleRepository
from rss_news_reader.repositories.feed_entries import FeedEntryRepository
from rss_news_reader.repositories.sources import SourceRepository
from rss_news_reader.services.article_fetcher import ArticleFetcher
from rss_news_reader.services.exporter import Exporter
from rss_news_reader.services.rss_fetcher import RSSFetcher


class NewsPipeline:
    """High-level application workflow."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger("pipeline")

    def init(self) -> None:
        """Initialize database and sync sources."""

        init_db()
        with Session(get_engine()) as session:
            SourceRepository(session).upsert_many(get_sources_config())

    def fetch_feeds(self) -> dict[str, dict[str, int]]:
        """Fetch all enabled RSS feeds."""

        results: dict[str, dict[str, int]] = {}
        with Session(get_engine()) as session:
            sources_repo = SourceRepository(session)
            fetcher = RSSFetcher(self.settings, FeedEntryRepository(session), ArticleRepository(session))
            for source in sources_repo.list_enabled():
                results[source.id] = fetcher.fetch_source(source)
        return results

    def fetch_articles(self, limit: int = 100) -> int:
        """Fetch article pages for pending feed entries."""

        stored = 0
        with Session(get_engine()) as session:
            sources = {item.id: item for item in SourceRepository(session).list_all()}
            entries = FeedEntryRepository(session).list_pending(limit=limit)
            fetcher = ArticleFetcher(self.settings, FeedEntryRepository(session), ArticleRepository(session))
            for entry in entries:
                source = sources.get(entry.source_id)
                if source and fetcher.fetch_entry(entry, source):
                    stored += 1
        return stored

    def run(self) -> dict[str, object]:
        """Run the full ingestion pipeline."""

        self.init()
        feeds = self.fetch_feeds()
        article_count = self.fetch_articles()
        return {"feeds": feeds, "articles_created": article_count}

    def export(self, fmt: str = "json") -> str:
        """Export stored articles."""

        with Session(get_engine()) as session:
            path = Exporter(self.settings, ArticleRepository(session)).export(fmt=fmt)
        return str(path)

    def retry_failures(self) -> int:
        """Retry failed feed entries."""

        with Session(get_engine()) as session:
            source_map = {item.id: item for item in SourceRepository(session).list_all()}
            fetcher = ArticleFetcher(self.settings, FeedEntryRepository(session), ArticleRepository(session))
            return fetcher.retry_failures(source_map, limit=self.settings.retry_failed_limit)

    def repair_short_articles(self, max_length: int = 300, source_id: str | None = None) -> dict[str, int]:
        """Requeue overly short extracted articles and fetch them again."""

        with Session(get_engine()) as session:
            article_statement = select(Article)
            if source_id:
                article_statement = article_statement.where(Article.source_id == source_id)
            articles = [
                article
                for article in session.exec(article_statement)
                if len(article.content_text.strip()) <= max_length
            ]
            slugs = {article.slug for article in articles}

            for article in articles:
                session.delete(article)

            entries = list(session.exec(select(FeedEntry).where(FeedEntry.slug.in_(slugs)))) if slugs else []
            for entry in entries:
                entry.fetch_status = "pending"
                entry.error_reason = None

            session.commit()

        refetched = self.fetch_articles(limit=max(len(slugs), 1)) if slugs else 0
        return {"requeued": len(slugs), "refetched": refetched}

    def stats(self) -> dict[str, object]:
        """Return pipeline statistics."""

        with Session(get_engine()) as session:
            sources_repo = SourceRepository(session)
            articles_repo = ArticleRepository(session)
            total_feed_entries = int(session.exec(select(func.count()).select_from(FeedEntry)).one())
            failed_feed_entries = int(
                session.exec(select(func.count()).select_from(FeedEntry).where(FeedEntry.fetch_status == "failed")).one()
            )
            total_sources = len(sources_repo.list_all())
            enabled_sources = len(sources_repo.list_enabled())
            return {
                "total_sources": total_sources,
                "enabled_sources": enabled_sources,
                "total_feed_entries": total_feed_entries,
                "total_articles": articles_repo.count_all(),
                "successful_articles": articles_repo.successful_count(),
                "failed_feed_entries": failed_feed_entries,
                "categories": articles_repo.category_counts(),
            }

    def test_source(self, source_id: str) -> dict[str, object]:
        """Fetch one source and return a small diagnostic payload."""

        self.init()
        with Session(get_engine()) as session:
            source = SourceRepository(session).get(source_id)
            if not source:
                raise ValueError(f"Unknown source: {source_id}")
            feed_result = RSSFetcher(self.settings, FeedEntryRepository(session), ArticleRepository(session)).fetch_source(source)
            pending = [
                item
                for item in FeedEntryRepository(session).list_pending(limit=10)
                if item.source_id == source.id
            ]
            return {
                "source_id": source.id,
                "feed_result": feed_result,
                "pending_entries": len(pending),
                "sample_titles": [entry.title for entry in pending[:3]],
            }
