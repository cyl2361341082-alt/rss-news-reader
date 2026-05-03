"""Article fetching service."""

from __future__ import annotations

from datetime import UTC, datetime
from html import escape
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError

from rss_news_reader.config import Settings
from rss_news_reader.logging import get_logger
from rss_news_reader.models import Article, FeedEntry, Source
from rss_news_reader.repositories.articles import ArticleRepository
from rss_news_reader.repositories.feed_entries import FeedEntryRepository
from rss_news_reader.services.extractor import ArticleExtractor
from rss_news_reader.services.rate_limit import RateLimiter
from rss_news_reader.utils import clean_text_content, estimate_reading_time, json_dumps, json_loads, normalize_text_for_compare, normalize_url, parse_datetime, resolve_local_path, short_hash, text_excerpt


class BlockedBySourceError(Exception):
    """Raised when a source explicitly blocks article fetching."""


class BrowserFetchUnavailableError(Exception):
    """Raised when browser-based fetching is not available."""


_DEFAULT_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)


class ArticleFetcher:
    """Fetch article HTML, extract clean content, and store articles."""

    def __init__(
        self,
        settings: Settings,
        feed_entries: FeedEntryRepository,
        articles: ArticleRepository,
    ) -> None:
        self.settings = settings
        self.feed_entries = feed_entries
        self.articles = articles
        self.extractor = ArticleExtractor()
        self.rate_limiter = RateLimiter(settings.fetch_delay_seconds)
        self.logger = get_logger("article_fetcher")

    def fetch_entry(self, entry: FeedEntry, source: Source) -> Article | None:
        """Fetch and store one article in a single atomic transaction."""

        local_source = not source.rss_url.startswith(("http://", "https://"))
        url = entry.url if local_source and "://" not in entry.url else normalize_url(entry.url, base_url=source.site_url)
        if self.articles.get_by_url(url) or (entry.canonical_url and self.articles.get_by_canonical_url(entry.canonical_url)):
            entry.fetch_status = "skipped"
            entry.error_reason = "duplicate"
            self.feed_entries.update(entry)
            return None

        if source.allowed_domains_json:
            allowed_domains = json_loads(source.allowed_domains_json, [])
            hostname = urlparse(url).netloc.lower()
            if hostname and allowed_domains and hostname not in allowed_domains:
                entry.fetch_status = "failed"
                entry.error_reason = "blocked"
                self.feed_entries.update(entry)
                self._log_failure(entry, source, "blocked")
                return None

        self.rate_limiter.wait()
        try:
            html = self._read_article_html(url, source)
        except BlockedBySourceError:
            fallback_article = self._build_feed_fallback_article(entry, source, url, failure_reason="blocked")
            if fallback_article:
                return fallback_article
            entry.fetch_status = "failed"
            entry.error_reason = "blocked"
            self.feed_entries.update(entry)
            self._log_failure(entry, source, "blocked")
            return None
        except (httpx.RequestError, httpx.HTTPStatusError, OSError) as exc:
            self.logger.warning("fetch_network_error", url=url, error=str(exc))
            fallback_article = self._build_feed_fallback_article(entry, source, url, failure_reason="network_error")
            if fallback_article:
                return fallback_article
            entry.fetch_status = "failed"
            entry.error_reason = "network_error"
            self.feed_entries.update(entry)
            self._log_failure(entry, source, "network_error")
            return None

        result = self.extractor.extract(html, source, url)
        if not result.success or not result.content_text.strip():
            fallback_article = self._build_feed_fallback_article(
                entry,
                source,
                url,
                failure_reason=result.error_reason or "extraction_error",
            )
            if fallback_article:
                return fallback_article
            entry.fetch_status = "failed"
            entry.error_reason = result.error_reason or "extraction_error"
            self.feed_entries.update(entry)
            self._log_failure(entry, source, entry.error_reason)
            return None

        metadata = self._extract_metadata(html)
        canonical_url = normalize_url(result.canonical_url or metadata.get("canonical_url") or entry.canonical_url or url, base_url=source.site_url)
        content_hash = short_hash(result.content_text)

        try:
            article = Article(
                source_id=source.id,
                url=url,
                canonical_url=canonical_url,
                title=result.title or entry.title,
                slug=entry.slug,
                authors_json=json_dumps(result.authors or metadata.get("authors", [])),
                published_at=parse_datetime(result.published_at) or metadata.get("published_at") or entry.published_at,
                fetched_at=datetime.now(UTC),
                language=result.language or metadata.get("language") or source.language,
                category=result.category or source.category,
                summary=result.summary or entry.summary,
                content_text=result.content_text,
                content_html=result.content_html,
                content_hash=content_hash,
                reading_time_minutes=result.reading_time_minutes,
                top_image=result.top_image or metadata.get("top_image"),
                extraction_method=result.method,
                extraction_success=True,
                metadata_json=json_dumps(
                    {
                        "html_excerpt": result.html_excerpt,
                        "tags": result.tags or metadata.get("tags", []),
                        "source_name": source.name,
                    }
                ),
            )
            stored = self.articles.add_no_commit(article)
            entry.fetch_status = "fetched"
            entry.error_reason = None
            entry.canonical_url = canonical_url
            self.feed_entries.update_no_commit(entry)
            self.feed_entries.session.commit()
            return stored
        except IntegrityError:
            self.feed_entries.session.rollback()
            entry.fetch_status = "skipped"
            entry.error_reason = "duplicate"
            self.feed_entries.update(entry)
            return None

    def _build_feed_fallback_article(
        self,
        entry: FeedEntry,
        source: Source,
        url: str,
        failure_reason: str,
    ) -> Article | None:
        """Build a readable article from RSS entry data when page fetching fails."""

        payload = json_loads(entry.raw_entry_json, {})
        text_blocks = self._feed_text_blocks(entry, payload)
        content_text = "\n\n".join(text_blocks).strip()
        if len(content_text) < self.settings.min_feed_fallback_chars:
            return None

        canonical_url = normalize_url(entry.canonical_url or url, base_url=source.site_url)
        content_hash = short_hash(content_text)

        top_image = self._feed_top_image(payload)
        try:
            article = Article(
                source_id=source.id,
                url=url,
                canonical_url=canonical_url,
                title=entry.title,
                slug=entry.slug,
                authors_json=json_dumps(self._feed_authors(payload)),
                published_at=entry.published_at or parse_datetime(payload.get("published")),
                fetched_at=datetime.now(UTC),
                language=source.language,
                category=source.category,
                summary=text_excerpt(content_text),
                content_text=content_text,
                content_html="".join(f"<p>{escape(block)}</p>" for block in text_blocks),
                content_hash=content_hash,
                reading_time_minutes=estimate_reading_time(content_text),
                top_image=top_image,
                extraction_method="feed_fallback",
                extraction_success=True,
                metadata_json=json_dumps(
                    {
                        "feed_fallback": True,
                        "fallback_reason": failure_reason,
                        "source_name": source.name,
                        "tags": [],
                    }
                ),
            )
            stored = self.articles.add_no_commit(article)
            entry.fetch_status = "fetched"
            entry.error_reason = None
            entry.canonical_url = canonical_url
            self.feed_entries.update_no_commit(entry)
            self.feed_entries.session.commit()
            return stored
        except IntegrityError:
            self.feed_entries.session.rollback()
            entry.fetch_status = "skipped"
            entry.error_reason = "duplicate"
            self.feed_entries.update(entry)
            return None

    def retry_failures(self, source_map: dict[str, Source], limit: int) -> int:
        """Retry failed feed entries."""

        recovered = 0
        for entry in self.feed_entries.list_failed(limit=limit):
            source = source_map.get(entry.source_id)
            if source and self.fetch_entry(entry, source):
                recovered += 1
        return recovered

    def _read_article_html(self, url: str, source: Source | None = None) -> str:
        """Read article HTML from HTTP or local sample files."""

        if url.startswith(("http://", "https://")):
            try:
                return self._read_http_article_html(url, source)
            except BlockedBySourceError:
                if source and self._should_use_browser_fetch(source):
                    return self._read_browser_article_html(url, source)
                raise
        path = resolve_local_path(url, self.settings.samples_path)
        return path.read_text(encoding="utf-8")

    def _read_http_article_html(self, url: str, source: Source | None = None) -> str:
        """Fetch article HTML over plain HTTP."""

        with httpx.Client(
            timeout=self.settings.request_timeout_seconds,
            headers=self._request_headers(source),
            follow_redirects=True,
        ) as client:
            response = client.get(url)
            if response.status_code in {401, 403, 429} or self._looks_like_block_page(response.text):
                raise BlockedBySourceError(f"Blocked with HTTP {response.status_code}")
            response.raise_for_status()
            return response.text

    def _read_browser_article_html(self, url: str, source: Source) -> str:
        """Fetch article HTML through a real browser session."""

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserFetchUnavailableError(
                "Playwright is not installed. Run `uv sync` in backend and `playwright install chromium`."
            ) from exc

        storage_state = self.settings.browser_storage_state_file
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.settings.browser_headless)
            context_kwargs: dict[str, object] = {
                "user_agent": self._request_headers(source)["User-Agent"],
                "locale": "en-US",
                "extra_http_headers": {
                    key: value
                    for key, value in self._request_headers(source).items()
                    if key.lower() != "user-agent"
                },
            }
            if storage_state and storage_state.exists():
                context_kwargs["storage_state"] = str(storage_state)
            context = browser.new_context(**context_kwargs)
            try:
                page = context.new_page()
                page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.settings.browser_timeout_seconds * 1000,
                )
                try:
                    page.wait_for_selector("article, main", timeout=15_000)
                except Exception:
                    pass
                try:
                    page.wait_for_load_state("networkidle", timeout=5_000)
                except Exception:
                    pass
                html = page.content()
                if self._looks_like_block_page(html):
                    raise BlockedBySourceError("Browser session is still blocked by the source")
                return html
            finally:
                context.close()
                browser.close()

    def _extract_metadata(self, html: str) -> dict[str, object]:
        """Extract best-effort metadata from the raw page."""

        soup = BeautifulSoup(html, "lxml")
        canonical_tag = soup.find("link", rel="canonical")
        published_tag = soup.find("meta", attrs={"property": "article:published_time"}) or soup.find("meta", attrs={"name": "article:published_time"})
        language = soup.html.get("lang") if soup.html else None
        author_tags = soup.find_all("meta", attrs={"name": "author"})
        tag_nodes = soup.find_all("meta", attrs={"property": "article:tag"})
        top_image = soup.find("meta", attrs={"property": "og:image"})
        return {
            "canonical_url": canonical_tag.get("href") if canonical_tag else None,
            "published_at": parse_datetime(published_tag.get("content")) if published_tag else None,
            "language": language,
            "authors": [tag.get("content") for tag in author_tags if tag.get("content")],
            "tags": [tag.get("content") for tag in tag_nodes if tag.get("content")],
            "top_image": top_image.get("content") if top_image else None,
        }

    def _log_failure(self, entry: FeedEntry, source: Source, reason: str) -> None:
        """Append a failed request record to JSONL."""

        self.settings.failed_requests_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "source_id": source.id,
            "url": entry.url,
            "reason": reason,
        }
        with self.settings.failed_requests_file.open("a", encoding="utf-8") as handle:
            handle.write(json_dumps(payload) + "\n")

    def _should_use_browser_fetch(self, source: Source) -> bool:
        """Return whether a source should use browser fallback when blocked."""

        return self.settings.browser_fetch_enabled and source.id in self.settings.browser_source_ids

    def _request_headers(self, source: Source | None = None) -> dict[str, str]:
        """Return browser-like headers for article fetching."""

        headers = {
            "User-Agent": (
                self.settings.user_agent
                if self.settings.user_agent != "rss-news-reader/0.1 (+local)"
                else _DEFAULT_BROWSER_USER_AGENT
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
        if source:
            headers["Referer"] = source.site_url
        return headers

    @staticmethod
    def _looks_like_block_page(html: str) -> bool:
        """Return whether the response body looks like an anti-bot or JS challenge page."""

        lowered = (html or "").lower()
        markers = (
            "please enable js and disable any ad blocker",
            "are you a robot?",
            "access denied",
            "captcha",
            "bot detection",
        )
        return any(marker in lowered for marker in markers)

    @staticmethod
    def _feed_text_blocks(entry: FeedEntry, payload: dict[str, object]) -> list[str]:
        """Extract deduplicated text blocks from RSS entry metadata."""

        blocks: list[str] = []
        seen: set[str] = set()

        def add_block(value: str | None) -> None:
            if not value:
                return
            text = clean_text_content(BeautifulSoup(value, "lxml").get_text("\n", strip=True), title=entry.title)
            normalized = normalize_text_for_compare(text)
            if not text or normalized in seen:
                return
            seen.add(normalized)
            blocks.append(text)

        add_block(str(payload.get("summary") or entry.summary or ""))
        for item in payload.get("content") or []:
            if isinstance(item, dict):
                add_block(str(item.get("value") or ""))
        return blocks

    @staticmethod
    def _feed_authors(payload: dict[str, object]) -> list[str]:
        """Extract author names from RSS entry payload."""

        authors: list[str] = []
        for item in payload.get("authors") or []:
            if isinstance(item, dict) and item.get("name"):
                authors.append(str(item["name"]))
        if not authors and payload.get("author"):
            authors.append(str(payload["author"]))
        return authors

    @staticmethod
    def _feed_top_image(payload: dict[str, object]) -> str | None:
        """Extract an image URL from RSS entry metadata."""

        for key in ("media_content", "media_thumbnail"):
            for item in payload.get(key) or []:
                if isinstance(item, dict) and item.get("url"):
                    return str(item["url"])
        return None
