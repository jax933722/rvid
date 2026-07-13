"""Integration test: DiscoverBusinesses use case against SQLite (fake source)."""

from __future__ import annotations

from config.containers import Container

from bise.application.dto.discovery_dto import DiscoverCommand
from bise.application.ports.discovery import DiscoveredBusiness
from bise.application.use_cases.discovery.discover_businesses import DiscoverBusinesses
from tests.fakes.discovery import FakeDiscoverySource

BUSINESSES = [
    DiscoveredBusiness(
        name="Acme Dental",
        category="dentist",
        website="acmedental.com",
        website_url="https://acmedental.com",
        city="Sydney",
    ),
    DiscoveredBusiness(
        name="Bright Dental",
        category="dentist",
        website="brightdental.com",
        website_url="https://brightdental.com",
        city="Sydney",
    ),
    DiscoveredBusiness(name="No Website Dental", category="dentist", website=None),
    DiscoveredBusiness(
        name="Acme Dental (dup)",
        category="dentist",
        website="acmedental.com",
        website_url="https://acmedental.com",
    ),
]


def _use_case(container: Container) -> DiscoverBusinesses:
    return DiscoverBusinesses(container.unit_of_work(), FakeDiscoverySource(BUSINESSES))


def test_saves_businesses_with_websites_as_companies(container: Container) -> None:
    results = _use_case(container).execute(DiscoverCommand(category="dentist", location="Sydney"))

    # All four are returned for display...
    assert len(results) == 4
    # ...but only the two unique websites become companies.
    saved = [r for r in results if r.company_id is not None]
    assert {r.name for r in saved} == {"Acme Dental", "Bright Dental"}
    assert next(r for r in results if r.website is None).company_id is None

    with container.unit_of_work() as uow:
        assert uow.companies.find_by_hostname("acmedental.com") is not None
        assert uow.companies.find_by_hostname("brightdental.com") is not None


def test_rediscovery_does_not_duplicate(container: Container) -> None:
    _use_case(container).execute(DiscoverCommand(category="dentist", location="Sydney"))
    results = _use_case(container).execute(DiscoverCommand(category="dentist", location="Sydney"))

    # The existing companies are reused (their ids returned), not duplicated.
    acme = next(r for r in results if r.name == "Acme Dental")
    assert acme.company_id is not None
    with container.unit_of_work() as uow:
        found = uow.companies.find_by_hostname("acmedental.com")
    assert found is not None
