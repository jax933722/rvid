"""End-to-end tests for the workspace API (saved searches, lists, tags)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _create_company(client: TestClient, name: str, host: str) -> int:
    res = client.post(
        "/api/v1/companies",
        json={"display_name": name, "domains": [{"hostname": host, "is_primary": True}]},
    )
    assert res.status_code == 201, res.text
    company_id: int = res.json()["id"]
    return company_id


def test_saved_search_endpoints(client: TestClient) -> None:
    payload = {"text": "dentist", "filters": [], "facets": [], "page": 1, "page_size": 25}
    created = client.post("/api/v1/saved-searches", json={"name": "Dentists", "query": payload})
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["name"] == "Dentists"
    assert body["query"]["text"] == "dentist"  # round-trips as structured JSON

    listed = client.get("/api/v1/saved-searches")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted = client.delete(f"/api/v1/saved-searches/{body['id']}")
    assert deleted.status_code == 204
    assert client.get("/api/v1/saved-searches").json() == []


def test_list_endpoints(client: TestClient) -> None:
    acme = _create_company(client, "Acme", "acme.com")

    created = client.post("/api/v1/lists", json={"name": "Outreach"})
    assert created.status_code == 201, created.text
    list_id = created.json()["id"]

    added = client.post(f"/api/v1/lists/{list_id}/companies", json={"company_id": acme})
    assert added.status_code == 200
    assert added.json()["member_count"] == 1

    members = client.get(f"/api/v1/lists/{list_id}/companies")
    assert members.status_code == 200
    assert [c["display_name"] for c in members.json()] == ["Acme"]

    removed = client.delete(f"/api/v1/lists/{list_id}/companies/{acme}")
    assert removed.status_code == 204
    assert client.get(f"/api/v1/lists/{list_id}/companies").json() == []

    assert client.delete(f"/api/v1/lists/{list_id}").status_code == 204


def test_add_to_missing_list_returns_404(client: TestClient) -> None:
    acme = _create_company(client, "Acme", "acme.com")
    res = client.post("/api/v1/lists/999/companies", json={"company_id": acme})
    assert res.status_code == 404


def test_tag_endpoints(client: TestClient) -> None:
    acme = _create_company(client, "Acme", "acme.com")

    created = client.post(f"/api/v1/companies/{acme}/tags", json={"label": "Priority"})
    assert created.status_code == 201, created.text
    assert created.json()["label"] == "priority"  # normalized

    tags = client.get(f"/api/v1/companies/{acme}/tags")
    assert [t["label"] for t in tags.json()] == ["priority"]

    removed = client.delete(f"/api/v1/companies/{acme}/tags/priority")
    assert removed.status_code == 204
    assert client.get(f"/api/v1/companies/{acme}/tags").json() == []
