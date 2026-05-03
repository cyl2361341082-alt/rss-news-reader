"""Utility helpers."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup
from feedparser import FeedParserDict

NOISE_TEXT_PATTERNS = (
    re.compile(r"^\d+\s+(minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\s+ago$", re.I),
)
NOISE_EXACT_LINES = {
    "share",
    "save",
    "add as preferred on google",
    "分享到 google 喜欢中",
    "分享",
    "保存",
}


def parse_datetime(value: Any) -> Optional[datetime]:
    """Convert RSS date values into UTC-naive datetimes."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value
    if hasattr(value, "tm_year"):
        return datetime(*value[:6])
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def normalize_url(url: str, base_url: str | None = None) -> str:
    """Normalize an article URL for deduplication."""

    if not url:
        return ""
    joined = urljoin(base_url or "", url)
    parsed = urlparse(joined)
    cleaned_query = "&".join(
        part
        for part in parsed.query.split("&")
        if part and not part.startswith(("utm_", "fbclid", "gclid"))
    )
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment="",
        query=cleaned_query,
    )
    path = re.sub(r"/{2,}", "/", normalized.path or "/")
    normalized = normalized._replace(path=path.rstrip("/") or "/")
    return urlunparse(normalized)


def slugify(value: str) -> str:
    """Create a filesystem-friendly and URL-friendly slug."""

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "article"


def short_hash(value: str) -> str:
    """Return a deterministic short hash."""

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def build_entry_slug(title: str, published_at: Optional[datetime], url: str = "") -> str:
    """Build a mostly stable article slug.

    Includes a short hash of the URL to prevent collisions when two articles
    published on the same day have similar titles.
    """

    date_part = published_at.strftime("%Y%m%d") if published_at else "undated"
    slug = f"{slugify(title)[:60]}-{date_part}"
    if url:
        slug = f"{slug}-{short_hash(url)[:8]}"
    return slug


def json_dumps(data: Any) -> str:
    """Serialize data into stable JSON."""

    return json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)


def json_loads(data: str | None, default: Any) -> Any:
    """Deserialize JSON with a fallback."""

    if not data:
        return default
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return default


def estimate_reading_time(text: str, words_per_minute: int = 220) -> int:
    """Estimate reading time in minutes."""

    words = len(text.split())
    return max(1, round(words / words_per_minute + 0.25))


def text_excerpt(text: str, limit: int = 240) -> str:
    """Create a plain-text excerpt."""

    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def normalize_text_for_compare(value: str) -> str:
    """Normalize text for duplicate detection."""

    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"[\"'`]+", "", value.lower())
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def is_noise_line(value: str, title: str | None = None) -> bool:
    """Return whether a line looks like extraction boilerplate."""

    compact = re.sub(r"\s+", " ", value).strip()
    if not compact:
        return True
    normalized = normalize_text_for_compare(compact)
    if normalized in NOISE_EXACT_LINES:
        return True
    if title and normalized == normalize_text_for_compare(title):
        return True
    return any(pattern.match(compact) for pattern in NOISE_TEXT_PATTERNS)


def sanitize_html(html: str) -> str:
    """Sanitize HTML for safe API delivery.

    Strips script/style tags, event-handler attributes, and javascript: hrefs
    while keeping safe structural and inline-formatting tags.
    """

    soup = BeautifulSoup(html or "", "lxml")
    for tag in soup(["script", "style", "noscript", "iframe", "object", "embed", "svg", "form", "input", "button", "textarea", "select"]):
        tag.decompose()
    for tag in soup.find_all(True):
        for attr in list(tag.attrs or {}):
            if attr.startswith("on") or attr == "style":
                del tag[attr]
        if tag.name == "a":
            href = str((tag.attrs or {}).get("href", "")).strip().lower()
            if href.startswith("javascript:"):
                del tag["href"]
        for img in soup.find_all("img"):
            src = str((img.attrs or {}).get("src", "")).strip().lower()
            if src.startswith("javascript:") or src.startswith("data:"):
                img.decompose()
    return str(soup)


