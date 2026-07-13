"""Use case: scan a company's homepage SEO from its stored pages.

Analyzes the crawled homepage (the primary domain's HOME page, or the first
stored page), scores it deterministically, optionally attaches Core Web Vitals
from a pluggable provider, and persists one profile per company.
"""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.seo_dto import SeoProfileDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import seo_profile_to_dto
from bise.application.ports.page_content import PageContent
from bise.application.ports.page_speed import PageSpeedPort
from bise.application.ports.seo_analyzer import SeoAnalyzerPort
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.company import Company
from bise.domain.entities.crawled_page import CrawledPage, PageType
from bise.domain.entities.seo_profile import SeoProfile
from bise.domain.services.seo_scoring import compute_seo_score

logger = get_logger(__name__)


class RunSeoScan:
    """Analyze, score, and persist a company's SEO profile."""

    def __init__(
        self,
        uow: UnitOfWork,
        analyzer: SeoAnalyzerPort,
        page_speed: PageSpeedPort,
    ) -> None:
        self._uow = uow
        self._analyzer = analyzer
        self._page_speed = page_speed

    def execute(self, company_id: int) -> SeoProfileDTO:
        with self._uow as uow:
            company = uow.companies.get(company_id)
            if company is None:
                raise NotFoundError(f"Company not found: {company_id}")

            page = self._select_homepage(uow, company)
            if page is None:
                raise NotFoundError(f"No crawled pages to analyze for company {company_id}")

            signals = self._analyzer.analyze(
                PageContent(url=page.url, html=page.html or "", headers=page.headers)
            )
            score = compute_seo_score(signals)
            metrics = self._page_speed.get_metrics(page.url)

            profile = SeoProfile(
                company_id=company_id,
                signals=signals,
                score=score,
                cwv_lcp_ms=metrics.lcp_ms if metrics else None,
                cwv_cls=metrics.cls if metrics else None,
                cwv_inp_ms=metrics.inp_ms if metrics else None,
            )
            saved = uow.seo_profiles.upsert(profile)
            uow.commit()

        logger.info("seo.scanned", company_id=company_id, score=score, grade=saved.grade)
        return seo_profile_to_dto(saved)

    @staticmethod
    def _select_homepage(uow: UnitOfWork, company: Company) -> CrawledPage | None:
        pages: list[CrawledPage] = []
        for domain in company.domains:
            if domain.id is not None:
                pages.extend(uow.crawled_pages.list_for_domain(domain.id))
        if not pages:
            return None
        home = next((p for p in pages if p.page_type is PageType.HOME and p.html), None)
        return home or next((p for p in pages if p.html), pages[0])
