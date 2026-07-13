"""Use case: list companies with pagination."""

from __future__ import annotations

from bise.application.dto.company_dto import CompanyDTO
from bise.application.mappers import company_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.shared.pagination import Page, PageRequest


class ListCompanies:
    """Return a page of company summaries (newest first)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, page: PageRequest) -> Page[CompanyDTO]:
        with self._uow as uow:
            result = uow.companies.list(page)
        return Page(
            items=[company_to_dto(c) for c in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
