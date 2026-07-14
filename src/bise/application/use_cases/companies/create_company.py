"""Use case: create a new company (with optional website domains)."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.company_dto import CompanyDTO, CreateCompanyCommand
from bise.application.errors import ConflictError
from bise.application.mappers import company_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.company import Company
from bise.domain.entities.website_domain import WebsiteDomain

logger = get_logger(__name__)


class CreateCompany:
    """Create and persist a company atomically within a Unit of Work."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CreateCompanyCommand) -> CompanyDTO:
        """Create the company, rejecting domains already owned by another company."""
        company = Company(
            display_name=command.display_name,
            legal_name=command.legal_name,
            industry=command.industry,
            size_bucket=command.size_bucket,
            country=command.country,
            state=command.state,
            city=command.city,
            founded_year=command.founded_year,
            employee_count=command.employee_count,
            contact_email=command.contact_email,
            contact_phone=command.contact_phone,
        )
        for d in command.domains:
            company.add_domain(WebsiteDomain(hostname=d.hostname, is_primary=d.is_primary))

        with self._uow as uow:
            for domain in company.domains:
                existing = uow.companies.find_by_hostname(domain.hostname)
                if existing is not None:
                    raise ConflictError(
                        f"Domain already owned by another company: {domain.hostname}"
                    )
            saved = uow.companies.add(company)
            uow.commit()

        logger.info("company.created", company_id=saved.id, display_name=saved.display_name)
        return company_to_dto(saved)
