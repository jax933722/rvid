"""Mapping between domain entities and application DTOs."""

from __future__ import annotations

from bise.application.dto.company_dto import CompanyDTO, DomainDTO
from bise.domain.entities.company import Company


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
