"""Use cases for company tags."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.workspace_dto import CompanyTagDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import company_tag_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.company_tag import CompanyTag

logger = get_logger(__name__)


class AddCompanyTag:
    """Attach a normalized tag to a company (idempotent)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, company_id: int, label: str) -> CompanyTagDTO:
        with self._uow as uow:
            if uow.companies.get(company_id) is None:
                raise NotFoundError(f"Company not found: {company_id}")
            saved = uow.company_tags.add(CompanyTag(company_id=company_id, label=label))
            uow.commit()
        logger.info("company_tag.added", company_id=company_id, label=saved.label)
        return company_tag_to_dto(saved)


class RemoveCompanyTag:
    """Remove a tag from a company."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, company_id: int, label: str) -> None:
        with self._uow as uow:
            uow.company_tags.remove(company_id, label)
            uow.commit()
        logger.info("company_tag.removed", company_id=company_id, label=label)


class ListCompanyTags:
    """Return all tags on a company, ordered by label."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, company_id: int) -> list[CompanyTagDTO]:
        with self._uow as uow:
            tags = uow.company_tags.list_for_company(company_id)
        return [company_tag_to_dto(t) for t in tags]
