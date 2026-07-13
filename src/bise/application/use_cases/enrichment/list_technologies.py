"""Use case: list the catalog of known technologies (facet source)."""

from __future__ import annotations

from bise.application.dto.technology_dto import TechnologyDTO
from bise.application.mappers import technology_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.shared.pagination import Page, PageRequest


class ListTechnologies:
    """Return a page of known technologies (used by the search filter panel)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, page: PageRequest) -> Page[TechnologyDTO]:
        with self._uow as uow:
            result = uow.technologies.list(page)
        return Page(
            items=[technology_to_dto(t) for t in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
