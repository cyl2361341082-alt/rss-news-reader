"""Database and API models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field as PydanticField
from sqlmodel import Column, DateTime, Field, SQLModel


class Source(SQLModel, table=True):
    """Configured RSS source."""

    __tablename__ = "sources"

    id: str = Field(primary_key=True)
    name: str
    category: str
    rss_url: str
    enabled: bool = True
    site_url: str
    language: str = "en"
    extraction_strategy: str = "readability"
    allowed_domains_json: str = "[]"
    extraction_selectors_json: str = "[]"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )


class FeedEntry(SQLModel, table=True):
    """Fetched RSS item before article extraction."""

    __tablename__ = "feed_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: str = Field(index=True, foreign_key="sources.id")
    title: str
    url: str = Field(index=True)
    canonical_url: Optional[str] = Field(default=None, index=True)
    slug: str = Field(index=True)
    summary: str = ""
    published_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=False), nullable=True))
    url_hash: str = Field(index=True)
    title_published_hash: str = Field(index=True)
    raw_entry_json: str = "{}"
    fetch_status: str = "pending"
    error_reason: Optional[str] = None
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )


class Article(SQLModel, table=True):
    """Stored article content."""

    __tablename__ = "articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: str = Field(index=True, foreign_key="sources.id")
    url: str = Field(index=True, unique=True)
    canonical_url: Optional[str] = Field(default=None, index=True)
    title: str
    slug: str = Field(unique=True, index=True)
    authors_json: str = "[]"
    published_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=False), nullable=True))
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=False), nullable=False),
    )
    language: Optional[str] = None
    category: Optional[str] = None
    summary: str = ""
    content_text: str
    content_html: str
    content_hash: str = Field(index=True, unique=True)
    reading_time_minutes: int = 1
    top_image: Optional[str] = None
    extraction_method: str = "unknown"
    extraction_success: bool = True
    metadata_json: str = "{}"
    is_favorite: bool = False
    read_later: bool = False


class SourceOut(BaseModel):
    """Public source response model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: str
    rss_url: str
    enabled: bool
    site_url: str
    language: str
    extraction_strategy: str
    article_count: int = 0


class ArticleSummaryOut(BaseModel):
    """Article list item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: str
    url: str
    canonical_url: Optional[str]
    title: str
    slug: str
    published_at: Optional[datetime]
    fetched_at: datetime
    language: Optional[str]
    category: Optional[str]
    summary: str
    reading_time_minutes: int
    top_image: Optional[str]
    extraction_method: str


class ArticleDetailOut(ArticleSummaryOut):
    """Full article response."""

    authors: list[str] = PydanticField(default_factory=list)
    content_text: str
    content_html: str
    metadata: dict[str, Any] = PydanticField(default_factory=dict)
    related_articles: list["ArticleSummaryOut"] = PydanticField(default_factory=list)


class PaginatedArticlesOut(BaseModel):
    """Paginated article response envelope."""

    items: list[ArticleSummaryOut]
    page: int
    page_size: int
    total: int
    total_pages: int


class HealthOut(BaseModel):
    """Health endpoint payload."""

    status: str
    app_name: str


class StatsOut(BaseModel):
    """Stats endpoint payload."""

    total_sources: int
    enabled_sources: int
    total_feed_entries: int
    total_articles: int
    successful_articles: int
    failed_feed_entries: int
    categories: dict[str, int]


class SearchOut(BaseModel):
    """Search endpoint payload."""

    query: str
    results: list[ArticleSummaryOut]


ArticleDetailOut.model_rebuild()
