"""End-to-end tests for people extraction + role search (offline enrich)."""

from __future__ import annotations

from config.containers import Container
from fastapi.testclient import TestClient

from bise.application.ports.fetcher import FetchedPage
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from tests.fakes.fetcher import FakePageFetcher

ABOUT = (
    "<html><head><title>About Acme</title></head><body>"
    '<div class="team-member"><h3>Jane Doe</h3><p class="role">Founder &amp; CEO</p>'
    '<a href="mailto:jane.doe@acme.com">email</a></div>'
    '<div class="team-member"><h3>John Smith</h3><p class="role">CTO</p></div>'
    '<a href="/about">About</a></body></html>'
)


def _company(client: TestClient, name: str, host: str) -> int:
    res = client.post(
        "/api/v1/companies",
        json={"display_name": name, "domains": [{"hostname": host, "is_primary": True}]},
    )
    assert res.status_code == 201, res.text
    company_id: int = res.json()["id"]
    return company_id


def test_enrich_extracts_people_and_enables_role_search(
    client: TestClient, container: Container
) -> None:
    container._fetcher = FakePageFetcher(  # noqa: SLF001 - test wiring
        {
            "https://acme.com/": FetchedPage(
                url="https://acme.com/", status_code=200, ok=True, html=ABOUT,
                content_type="text/html",
            ),
            "https://acme.com/about": FetchedPage(
                url="https://acme.com/about", status_code=200, ok=True, html=ABOUT,
                content_type="text/html",
            ),
        }
    )
    container._html_parser = BeautifulSoupHtmlParser()  # noqa: SLF001

    acme = _company(client, "Acme", "acme.com")
    assert client.post(f"/api/v1/companies/{acme}/enrich").status_code == 200

    people = client.get(f"/api/v1/companies/{acme}/people")
    assert people.status_code == 200
    by_name = {p["name"]: p for p in people.json()}
    assert by_name["Jane Doe"]["role_category"] == "founder"
    assert by_name["Jane Doe"]["email"] == "jane.doe@acme.com"
    assert by_name["Jane Doe"]["email_status"] == "published"
    assert by_name["John Smith"]["role_category"] == "cto"
    assert by_name["John Smith"]["email_status"] == "guessed"  # inferred pattern

    # The company is now findable by "has a CTO".
    search = client.post(
        "/api/v1/search",
        json={
            "filters": [{"field": "role", "op": "contains", "values": ["cto"]}],
            "facets": [],
            "page": 1,
            "page_size": 25,
        },
    )
    assert search.status_code == 200
    assert search.json()["total"] == 1


def test_people_empty_for_unknown_company(client: TestClient) -> None:
    assert client.get("/api/v1/companies/999/people").json() == []
