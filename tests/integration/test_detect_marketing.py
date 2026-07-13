"""Integration test: DetectMarketing use case end to end against SQLite."""

from __future__ import annotations

from config.containers import Container

from bise.application.use_cases.enrichment.detect_marketing import DetectMarketing
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.website_domain import WebsiteDomain
from bise.infrastructure.analyzers.marketing_fingerprint import RuleBasedMarketingDetector

HTML = (
    "<html><head>"
    '<script src="https://connect.facebook.net/en_US/fbevents.js"></script>'
    '<script src="https://www.googletagmanager.com/gtm.js?id=GTM-XYZ"></script>'
    "</head><body>x</body></html>"
)


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


def test_detect_persists_marketing_signals(container: Container) -> None:
    company_id = _seed(container)
    use_case = DetectMarketing(container.unit_of_work(), RuleBasedMarketingDetector())

    detections = use_case.execute(company_id)
    names = {d.tool_name for d in detections}
    assert "Meta Pixel" in names
    assert "Google Tag Manager" in names

    with container.unit_of_work() as uow:
        stored = uow.marketing_signals.list_for_company(company_id)
    assert {s.tool_name for s in stored} == names


def test_detection_is_idempotent(container: Container) -> None:
    company_id = _seed(container)
    use_case = DetectMarketing(container.unit_of_work(), RuleBasedMarketingDetector())
    use_case.execute(company_id)
    second = use_case.execute(company_id)
    with container.unit_of_work() as uow:
        stored = uow.marketing_signals.list_for_company(company_id)
    assert len(stored) == len(second)
