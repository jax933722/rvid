"""Mapping between domain entities and application DTOs."""

from __future__ import annotations

from bise.application.dto.company_dto import CompanyDTO, DomainDTO
from bise.application.dto.crawl_dto import CrawledPageDTO, CrawlJobDTO
from bise.application.dto.seo_dto import SeoProfileDTO
from bise.application.dto.technology_dto import CompanyTechnologyDTO, TechnologyDTO
from bise.domain.entities.company import Company
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage
from bise.domain.entities.seo_profile import SeoProfile
from bise.domain.entities.technology import CompanyTechnology, Technology


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


def technology_to_dto(technology: Technology) -> TechnologyDTO:
    """Convert a :class:`Technology` entity into its boundary DTO."""
    return TechnologyDTO(
        id=technology.id,
        name=technology.name,
        category=technology.category,
        vendor=technology.vendor,
    )


def seo_profile_to_dto(profile: SeoProfile) -> SeoProfileDTO:
    """Convert a :class:`SeoProfile` entity into its boundary DTO."""
    s = profile.signals
    return SeoProfileDTO(
        url=s.url,
        score=profile.score,
        grade=profile.grade,
        title=s.title,
        meta_description=s.meta_description,
        canonical=s.canonical,
        meta_robots=s.meta_robots,
        is_indexable=s.is_indexable,
        h1_count=s.h1_count,
        h2_count=s.h2_count,
        has_open_graph=s.has_open_graph,
        has_twitter_card=s.has_twitter_card,
        has_structured_data=s.has_structured_data,
        has_ssl=s.has_ssl,
        images_total=s.images_total,
        images_missing_alt=s.images_missing_alt,
        internal_links=s.internal_links,
        external_links=s.external_links,
        word_count=s.word_count,
        cwv_lcp_ms=profile.cwv_lcp_ms,
        cwv_cls=profile.cwv_cls,
        cwv_inp_ms=profile.cwv_inp_ms,
        scanned_at=profile.scanned_at,
    )


def company_technology_to_dto(link: CompanyTechnology) -> CompanyTechnologyDTO:
    """Convert a :class:`CompanyTechnology` entity into its boundary DTO."""
    name = link.technology.name if link.technology is not None else ""
    category = link.technology.category if link.technology is not None else ""
    return CompanyTechnologyDTO(
        name=name,
        category=category,
        confidence=float(link.confidence),
        evidence=link.evidence,
        version=link.version,
        detected_at=link.detected_at,
    )
