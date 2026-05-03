"""CSS selector extraction fallback."""

from __future__ import annotations

from bs4 import BeautifulSoup

from rss_news_reader.services.extraction_types import ExtractionResult


class CSSSelectorStrategy:
    """Extract content with source-specific CSS selectors."""

    def extract(self, html: str, selectors: list[str], source_name: str, url: str) -> ExtractionResult:
        """Extract content with CSS selectors."""

        soup = BeautifulSoup(html, "lxml")
        for selector in selectors:
            nodes = soup.select(selector)
            if not nodes:
                continue
            content_html = "\n".join(str(node) for node in nodes)
            text = "\n".join(node.get_text("\n", strip=True) for node in nodes).strip()
            if text:
                return ExtractionResult(
                    success=True,
                    method=f"css:{selector}",
                    title=(soup.title.string.strip() if soup.title and soup.title.string else source_name),
                    content_text=text,
                    content_html=content_html,
                )
        return ExtractionResult(success=False, method="css_selector", error_reason="empty_content")
