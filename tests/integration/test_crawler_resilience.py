"""Website Crawler resilience: failed fetches and empty content don't break jobs."""

from __future__ import annotations

from config.containers import Container

from bise.crawlers.website_crawler import WebsiteCrawler
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob, CrawlJobStatus
from bise.domain.entities.website_domain import CrawlStatus, WebsiteDomain
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from tests.fakes.fetcher import FakePageFetcher


def _seed_job(container: Container) -> tuple[int, int]:
    company = Company(display_name="Acme")
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    with container.unit_of_work() as uow:
        saved = uow.companies.add(company)
        domain_id = saved.domains[0].id
        assert domain_id is not None
        job = uow.crawl_jobs.add(CrawlJob(domain_id=domain_id, hostname="acme.com"))
        uow.commit()
        assert job.id is not None
        return job.id, domain_id


def test_homepage_network_failure_still_completes(container: Container) -> None:
    job_id, domain_id = _seed_job(container)
    # Empty page dict -> fetcher returns 404 for the homepage.
    crawler = WebsiteCrawler(container.unit_of_work, FakePageFetcher({}), BeautifulSoupHtmlParser())
    crawler.run(job_id)

    with container.unit_of_work() as uow:
        job = uow.crawl_jobs.get(job_id)
        pages = uow.crawled_pages.list_for_job(job_id)
        company = uow.companies.get(_company_id(container))
    assert job is not None
    assert job.status is CrawlJobStatus.COMPLETED
    # The homepage attempt is still recorded (with its failure status).
    assert len(pages) == 1
    assert pages[0].http_status == 404
    assert company is not None
    assert company.domains[0].crawl_status is CrawlStatus.CRAWLED
    assert domain_id == company.domains[0].id


def test_all_robots_disallowed_completes_with_zero_pages(container: Container) -> None:
    job_id, _ = _seed_job(container)
    fetcher = FakePageFetcher({}, disallowed=["https://acme.com/"])
    crawler = WebsiteCrawler(container.unit_of_work, fetcher, BeautifulSoupHtmlParser())
    crawler.run(job_id)

    with container.unit_of_work() as uow:
        job = uow.crawl_jobs.get(job_id)
    assert job is not None
    assert job.status is CrawlJobStatus.COMPLETED
    assert job.pages_crawled == 0


def _company_id(container: Container) -> int:
    with container.unit_of_work() as uow:
        company = uow.companies.find_by_hostname("acme.com")
    assert company is not None and company.id is not None
    return company.id
