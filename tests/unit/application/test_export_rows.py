"""Unit tests for export row projections."""

from __future__ import annotations

from datetime import UTC, datetime

from bise.application.dto.company_dto import CompanyDTO, DomainDTO
from bise.application.dto.search_dto import SearchResultItem
from bise.application.export.rows import EXPORT_COLUMNS, company_to_row, search_item_to_row


def _company(domains: tuple[DomainDTO, ...]) -> CompanyDTO:
    now = datetime.now(UTC)
    return CompanyDTO(
        id=7,
        display_name="Acme",
        legal_name=None,
        status="enriched",
        industry="Dentistry",
        size_bucket="11-50",
        country="Australia",
        state="NSW",
        city="Sydney",
        founded_year=2010,
        employee_count=20,
        contact_email="hi@acme.com",
        contact_phone="+61 2 9000 0000",
        domains=domains,
        created_at=now,
        updated_at=now,
    )


def test_search_item_row_joins_technologies() -> None:
    item = SearchResultItem(
        company_id=1,
        display_name="Acme",
        primary_domain="acme.com",
        industry="Dentistry",
        country="Australia",
        state="NSW",
        city="Sydney",
        size_bucket="11-50",
        founded_year=2010,
        employee_count=20,
        seo_score=88.0,
        seo_grade="B",
        technologies=["WordPress", "Shopify"],
    )
    row = search_item_to_row(item)
    assert row["website"] == "acme.com"
    assert row["technologies"] == "WordPress; Shopify"
    assert set(row.keys()) == set(EXPORT_COLUMNS)


def test_company_row_uses_primary_domain() -> None:
    row = company_to_row(
        _company((DomainDTO(id=1, hostname="acme.com", is_primary=True, crawl_status="done"),))
    )
    assert row["website"] == "acme.com"
    assert row["contact_email"] == "hi@acme.com"


def test_company_row_falls_back_to_first_domain_when_no_primary() -> None:
    row = company_to_row(
        _company((DomainDTO(id=1, hostname="secondary.com", is_primary=False, crawl_status="x"),))
    )
    assert row["website"] == "secondary.com"


def test_company_row_website_none_without_domains() -> None:
    assert company_to_row(_company(()))["website"] is None
