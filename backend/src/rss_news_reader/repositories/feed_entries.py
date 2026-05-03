"""Feed entry repository."""

from __future__ import annotations

from sqlmodel import Session, select

from rss_news_reader.models import FeedEntry


class FeedEntryRepository:
    """Persistence operations for feed entries."""

    def __init__(self, session: Session):
        self.session = session

    def add(self, entry: FeedEntry) -> FeedEntry:
        """Persist and commit a feed entry."""

        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def add_no_commit(self, entry: FeedEntry) -> FeedEntry:
        """Stage a feed entry without committing — caller controls the transaction."""

        self.session.add(entry)
        self.session.flush()
        self.session.refresh(entry)
        return entry

    def update(self, entry: FeedEntry) -> FeedEntry:
        """Persist and commit changes to an existing feed entry."""

        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def update_no_commit(self, entry: FeedEntry) -> FeedEntry:
        """Stage feed entry changes without committing — caller controls the transaction."""

        self.session.add(entry)
        self.session.flush()
        self.session.refresh(entry)
        return entry

    def list_pending(self, limit: int = 100) -> list[FeedEntry]:
        """Return pending feed entries for article extraction."""

        statement = (
            select(FeedEntry)
            .where(FeedEntry.fetch_status == "pending")
            .order_by(FeedEntry.published_at.desc(), FeedEntry.id.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def list_failed(self, limit: int = 50) -> list[FeedEntry]:
        """Return failed feed entries."""

        statement = (
            select(FeedEntry)
            .where(FeedEntry.fetch_status == "failed")
            .order_by(FeedEntry.id.desc())
            .limit(limit)
        )
        return list(self.session.exec(statement))

    def get_by_url_hash(self, url_hash: str) -> FeedEntry | None:
        """Find a feed entry by URL hash."""

        return self.session.exec(select(FeedEntry).where(FeedEntry.url_hash == url_hash)).first()

    def get_by_canonical_url(self, canonical_url: str) -> FeedEntry | None:
        """Find a feed entry by canonical URL."""

        return self.session.exec(select(FeedEntry).where(FeedEntry.canonical_url == canonical_url)).first()

    def get_by_title_published_hash(self, hash_value: str) -> FeedEntry | None:
        """Find a feed entry by title and published timestamp hash."""

        return self.session.exec(select(FeedEntry).where(FeedEntry.title_published_hash == hash_value)).first()
