"""Source repository."""

from __future__ import annotations

from sqlmodel import Session, func, select

from rss_news_reader.config import SourceConfig
from rss_news_reader.models import Article, Source
from rss_news_reader.utils import json_dumps


class SourceRepository:
    """Persistence operations for sources."""

    def __init__(self, session: Session):
        self.session = session

    def upsert_many(self, sources: list[SourceConfig]) -> None:
        """Insert or update source definitions."""

        for item in sources:
            existing = self.session.get(Source, item.id)
            payload = {
                "name": item.name,
                "category": item.category,
                "rss_url": item.rss_url,
                "enabled": item.enabled,
                "site_url": item.site_url,
                "language": item.language,
                "extraction_strategy": item.extraction_strategy,
                "allowed_domains_json": json_dumps(item.allowed_domains),
                "extraction_selectors_json": json_dumps(item.extraction_selectors),
            }
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
            else:
                self.session.add(Source(id=item.id, **payload))
        self.session.commit()

    def list_all(self) -> list[Source]:
        """Return all sources."""

        return list(self.session.exec(select(Source).order_by(Source.name)))

    def list_enabled(self) -> list[Source]:
        """Return enabled sources."""

        return list(self.session.exec(select(Source).where(Source.enabled.is_(True)).order_by(Source.name)))

    def get(self, source_id: str) -> Source | None:
        """Return a source by id."""

        return self.session.get(Source, source_id)

    def list_with_article_counts(self) -> list[tuple[Source, int]]:
        """Return sources with stored article counts."""

        statement = (
            select(Source, func.count(Article.id))
            .join(Article, Article.source_id == Source.id, isouter=True)
            .group_by(Source.id)
            .order_by(Source.name)
        )
        return list(self.session.exec(statement).all())