def escape_like(value: str, escape_char: str = "\\") -> str:
    """Escape SQL LIKE metacharacters so they are matched literally."""

    for char in ("%", "_", escape_char):
        value = value.replace(char, escape_char + char)
    return value


def clean_html_fragment(html: str, title: str | None = None) -> str:
    """Remove noisy UI controls and wrappers from extracted HTML."""

    soup = BeautifulSoup(html or "", "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "button", "form", "input", "iframe", "object", "embed"]):
        tag.decompose()

    dangerous_attr_prefixes = ("on",)
    dangerous_attr_names = {"style"}
    for tag in list(soup.find_all(True)):
        attrs = dict(tag.attrs) if tag.attrs else {}
        for attr_name in list(attrs.keys()):
            if attr_name.startswith(dangerous_attr_prefixes) or attr_name in dangerous_attr_names:
                del tag[attr_name]
        if tag.name == "a":
            href = str(attrs.get("href", "")).strip().lower()
            if href.startswith("javascript:"):
                del tag["href"]

    for image in list(soup.find_all("img")):
        src = str((image.attrs or {}).get("src", "")).lower()
        alt = str((image.attrs or {}).get("alt", "")).lower()
        aria_label = str((image.attrs or {}).get("aria-label", "")).lower()
        class_names = " ".join(str(item) for item in (image.attrs or {}).get("class", []))
        if (
            "grey-placeholder" in src
            or "image unavailable" in alt
            or "image unavailable" in aria_label
            or "hide-when-no-script" in class_names
        ):
            image.decompose()

    attribute_noise_tokens = ("headline", "byline", "share", "save", "social", "google_preferred")
    for tag in list(soup.find_all(True)):
        attrs_map = tag.attrs or {}
        attrs = " ".join(
            str(value)
            for key, value in attrs_map.items()
            if key in {"class", "id", "data-component", "data-testid", "aria-label", "title"}
        ).lower()
        if any(token in attrs for token in attribute_noise_tokens):
            tag.decompose()
            continue
        if tag.name == "a" and "href" in attrs_map and "google.com/preferences/source" in str(attrs_map["href"]).lower():
            tag.decompose()
            continue
        text = tag.get_text(" ", strip=True)
        if tag.name == "time" and is_noise_line(text, title=title):
            tag.decompose()

    body = soup.body or soup
    first_heading = body.find(re.compile(r"^h[1-3]$"))
    if first_heading and title and normalize_text_for_compare(first_heading.get_text(" ", strip=True)) == normalize_text_for_compare(title):
        first_heading.decompose()

    return "".join(str(child) for child in body.children).strip()


def clean_text_content(text: str, title: str | None = None) -> str:
    """Remove noisy lines from extracted text."""

    lines = [line.strip() for line in text.splitlines()]
    kept = [line for line in lines if not is_noise_line(line, title=title)]
    return "\n".join(line for line in kept if line).strip()


def entry_to_dict(entry: FeedParserDict) -> dict[str, Any]:
    """Convert feedparser entry to plain dict."""

    return {key: entry.get(key) for key in entry.keys()}


def resolve_local_path(candidate: str, base_dir: Path) -> Path:
    """Resolve a possibly relative local path and verify it stays inside base_dir."""

    path = Path(candidate)
    resolved = path if path.is_absolute() else (base_dir / candidate).resolve()
    if not resolved.is_relative_to(base_dir.resolve()):
        raise ValueError(f"Path {candidate!r} escapes the allowed base directory")
    return resolved


def extract_domain(url: str) -> str:
    """Return the lowercased hostname for a URL."""

    return urlparse(url).netloc.lower()


def coalesce(*values: Any) -> Any:
    """Return the first non-empty value."""

    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None
