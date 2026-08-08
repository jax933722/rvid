"""Use case: discover businesses online and save those with websites.

Queries a discovery source (OpenStreetMap by default), then upserts each
business that has a website as a Company (status=discovered) so it can be
enriched on demand. Businesses without a website are returned for display but
not saved (nothing to crawl).
"""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.discovery_dto import DiscoverCommand, DiscoveredBusinessDTO
from bise.application.ports.discovery import (
    DiscoveredBusiness,
    DiscoveryCriteria,
    DiscoverySourcePort,
)
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.company import Company
from bise.domain.entities.website_domain import WebsiteDomain

logger = get_logger(__name__)


class DiscoverBusinesses:
    """Discover businesses from a public source and persist the ones we can crawl."""

    def __init__(self, uow: UnitOfWork, source: DiscoverySourcePort) -> None:
        self._uow = uow
        self._source = source

    def execute(self, command: DiscoverCommand) -> list[DiscoveredBusinessDTO]:
        criteria = DiscoveryCriteria(
            category=command.category, location=command.location, limit=command.limit
        )
        found = self._source.discover(criteria)

        results: list[DiscoveredBusinessDTO] = []
        seen: set[str] = set()
        with self._uow as uow:
            for biz in found:
                company_id: int | None = None
                if biz.website and biz.website not in seen:
                    seen.add(biz.website)
                    existing = uow.companies.find_by_hostname(biz.website)
                    if existing is not None:
                        company_id = existing.id
                    else:
                        company = Company(
                            display_name=biz.name,
                            industry=biz.category,
                            country=biz.country,
                            state=biz.state,
                            city=biz.city,
                            contact_phone=biz.phone,
                        )
                        company.add_domain(WebsiteDomain(hostname=biz.website, is_primary=True))
                        saved = uow.companies.add(company)
                        company_id = saved.id
                results.append(self._to_dto(biz, company_id))
            uow.commit()

        saved_count = sum(1 for r in results if r.company_id is not None)
        logger.info(
            "discovery.completed",
            category=command.category,
            location=command.location,
            found=len(results),
            saved=saved_count,
        )
        return results

    @staticmethod
    def _to_dto(b: DiscoveredBusiness, company_id: int | None) -> DiscoveredBusinessDTO:
        return DiscoveredBusinessDTO(
            name=b.name,
            category=b.category,
            website=b.website,
            website_url=b.website_url,
            phone=b.phone,
            address=b.address,
            city=b.city,
            state=b.state,
            country=b.country,
            postal_code=b.postal_code,
            latitude=b.latitude,
            longitude=b.longitude,
            source_url=b.source_url,
            company_id=company_id,
        )
