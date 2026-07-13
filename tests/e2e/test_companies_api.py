"""End-to-end API tests via FastAPI TestClient (real SQLite behind the app)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_readiness_checks_database(client: TestClient) -> None:
    assert client.get("/api/v1/health/ready").json() == {"status": "ready"}


def test_create_then_get_company(client: TestClient) -> None:
    payload = {
        "display_name": "Acme Dental",
        "industry": "Dentistry",
        "domains": [{"hostname": "acme.com", "is_primary": True}],
    }
    created = client.post("/api/v1/companies", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["id"] is not None
    assert body["domains"][0]["hostname"] == "acme.com"

    fetched = client.get(f"/api/v1/companies/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["display_name"] == "Acme Dental"


def test_get_missing_company_returns_404(client: TestClient) -> None:
    resp = client.get("/api/v1/companies/999999")
    assert resp.status_code == 404
    assert resp.json()["title"] == "Not Found"


def test_duplicate_domain_returns_409(client: TestClient) -> None:
    payload = {"display_name": "A", "domains": [{"hostname": "dup.com"}]}
    assert client.post("/api/v1/companies", json=payload).status_code == 201
    second = client.post(
        "/api/v1/companies",
        json={"display_name": "B", "domains": [{"hostname": "dup.com"}]},
    )
    assert second.status_code == 409


def test_list_companies_pagination(client: TestClient) -> None:
    for i in range(3):
        client.post(
            "/api/v1/companies",
            json={"display_name": f"Co {i}", "domains": [{"hostname": f"co{i}.com"}]},
        )
    resp = client.get("/api/v1/companies", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
