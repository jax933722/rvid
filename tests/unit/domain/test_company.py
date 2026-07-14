"""Unit tests for the Company aggregate and its invariants."""

from __future__ import annotations

import pytest

from bise.domain.entities.company import Company, CompanyStatus
from bise.domain.entities.website_domain import WebsiteDomain
from bise.domain.errors import InvalidValueError, InvariantViolationError


def test_requires_non_empty_display_name() -> None:
    with pytest.raises(InvalidValueError):
        Company(display_name="   ")


def test_first_domain_becomes_primary_automatically() -> None:
    company = Company(display_name="Acme")
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    assert company.primary_domain is not None
    assert company.primary_domain.hostname == "acme.com"


def test_rejects_duplicate_hostname() -> None:
    company = Company(display_name="Acme")
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    with pytest.raises(InvariantViolationError):
        company.add_domain(WebsiteDomain(hostname="www.acme.com"))  # normalizes to acme.com


def test_rejects_two_primary_domains() -> None:
    company = Company(display_name="Acme")
    company.add_domain(WebsiteDomain(hostname="acme.com", is_primary=True))
    with pytest.raises(InvariantViolationError):
        company.add_domain(WebsiteDomain(hostname="acme.io", is_primary=True))


def test_cannot_enrich_without_domain() -> None:
    company = Company(display_name="Acme")
    with pytest.raises(InvariantViolationError):
        company.mark_enriched()


def test_enrich_succeeds_with_domain() -> None:
    company = Company(display_name="Acme")
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    company.mark_enriched()
    assert company.status is CompanyStatus.ENRICHED


def test_accepts_firmographics() -> None:
    company = Company(
        display_name="Acme",
        country="Australia",
        state="NSW",
        city="Sydney",
        founded_year=1999,
        employee_count=42,
        contact_email="hello@acme.com",
        contact_phone="+61 2 9000 0000",
    )
    assert company.city == "Sydney"
    assert company.founded_year == 1999
    assert company.employee_count == 42


@pytest.mark.parametrize("year", [1799, 3000])
def test_rejects_founded_year_out_of_range(year: int) -> None:
    with pytest.raises(InvalidValueError):
        Company(display_name="Acme", founded_year=year)


def test_rejects_negative_employee_count() -> None:
    with pytest.raises(InvalidValueError):
        Company(display_name="Acme", employee_count=-1)
