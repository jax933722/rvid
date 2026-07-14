"""Use case: (re)build a company's search projection from normalized truth.

Reads the company, its detected technologies, SEO profile, and crawled page
types, assembles a :class:`SearchDocument`, and upserts it into the search index.
Idempotent — safe to run after any enrichment step.
"""

from __future__ import annotations

from config.logging import get_logger

from bise.application.errors import NotFoundError
from bise.application.ports.search import SearchIndexPort
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.company import Company
from bise.domain.entities.crawled_page import PageType
from bise.domain.entities.search_document import SearchDocument
from bise.domain.entities.seo_profile import SeoProfile

logger = get_logger(__name__)


class RebuildSearchDocument:
    """Assemble and index one company's searchable projection."""

    def __init__(self, uow: UnitOfWork, search_index: SearchIndexPort) -> None:
        self._uow = uow
        self._search_index = search_index

    def execute(self, company_id: int) -> None:
        with self._uow as uow:
            company = uow.companies.get(company_id)
            if company is None:
                raise NotFoundError(f"Company not found: {company_id}")

            technologies = [
                link.technology.name
                for link in uow.company_technologies.list_for_company(company_id)
                if link.technology is not None
            ]
            seo = uow.seo_profiles.get_for_company(company_id)
            page_types = self._page_types(uow, company)
            document = self._build(company, technologies, seo, page_types)

        # Indexing happens outside the read transaction (own session in the adapter).
        self._search_index.upsert(document)
        logger.info("search.indexed", company_id=company_id, technologies=len(technologies))

    @staticmethod
    def _page_types(uow: UnitOfWork, company: Company) -> set[PageType]:
        types: set[PageType] = set()
        for domain in company.domains:
            if domain.id is not None:
                types.update(p.page_type for p in uow.crawled_pages.list_for_domain(domain.id))
        return types

    @staticmethod
    def _build(
        company: Company,
        technologies: list[str],
        seo: SeoProfile | None,
        page_types: set[PageType],
    ) -> SearchDocument:
        assert company.id is not None
        primary = company.primary_domain.hostname if company.primary_domain else None
        has_ssl = bool(seo and seo.signals.has_ssl)
        seo_score = seo.score if seo else None
        seo_grade = seo.grade if seo else None
        text_parts = [company.display_name, company.industry or "", *technologies]

        return SearchDocument(
            company_id=company.id,
            display_name=company.display_name,
            primary_domain=primary,
            industry=company.industry,
            country=company.country,
            state=company.state,
            city=company.city,
            size_bucket=company.size_bucket,
            founded_year=company.founded_year,
            employee_count=company.employee_count,
            seo_score=seo_score,
            seo_grade=seo_grade,
            technologies=technologies,
            has_ssl=has_ssl,
            has_contact_page=PageType.CONTACT in page_types,
            has_careers_page=PageType.CAREERS in page_types,
            has_blog=PageType.BLOG in page_types,
            has_privacy=PageType.PRIVACY in page_types,
            has_terms=PageType.TERMS in page_types,
            text_blob=" ".join(part for part in text_parts if part).lower(),
        )
