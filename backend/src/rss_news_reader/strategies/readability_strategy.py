"""Readability-based content extraction."""

from __future__ import annotations

import logging

from bs4 import BeautifulSoup
from readability import Document

from rss_news_reader.services.extraction_types import ExtractionResult
from rss_news_reader.utils import text_excerpt

logger = logging.getLogger(__name__)


class ReadabilityStrategy:
    """Extract readable content using readability-lxml."""

    def extract(self, html: str, _source, _url: str) -> ExtractionResult:
        """Extract article body with readability."""

        try:
            document = Document(html)
            summary_html = document.summary(html_partial=True)
            summary_title = document.short_title()
            soup = BeautifulSoup(summary_html, "lxml")
            text = soup.get_text("\n", strip=True).strip()
            if not text:
                return ExtractionResult(success=False, method="readability", error_reason="empty_content")
            return ExtractionResult(
                success=True,
                method="readability",
                title=summary_title or "",
                content_text=text,
                content_html=summary_html,
                html_excerpt=text_excerpt(text, 400),
            )
        except (ValueError, TypeError, AttributeError, KeyError, IndexError, RecursionError) as exc:
            logger.debug("readability extraction failed: %s", exc)
            return ExtractionResult(success=False, method="readability", error_reason="parse_error")
