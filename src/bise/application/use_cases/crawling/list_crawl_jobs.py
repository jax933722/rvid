"""Use case: list crawl jobs with pagination and optional status filter."""

from __future__ import annotations

from bise.application.dto.crawl_dto import CrawlJobDTO
from bise.application.mappers import crawl_job_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.crawl_job import CrawlJobStatus
from bise.shared.pagination import Page, PageRequest


class ListCrawlJobs:
    """Return a page of crawl jobs (newest first)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, page: PageRequest, status: CrawlJobStatus | None = None) -> Page[CrawlJobDTO]:
        with self._uow as uow:
            result = uow.crawl_jobs.list(page, status)
        return Page(
            items=[crawl_job_to_dto(j) for j in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
