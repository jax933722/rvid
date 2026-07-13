"""Use case: list the technologies detected for a company."""

from __future__ import annotations

from bise.application.dto.technology_dto import CompanyTechnologyDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import company_technology_to_dto
from bise.application.ports.unit_of_work import UnitOfWork


class ListCompanyTechnologies:
    """Return the technologies detected for a company."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, company_id: int) -> list[CompanyTechnologyDTO]:
        with self._uow as uow:
            if uow.companies.get(company_id) is None:
                raise NotFoundError(f"Company not found: {company_id}")
            links = uow.company_technologies.list_for_company(company_id)
        return [company_technology_to_dto(link) for link in links]
