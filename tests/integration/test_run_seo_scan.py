"""Integration test: RunSeoScan use case end to end against SQLite."""

from __future__ import annotations

from config.containers import Container

from bise.application.use_cases.enrichment.run_seo_scan import RunSeoScan
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.website_domain import WebsiteDomain
from bise.infrastructure.analyzers.seo_analyzer import BeautifulSoupSeoAnalyzer
from bise.infrastructure.pagespeed.null_provider import NullPageSpeedProvider

HTML = """
<html><head><title>Acme Dental — Sydney Dentist Clinic</title>
<meta name="description" content="Gentle family dentistry in Sydney with modern equipment.">
<link rel="canonical" href="https://acme.com/">
<meta property="og:title" content="Acme"></head>
<body><h1>Welcome</h1><img src="a.png" alt="team"><a href="/about">About</a></body></html>
"""


def _seed(container: Container) -> int:
    company = Company(display_name="Acme")
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
                url="https://acme.com/",
                page_type=PageType.HOME,
                http_status=200,
                content_hash="h",
                html=HTML,
            )
        )
        uow.commit()
        return company_id


def _use_case(container: Container) -> RunSeoScan:
    return RunSeoScan(container.unit_of_work(), BeautifulSoupSeoAnalyzer(), NullPageSpeedProvider())


def test_scan_persists_scored_profile(container: Container) -> None:
    company_id = _seed(container)
    dto = _use_case(container).execute(company_id)

    assert dto.title == "Acme Dental — Sydney Dentist Clinic"
    assert dto.has_ssl is True
    assert dto.score > 50
    assert dto.grade in {"A", "B", "C", "D", "F"}

    with container.unit_of_work() as uow:
        stored = uow.seo_profiles.get_for_company(company_id)
    assert stored is not None
    assert stored.score == dto.score


def test_scan_is_idempotent_upsert(container: Container) -> None:
    company_id = _seed(container)
    _use_case(container).execute(company_id)
    _use_case(container).execute(company_id)

    # Only one profile row exists per company (upsert, not insert).
    with container.unit_of_work() as uow:
        profile = uow.seo_profiles.get_for_company(company_id)
    assert profile is not None
