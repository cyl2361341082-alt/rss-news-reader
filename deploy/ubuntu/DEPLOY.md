# Ubuntu Deployment

This directory contains production deployment templates for a single Ubuntu server.

Included files:

- `backend.env.example`: backend environment variables
- `frontend.env.example`: frontend environment variables
- `rss-news-reader-api.service`: FastAPI systemd service
- `rss-news-reader-web.service`: Next.js systemd service
- `rss-news-reader-ingest.service`: one-shot ingestion job
- `rss-news-reader-ingest.timer`: periodic ingestion timer
- `rss-news-reader.nginx.conf`: Nginx reverse proxy example

Recommended stack:

- Ubuntu 22.04 or newer
- Python 3.11+
- `uv`
- Node.js 20+
- `nginx`
- `systemd`

Before using these files:

1. Replace `<DEPLOY_USER>` in the service files.
2. Copy this repository to `/opt/rss-news-reader`.
3. Copy `backend.env.example` to `backend.env` and adjust values.
4. Copy `frontend.env.example` to `frontend.env` and set your public domain.
5. Build the frontend with `npm run build`.
6. Install the service files into `/etc/systemd/system/`.
7. Install the Nginx file into `/etc/nginx/sites-available/`.

Do not store your SSH password in these files. Use SSH keys or type passwords directly into the terminal when prompted.
