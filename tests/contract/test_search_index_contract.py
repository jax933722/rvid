"""Shared contract suite for SearchIndexPort implementations.

Every implementation (the portable SQL adapter today, an OpenSearch adapter
tomorrow) must pass these tests. That is what guarantees the backend can be
swapped without changing business logic.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

import pytest
from config.containers import Container

from bise.application.dto.search_dto import Filter, FilterOp, SearchQuery
from bise.application.ports.search import SearchIndexPort
from bise.application.use_cases.search.compile_query import compile_query
from bise.domain.entities.company import Company
from bise.domain.entities.search_document import SearchDocument
from bise.domain.entities.website_domain import WebsiteDomain
from tests.fakes.search import InMemorySearchIndex


@dataclass
class IndexHarness:
    """Bundles an index implementation with a way to mint valid company ids."""

    index: SearchIndexPort
    new_company_id: Callable[[str, str], int]


@pytest.fixture(params=["sql", "memory"])
def harness(request: pytest.FixtureRequest, container: Container) -> Iterator[IndexHarness]:
    if request.param == "memory":
        counter = {"n": 0}

        def mint_memory(_name: str, _host: str) -> int:
            counter["n"] += 1
            return counter["n"]

        yield IndexHarness(index=InMemorySearchIndex(), new_company_id=mint_memory)
        return

    from bise.infrastructure.search.sql_search_adapter import SqlSearchAdapter

    def mint_sql(name: str, host: str) -> int:
        company = Company(display_name=name)
        company.add_domain(WebsiteDomain(hostname=host))
        with container.unit_of_work() as uow:
            saved = uow.companies.add(company)
            uow.commit()
            assert saved.id is not None
            return saved.id

    yield IndexHarness(index=SqlSearchAdapter(container.session_factory), new_company_id=mint_sql)


def _doc(company_id: int, name: str, **kwargs: object) -> SearchDocument:
    return SearchDocument(company_id=company_id, display_name=name, **kwargs)  # type: ignore[arg-type]


def _seed(h: IndexHarness) -> None:
    acme = h.new_company_id("Acme Dental", "acme.com")
    beta = h.new_company_id("Beta Plumbing", "beta.com")
    h.index.upsert(
        _doc(
            acme,
            "Acme Dental",
            industry="Dentistry",
            seo_score=40.0,
            seo_grade="D",
            technologies=["WordPress"],
            has_contact_page=True,
            text_blob="acme dental wordpress",
        )
    )
    h.index.upsert(
        _doc(
            beta,
            "Beta Plumbing",
            industry="Plumbing",
            seo_score=80.0,
            seo_grade="B",
            technologies=["Shopify"],
            has_contact_page=False,
            text_blob="beta plumbing shopify",
        )
    )


def test_text_search(harness: IndexHarness) -> None:
    _seed(harness)
    result = harness.index.search(compile_query(SearchQuery(text="plumbing")))
    assert result.total == 1
    assert result.items[0].display_name == "Beta Plumbing"


def test_industry_filter(harness: IndexHarness) -> None:
    _seed(harness)
    result = harness.index.search(
        compile_query(SearchQuery(filters=(Filter("industry", FilterOp.EQ, ("Dentistry",)),)))
    )
    assert result.total == 1
    assert result.items[0].display_name == "Acme Dental"


def test_technology_contains(harness: IndexHarness) -> None:
    _seed(harness)
    result = harness.index.search(
        compile_query(
            SearchQuery(filters=(Filter("technology", FilterOp.CONTAINS, ("WordPress",)),))
        )
    )
    assert {i.display_name for i in result.items} == {"Acme Dental"}


def test_numeric_and_bool(harness: IndexHarness) -> None:
    _seed(harness)
    lte = harness.index.search(
        compile_query(SearchQuery(filters=(Filter("seo_score", FilterOp.LTE, ("50",)),)))
    )
    assert lte.total == 1
    contact = harness.index.search(
        compile_query(SearchQuery(filters=(Filter("has_contact_page", FilterOp.IS_TRUE),)))
    )
    assert contact.total == 1


def test_facets(harness: IndexHarness) -> None:
    _seed(harness)
    result = harness.index.search(compile_query(SearchQuery(facets=("industry", "technology"))))
    industries = {f.value: f.count for f in result.facets["industry"]}
    assert industries == {"Dentistry": 1, "Plumbing": 1}


def test_pagination(harness: IndexHarness) -> None:
    _seed(harness)
    result = harness.index.search(compile_query(SearchQuery(page=1, page_size=1)))
    assert result.total == 2
    assert len(result.items) == 1


def test_upsert_replaces(harness: IndexHarness) -> None:
    cid = harness.new_company_id("Gamma", "gamma.com")
    harness.index.upsert(_doc(cid, "Gamma", seo_score=10.0, text_blob="gamma"))
    harness.index.upsert(_doc(cid, "Gamma", seo_score=95.0, text_blob="gamma"))
    result = harness.index.search(compile_query(SearchQuery(text="gamma")))
    assert result.total == 1
    assert result.items[0].seo_score == 95.0
