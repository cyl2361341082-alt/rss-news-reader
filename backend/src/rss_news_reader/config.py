"""Application configuration loading."""

from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SourceConfig(BaseModel):
    """Configuration for a single RSS source."""

    id: str
    name: str
    category: str
    rss_url: str
    enabled: bool = True
    site_url: str
    language: str = "en"
    extraction_strategy: str = "readability"
    allowed_domains: list[str] = Field(default_factory=list)
    extraction_selectors: list[str] = Field(default_factory=list)


class Settings(BaseSettings):
    """Runtime settings with environment override support."""

    app_name: str = "rss-news-reader"
    environment: str = "development"
    database_url: str = "sqlite:///data/news.db"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    request_timeout_seconds: int = 20
    user_agent: str = "rss-news-reader/0.1 (+local)"
    browser_fetch_enabled: bool = True
    browser_fetch_sources: str = "wsj-world-news,wsj-markets"
    browser_storage_state_path: str | None = None
    browser_headless: bool = True
    browser_timeout_seconds: int = 45
    default_page_size: int = 10
    max_page_size: int = 50
    fetch_delay_seconds: float = 0.5
    retry_failed_limit: int = 50
    min_feed_fallback_chars: int = 250
    export_dir: str = "data/exports"
    failed_requests_path: str = "data/failed_requests.jsonl"
    samples_dir: str = "samples"
    config_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2] / "config")

    model_config = SettingsConfigDict(
        env_prefix="RSS_NEWS_READER_",
        extra="ignore",
    )

    @property
    def project_root(self) -> Path:
        """Return the backend project root."""

        return self.config_dir.parent

    @property
    def db_path(self) -> Path:
        """Return the resolved SQLite file path."""

        if self.database_url.startswith("sqlite:///"):
            return (self.project_root / self.database_url.removeprefix("sqlite:///")).resolve()
        return self.project_root / "data" / "news.db"

    @property
    def export_path(self) -> Path:
        """Return the resolved export directory."""

        return (self.project_root / self.export_dir).resolve()

    @property
    def failed_requests_file(self) -> Path:
        """Return the resolved failure log file."""

        return (self.project_root / self.failed_requests_path).resolve()

    @property
    def samples_path(self) -> Path:
        """Return the resolved samples directory."""

        return (self.project_root / self.samples_dir).resolve()

    @property
    def browser_source_ids(self) -> set[str]:
        """Return sources that should use browser fallback when blocked."""

        return {
            item.strip()
            for item in self.browser_fetch_sources.split(",")
            if item.strip()
        }

    @property
    def browser_storage_state_file(self) -> Path | None:
        """Return the optional Playwright storage state file."""

        if not self.browser_storage_state_path:
            return None
        return (self.project_root / self.browser_storage_state_path).resolve()


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary."""

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load merged settings from YAML and environment variables."""

    env_config_dir = os.environ.get("RSS_NEWS_READER_CONFIG_DIR")
    default_config_dir = (
        Path(env_config_dir).resolve()
        if env_config_dir
        else Path(__file__).resolve().parents[2] / "config"
    )
    yaml_data = _load_yaml(default_config_dir / "settings.yaml")
    base = Settings(config_dir=default_config_dir)
    overrides = {
        key: value
        for key, value in yaml_data.items()
        if f"RSS_NEWS_READER_{key.upper()}" not in os.environ
    }
    return base.model_copy(update=overrides)


@lru_cache(maxsize=1)
def get_sources_config() -> list[SourceConfig]:
    """Load source definitions from YAML."""

    settings = get_settings()
    data = _load_yaml(settings.config_dir / "sources.yaml")
    sources = data.get("sources", [])
    return [SourceConfig.model_validate(item) for item in sources]


def reset_settings_cache() -> None:
    """Clear cached settings and sources — useful after env or YAML changes."""

    get_settings.cache_clear()
    get_sources_config.cache_clear()
