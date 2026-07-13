"""Use case: request a website crawl for a company's domain.

Creates a PENDING crawl job and returns immediately. Execution is performed
later by the Website Crawler worker, so no HTTP request ever blocks on crawling.
"""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.crawl_dto import CrawlJobDTO, RequestCrawlCommand
from bise.application.errors import NotFoundError
from bise.application.mappers import crawl_job_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.website_domain import _normalize_hostname

logger = get_logger(__name__)


class RequestCrawl:
    """Enqueue a crawl job for a known company domain."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: RequestCrawlCommand) -> CrawlJobDTO:
        hostname = _normalize_hostname(command.hostname)
        with self._uow as uow:
            company = uow.companies.find_by_hostname(hostname)
            if company is None:
                raise NotFoundError(f"No company owns domain: {hostname}")
            domain = next((d for d in company.domains if d.hostname == hostname), None)
            if domain is None or domain.id is None:
                raise NotFoundError(f"Domain not found: {hostname}")

            job = CrawlJob(domain_id=domain.id, hostname=hostname)
            saved = uow.crawl_jobs.add(job)
            uow.commit()

        logger.info("crawl.requested", job_id=saved.id, hostname=hostname)
        return crawl_job_to_dto(saved)
