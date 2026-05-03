"""Extractor tests."""

from __future__ import annotations

from rss_news_reader.models import Source
from rss_news_reader.services.extraction_types import ExtractionResult
from rss_news_reader.services.extractor import ArticleExtractor


def test_extractor_falls_back_to_css(monkeypatch) -> None:
    """Extractor should use CSS fallback when primary strategies fail."""

    extractor = ArticleExtractor()
    source = Source(
        id="sample-local",
        name="Sample",
        category="sample",
        rss_url="samples/sample_feed.xml",
        site_url="https://example.local",
        extraction_selectors_json='["article"]',
    )
    html = "<html><body><article><h1>Sample</h1><p>Fallback body content.</p></article></body></html>"

    monkeypatch.setattr(
        extractor.readability,
        "extract",
        lambda *_args, **_kwargs: ExtractionResult(success=False, method="readability", error_reason="parse_error"),
    )
    monkeypatch.setattr(
        extractor.trafilatura,
        "extract",
        lambda *_args, **_kwargs: ExtractionResult(success=False, method="trafilatura", error_reason="empty_content"),
    )

    result = extractor.extract(html, source, "https://example.local/story")

    assert result.success is True
    assert result.method.startswith("css:")
    assert "Fallback body content." in result.content_text


def test_extractor_prefers_longer_candidate(monkeypatch) -> None:
    """Extractor should prefer the more complete successful candidate."""

    extractor = ArticleExtractor()
    source = Source(
        id="sample-local",
        name="Sample",
        category="sample",
        rss_url="samples/sample_feed.xml",
        site_url="https://example.local",
        extraction_strategy="readability",
        extraction_selectors_json='["article"]',
    )
    html = "<html><body><article><p>Long body content from css.</p><p>Second paragraph.</p></article></body></html>"

    monkeypatch.setattr(
        extractor.readability,
        "extract",
        lambda *_args, **_kwargs: ExtractionResult(
            success=True,
            method="readability",
            content_text="Short quote only.",
            content_html="<p>Short quote only.</p>",
        ),
    )
    monkeypatch.setattr(
        extractor.trafilatura,
        "extract",
        lambda *_args, **_kwargs: ExtractionResult(
            success=True,
            method="trafilatura",
            content_text="This is a much longer article body with more context and details.",
            content_html="<p>This is a much longer article body with more context and details.</p>",
        ),
    )

    result = extractor.extract(html, source, "https://example.local/story")

    assert result.success is True
    assert result.method == "trafilatura"
    assert "much longer article body" in result.content_text


def test_extractor_cleans_duplicate_title_and_share_ui(monkeypatch) -> None:
    """Extractor should remove duplicate title and share/save boilerplate."""

    extractor = ArticleExtractor()
    source = Source(
        id="sample-local",
        name="Sample",
        category="sample",
        rss_url="samples/sample_feed.xml",
        site_url="https://example.local",
        extraction_strategy="css_selector",
        extraction_selectors_json='["article"]',
    )
    title = "Example headline"
    html = f"""
    <html>
      <body>
        <article>
          <div data-component="headline-block"><h1>{title}</h1></div>
          <div data-testid="byline">
            <time>9 hours ago</time>
            <button>Share</button>
            <button>Save</button>
            <a href="https://www.google.com/preferences/source?q=bbc.com">Add as preferred on Google</a>
          </div>
          <p>Real first paragraph.</p>
          <p>Real second paragraph.</p>
        </article>
      </body>
    </html>
    """

    result = extractor.extract(html, source, "https://example.local/story")

    assert result.success is True
    assert title not in result.content_text
    assert "Share" not in result.content_text
    assert "Add as preferred on Google" not in result.content_text
    assert "Real first paragraph." in result.content_text


def test_extractor_removes_placeholder_images() -> None:
    """Extractor should remove BBC placeholder images from cleaned HTML."""

    extractor = ArticleExtractor()
    source = Source(
        id="sample-local",
        name="Sample",
        category="sample",
        rss_url="samples/sample_feed.xml",
        site_url="https://example.local",
        extraction_strategy="css_selector",
        extraction_selectors_json='["article"]',
    )
    html = """
    <html>
      <body>
        <article>
          <img src="https://static.files.bbci.co.uk/grey-placeholder.png" aria-label="image unavailable" class="hide-when-no-script" />
          <img src="https://ichef.bbci.co.uk/news/example.jpg.webp" alt="Real image" />
          <p>Body paragraph.</p>
        </article>
      </body>
    </html>
    """

    result = extractor.extract(html, source, "https://example.local/story")

    assert result.success is True
    assert "grey-placeholder" not in result.content_html
    assert "example.jpg.webp" in result.content_html
