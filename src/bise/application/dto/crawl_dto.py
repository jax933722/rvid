"""DTOs for the crawler engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RequestCrawlCommand:
    """Input: request a website crawl for a company's domain."""

    hostname: str


@dataclass(frozen=True, slots=True)
class CrawledPageDTO:
    """Output: a page recorded during a crawl."""

    id: int | None
    url: str
    page_type: str
    http_status: int
    content_type: str | None
    title: str | None
    fetched_at: datetime


@dataclass(frozen=True, slots=True)
class CrawlJobDTO:
    """Output: a crawl job's state."""

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
