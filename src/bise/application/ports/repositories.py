"""Repository ports (interfaces) owned by the application layer.

Concrete implementations live in ``infrastructure/db/repositories``. Business
logic depends only on these abstractions (Dependency Inversion), which is what
makes persistence swappable and use cases unit-testable with in-memory fakes.
"""

from __future__ import annotations

from typing import Protocol

from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob, CrawlJobStatus
from bise.domain.entities.crawled_page import CrawledPage
from bise.domain.entities.website_domain import CrawlStatus
from bise.shared.pagination import Page, PageRequest


class CompanyRepository(Protocol):
    """Persistence operations for the :class:`Company` aggregate."""

    def add(self, company: Company) -> Company:
        """Persist a new company and return it with its assigned id."""
        ...

    def get(self, company_id: int) -> Company | None:
        """Return the company with the given id, or ``None`` if absent."""
        ...

    def find_by_hostname(self, hostname: str) -> Company | None:
        """Return the company owning the given domain hostname, if any."""
        ...

    def list(self, page: PageRequest) -> Page[Company]:
        """Return a page of companies ordered by creation time (newest first)."""
        ...

    def mark_domain_crawl_status(self, domain_id: int, status: CrawlStatus) -> None:
        """Update the crawl status of a single owned domain."""
        ...


class CrawlJobRepository(Protocol):
    """Persistence operations for :class:`CrawlJob`."""

    def add(self, job: CrawlJob) -> CrawlJob:
        """Persist a new crawl job and return it with its assigned id."""
        ...

    def get(self, job_id: int) -> CrawlJob | None:
        """Return the crawl job with the given id, or ``None`` if absent."""
        ...

    def update(self, job: CrawlJob) -> None:
        """Persist state changes to an existing crawl job."""
        ...

    def list(self, page: PageRequest, status: CrawlJobStatus | None = None) -> Page[CrawlJob]:
        """Return a page of crawl jobs, optionally filtered by status."""
        ...


class CrawledPageRepository(Protocol):
    """Persistence operations for :class:`CrawledPage`."""

    def add(self, page: CrawledPage) -> CrawledPage:
        """Persist a crawled page record and return it with its assigned id."""
        ...

    def list_for_job(self, crawl_job_id: int) -> list[CrawledPage]:
        """Return all pages recorded for a crawl job."""
        ...
