"""Export service for stored articles."""

from __future__ import annotations

import re
from pathlib import Path

from rss_news_reader.config import Settings
from rss_news_reader.models import Article
from rss_news_reader.repositories.articles import ArticleRepository
from rss_news_reader.utils import json_dumps, json_loads


def _sanitize_markdown_title(title: str) -> str:
    """Strip Markdown-injected link/image syntax from a title."""

    return re.sub(r"[\[\]()`*#|]", "", title)


class Exporter:
    """Export articles to JSON or Markdown."""

    def __init__(self, settings: Settings, articles: ArticleRepository) -> None:
        self.settings = settings
        self.articles = articles

    def export(self, fmt: str = "json") -> Path:
        """Export all stored articles to disk."""

        self.settings.export_path.mkdir(parents=True, exist_ok=True)
        if fmt == "md":
            return self._export_markdown()
        return self._export_json()

    def _export_json(self) -> Path:
        target = self.settings.export_path / "articles.json"
        all_items: list[dict[str, object]] = []
        page = 1
        while True:
            items, total, _ = self.articles.list_paginated(page=page, page_size=1000)
            all_items.extend(self._to_dict(article) for article in items)
            if len(all_items) >= total or not items:
                break
            page += 1
        target.write_text(json_dumps(all_items), encoding="utf-8")
        return target

    def _export_markdown(self) -> Path:
        target = self.settings.export_path / "articles.md"
        chunks: list[str] = []
        page = 1
        while True:
            items, total, _ = self.articles.list_paginated(page=page, page_size=1000)
            for article in items:
                chunks.append(self._article_to_markdown(article))
            if len(chunks) >= total or not items:
                break
            page += 1
        target.write_text("\n---\n".join(chunks), encoding="utf-8")
        return target

    @staticmethod
    def _article_to_markdown(article: Article) -> str:
        safe_title = _sanitize_markdown_title(article.title)
        return "\n".join(
            [
                f"# {safe_title}",
                "",
                f"- Source: {article.source_id}",
                f"- Published: {article.published_at.isoformat() if article.published_at else 'unknown'}",
                f"- Reading time: {article.reading_time_minutes} min",
                "",
                article.content_text,
                "",
            ]
        )

    @staticmethod
    def _to_dict(article: Article) -> dict[str, object]:
        metadata = json_loads(article.metadata_json, {})
        return {
            "id": article.id,
            "slug": article.slug,
            "title": article.title,
            "source_id": article.source_id,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "summary": article.summary,
            "reading_time_minutes": article.reading_time_minutes,
            "content_text": article.content_text,
            "content_html": article.content_html,
            "authors": json_loads(article.authors_json, []),
            "metadata": metadata,
        }
