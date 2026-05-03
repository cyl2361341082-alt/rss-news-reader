"""Trafilatura fallback extraction."""

from __future__ import annotations

import logging

import trafilatura

from rss_news_reader.services.extraction_types import ExtractionResult

logger = logging.getLogger(__name__)


class TrafilaturaStrategy:
    """Extract content with trafilatura as a fallback."""

    def extract(self, html: str, _source, url: str) -> ExtractionResult:
        """Extract article body with trafilatura.

        Extracts once with HTML output and derives plain text from it
        to avoid running the extraction pipeline twice.
        """

        try:
            html_content = trafilatura.extract(
                html,
                url=url,
                output_format="html",
                include_comments=False,
                include_tables=False,
            ) or ""
            if not html_content.strip():
                return ExtractionResult(success=False, method="trafilatura", error_reason="empty_content")
            from bs4 import BeautifulSoup

            text = BeautifulSoup(html_content, "lxml").get_text("\n", strip=True).strip()
            if not text:
                return ExtractionResult(success=False, method="trafilatura", error_reason="empty_content")
            return ExtractionResult(
                success=True,
                method="trafilatura",
                content_text=text,
                content_html=html_content.strip(),
            )
        except (ValueError, TypeError, AttributeError, KeyError, IndexError, RecursionError) as exc:
            logger.debug("trafilatura extraction failed: %s", exc)
            return ExtractionResult(success=False, method="trafilatura", error_reason="parse_error")
