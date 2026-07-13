"""End-to-end search test: crawl -> enrich -> index -> search (no network)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from bise.presentation.workers.crawl_worker import process_pending_jobs
from tests.fakes.fetcher import FakePageFetcher

WP_HOME = (
    '<html><head><meta name="generator" content="WordPress 6.4">'
    "<title>Acme Dental Sydney</title>"
    '<script src="https://connect.facebook.net/en_US/fbevents.js"></script></head>'
    '<body><h1>Dentist</h1><a href="/contact">Contact</a></body></html>'
)


def _pipeline(client: TestClient, container: Container) -> int:
    client.post(
        "/api/v1/companies",
        json={
            "display_name": "Acme Dental",
            "industry": "Dentistry",
            "domains": [{"hostname": "acme.com"}],
        },
    )
    company_id = int(client.get("/api/v1/companies").json()["items"][0]["id"])
    client.post("/api/v1/crawl", json={"hostname": "acme.com"})

    container._fetcher = FakePageFetcher(  # noqa: SLF001 - test wiring
        {
            "https://acme.com/": FetchedPage(
                url="https://acme.com/",
                status_code=200,
                ok=True,
                html=WP_HOME,
                content_type="text/html",
            ),
            "https://acme.com/contact": FetchedPage(
                url="https://acme.com/contact",
                status_code=200,
                ok=True,
                html="<html><title>Contact</title></html>",
                content_type="text/html",
            ),
        }
    )
    container._html_parser = BeautifulSoupHtmlParser()  # noqa: SLF001 - test wiring
    process_pending_jobs(container)

    client.post(f"/api/v1/companies/{company_id}/technologies/detect")
    client.post(f"/api/v1/companies/{company_id}/seo/scan")
    assert client.post(f"/api/v1/companies/{company_id}/index").status_code == 202
    return company_id


def test_sales_navigator_style_search(client: TestClient, container: Container) -> None:
    _pipeline(client, container)

    body = {
        "text": "dental",
        "filters": [
            {"field": "industry", "op": "eq", "values": ["Dentistry"]},
            {"field": "technology", "op": "contains", "values": ["WordPress"]},
            {"field": "has_contact_page", "op": "is_true", "values": []},
            {"field": "seo_score", "op": "lte", "values": ["100"]},
        ],
        "facets": ["industry", "technology"],
    }
    resp = client.post("/api/v1/search", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["display_name"] == "Acme Dental"
    assert "WordPress" in item["technologies"]
    assert {f["value"] for f in data["facets"]["industry"]} == {"Dentistry"}


def test_search_excludes_non_matching_filters(client: TestClient, container: Container) -> None:
    _pipeline(client, container)
    body = {"filters": [{"field": "technology", "op": "contains", "values": ["Shopify"]}]}
    assert client.post("/api/v1/search", json=body).json()["total"] == 0


def test_invalid_filter_field_returns_422(client: TestClient) -> None:
    body = {"filters": [{"field": "not_a_field", "op": "eq", "values": ["x"]}]}
    assert client.post("/api/v1/search", json=body).status_code == 422


def test_empty_search_returns_all_indexed(client: TestClient, container: Container) -> None:
    _pipeline(client, container)
    assert client.post("/api/v1/search", json={}).json()["total"] == 1
