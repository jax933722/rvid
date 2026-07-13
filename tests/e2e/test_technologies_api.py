"""End-to-end tests for the technology API (crawl -> detect -> read)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from bise.presentation.workers.crawl_worker import process_pending_jobs
from tests.fakes.fetcher import FakePageFetcher

WP_HOME = (
    '<html><head><meta name="generator" content="WordPress 6.4">'
    '<script src="https://www.googletagmanager.com/gtag/js?id=G-XYZ12345"></script>'
    '</head><body><a href="/contact">Contact</a> woocommerce</body></html>'
)


def _crawl_acme(client: TestClient, container: Container) -> int:
    client.post(
        "/api/v1/companies", json={"display_name": "Acme", "domains": [{"hostname": "acme.com"}]}
    )
    company_id = client.get("/api/v1/companies").json()["items"][0]["id"]
    client.post("/api/v1/crawl", json={"hostname": "acme.com"})

    container._fetcher = FakePageFetcher(  # noqa: SLF001 - test wiring
        {
            "https://acme.com/": FetchedPage(
                url="https://acme.com/",
                status_code=200,
                ok=True,
                html=WP_HOME,
                content_type="text/html",
                headers={"cf-ray": "abc"},
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
    return int(company_id)


def test_detect_and_list_company_technologies(client: TestClient, container: Container) -> None:
    company_id = _crawl_acme(client, container)

    detected = client.post(f"/api/v1/companies/{company_id}/technologies/detect")
    assert detected.status_code == 200
    names = {t["name"] for t in detected.json()}
    assert "WordPress" in names
    assert "Google Analytics 4" in names
    assert "Cloudflare" in names  # from the cf-ray header stored during crawl

    listed = client.get(f"/api/v1/companies/{company_id}/technologies")
    assert listed.status_code == 200
    assert {t["name"] for t in listed.json()} == names


def test_technology_catalog_is_populated_after_detection(
    client: TestClient, container: Container
) -> None:
    company_id = _crawl_acme(client, container)
    client.post(f"/api/v1/companies/{company_id}/technologies/detect")

    catalog = client.get("/api/v1/technologies")
    assert catalog.status_code == 200
    assert catalog.json()["total"] >= 1


def test_detect_for_missing_company_returns_404(client: TestClient) -> None:
    assert client.post("/api/v1/companies/999/technologies/detect").status_code == 404
