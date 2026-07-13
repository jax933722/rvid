"""End-to-end tests for the discovery + on-demand enrich API (no network)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.discovery import DiscoveredBusiness
from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from tests.fakes.discovery import FakeDiscoverySource
from tests.fakes.fetcher import FakePageFetcher

WP_HOME = (
    '<html><head><meta name="generator" content="WordPress 6.4">'
    '<script src="https://connect.facebook.net/en_US/fbevents.js"></script>'
    "<title>Acme Dental</title></head><body><h1>Dentist</h1>"
    '<a href="/contact">Contact</a></body></html>'
)


def test_discover_saves_companies(client: TestClient, container: Container) -> None:
    container._discovery_source = FakeDiscoverySource(  # noqa: SLF001 - test wiring
        [
            DiscoveredBusiness(
                name="Acme Dental",
                category="dentist",
                website="acme.com",
                website_url="https://acme.com",
                city="Sydney",
                phone="+61",
            ),
            DiscoveredBusiness(name="No Web Dental", category="dentist"),
        ]
    )
    resp = client.post("/api/v1/discover", json={"category": "dentist", "location": "Sydney"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    acme = next(b for b in data if b["name"] == "Acme Dental")
    assert acme["company_id"] is not None
    assert acme["city"] == "Sydney"
    assert next(b for b in data if b["name"] == "No Web Dental")["company_id"] is None


def test_discover_then_enrich_makes_it_searchable(client: TestClient, container: Container) -> None:
    container._discovery_source = FakeDiscoverySource(  # noqa: SLF001 - test wiring
        [
            DiscoveredBusiness(
                name="Acme Dental",
                category="dentist",
                website="acme.com",
                website_url="https://acme.com",
            )
        ]
    )
    discovered = client.post(
        "/api/v1/discover", json={"category": "dentist", "location": "Sydney"}
    ).json()
    company_id = discovered[0]["company_id"]

    # Inject a deterministic fetcher/parser, then enrich on demand.
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

    enriched = client.post(f"/api/v1/companies/{company_id}/enrich")
    assert enriched.status_code == 200
    assert enriched.json()["status"] == "enriched"

    # It now appears in search with detected technologies.
    result = client.post(
        "/api/v1/search",
        json={"filters": [{"field": "technology", "op": "contains", "values": ["WordPress"]}]},
    ).json()
    assert result["total"] == 1
    assert result["items"][0]["display_name"] == "Acme Dental"

    # ...and its marketing + SEO were detected too.
    assert client.get(f"/api/v1/companies/{company_id}/marketing").json()
    assert client.get(f"/api/v1/companies/{company_id}/seo").json()["grade"] in "ABCDF"
