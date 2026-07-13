"""Use case: fetch a single company by id."""

from __future__ import annotations

from bise.application.dto.company_dto import CompanyDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import company_to_dto
from bise.application.ports.unit_of_work import UnitOfWork


class GetCompany:
    """Return one company's detail view, or raise :class:`NotFoundError`."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, company_id: int) -> CompanyDTO:
        with self._uow as uow:
            company = uow.companies.get(company_id)
        if company is None:
            raise NotFoundError(f"Company not found: {company_id}")
        return company_to_dto(company)
