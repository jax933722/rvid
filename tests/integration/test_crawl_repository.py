"""Integration tests for the crawl repositories against SQLite."""

from __future__ import annotations

from config.containers import Container

from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob, CrawlJobStatus
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.website_domain import WebsiteDomain
from bise.shared.pagination import PageRequest


def _seed_domain(container: Container) -> int:
    company = Company(display_name="Acme")
    company.add_domain(WebsiteDomain(hostname="acme.com"))
    with container.unit_of_work() as uow:
        saved = uow.companies.add(company)
        uow.commit()
        assert saved.domains[0].id is not None
        return saved.domains[0].id


def test_crawl_job_add_update_and_filter(container: Container) -> None:
    domain_id = _seed_domain(container)
    with container.unit_of_work() as uow:
        job = uow.crawl_jobs.add(CrawlJob(domain_id=domain_id, hostname="acme.com"))
        uow.commit()
        job_id = job.id
    assert job_id is not None

    with container.unit_of_work() as uow:
        job = uow.crawl_jobs.get(job_id)
        assert job is not None
        job.start()
        job.complete(3)
        uow.crawl_jobs.update(job)
        uow.commit()

    with container.unit_of_work() as uow:
        completed = uow.crawl_jobs.list(PageRequest(), CrawlJobStatus.COMPLETED)
        pending = uow.crawl_jobs.list(PageRequest(), CrawlJobStatus.PENDING)
    assert completed.total == 1
    assert pending.total == 0


def test_crawled_page_persistence(container: Container) -> None:
    domain_id = _seed_domain(container)
    with container.unit_of_work() as uow:
        job = uow.crawl_jobs.add(CrawlJob(domain_id=domain_id, hostname="acme.com"))
        uow.commit()
        job_id = job.id
    assert job_id is not None

    with container.unit_of_work() as uow:
        uow.crawled_pages.add(
            CrawledPage(
                crawl_job_id=job_id,
                domain_id=domain_id,
                url="https://acme.com/",
                page_type=PageType.HOME,
                http_status=200,
                content_hash="abc",
                title="Acme",
            )
        )
        uow.commit()

    with container.unit_of_work() as uow:
        pages = uow.crawled_pages.list_for_job(job_id)
    assert len(pages) == 1
    assert pages[0].page_type is PageType.HOME
    assert pages[0].title == "Acme"
