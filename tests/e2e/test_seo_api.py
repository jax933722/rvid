"""End-to-end tests for the SEO API (crawl -> scan -> read)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from bise.presentation.workers.crawl_worker import process_pending_jobs
from tests.fakes.fetcher import FakePageFetcher

HOME = """
<html><head><title>Acme Dental — Sydney Dentist</title>
<meta name="description" content="Gentle family dentistry in Sydney with modern care today.">
<link rel="canonical" href="https://acme.com/"><meta property="og:title" content="Acme">
</head><body><h1>Welcome</h1><img src="a.png" alt="team">
<a href="/contact">Contact</a></body></html>
"""


def _crawl_acme(client: TestClient, container: Container) -> int:
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


def test_scan_then_get_seo(client: TestClient, container: Container) -> None:
    company_id = _crawl_acme(client, container)

    scanned = client.post(f"/api/v1/companies/{company_id}/seo/scan")
    assert scanned.status_code == 200
    body = scanned.json()
    assert body["has_ssl"] is True
    assert body["title"].startswith("Acme Dental")
    assert 0 <= body["score"] <= 100

    fetched = client.get(f"/api/v1/companies/{company_id}/seo")
    assert fetched.status_code == 200
    assert fetched.json()["score"] == body["score"]


def test_get_seo_before_scan_returns_404(client: TestClient, container: Container) -> None:
    company_id = _crawl_acme(client, container)
    assert client.get(f"/api/v1/companies/{company_id}/seo").status_code == 404


def test_scan_missing_company_returns_404(client: TestClient) -> None:
    assert client.post("/api/v1/companies/999/seo/scan").status_code == 404
