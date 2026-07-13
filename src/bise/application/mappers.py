"""Mapping between domain entities and application DTOs."""

from __future__ import annotations

from bise.application.dto.company_dto import CompanyDTO, DomainDTO
from bise.application.dto.crawl_dto import CrawledPageDTO, CrawlJobDTO
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage


def company_to_dto(company: Company) -> CompanyDTO:
    """Convert a :class:`Company` aggregate into its boundary DTO."""
    return CompanyDTO(
        id=company.id,
        display_name=company.display_name,
        legal_name=company.legal_name,
        status=company.status.value,
        industry=company.industry,
        size_bucket=company.size_bucket,
        domains=tuple(
            DomainDTO(
                id=d.id,
                hostname=d.hostname,
                is_primary=d.is_primary,
                crawl_status=d.crawl_status.value,
            )
            for d in company.domains
        ),
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def crawl_job_to_dto(job: CrawlJob) -> CrawlJobDTO:
    """Convert a :class:`CrawlJob` entity into its boundary DTO."""
    return CrawlJobDTO(
        id=job.id,
        domain_id=job.domain_id,
        hostname=job.hostname,
        job_type=job.job_type.value,
        status=job.status.value,
        attempts=job.attempts,
        pages_crawled=job.pages_crawled,
        error=job.error,
        started_at=job.started_at,
        finished_at=job.finished_at,
        created_at=job.created_at,
    )


def crawled_page_to_dto(page: CrawledPage) -> CrawledPageDTO:
    """Convert a :class:`CrawledPage` entity into its boundary DTO."""
    return CrawledPageDTO(
        id=page.id,
        url=page.url,
        page_type=page.page_type.value,
        http_status=page.http_status,
        content_type=page.content_type,
        title=page.title,
        fetched_at=page.fetched_at,
    )
