"""End-to-end tests for search response caching and its invalidation."""

from __future__ import annotations

from fastapi.testclient import TestClient

_QUERY = {"filters": [], "facets": [], "page": 1, "page_size": 25}


def _company(client: TestClient, name: str, host: str) -> int:
    res = client.post(
        "/api/v1/companies",
        json={"display_name": name, "domains": [{"hostname": host, "is_primary": True}]},
    )
    assert res.status_code == 201, res.text
    company_id: int = res.json()["id"]
    return company_id


def test_identical_search_is_cached(client: TestClient) -> None:
    first = client.post("/api/v1/search", json=_QUERY)
    assert first.status_code == 200
    assert first.headers["X-Cache"] == "MISS"

    second = client.post("/api/v1/search", json=_QUERY)
    assert second.headers["X-Cache"] == "HIT"
    assert second.json() == first.json()


def test_reindex_invalidates_cache(client: TestClient) -> None:
    # Warm the cache with an empty result set.
    assert client.post("/api/v1/search", json=_QUERY).json()["total"] == 0
    assert client.post("/api/v1/search", json=_QUERY).headers["X-Cache"] == "HIT"

    # Index a company -> cache cleared -> the next search sees it (fresh MISS).
    acme = _company(client, "Acme Dental", "acme.com")
    assert client.post(f"/api/v1/companies/{acme}/index").status_code == 202

    after = client.post("/api/v1/search", json=_QUERY)
    assert after.headers["X-Cache"] == "MISS"
    assert after.json()["total"] == 1


def test_distinct_queries_are_cached_separately(client: TestClient) -> None:
    a = client.post("/api/v1/search", json={**_QUERY, "text": "alpha"})
    b = client.post("/api/v1/search", json={**_QUERY, "text": "beta"})
    assert a.headers["X-Cache"] == "MISS"
    assert b.headers["X-Cache"] == "MISS"  # different key, not served from a's entry
    again = client.post("/api/v1/search", json={**_QUERY, "text": "alpha"})
    assert again.headers["X-Cache"] == "HIT"
