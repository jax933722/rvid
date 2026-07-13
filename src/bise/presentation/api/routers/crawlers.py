"""Crawler API — request crawls and inspect crawl jobs."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from bise.application.dto.crawl_dto import RequestCrawlCommand
from bise.application.use_cases.crawling.get_crawl_job import GetCrawlJob
from bise.application.use_cases.crawling.list_crawl_jobs import ListCrawlJobs
from bise.application.use_cases.crawling.request_crawl import RequestCrawl
from bise.domain.entities.crawl_job import CrawlJobStatus
from bise.presentation.api.dependencies import (
    get_get_crawl_job,
    get_list_crawl_jobs,
    get_request_crawl,
)
from bise.presentation.api.schemas.common import PageResponse
from bise.presentation.api.schemas.crawl import (
    CrawledPageResponse,
    CrawlJobDetailResponse,
    CrawlJobResponse,
    RequestCrawlRequest,
)
from bise.shared.pagination import PageRequest

router = APIRouter(tags=["crawlers"])


@router.post(
    "/crawl",
    response_model=CrawlJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a website crawl",
)
async def request_crawl(
    body: RequestCrawlRequest,
    use_case: Annotated[RequestCrawl, Depends(get_request_crawl)],
) -> CrawlJobResponse:
    """Enqueue a crawl job for a known company domain (returns 202, does not block)."""
    dto = use_case.execute(RequestCrawlCommand(hostname=body.hostname))
    return CrawlJobResponse.from_dto(dto)


@router.get(
    "/crawlers/jobs",
    response_model=PageResponse[CrawlJobResponse],
    summary="List crawl jobs",
)
async def list_crawl_jobs(
    use_case: Annotated[ListCrawlJobs, Depends(get_list_crawl_jobs)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 25,
    job_status: Annotated[CrawlJobStatus | None, Query(alias="status")] = None,
) -> PageResponse[CrawlJobResponse]:
    """Return a paginated list of crawl jobs, optionally filtered by status."""
    result = use_case.execute(PageRequest(page=page, page_size=page_size), job_status)
    return PageResponse[CrawlJobResponse](
        items=[CrawlJobResponse.from_dto(j) for j in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
    )


@router.get(
    "/crawlers/jobs/{job_id}",
    response_model=CrawlJobDetailResponse,
    summary="Get a crawl job with its pages",
)
async def get_crawl_job(
    job_id: int,
    use_case: Annotated[GetCrawlJob, Depends(get_get_crawl_job)],
) -> CrawlJobDetailResponse:
    """Return a crawl job and the pages it produced, or 404 if it does not exist."""
    detail = use_case.execute(job_id)
    base = CrawlJobResponse.from_dto(detail.job)
    return CrawlJobDetailResponse(
        **base.model_dump(),
        pages=[CrawledPageResponse.from_dto(p) for p in detail.pages],
    )
