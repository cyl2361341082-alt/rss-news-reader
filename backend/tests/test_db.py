"""Repository tests."""

from __future__ import annotations

from sqlmodel import Session


def test_article_repository_round_trip(session: Session) -> None:
    """Article repository should persist and retrieve an article."""

    from rss_news_reader.models import Article
    from rss_news_reader.repositories.articles import ArticleRepository

    repo = ArticleRepository(session)
    article = repo.add(
        Article(
            source_id="sample-local",
            url="https://example.local/story",
            canonical_url="https://example.local/story",
            title="Stored story",
            slug="stored-story-20240402",
            content_text="A stored article body.",
            content_html="<p>A stored article body.</p>",
            content_hash="hash-1",
            reading_time_minutes=1,
        )
    )

    loaded = repo.get_by_slug(article.slug)

    assert loaded is not None
    assert loaded.title == "Stored story"
