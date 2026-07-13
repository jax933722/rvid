"""Use case: fetch a crawl job and the pages it produced."""

from __future__ import annotations

from dataclasses import dataclass

from bise.application.dto.crawl_dto import CrawledPageDTO, CrawlJobDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import crawl_job_to_dto, crawled_page_to_dto
from bise.application.ports.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class CrawlJobDetail:
    """A crawl job together with its recorded pages."""

    job: CrawlJobDTO
    pages: list[CrawledPageDTO]


class GetCrawlJob:
    """Return one crawl job's detail, or raise :class:`NotFoundError`."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, job_id: int) -> CrawlJobDetail:
        with self._uow as uow:
            job = uow.crawl_jobs.get(job_id)
            if job is None:
                raise NotFoundError(f"Crawl job not found: {job_id}")
            pages = uow.crawled_pages.list_for_job(job_id)
        return CrawlJobDetail(
            job=crawl_job_to_dto(job),
            pages=[crawled_page_to_dto(p) for p in pages],
        )
