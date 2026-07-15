"""Mapping between domain entities and application DTOs."""

from __future__ import annotations

from bise.application.dto.auth_dto import ApiKeyDTO, WorkspaceDTO
from bise.application.dto.company_dto import CompanyDTO, DomainDTO
from bise.application.dto.crawl_dto import CrawledPageDTO, CrawlJobDTO
from bise.application.dto.enrichment_dto import EnrichmentJobDTO
from bise.application.dto.marketing_dto import MarketingSignalDTO
from bise.application.dto.person_dto import PersonDTO
from bise.application.dto.seo_dto import SeoProfileDTO
from bise.application.dto.technology_dto import CompanyTechnologyDTO, TechnologyDTO
from bise.application.dto.workspace_dto import CompanyListDTO, CompanyTagDTO, SavedSearchDTO
from bise.domain.entities.api_key import ApiKey
from bise.domain.entities.company import Company
from bise.domain.entities.company_list import CompanyList
from bise.domain.entities.company_tag import CompanyTag
from bise.domain.entities.crawl_job import CrawlJob
from bise.domain.entities.crawled_page import CrawledPage
from bise.domain.entities.enrichment_job import EnrichmentJob
from bise.domain.entities.marketing_signal import MarketingSignal
from bise.domain.entities.person import Person
from bise.domain.entities.saved_search import SavedSearch
from bise.domain.entities.seo_profile import SeoProfile
from bise.domain.entities.technology import CompanyTechnology, Technology
from bise.domain.entities.workspace import Workspace


def company_to_dto(company: Company) -> CompanyDTO:
    """Convert a :class:`Company` aggregate into its boundary DTO."""
    return CompanyDTO(
        id=company.id,
        display_name=company.display_name,
        legal_name=company.legal_name,
        status=company.status.value,
        industry=company.industry,
        size_bucket=company.size_bucket,
        country=company.country,
        state=company.state,
        city=company.city,
        founded_year=company.founded_year,
        employee_count=company.employee_count,
        contact_email=company.contact_email,
        contact_phone=company.contact_phone,
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


def marketing_signal_to_dto(signal: MarketingSignal) -> MarketingSignalDTO:
    """Convert a :class:`MarketingSignal` entity into its boundary DTO."""
    return MarketingSignalDTO(
        tool_name=signal.tool_name,
        category=signal.category,
        evidence=signal.evidence,
        detected_at=signal.detected_at,
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


def saved_search_to_dto(search: SavedSearch) -> SavedSearchDTO:
    """Convert a :class:`SavedSearch` entity into its boundary DTO."""
    return SavedSearchDTO(
        id=search.id,
        name=search.name,
        query_json=search.query_json,
        created_at=search.created_at,
        updated_at=search.updated_at,
    )


def company_list_to_dto(company_list: CompanyList) -> CompanyListDTO:
    """Convert a :class:`CompanyList` entity into its boundary DTO."""
    return CompanyListDTO(
        id=company_list.id,
        name=company_list.name,
        description=company_list.description,
        member_count=company_list.member_count,
        created_at=company_list.created_at,
        updated_at=company_list.updated_at,
    )


def company_tag_to_dto(tag: CompanyTag) -> CompanyTagDTO:
    """Convert a :class:`CompanyTag` entity into its boundary DTO."""
    return CompanyTagDTO(
        id=tag.id,
        company_id=tag.company_id,
        label=tag.label,
        created_at=tag.created_at,
    )


def enrichment_job_to_dto(job: EnrichmentJob) -> EnrichmentJobDTO:
    """Convert an :class:`EnrichmentJob` entity into its boundary DTO."""
    return EnrichmentJobDTO(
        id=job.id,
        company_id=job.company_id,
        status=job.status.value,
        attempts=job.attempts,
        error=job.error,
        started_at=job.started_at,
        finished_at=job.finished_at,
        created_at=job.created_at,
    )


def workspace_to_dto(workspace: Workspace) -> WorkspaceDTO:
    """Convert a :class:`Workspace` entity into its boundary DTO."""
    return WorkspaceDTO(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        created_at=workspace.created_at,
    )


def api_key_to_dto(api_key: ApiKey) -> ApiKeyDTO:
    """Convert an :class:`ApiKey` entity into its boundary DTO (no secret)."""
    return ApiKeyDTO(
        id=api_key.id,
        workspace_id=api_key.workspace_id,
        name=api_key.name,
        prefix=api_key.prefix,
        revoked=api_key.revoked,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
    )


def person_to_dto(person: Person) -> PersonDTO:
    """Convert a :class:`Person` entity into its boundary DTO."""
    return PersonDTO(
        id=person.id,
        company_id=person.company_id,
        name=person.name,
        title=person.title,
        role_category=person.role_category.value,
        email=person.email,
        email_status=person.email_status.value,
        source_url=person.source_url,
    )
