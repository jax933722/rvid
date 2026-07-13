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
