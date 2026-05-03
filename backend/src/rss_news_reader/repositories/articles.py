"""Article repository."""

from __future__ import annotations

from math import ceil
from typing import Optional

from sqlmodel import Session, col, func, or_, select

from rss_news_reader.models import Article
from rss_news_reader.utils import escape_like


class ArticleRepository:
    """Persistence operations for articles."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, article: Article) -> Article:
        """Persist and commit an article."""

        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def add_no_commit(self, article: Article) -> Article:
        """Stage an article without committing — caller controls the transaction."""

        self.session.add(article)
        self.session.flush()
        self.session.refresh(article)
        return article

    def update(self, article: Article) -> Article:
        """Persist and commit changes to an article."""

        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def update_no_commit(self, article: Article) -> Article:
        """Stage article changes without committing — caller controls the transaction."""

        self.session.add(article)
        self.session.flush()
        self.session.refresh(article)
        return article

    def get_by_slug(self, slug: str) -> Article | None:
        """Return one article by slug."""

        return self.session.exec(select(Article).where(Article.slug == slug)).first()

    def get_by_canonical_url(self, canonical_url: str) -> Article | None:
        """Return one article by canonical URL."""

        return self.session.exec(select(Article).where(Article.canonical_url == canonical_url)).first()

    def get_by_url(self, url: str) -> Article | None:
        """Return one article by URL."""

        return self.session.exec(select(Article).where(Article.url == url)).first()

    def get_by_content_hash(self, content_hash: str) -> Article | None:
        """Return one article by content hash."""

        return self.session.exec(select(Article).where(Article.content_hash == content_hash)).first()

    def list_paginated(
        self,
        page: int,
        page_size: int,
        source: Optional[str] = None,
        category: Optional[str] = None,
        query: Optional[str] = None,
        sort: str = "published_desc",
    ) -> tuple[list[Article], int, int]:
        """Return paginated articles and totals."""

        page = max(1, page)
        page_size = max(1, page_size)

        statement = select(Article)
        if source:
            statement = statement.where(Article.source_id == source)
        if category:
            statement = statement.where(Article.category == category)
        if query:
            escaped = escape_like(query)
            like = f"%{escaped}%"
            statement = statement.where(or_(Article.title.like(like, escape="\\"), Article.content_text.like(like, escape="\\")))

        if sort == "published_asc":
            statement = statement.order_by(Article.published_at.asc(), Article.id.asc())
        else:
            statement = statement.order_by(Article.published_at.desc(), Article.id.desc())

        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self.session.exec(count_statement).one())
        total_pages = max(1, ceil(total / page_size)) if total else 1
        items = list(self.session.exec(statement.offset((page - 1) * page_size).limit(page_size)))
        return items, total, total_pages

    def search(self, query: str, limit: int = 20) -> list[Article]:
        """Run a simple LIKE-based full text search."""

        escaped = escape_like(query)
        like = f"%{escaped}%"
        statement = (
            select(Article)
            .where(or_(Article.title.like(like, escape="\\"), Article.content_text.like(like, escape="\\")))
            .order_by(Article.published_at.desc(), Article.id.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def related(self, article: Article, limit: int = 4) -> list[Article]:
        """Return related articles by source or category."""

        statement = (
            select(Article)
            .where(Article.slug != article.slug)
            .where(or_(Article.source_id == article.source_id, Article.category == article.category))
            .order_by(Article.published_at.desc(), Article.id.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def count_all(self) -> int:
        """Return article count."""

        return int(self.session.exec(select(func.count()).select_from(Article)).one())

    def category_counts(self) -> dict[str, int]:
        """Return counts grouped by category."""

        rows = self.session.exec(
            select(Article.category, func.count(Article.id))
            .group_by(Article.category)
            .order_by(col(Article.category))
        ).all()
        return {category or "uncategorized": int(count) for category, count in rows}

    def successful_count(self) -> int:
        """Return successful extraction count."""

        return int(self.session.exec(select(func.count()).select_from(Article).where(Article.extraction_success.is_(True))).one())
