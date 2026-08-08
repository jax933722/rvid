"""End-to-end tests for the export API (CSV / JSON / XLSX)."""

from __future__ import annotations

import io
import json

from fastapi.testclient import TestClient
from openpyxl import load_workbook


def _company(client: TestClient, name: str, host: str, **extra: object) -> int:
    body = {"display_name": name, "domains": [{"hostname": host, "is_primary": True}], **extra}
    res = client.post("/api/v1/companies", json=body)
    assert res.status_code == 201, res.text
    company_id: int = res.json()["id"]
    # Build its search projection so it shows up in search exports.
    assert client.post(f"/api/v1/companies/{company_id}/index").status_code == 202
    return company_id


def test_export_search_csv(client: TestClient) -> None:
    _company(client, "Acme Dental", "acme.com", industry="Dentistry", city="Sydney")
    res = client.post(
        "/api/v1/export/search?format=csv",
        json={"filters": [], "facets": [], "page": 1, "page_size": 25},
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment" in res.headers["content-disposition"]
    text = res.content.decode("utf-8-sig")
    assert "Acme Dental" in text
    assert "display_name" in text.splitlines()[0]


def test_export_search_xlsx(client: TestClient) -> None:
    _company(client, "Acme Dental", "acme.com")
    res = client.post(
        "/api/v1/export/search?format=xlsx",
        json={"filters": [], "facets": [], "page": 1, "page_size": 25},
    )
    assert res.status_code == 200
    assert res.headers["content-disposition"].endswith('.xlsx"')
    workbook = load_workbook(io.BytesIO(res.content))
    values = [c.value for c in workbook.active["B"]]
    assert "Acme Dental" in values


def test_export_list_json(client: TestClient) -> None:
    acme = _company(client, "Acme Dental", "acme.com", city="Sydney")
    list_id = client.post("/api/v1/lists", json={"name": "Targets"}).json()["id"]
    client.post(f"/api/v1/lists/{list_id}/companies", json={"company_id": acme})

    res = client.get(f"/api/v1/export/lists/{list_id}?format=json")
    assert res.status_code == 200
    payload = json.loads(res.content)
    assert len(payload) == 1
    assert payload[0]["display_name"] == "Acme Dental"
    assert payload[0]["city"] == "Sydney"


def test_export_missing_list_returns_404(client: TestClient) -> None:
    res = client.get("/api/v1/export/lists/999?format=csv")
    assert res.status_code == 404
