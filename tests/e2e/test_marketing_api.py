"""End-to-end tests for the marketing API (crawl -> detect -> read)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from bise.presentation.workers.crawl_worker import process_pending_jobs
from tests.fakes.fetcher import FakePageFetcher

HOME = (
    "<html><head>"
    '<script src="https://connect.facebook.net/en_US/fbevents.js"></script>'
    '</head><body><a href="/contact">Contact</a>'
    '<a href="https://wa.me/61400000000">WhatsApp</a></body></html>'
)


def _crawl(client: TestClient, container: Container) -> int:
    client.post(
        "/api/v1/companies", json={"display_name": "Acme", "domains": [{"hostname": "acme.com"}]}
    )
    company_id = int(client.get("/api/v1/companies").json()["items"][0]["id"])
    client.post("/api/v1/crawl", json={"hostname": "acme.com"})
    container._fetcher = FakePageFetcher(  # noqa: SLF001 - test wiring
        {
            "https://acme.com/": FetchedPage(
                url="https://acme.com/",
                status_code=200,
                ok=True,
                html=HOME,
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
    return company_id


def test_detect_and_list_marketing(client: TestClient, container: Container) -> None:
    company_id = _crawl(client, container)

    detected = client.post(f"/api/v1/companies/{company_id}/marketing/detect")
    assert detected.status_code == 200
    names = {s["tool_name"] for s in detected.json()}
    assert "Meta Pixel" in names
    assert "WhatsApp" in names

    listed = client.get(f"/api/v1/companies/{company_id}/marketing")
    assert listed.status_code == 200
    assert {s["tool_name"] for s in listed.json()} == names


def test_detect_missing_company_returns_404(client: TestClient) -> None:
    assert client.post("/api/v1/companies/999/marketing/detect").status_code == 404
