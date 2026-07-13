"""Request/response schemas for the crawler API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from bise.application.dto.crawl_dto import CrawledPageDTO, CrawlJobDTO


class RequestCrawlRequest(BaseModel):
    """Request body for ``POST /crawl``."""

    hostname: str = Field(..., examples=["acme.com"])


class CrawlJobResponse(BaseModel):
    """A crawl job's state."""

    id: int | None
    domain_id: int
    hostname: str
    job_type: str
    status: str
    attempts: int
    pages_crawled: int
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    @classmethod
    def from_dto(cls, dto: CrawlJobDTO) -> CrawlJobResponse:
        return cls(
            id=dto.id,
            domain_id=dto.domain_id,
            hostname=dto.hostname,
            job_type=dto.job_type,
            status=dto.status,
            attempts=dto.attempts,
            pages_crawled=dto.pages_crawled,
            error=dto.error,
            started_at=dto.started_at,
            finished_at=dto.finished_at,
            created_at=dto.created_at,
        )


class CrawledPageResponse(BaseModel):
    """A page recorded during a crawl."""

    id: int | None
    url: str
    page_type: str
    http_status: int
    content_type: str | None
    title: str | None
    fetched_at: datetime

    @classmethod
    def from_dto(cls, dto: CrawledPageDTO) -> CrawledPageResponse:
        return cls(
            id=dto.id,
            url=dto.url,
            page_type=dto.page_type,
            http_status=dto.http_status,
            content_type=dto.content_type,
            title=dto.title,
            fetched_at=dto.fetched_at,
        )


class CrawlJobDetailResponse(CrawlJobResponse):
    """A crawl job plus the pages it produced."""

    pages: list[CrawledPageResponse] = Field(default_factory=list)
