"""Shared extraction result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExtractionResult:
    """Normalized article extraction payload."""

    success: bool
    method: str
    title: str = ""
    authors: list[str] = field(default_factory=list)
    published_at: Optional[str] = None
    canonical_url: Optional[str] = None
    content_text: str = ""
    content_html: str = ""
    html_excerpt: str = ""
    top_image: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    category: Optional[str] = None
    language: Optional[str] = None
    error_reason: Optional[str] = None
    summary: str = ""
    reading_time_minutes: int = 1
