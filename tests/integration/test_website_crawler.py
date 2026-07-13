"""Integration test: the Website Crawler end to end against SQLite.

Uses the real HTML parser (pure, offline) and a fake fetcher, so it exercises
the full orchestration, persistence, and state transitions with no network.
"""

from __future__ import annotations

from config.containers import Container

from bise.application.ports.fetcher import FetchedPage
from bise.crawlers.website_crawler import WebsiteCrawler
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob, CrawlJobStatus
from bise.domain.entities.crawled_page import PageType
from bise.domain.entities.website_domain import CrawlStatus, WebsiteDomain
from bise.infrastructure.crawling.html_parser import BeautifulSoupHtmlParser
from tests.fakes.fetcher import FakePageFetcher

HOME_HTML = """
<html><head><title>Acme Dental</title></head><body>
  <a href="/about-us">About</a>
  <a href="/contact">Contact</a>
  <a href="/blog/hello">Blog</a>
  <a href="/careers">Careers</a>
  <a href="/privacy-policy">Privacy</a>
  <a href="/terms">Terms</a>
  <a href="https://external.example/partner">Partner</a>
  <a href="/about-us#team">About dup</a>
</body></html>
"""


def _html_page(url: str, title: str) -> FetchedPage:
    body = f"<html><head><title>{title}</title></head><body>ok</body></html>"
    return FetchedPage(url=url, status_code=200, ok=True, html=body, content_type="text/html")


def _seed_job(container: Container) -> tuple[int, int]:
    company = Company(display_name="Acme Dental")
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    with container.unit_of_work() as uow:
        saved = uow.companies.add(company)
        domain_id = saved.domains[0].id
        assert domain_id is not None
        job = uow.crawl_jobs.add(CrawlJob(domain_id=domain_id, hostname="acme.com"))
        uow.commit()
        assert job.id is not None
        return job.id, domain_id


def _pages() -> dict[str, FetchedPage]:
    home = FetchedPage(
        url="https://acme.com/", status_code=200, ok=True, html=HOME_HTML, content_type="text/html"
    )
    return {
        "https://acme.com/": home,
        "https://acme.com/about-us": _html_page("https://acme.com/about-us", "About"),
        "https://acme.com/contact": _html_page("https://acme.com/contact", "Contact"),
        "https://acme.com/blog/hello": _html_page("https://acme.com/blog/hello", "Blog"),
        "https://acme.com/careers": _html_page("https://acme.com/careers", "Careers"),
        "https://acme.com/privacy-policy": _html_page("https://acme.com/privacy-policy", "Privacy"),
        "https://acme.com/terms": _html_page("https://acme.com/terms", "Terms"),
    }


def test_full_crawl_records_pages_and_completes(container: Container) -> None:
    job_id, domain_id = _seed_job(container)
    fetcher = FakePageFetcher(_pages())
    crawler = WebsiteCrawler(container.unit_of_work, fetcher, BeautifulSoupHtmlParser())

    crawler.run(job_id)

    with container.unit_of_work() as uow:
        job = uow.crawl_jobs.get(job_id)
        pages = uow.crawled_pages.list_for_job(job_id)

    assert job is not None
    assert job.status is CrawlJobStatus.COMPLETED
    # home + about + contact + blog + careers + privacy + terms = 7
    assert job.pages_crawled == 7
    types = {p.page_type for p in pages}
    assert PageType.HOME in types
    assert PageType.ABOUT in types
    assert PageType.CAREERS in types
    # external link never fetched
    assert "https://external.example/partner" not in fetcher.fetched
    # duplicate about only fetched once
    assert fetcher.fetched.count("https://acme.com/about-us") == 1

    with container.unit_of_work() as uow:
        refreshed = uow.companies.get(_company_id(container, domain_id))
    assert refreshed is not None
    assert refreshed.domains[0].crawl_status is CrawlStatus.CRAWLED


def test_robots_disallowed_pages_are_skipped(container: Container) -> None:
    job_id, _ = _seed_job(container)
    fetcher = FakePageFetcher(_pages(), disallowed=["https://acme.com/privacy-policy"])
    crawler = WebsiteCrawler(container.unit_of_work, fetcher, BeautifulSoupHtmlParser())

    crawler.run(job_id)

    with container.unit_of_work() as uow:
        job = uow.crawl_jobs.get(job_id)
    assert job is not None
    assert job.pages_crawled == 6
    assert "https://acme.com/privacy-policy" not in fetcher.fetched


def _company_id(container: Container, domain_id: int) -> int:
    with container.unit_of_work() as uow:
        company = uow.companies.find_by_hostname("acme.com")
    assert company is not None and company.id is not None
    return company.id
