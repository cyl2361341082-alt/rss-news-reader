# rss-news-reader backend

Python backend for `rss-news-reader`.

Includes:

- RSS source loading
- feed fetching
- article extraction
- SQLite storage
- FastAPI JSON API
- Typer CLI

Typical commands:

```bash
uv sync
uv run news init
uv run news run
uv run news serve-api
```
