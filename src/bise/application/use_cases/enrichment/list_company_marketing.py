"""Use case: list the marketing tools detected for a company."""

from __future__ import annotations

from bise.application.dto.marketing_dto import MarketingSignalDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import marketing_signal_to_dto
from bise.application.ports.unit_of_work import UnitOfWork


class ListCompanyMarketing:
    """Return the marketing tools detected for a company."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, company_id: int) -> list[MarketingSignalDTO]:
        with self._uow as uow:
            if uow.companies.get(company_id) is None:
                raise NotFoundError(f"Company not found: {company_id}")
            signals = uow.marketing_signals.list_for_company(company_id)
        return [marketing_signal_to_dto(s) for s in signals]
