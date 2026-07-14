"""Integration test: RebuildSearchDocument projects firmographics + page titles."""

from __future__ import annotations

from config.containers import Container

from bise.application.dto.search_dto import Filter, FilterOp, SearchQuery
from bise.application.use_cases.search.compile_query import compile_query
from bise.application.use_cases.search.rebuild_search_document import RebuildSearchDocument
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.website_domain import WebsiteDomain
from bise.infrastructure.search.sql_search_adapter import SqlSearchAdapter


def _seed(container: Container) -> tuple[int, SqlSearchAdapter]:
    company = Company(
        display_name="Acme Dental",
        industry="Dentistry",
        city="Sydney",
        state="NSW",
        country="Australia",
        founded_year=2005,
        employee_count=12,
    )
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    with container.unit_of_work() as uow:
        saved = uow.companies.add(company)
        company_id = saved.id
        domain_id = saved.domains[0].id
        assert company_id is not None and domain_id is not None
        job = uow.crawl_jobs.add(CrawlJob(domain_id=domain_id, hostname="acme.com"))
        uow.crawled_pages.add(
            CrawledPage(
                domain_id=domain_id,
                crawl_job_id=job.id,
                url="https://acme.com/services",
                page_type=PageType.OTHER,
                http_status=200,
                content_hash="h",
                title="Emergency Root Canal Treatment",
            )
        )
        uow.commit()
    adapter = SqlSearchAdapter(container.session_factory)
    RebuildSearchDocument(container.unit_of_work(), adapter).execute(company_id)
    return company_id, adapter


def test_keyword_search_matches_page_title(container: Container) -> None:
    _, adapter = _seed(container)
    # "root canal" appears only in a crawled page title, not the company name.
    result = adapter.search(compile_query(SearchQuery(text="root canal")))
    assert result.total == 1
    assert result.items[0].display_name == "Acme Dental"


def test_keyword_search_matches_location(container: Container) -> None:
    _, adapter = _seed(container)
    result = adapter.search(compile_query(SearchQuery(text="sydney")))
    assert result.total == 1


def test_firmographics_are_filterable_after_rebuild(container: Container) -> None:
    _, adapter = _seed(container)
    query = SearchQuery(
        filters=(
            Filter("city", FilterOp.EQ, ("Sydney",)),
            Filter("founded_year", FilterOp.BETWEEN, ("2000", "2010")),
            Filter("employee_count", FilterOp.LTE, ("50",)),
        )
    )
    result = adapter.search(compile_query(query))
    assert result.total == 1
    item = result.items[0]
    assert item.city == "Sydney"
    assert item.founded_year == 2005
    assert item.employee_count == 12
