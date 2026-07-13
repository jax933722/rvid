"""Integration tests for the SQL search adapter against SQLite."""

from __future__ import annotations

from config.containers import Container

from bise.application.dto.search_dto import Filter, FilterOp, SearchQuery, SortSpec
from bise.application.use_cases.search.compile_query import compile_query
from bise.domain.entities.company import Company
from bise.domain.entities.search_document import SearchDocument
from bise.domain.entities.website_domain import WebsiteDomain
from bise.infrastructure.search.sql_search_adapter import SqlSearchAdapter


def _company(container: Container, name: str, hostname: str) -> int:
    company = Company(display_name=name)
    company.add_domain(WebsiteDomain(hostname=hostname))
    with container.unit_of_work() as uow:
        saved = uow.companies.add(company)
        uow.commit()
        assert saved.id is not None
        return saved.id


def _index(container: Container) -> SqlSearchAdapter:
    adapter = SqlSearchAdapter(container.session_factory)
    acme = _company(container, "Acme Dental", "acme.com")
    beta = _company(container, "Beta Plumbing", "beta.com")
    gamma = _company(container, "Gamma Dental", "gamma.com")
    adapter.upsert(
        SearchDocument(
            company_id=acme,
            display_name="Acme Dental",
            primary_domain="acme.com",
            industry="Dentistry",
            seo_score=40.0,
            seo_grade="D",
            technologies=["WordPress", "Meta Pixel"],
            has_contact_page=True,
            text_blob="acme dental dentistry wordpress meta pixel",
        )
    )
    adapter.upsert(
        SearchDocument(
            company_id=beta,
            display_name="Beta Plumbing",
            primary_domain="beta.com",
            industry="Plumbing",
            seo_score=80.0,
            seo_grade="B",
            technologies=["Shopify"],
            has_contact_page=False,
            text_blob="beta plumbing shopify",
        )
    )
    adapter.upsert(
        SearchDocument(
            company_id=gamma,
            display_name="Gamma Dental",
            primary_domain="gamma.com",
            industry="Dentistry",
            seo_score=90.0,
            seo_grade="A",
            technologies=["WordPress"],
            has_contact_page=True,
            text_blob="gamma dental dentistry wordpress",
        )
    )
    return adapter


def test_text_search(container: Container) -> None:
    adapter = _index(container)
    result = adapter.search(compile_query(SearchQuery(text="plumbing")))
    assert result.total == 1
    assert result.items[0].display_name == "Beta Plumbing"


def test_filter_industry_and_technology(container: Container) -> None:
    adapter = _index(container)
    query = SearchQuery(
        filters=(
            Filter("industry", FilterOp.EQ, ("Dentistry",)),
            Filter("technology", FilterOp.CONTAINS, ("WordPress",)),
        )
    )
    result = adapter.search(compile_query(query))
    assert result.total == 2
    assert {i.display_name for i in result.items} == {"Acme Dental", "Gamma Dental"}


def test_numeric_range_filter(container: Container) -> None:
    adapter = _index(container)
    query = SearchQuery(filters=(Filter("seo_score", FilterOp.LTE, ("50",)),))
    result = adapter.search(compile_query(query))
    assert result.total == 1
    assert result.items[0].display_name == "Acme Dental"


def test_bool_filter(container: Container) -> None:
    adapter = _index(container)
    query = SearchQuery(filters=(Filter("has_contact_page", FilterOp.IS_TRUE),))
    assert adapter.search(compile_query(query)).total == 2


def test_technology_contains_is_or(container: Container) -> None:
    adapter = _index(container)
    query = SearchQuery(
        filters=(Filter("technology", FilterOp.CONTAINS, ("WordPress", "Shopify")),)
    )
    assert adapter.search(compile_query(query)).total == 3


def test_facets_counts(container: Container) -> None:
    adapter = _index(container)
    result = adapter.search(compile_query(SearchQuery(facets=("industry", "technology"))))
    industry = {f.value: f.count for f in result.facets["industry"]}
    assert industry == {"Dentistry": 2, "Plumbing": 1}
    tech = {f.value: f.count for f in result.facets["technology"]}
    assert tech["WordPress"] == 2


def test_sort_and_pagination(container: Container) -> None:
    adapter = _index(container)
    query = SearchQuery(sort=SortSpec(field="seo_score", descending=True), page=1, page_size=2)
    result = adapter.search(compile_query(query))
    assert result.total == 3
    assert len(result.items) == 2
    assert result.items[0].seo_score == 90.0  # highest first


def test_upsert_replaces(container: Container) -> None:
    adapter = _index(container)
    # Re-index Acme with a new score; row count stays the same.
    acme_id = adapter.search(compile_query(SearchQuery(text="acme"))).items[0].company_id
    adapter.upsert(
        SearchDocument(
            company_id=acme_id,
            display_name="Acme Dental",
            industry="Dentistry",
            seo_score=99.0,
            technologies=["WordPress"],
            text_blob="acme dental",
        )
    )
    result = adapter.search(compile_query(SearchQuery(text="acme")))
    assert result.total == 1
    assert result.items[0].seo_score == 99.0
