"""Use case: detect marketing tools for a company from its stored pages."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.marketing_dto import MarketingSignalDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import marketing_signal_to_dto
from bise.application.ports.marketing_detector import MarketingDetectorPort
from bise.application.ports.page_content import PageContent
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.marketing_signal import MarketingSignal

logger = get_logger(__name__)


class DetectMarketing:
    """Detect and persist the marketing tools used by a company's website."""

    def __init__(self, uow: UnitOfWork, detector: MarketingDetectorPort) -> None:
        self._uow = uow
        self._detector = detector

    def execute(self, company_id: int) -> list[MarketingSignalDTO]:
        with self._uow as uow:
            company = uow.companies.get(company_id)
            if company is None:
                raise NotFoundError(f"Company not found: {company_id}")

            pages: list[PageContent] = []
            for domain in company.domains:
                if domain.id is None:
                    continue
                for page in uow.crawled_pages.list_for_domain(domain.id):
                    pages.append(PageContent(url=page.url, html=page.html or ""))

            detections = self._detector.detect(pages)
            signals = [
                MarketingSignal(
                    company_id=company_id,
                    tool_name=d.tool_name,
                    category=d.category,
                    evidence=d.evidence,
                )
                for d in detections
            ]
            uow.marketing_signals.replace_for_company(company_id, signals)
            uow.commit()

        logger.info("marketing.detected", company_id=company_id, count=len(signals))
        return [marketing_signal_to_dto(s) for s in signals]
