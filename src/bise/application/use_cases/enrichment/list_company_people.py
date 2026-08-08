"""Use case: list the people extracted for a company."""

from __future__ import annotations

from bise.application.dto.person_dto import PersonDTO
from bise.application.mappers import person_to_dto
from bise.application.ports.unit_of_work import UnitOfWork


class ListCompanyPeople:
    """Return a company's people, seniority first."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, company_id: int) -> list[PersonDTO]:
        with self._uow as uow:
            people = uow.people.list_for_company(company_id)
        return [person_to_dto(p) for p in people]
