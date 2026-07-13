"""Integration test: DetectTechnologies use case end to end against SQLite."""

from __future__ import annotations

from config.containers import Container

from bise.application.use_cases.enrichment.detect_technologies import DetectTechnologies
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.website_domain import WebsiteDomain
from bise.infrastructure.analyzers.tech_fingerprint import RuleBasedTechnologyDetector

WP_HTML = """
<html><head><meta name="generator" content="WordPress 6.4">
<link href="https://acme.com/wp-content/x.css"></head><body>woocommerce</body></html>
"""


def _seed_company_with_pages(container: Container) -> int:
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
                html=WP_HTML,
            )
        )
        uow.commit()
        return company_id


def test_detect_persists_company_technologies(container: Container) -> None:
    company_id = _seed_company_with_pages(container)
    use_case = DetectTechnologies(container.unit_of_work(), RuleBasedTechnologyDetector())

    detections = use_case.execute(company_id)
    names = {d.name for d in detections}
    assert "WordPress" in names
    assert "WooCommerce" in names

    # Persisted and reloadable.
    with container.unit_of_work() as uow:
        stored = uow.company_technologies.list_for_company(company_id)
    assert {t.technology.name for t in stored if t.technology} >= {"WordPress", "WooCommerce"}


def test_detection_is_idempotent(container: Container) -> None:
    company_id = _seed_company_with_pages(container)
    use_case = DetectTechnologies(container.unit_of_work(), RuleBasedTechnologyDetector())

    use_case.execute(company_id)
    second = use_case.execute(company_id)

    with container.unit_of_work() as uow:
        stored = uow.company_technologies.list_for_company(company_id)
    # Re-running replaces rather than duplicates.
    assert len(stored) == len(second)
