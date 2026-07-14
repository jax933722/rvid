"""Use cases for saved Prospector searches."""

from __future__ import annotations

from config.logging import get_logger

from bise.application.dto.workspace_dto import SavedSearchDTO
from bise.application.errors import NotFoundError
from bise.application.mappers import saved_search_to_dto
from bise.application.ports.unit_of_work import UnitOfWork
from bise.domain.entities.saved_search import SavedSearch

logger = get_logger(__name__)


class SaveSearch:
    """Persist a named Prospector search (opaque query payload)."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, name: str, query_json: str) -> SavedSearchDTO:
        search = SavedSearch(workspace_id=workspace_id, name=name, query_json=query_json)
        with self._uow as uow:
            saved = uow.saved_searches.add(search)
            uow.commit()
        logger.info("saved_search.created", saved_search_id=saved.id, name=saved.name)
        return saved_search_to_dto(saved)


class ListSavedSearches:
    """Return all saved searches, newest first."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int) -> list[SavedSearchDTO]:
        with self._uow as uow:
            searches = uow.saved_searches.list(workspace_id)
        return [saved_search_to_dto(s) for s in searches]


class DeleteSavedSearch:
    """Delete a saved search by id."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, workspace_id: int, search_id: int) -> None:
        with self._uow as uow:
            removed = uow.saved_searches.delete(workspace_id, search_id)
            if not removed:
                raise NotFoundError(f"Saved search not found: {search_id}")
            uow.commit()
        logger.info("saved_search.deleted", saved_search_id=search_id)
