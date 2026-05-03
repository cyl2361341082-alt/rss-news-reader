"""FastAPI application."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, func, select

from rss_news_reader.config import get_settings
from rss_news_reader.db import get_session, init_db
from rss_news_reader.models import Article, ArticleDetailOut, ArticleSummaryOut, FeedEntry, HealthOut, PaginatedArticlesOut, SearchOut, SourceOut, StatsOut
from rss_news_reader.repositories.articles import ArticleRepository
from rss_news_reader.repositories.feed_entries import FeedEntryRepository
from rss_news_reader.repositories.sources import SourceRepository
from rss_news_reader.utils import json_loads, sanitize_html


def _article_summary(article: Article) -> ArticleSummaryOut:
    return ArticleSummaryOut.model_validate(article)


def _article_detail(article: Article, related: list[Article]) -> ArticleDetailOut:
    return ArticleDetailOut(
        **ArticleSummaryOut.model_validate(article).model_dump(),
        authors=json_loads(article.authors_json, []),
        content_text=article.content_text,
        content_html=sanitize_html(article.content_html),
        metadata=json_loads(article.metadata_json, {}),
        related_articles=[ArticleSummaryOut.model_validate(item) for item in related],
    )


def create_app() -> FastAPI:
    """Create the FastAPI application."""

    settings = get_settings()
    init_db()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthOut)
    def health() -> HealthOut:
        """Return application health."""

        return HealthOut(status="ok", app_name=settings.app_name)

    @app.get("/api/sources", response_model=list[SourceOut])
    def list_sources(session: Session = Depends(get_session)) -> list[SourceOut]:
        """List all sources."""

        repo = SourceRepository(session)
        items: list[SourceOut] = []
        for source, count in repo.list_with_article_counts():
            item = SourceOut.model_validate(source)
            item.article_count = int(count)
            items.append(item)
        return items

    @app.get("/api/articles", response_model=PaginatedArticlesOut)
    def list_articles(
        page: int = Query(1, ge=1),
        page_size: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
        source: str | None = None,
        category: str | None = None,
        q: str | None = None,
        sort: str = "published_desc",
        session: Session = Depends(get_session),
    ) -> PaginatedArticlesOut:
        """List paginated articles."""

        items, total, total_pages = ArticleRepository(session).list_paginated(
            page=page,
            page_size=page_size,
            source=source,
            category=category,
            query=q,
            sort=sort,
        )
        return PaginatedArticlesOut(
            items=[_article_summary(item) for item in items],
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

    @app.get("/api/articles/{slug}", response_model=ArticleDetailOut)
    def get_article(slug: str, session: Session = Depends(get_session)) -> ArticleDetailOut:
        """Return one full article by slug."""

        repo = ArticleRepository(session)
        article = repo.get_by_slug(slug)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return _article_detail(article, repo.related(article))

    @app.get("/api/stats", response_model=StatsOut)
    def stats(session: Session = Depends(get_session)) -> StatsOut:
        """Return API stats."""

        sources_repo = SourceRepository(session)
        articles_repo = ArticleRepository(session)
        total_sources = len(sources_repo.list_all())
        enabled_sources = len(sources_repo.list_enabled())
        total_feed_entries = int(session.exec(select(func.count()).select_from(FeedEntry)).one())
        failed_feed_entries = int(
            session.exec(select(func.count()).select_from(FeedEntry).where(FeedEntry.fetch_status == "failed")).one()
        )
        return StatsOut(
            total_sources=total_sources,
            enabled_sources=enabled_sources,
            total_feed_entries=total_feed_entries,
            total_articles=articles_repo.count_all(),
            successful_articles=articles_repo.successful_count(),
            failed_feed_entries=failed_feed_entries,
            categories=articles_repo.category_counts(),
        )

    @app.get("/api/search", response_model=SearchOut)
    def search(q: str = Query(..., min_length=1), session: Session = Depends(get_session)) -> SearchOut:
        """Search titles and content."""

        results = ArticleRepository(session).search(q)
        return SearchOut(query=q, results=[_article_summary(item) for item in results])

    return app


app = create_app()
