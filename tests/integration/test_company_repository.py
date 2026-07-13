"""Integration tests for the SQLAlchemy Company repository (real SQLite)."""

from __future__ import annotations

from config.containers import Container

from bise.domain.entities.company import Company
from bise.domain.entities.website_domain import WebsiteDomain
from bise.shared.pagination import PageRequest


def _make_company(name: str, hostname: str) -> Company:
    company = Company(display_name=name)
    company.add_domain(WebsiteDomain(hostname=hostname))
    return company


def test_add_assigns_ids_and_get_round_trips(container: Container) -> None:
    with container.unit_of_work() as uow:
        saved = uow.companies.add(_make_company("Acme Dental", "acme.com"))
        uow.commit()
        company_id = saved.id

    assert company_id is not None
    with container.unit_of_work() as uow:
        fetched = uow.companies.get(company_id)

    assert fetched is not None
    assert fetched.display_name == "Acme Dental"
    assert fetched.primary_domain is not None
    assert fetched.primary_domain.hostname == "acme.com"


def test_find_by_hostname(container: Container) -> None:
    with container.unit_of_work() as uow:
        uow.companies.add(_make_company("Acme", "acme.com"))
        uow.commit()

    with container.unit_of_work() as uow:
        found = uow.companies.find_by_hostname("acme.com")
        missing = uow.companies.find_by_hostname("nope.com")

    assert found is not None
    assert missing is None


def test_list_is_paginated_and_counts_total(container: Container) -> None:
    with container.unit_of_work() as uow:
        for i in range(3):
            uow.companies.add(_make_company(f"Co {i}", f"co{i}.com"))
        uow.commit()

    with container.unit_of_work() as uow:
        page = uow.companies.list(PageRequest(page=1, page_size=2))

    assert page.total == 3
    assert len(page.items) == 2


def test_rollback_discards_changes(container: Container) -> None:
    with container.unit_of_work() as uow:
        uow.companies.add(_make_company("Ghost", "ghost.com"))
        # no commit -> context exit closes without persisting

    with container.unit_of_work() as uow:
        assert uow.companies.find_by_hostname("ghost.com") is None
