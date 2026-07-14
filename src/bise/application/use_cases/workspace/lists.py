"""Use cases for company lists (scoped to a workspace; also bookmarking)."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.company_dto import CompanyDTO
from bise.application.dto.workspace_dto import CompanyListDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import company_list_to_dto, company_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.company_list import CompanyList

logger = get_logger(__name__)


class CreateCompanyList:
    """Create a new (empty) company list in a workspace."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self, workspace_id: int, name: str, description: str | None = None
    ) -> CompanyListDTO:
        company_list = CompanyList(workspace_id=workspace_id, name=name, description=description)
        with self._uow as uow:
            saved = uow.company_lists.add(company_list)
            uow.commit()
        logger.info("company_list.created", list_id=saved.id, name=saved.name)
        return company_list_to_dto(saved)


class ListCompanyLists:
    """Return a workspace's lists with their member counts, newest first."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int) -> list[CompanyListDTO]:
        with self._uow as uow:
            lists = uow.company_lists.list(workspace_id)
        return [company_list_to_dto(cl) for cl in lists]


class DeleteCompanyList:
    """Delete a workspace's list and its memberships."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, list_id: int) -> None:
        with self._uow as uow:
            removed = uow.company_lists.delete(workspace_id, list_id)
            if not removed:
                raise NotFoundError(f"List not found: {list_id}")
            uow.commit()
        logger.info("company_list.deleted", list_id=list_id)


class AddCompanyToList:
    """Add a company to a workspace's list (idempotent); returns updated count."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, list_id: int, company_id: int) -> CompanyListDTO:
        with self._uow as uow:
            company_list = uow.company_lists.get(workspace_id, list_id)
            if company_list is None:
                raise NotFoundError(f"List not found: {list_id}")
            if uow.companies.get(company_id) is None:
                raise NotFoundError(f"Company not found: {company_id}")
            added = uow.company_lists.add_company(list_id, company_id)
            uow.commit()
            refreshed = uow.company_lists.get(workspace_id, list_id)
        assert refreshed is not None
        logger.info("company_list.member_added", list_id=list_id, company_id=company_id, new=added)
        return company_list_to_dto(refreshed)


class RemoveCompanyFromList:
    """Remove a company from a workspace's list."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, list_id: int, company_id: int) -> None:
        with self._uow as uow:
            if uow.company_lists.get(workspace_id, list_id) is None:
                raise NotFoundError(f"List not found: {list_id}")
            uow.company_lists.remove_company(list_id, company_id)
            uow.commit()
        logger.info("company_list.member_removed", list_id=list_id, company_id=company_id)


class ListListMembers:
    """Return the companies belonging to a workspace's list."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, list_id: int) -> list[CompanyDTO]:
        with self._uow as uow:
            if uow.company_lists.get(workspace_id, list_id) is None:
                raise NotFoundError(f"List not found: {list_id}")
            members = uow.company_lists.list_members(list_id)
        return [company_to_dto(c) for c in members]
