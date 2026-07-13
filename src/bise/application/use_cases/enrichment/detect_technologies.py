"""Use case: detect technologies for a company from its stored pages.

Reads the pages captured by the Website Crawler (no re-fetching), runs the
detector, and replaces the company's technology detections idempotently.
"""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.technology_dto import CompanyTechnologyDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import company_technology_to_dto
from bise.application.ports.technology_detector import PageContent, TechnologyDetectorPort
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.technology import CompanyTechnology
from bise.domain.value_objects.confidence import Confidence

logger = get_logger(__name__)


class DetectTechnologies:
    """Detect and persist the technologies used by a company's website."""

    def __init__(self, uow: UnitOfWork, detector: TechnologyDetectorPort) -> None:
        self._uow = uow
        self._detector = detector

    def execute(self, company_id: int) -> list[CompanyTechnologyDTO]:
        with self._uow as uow:
            company = uow.companies.get(company_id)
            if company is None:
                raise NotFoundError(f"Company not found: {company_id}")

            pages: list[PageContent] = []
            for domain in company.domains:
                if domain.id is None:
                    continue
                for page in uow.crawled_pages.list_for_domain(domain.id):
                    pages.append(
                        PageContent(url=page.url, html=page.html or "", headers=page.headers)
                    )

            detections = self._detector.detect(pages)
            links: list[CompanyTechnology] = []
            for det in detections:
                technology = uow.technologies.get_or_create(det.name, det.category)
                assert technology.id is not None
                links.append(
                    CompanyTechnology(
                        company_id=company_id,
                        technology_id=technology.id,
                        confidence=Confidence(det.confidence),
                        evidence=det.evidence,
                        version=det.version,
                        technology=technology,
                    )
                )
            uow.company_technologies.replace_for_company(company_id, links)
            uow.commit()

        logger.info("technologies.detected", company_id=company_id, count=len(links))
        return [company_technology_to_dto(link) for link in links]
