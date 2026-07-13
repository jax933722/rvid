"""Integration tests for the technology repositories against SQLite."""

from __future__ import annotations

from config.containers import Container

from bise.domain.entities.company import Company
from bise.domain.entities.technology import CompanyTechnology
from bise.domain.entities.website_domain import WebsiteDomain
from bise.domain.value_objects.confidence import Confidence
from bise.shared.pagination import PageRequest


def _company_id(container: Container) -> int:
    company = Company(display_name="Acme")
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    with container.unit_of_work() as uow:
        saved = uow.companies.add(company)
        uow.commit()
        assert saved.id is not None
        return saved.id


def test_get_or_create_is_idempotent(container: Container) -> None:
    with container.unit_of_work() as uow:
        first = uow.technologies.get_or_create("WordPress", "CMS")
        second = uow.technologies.get_or_create("WordPress", "CMS")
        uow.commit()
    assert first.id == second.id


def test_replace_for_company_overwrites(container: Container) -> None:
    company_id = _company_id(container)
    with container.unit_of_work() as uow:
        wp = uow.technologies.get_or_create("WordPress", "CMS")
        ga = uow.technologies.get_or_create("Google Analytics 4", "Analytics")
        assert wp.id is not None and ga.id is not None
        uow.company_technologies.replace_for_company(
            company_id,
            [
                CompanyTechnology(company_id, wp.id, Confidence(0.9), "meta"),
                CompanyTechnology(company_id, ga.id, Confidence(0.95), "html"),
            ],
        )
        uow.commit()

    # Replace with a single detection.
    with container.unit_of_work() as uow:
        wp = uow.technologies.get_or_create("WordPress", "CMS")
        assert wp.id is not None
        uow.company_technologies.replace_for_company(
            company_id, [CompanyTechnology(company_id, wp.id, Confidence(0.9), "meta")]
        )
        uow.commit()

    with container.unit_of_work() as uow:
        stored = uow.company_technologies.list_for_company(company_id)
        catalog = uow.technologies.list(PageRequest())
    assert len(stored) == 1
    assert stored[0].technology is not None
    assert stored[0].technology.name == "WordPress"
    assert catalog.total == 2  # both technologies remain in the shared catalog
