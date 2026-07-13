"""End-to-end tests for the crawler API and worker flow (no network)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from bise.presentation.workers.crawl_worker import process_pending_jobs
from tests.fakes.fetcher import FakePageFetcher

HOME_HTML = (
    '<html><head><title>Acme</title></head><body><a href="/contact">Contact</a></body></html>'
)


def _create_company(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/companies",
        json={"display_name": "Acme", "domains": [{"hostname": "acme.com"}]},
    )
    assert resp.status_code == 201


def test_request_crawl_for_unknown_host_returns_404(client: TestClient) -> None:
    resp = client.post("/api/v1/crawl", json={"hostname": "nobody.com"})
    assert resp.status_code == 404


def test_request_crawl_creates_pending_job(client: TestClient) -> None:
    _create_company(client)
    resp = client.post("/api/v1/crawl", json={"hostname": "acme.com"})
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "pending"

    listed = client.get("/api/v1/crawlers/jobs", params={"status": "pending"})
    assert listed.json()["total"] == 1


def test_worker_processes_job_end_to_end(client: TestClient, container: Container) -> None:
    _create_company(client)
    job_id = client.post("/api/v1/crawl", json={"hostname": "acme.com"}).json()["id"]

    # Inject deterministic fetcher/parser into the shared container, then run the worker.
    container._fetcher = FakePageFetcher(  # noqa: SLF001 - test wiring
        {
            "https://acme.com/": FetchedPage(
                url="https://acme.com/",
                status_code=200,
                ok=True,
                html=HOME_HTML,
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

    processed = process_pending_jobs(container)
    assert processed == 1

    detail = client.get(f"/api/v1/crawlers/jobs/{job_id}").json()
    assert detail["status"] == "completed"
    assert detail["pages_crawled"] == 2
    page_types = {p["page_type"] for p in detail["pages"]}
    assert page_types == {"home", "contact"}
