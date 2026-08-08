"""End-to-end tests for the enrichment queue API (no live crawl)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from tests.fakes.fetcher import FakePageFetcher

WP_HOME = (
    '<html><head><meta name="generator" content="WordPress 6.4">'
    "<title>Acme Dental — Sydney</title></head><body><h1>Dentist</h1>"
    '<a href="/contact">Contact</a></body></html>'
)


def _company(client: TestClient, name: str, host: str) -> int:
    res = client.post(
        "/api/v1/companies",
        json={"display_name": name, "domains": [{"hostname": host, "is_primary": True}]},
    )
    assert res.status_code == 201, res.text
    company_id: int = res.json()["id"]
    return company_id


def test_enqueue_and_status(client: TestClient) -> None:
    acme = _company(client, "Acme", "acme.com")
    res = client.post("/api/v1/enrichment/jobs", json={"company_ids": [acme]})
    assert res.status_code == 202, res.text
    assert res.json()["enqueued"] == 1

    status = client.get("/api/v1/enrichment/queue")
    assert status.status_code == 200
    assert status.json()["counts"].get("pending") == 1
    assert len(status.json()["recent"]) == 1


def test_enqueue_missing_list_returns_404(client: TestClient) -> None:
    res = client.post("/api/v1/enrichment/jobs", json={"list_id": 999})
    assert res.status_code == 404


def test_run_drains_queue_and_makes_searchable(client: TestClient, container: Container) -> None:
    # Wire offline crawl so the real enrichment pipeline runs without network.
    container._fetcher = FakePageFetcher(  # noqa: SLF001 - test wiring
        {
            "https://acme.com/": FetchedPage(
                url="https://acme.com/",
                status_code=200,
                ok=True,
                html=WP_HOME,
                content_type="text/html",
            )
        }
    )
    container._html_parser = BeautifulSoupHtmlParser()  # noqa: SLF001

    acme = _company(client, "Acme", "acme.com")
    client.post("/api/v1/enrichment/jobs", json={"company_ids": [acme]})

    run = client.post("/api/v1/enrichment/run?max_jobs=5")
    assert run.status_code == 200
    assert run.json()["processed"] == 1

    # The queue is drained and the company is now searchable by its technology.
    assert client.get("/api/v1/enrichment/queue").json()["counts"].get("completed") == 1
    search = client.post(
        "/api/v1/search",
        json={
            "filters": [{"field": "technology", "op": "contains", "values": ["WordPress"]}],
            "facets": [],
            "page": 1,
            "page_size": 25,
        },
    )
    assert search.status_code == 200
    assert search.json()["total"] == 1
