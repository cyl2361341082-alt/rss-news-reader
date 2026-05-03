"""Article extraction orchestrator."""

from __future__ import annotations

from typing import Optional

from bs4 import BeautifulSoup

from rss_news_reader.models import Source
from rss_news_reader.services.extraction_types import ExtractionResult
from rss_news_reader.strategies.css_selector_strategy import CSSSelectorStrategy
from rss_news_reader.strategies.readability_strategy import ReadabilityStrategy
from rss_news_reader.strategies.trafilatura_strategy import TrafilaturaStrategy
from rss_news_reader.utils import clean_html_fragment, clean_text_content, coalesce, estimate_reading_time, text_excerpt


class ArticleExtractor:
    """Try multiple extraction strategies in order."""

    def __init__(self) -> None:
        self.readability = ReadabilityStrategy()
        self.trafilatura = TrafilaturaStrategy()
        self.css = CSSSelectorStrategy()

    def extract(self, html: str, source: Source, url: str) -> ExtractionResult:
        """Extract article content from raw HTML."""

        strategies = self._strategies_for_source(source)
        errors: list[str] = []
        candidates: list[ExtractionResult] = []
        for strategy in strategies:
            result = strategy(html, source, url)
            if result.success and result.content_text.strip():
                finalized = self._finalize(result, html, source)
                if source.extraction_strategy == "css_selector" and finalized.method.startswith("css:"):
                    return finalized
                candidates.append(finalized)
            if result.error_reason:
                errors.append(result.error_reason)
        if candidates:
            return max(candidates, key=lambda item: len(item.content_text.strip()))
        return ExtractionResult(
            success=False,
            method="none",
            error_reason=errors[-1] if errors else "extraction_error",
        )

    def _strategies_for_source(self, source: Source):
        """Return extraction functions in source-preferred order."""

        css_strategy = lambda value, source_value, url_value: self.css.extract(
            value,
            selectors=self._selectors(source),
            source_name=source.name,
            url=url_value,
        )
        strategy_map = {
            "readability": [self.readability.extract, self.trafilatura.extract, css_strategy],
            "trafilatura": [self.trafilatura.extract, self.readability.extract, css_strategy],
            "css_selector": [css_strategy, self.readability.extract, self.trafilatura.extract],
        }
        return strategy_map.get(source.extraction_strategy, strategy_map["readability"])

    def _selectors(self, source: Source) -> list[str]:
        from rss_news_reader.utils import json_loads

        return json_loads(source.extraction_selectors_json, [])

    def _finalize(self, result: ExtractionResult, html: str, source: Source) -> ExtractionResult:
        soup = BeautifulSoup(html, "lxml")
        result.title = coalesce(result.title, self._meta_content(soup, "og:title"), source.name) or source.name
        result.top_image = coalesce(result.top_image, self._meta_content(soup, "og:image"))
        result.content_html = clean_html_fragment(result.content_html, title=result.title)
        cleaned_text_from_html = BeautifulSoup(result.content_html, "lxml").get_text("\n", strip=True)
        result.content_text = clean_text_content(cleaned_text_from_html or result.content_text, title=result.title)
        result.html_excerpt = clean_html_fragment(result.content_html[:1200], title=result.title)
        result.summary = text_excerpt(result.content_text)
        result.reading_time_minutes = estimate_reading_time(result.content_text)
        return result

    @staticmethod
    def _meta_content(soup: BeautifulSoup, property_name: str) -> Optional[str]:
        tag = soup.find("meta", attrs={"property": property_name}) or soup.find("meta", attrs={"name": property_name})
        return tag.get("content") if tag else None
