"""FastAPI tests."""

from __future__ import annotations


def test_api_health(client) -> None:
    """Health endpoint should return ok."""

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_articles_returns_seeded_data(client, seeded_data) -> None:
    """Articles endpoint should return stored articles."""

    response = client.get("/api/articles?page=1&page_size=10")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"]
