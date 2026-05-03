"""Typer CLI entrypoint."""

from __future__ import annotations

import json
from pathlib import Path

import typer
import uvicorn
from sqlmodel import Session

from rss_news_reader.config import get_settings
from rss_news_reader.db import get_engine
from rss_news_reader.pipeline import NewsPipeline
from rss_news_reader.repositories.sources import SourceRepository

app = typer.Typer(help="RSS news reader CLI.")

DEFAULT_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)


def _resolve_user_agent(settings) -> str:
    """Return either the configured user-agent or a real browser string."""

    if settings.user_agent and settings.user_agent != "rss-news-reader/0.1 (+local)":
        return settings.user_agent
    return DEFAULT_BROWSER_USER_AGENT


@app.command("init")
def init_command() -> None:
    """Initialize the database and source catalog."""

    NewsPipeline().init()
    typer.echo("Initialized database and synced sources.")


@app.command("fetch-feeds")
def fetch_feeds_command() -> None:
    """Fetch all enabled RSS feeds."""

    typer.echo(json.dumps(NewsPipeline().fetch_feeds(), indent=2))


@app.command("fetch-articles")
def fetch_articles_command(limit: int = typer.Option(100, min=1, help="Maximum pending entries to process.")) -> None:
    """Fetch article pages for pending feed entries."""

    typer.echo(f"Stored {NewsPipeline().fetch_articles(limit=limit)} articles.")


@app.command("run")
def run_command() -> None:
    """Run the full feed + article ingestion pipeline."""

    typer.echo(json.dumps(NewsPipeline().run(), indent=2))


@app.command("export")
def export_command(fmt: str = typer.Option("json", "--format", "-f")) -> None:
    """Export stored articles."""

    typer.echo(NewsPipeline().export(fmt=fmt))


@app.command("stats")
def stats_command() -> None:
    """Print pipeline stats."""

    typer.echo(json.dumps(NewsPipeline().stats(), indent=2))


@app.command("retry-failures")
def retry_failures_command() -> None:
    """Retry failed article requests."""

    typer.echo(f"Recovered {NewsPipeline().retry_failures()} items.")


@app.command("save-browser-state")
def save_browser_state_command(
    target: str = typer.Argument(..., help="Source id or a direct URL to open for manual login."),
    output: str | None = typer.Option(
        None,
        help="Path to write Playwright storage state JSON. Defaults to the configured browser storage state path.",
    ),
) -> None:
    """Open a real browser, let the user pass login/challenge, then save storage state."""

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise typer.BadParameter(
            "Playwright is not installed. Run `uv sync` and `python -m playwright install chromium` first."
        ) from exc

    settings = get_settings()
    resolved_output = output or settings.browser_storage_state_path or "data/playwright-state.json"
    output_path = Path(resolved_output)
    if not output_path.is_absolute():
        output_path = (settings.project_root / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    start_url = target
    with Session(get_engine()) as session:
        source = SourceRepository(session).get(target)
        if source:
            start_url = source.site_url

    typer.echo(f"Opening browser at {start_url}")
    typer.echo("Complete the login or anti-bot challenge in the browser window, then come back here.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent=_resolve_user_agent(settings),
            locale="en-US",
        )
        try:
            page = context.new_page()
            page.goto(
                start_url,
                wait_until="domcontentloaded",
                timeout=settings.browser_timeout_seconds * 1000,
            )
            typer.prompt("Press Enter after the page is fully usable", default="", show_default=False)
            context.storage_state(path=str(output_path))
        finally:
            context.close()
            browser.close()

    typer.echo(f"Saved browser storage state to {output_path}")
    typer.echo(
        "Set RSS_NEWS_READER_BROWSER_STORAGE_STATE_PATH to this file if you want the fetcher to reuse it."
    )


@app.command("repair-short-articles")
def repair_short_articles_command(
    max_length: int = typer.Option(300, min=1, help="Requeue articles whose text length is at or below this threshold."),
    source_id: str | None = typer.Option(None, help="Limit the repair to one source id."),
) -> None:
    """Requeue and refetch articles with suspiciously short bodies."""

    typer.echo(json.dumps(NewsPipeline().repair_short_articles(max_length=max_length, source_id=source_id), indent=2))


@app.command("test-source")
def test_source_command(source_id: str) -> None:
    """Fetch one source and show a short diagnostic summary."""

    typer.echo(json.dumps(NewsPipeline().test_source(source_id), indent=2))


@app.command("serve-api")
def serve_api_command(reload: bool = typer.Option(False, help="Enable reload for development.")) -> None:
    """Start the FastAPI application."""

    settings = get_settings()
    uvicorn.run(
        "rss_news_reader.api:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=reload,
    )
